"""
Shared FastAPI dependencies used by both main.py and EE routers.

Moved here to avoid circular imports between main.py and ee/routers/*.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select

from .db import get_db, AsyncSession, User, RolePermission, AuditLog, ServicePrincipal, UserApiKey
from .security import oauth2_scheme
from .auth import verify_password


class _SPUserProxy:
    """Makes a ServicePrincipal quack like a User for permission checks and auditing."""
    def __init__(self, sp: ServicePrincipal):
        self.username = f"sp:{sp.name}"
        self.role = sp.role
        self.token_version = 0
        self.must_change_password = False
        self._sp = sp


async def _authenticate_api_key(raw_key: str, db: AsyncSession):
    """Authenticate using a personal API key (mop_...). Returns the owning User."""
    prefix = raw_key[:12]
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.key_prefix == prefix)
    )
    candidates = result.scalars().all()

    for candidate in candidates:
        if verify_password(raw_key, candidate.key_hash):
            if candidate.expires_at and candidate.expires_at < datetime.utcnow():
                raise HTTPException(401, "API key has expired")
            candidate.last_used_at = datetime.utcnow()
            await db.commit()
            user_result = await db.execute(
                select(User).where(User.username == candidate.username)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(401, "User account not found")
            return user

    raise HTTPException(401, "Invalid API key")


async def _authenticate_sp_jwt(payload: dict, db: AsyncSession):
    """Authenticate a service principal JWT. Returns an _SPUserProxy."""
    sp_id = payload.get("sp_id")
    if not sp_id:
        raise HTTPException(401, "Invalid service principal token")

    result = await db.execute(
        select(ServicePrincipal).where(ServicePrincipal.id == sp_id)
    )
    sp = result.scalar_one_or_none()

    if not sp or not sp.is_active:
        raise HTTPException(401, "Service principal not found or disabled")

    if sp.expires_at and sp.expires_at < datetime.utcnow():
        raise HTTPException(401, "Service principal has expired")

    return _SPUserProxy(sp)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """JWT / API key / SP token auth."""
    # API key authentication
    if token.startswith("mop_"):
        return await _authenticate_api_key(token, db)

    from jose import jwt, JWTError
    from .auth import SECRET_KEY, ALGORITHM
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception

    # Service principal JWT
    if payload.get("type") == "service_principal":
        return await _authenticate_sp_jwt(payload, db)

    # Regular user JWT
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    # Reject tokens issued before a password change (token_version mismatch)
    if payload.get("tv", 0) != user.token_version:
        raise credentials_exception
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optional JWT User Auth."""
    if not token:
        return None

    from jose import jwt, JWTError
    from .auth import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


_perm_cache: dict[str, set[str]] = {}


def _invalidate_perm_cache(role: str | None = None) -> None:
    """Clear cached permissions for a role (or all roles)."""
    if role:
        _perm_cache.pop(role, None)
    else:
        _perm_cache.clear()


def require_permission(perm: str):
    """Dependency factory that enforces a named permission via DB-backed RBAC."""
    async def _check(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        if current_user.role == "admin":
            return current_user
        if current_user.role not in _perm_cache:
            result = await db.execute(
                select(RolePermission.permission).where(RolePermission.role == current_user.role)
            )
            _perm_cache[current_user.role] = {row for row in result.scalars().all()}
        if perm not in _perm_cache[current_user.role]:
            raise HTTPException(status_code=403, detail=f"Missing permission: {perm}")
        return current_user
    return _check


def audit(db: AsyncSession, user, action: str, resource_id: str = None, detail: dict = None):
    """Append an audit entry to the current session. Caller must commit."""
    db.add(AuditLog(
        username=user.username,
        action=action,
        resource_id=resource_id,
        detail=json.dumps(detail) if detail else None,
    ))

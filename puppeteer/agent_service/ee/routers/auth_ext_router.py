"""EE Router: Auth extensions — user signing keys, API keys, service principals."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select

from ...db import (
    get_db, AsyncSession, User, Signature, AuditLog,
    UserSigningKey, UserApiKey, ServicePrincipal,
)
from ...deps import require_permission, get_current_user, audit
from ...auth import get_password_hash, verify_password, create_access_token
from ...security import cipher_suite
from ...models import (
    UserSigningKeyCreate, UserSigningKeyResponse, UserSigningKeyGeneratedResponse,
    UserApiKeyCreate, UserApiKeyResponse, UserApiKeyCreatedResponse,
    ServicePrincipalCreate, ServicePrincipalResponse, ServicePrincipalCreatedResponse,
    ServicePrincipalUpdate, ServicePrincipalTokenRequest, ServicePrincipalRotateResponse,
    ALLOWED_ROLES,
)

auth_ext_router = APIRouter()


# --- User Signing Keys ---

@auth_ext_router.post("/auth/me/signing-keys", tags=["Authentication"])
async def create_signing_key(
    req: UserSigningKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    key_id = str(uuid.uuid4())
    private_key_pem_str = None

    if req.public_key_pem:
        try:
            pub = serialization.load_pem_public_key(req.public_key_pem.encode())
            if not isinstance(pub, ed25519.Ed25519PublicKey):
                raise HTTPException(400, "Key must be Ed25519")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(400, "Invalid Ed25519 public key PEM")
        public_pem = req.public_key_pem
        encrypted_priv = None
    else:
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        private_key_pem_str = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ).decode()
        encrypted_priv = cipher_suite.encrypt(private_key_pem_str.encode()).decode()

    signing_key = UserSigningKey(
        id=key_id,
        username=current_user.username,
        name=req.name,
        public_key_pem=public_pem,
        encrypted_private_key=encrypted_priv,
    )
    db.add(signing_key)

    sig = Signature(
        id=str(uuid.uuid4()),
        name=f"{current_user.username}/{req.name}",
        public_key=public_pem,
        uploaded_by=current_user.username,
    )
    db.add(sig)

    audit(db, current_user, "user:signing_key_created", key_id, {"name": req.name})
    await db.commit()

    if private_key_pem_str:
        return UserSigningKeyGeneratedResponse(
            id=key_id, name=req.name, public_key_pem=public_pem,
            private_key_pem=private_key_pem_str, created_at=signing_key.created_at,
        )
    return UserSigningKeyResponse(
        id=key_id, name=req.name, public_key_pem=public_pem,
        created_at=signing_key.created_at,
    )


@auth_ext_router.get("/auth/me/signing-keys", response_model=list[UserSigningKeyResponse], tags=["Authentication"])
async def list_signing_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSigningKey).where(UserSigningKey.username == current_user.username)
    )
    return result.scalars().all()


@auth_ext_router.delete("/auth/me/signing-keys/{key_id}", tags=["Authentication"])
async def delete_signing_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSigningKey).where(
            UserSigningKey.id == key_id,
            UserSigningKey.username == current_user.username,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(404, "Signing key not found")

    sig_name = f"{current_user.username}/{key.name}"
    sig_result = await db.execute(
        select(Signature).where(Signature.name == sig_name)
    )
    sig = sig_result.scalar_one_or_none()
    if sig:
        await db.delete(sig)

    await db.delete(key)
    audit(db, current_user, "user:signing_key_deleted", key_id)
    await db.commit()
    return {"status": "deleted"}


# --- User API Keys ---

@auth_ext_router.post("/auth/me/api-keys", tags=["Authentication"])
async def create_api_key(
    req: UserApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import secrets as _secrets

    raw_key = "mop_" + _secrets.token_hex(24)
    key_hash = get_password_hash(raw_key)
    key_prefix = raw_key[:12]

    expires_at = None
    if req.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)

    api_key = UserApiKey(
        id=str(uuid.uuid4()),
        username=current_user.username,
        name=req.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        expires_at=expires_at,
    )
    db.add(api_key)
    audit(db, current_user, "user:api_key_created", api_key.id, {"name": req.name})
    await db.commit()

    return UserApiKeyCreatedResponse(
        id=api_key.id, name=api_key.name, key_prefix=key_prefix,
        raw_key=raw_key, expires_at=expires_at,
        last_used_at=None, created_at=api_key.created_at,
    )


@auth_ext_router.get("/auth/me/api-keys", response_model=list[UserApiKeyResponse], tags=["Authentication"])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApiKey).where(UserApiKey.username == current_user.username)
    )
    return result.scalars().all()


@auth_ext_router.delete("/auth/me/api-keys/{key_id}", tags=["Authentication"])
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserApiKey).where(
            UserApiKey.id == key_id,
            UserApiKey.username == current_user.username,
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(404, "API key not found")

    await db.delete(key)
    audit(db, current_user, "user:api_key_revoked", key_id)
    await db.commit()
    return {"status": "revoked"}


# --- Service Principals ---

@auth_ext_router.post("/admin/service-principals", tags=["Service Principals"])
async def create_service_principal(
    req: ServicePrincipalCreate,
    current_user: User = Depends(require_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    import secrets as _secrets

    client_id = "sp_" + uuid.uuid4().hex
    client_secret = "mop_sp_" + _secrets.token_hex(24)
    secret_hash = get_password_hash(client_secret)

    expires_at = None
    if req.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)

    sp = ServicePrincipal(
        id=str(uuid.uuid4()),
        name=req.name,
        description=req.description,
        role=req.role,
        client_id=client_id,
        client_secret_hash=secret_hash,
        is_active=True,
        created_by=current_user.username,
        expires_at=expires_at,
    )
    db.add(sp)
    audit(db, current_user, "sp:created", sp.id, {"name": sp.name, "role": sp.role})
    await db.commit()

    return ServicePrincipalCreatedResponse(
        id=sp.id, name=sp.name, description=sp.description, role=sp.role,
        client_id=client_id, client_secret=client_secret, is_active=True,
        created_by=current_user.username, expires_at=expires_at,
        created_at=sp.created_at,
    )


@auth_ext_router.get("/admin/service-principals", response_model=list[ServicePrincipalResponse], tags=["Service Principals"])
async def list_service_principals(
    current_user: User = Depends(require_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServicePrincipal))
    return result.scalars().all()


@auth_ext_router.patch("/admin/service-principals/{sp_id}", tags=["Service Principals"])
async def update_service_principal(
    sp_id: str,
    req: ServicePrincipalUpdate,
    current_user: User = Depends(require_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServicePrincipal).where(ServicePrincipal.id == sp_id))
    sp = result.scalar_one_or_none()
    if not sp:
        raise HTTPException(404, "Service principal not found")

    if req.name is not None:
        sp.name = req.name
    if req.description is not None:
        sp.description = req.description
    if req.role is not None:
        if req.role not in ALLOWED_ROLES:
            raise HTTPException(400, f"role must be one of {sorted(ALLOWED_ROLES)}")
        sp.role = req.role
    if req.is_active is not None:
        sp.is_active = req.is_active

    audit(db, current_user, "sp:updated", sp_id)
    await db.commit()

    return ServicePrincipalResponse.model_validate(sp)


@auth_ext_router.delete("/admin/service-principals/{sp_id}", tags=["Service Principals"])
async def delete_service_principal(
    sp_id: str,
    current_user: User = Depends(require_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ServicePrincipal).where(ServicePrincipal.id == sp_id))
    sp = result.scalar_one_or_none()
    if not sp:
        raise HTTPException(404, "Service principal not found")

    await db.delete(sp)
    audit(db, current_user, "sp:deleted", sp_id, {"name": sp.name})
    await db.commit()
    return {"status": "deleted"}


@auth_ext_router.post("/admin/service-principals/{sp_id}/rotate-secret", tags=["Service Principals"])
async def rotate_sp_secret(
    sp_id: str,
    current_user: User = Depends(require_permission("users:write")),
    db: AsyncSession = Depends(get_db),
):
    import secrets as _secrets

    result = await db.execute(select(ServicePrincipal).where(ServicePrincipal.id == sp_id))
    sp = result.scalar_one_or_none()
    if not sp:
        raise HTTPException(404, "Service principal not found")

    new_secret = "mop_sp_" + _secrets.token_hex(24)
    sp.client_secret_hash = get_password_hash(new_secret)

    audit(db, current_user, "sp:secret_rotated", sp_id, {"name": sp.name})
    await db.commit()

    return ServicePrincipalRotateResponse(
        client_id=sp.client_id,
        client_secret=new_secret,
    )

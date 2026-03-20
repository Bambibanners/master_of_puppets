"""EE Router: Audit Log."""
from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.future import select

from ...db import get_db, AsyncSession, AuditLog, User
from ...deps import require_permission

audit_router = APIRouter()


@audit_router.get("/admin/audit-log", tags=["Audit Log"])
async def get_audit_log(
    limit: int = 200,
    current_user: User = Depends(require_permission("users:write")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "username": r.username,
            "action": r.action,
            "resource_id": r.resource_id,
            "detail": json.loads(r.detail) if r.detail else None,
        }
        for r in rows
    ]

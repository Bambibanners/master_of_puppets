"""EE Router: Webhooks."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ...db import get_db, AsyncSession, User
from ...deps import require_permission
from ...models import WebhookCreate, WebhookResponse
from ...services.webhook_service import WebhookService

webhook_router = APIRouter()


@webhook_router.get("/api/webhooks", response_model=List[WebhookResponse], tags=["Alerts & Webhooks"])
async def list_webhooks(
    current_user: User = Depends(require_permission("webhooks:read")),
    db: AsyncSession = Depends(get_db)
):
    """List all registered outbound webhooks."""
    return await WebhookService.list_webhooks(db)


@webhook_router.post("/api/webhooks", response_model=WebhookResponse, tags=["Alerts & Webhooks"])
async def create_webhook(
    hook: WebhookCreate,
    current_user: User = Depends(require_permission("webhooks:write")),
    db: AsyncSession = Depends(get_db)
):
    """Register a new outbound webhook with a signed secret."""
    wh = await WebhookService.create_webhook(db, hook.url, hook.events)
    await db.commit()
    return wh


@webhook_router.delete("/api/webhooks/{webhook_id}", tags=["Alerts & Webhooks"])
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(require_permission("webhooks:write")),
    db: AsyncSession = Depends(get_db)
):
    """Remove a webhook."""
    success = await WebhookService.delete_webhook(db, webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.commit()
    return {"status": "deleted", "id": webhook_id}

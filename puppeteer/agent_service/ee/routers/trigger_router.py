"""EE Router: Automation Triggers."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from ...db import get_db, AsyncSession, User
from ...deps import require_permission
from ...models import TriggerCreate, TriggerResponse, TriggerUpdate
from ...services.trigger_service import trigger_service

trigger_router = APIRouter()


@trigger_router.post("/api/trigger/{slug}", tags=["Headless Automation"])
async def fire_automation_trigger(
    slug: str,
    request: Request,
    x_mop_trigger_key: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Headless endpoint for CI/CD pipelines to fire a job trigger.

    - **slug**: The unique URL slug for the trigger.
    - **X-MOP-Trigger-Key**: The secret token associated with this trigger.
    - **Body**: (Optional) JSON object containing variables to inject into the job payload.
    """
    payload_data = {}
    try:
        if await request.body():
            payload_data = await request.json()
    except:
        pass

    return await trigger_service.fire_trigger(slug, x_mop_trigger_key, payload_data, db)


@trigger_router.get("/api/admin/triggers", response_model=List[TriggerResponse], tags=["Headless Automation"])
async def list_automation_triggers(
    current_user: User = Depends(require_permission("foundry:read")),
    db: AsyncSession = Depends(get_db)
):
    """List all registered automation triggers (Admin Only)."""
    return await trigger_service.list_triggers(db)


@trigger_router.post("/api/admin/triggers", response_model=TriggerResponse, tags=["Headless Automation"])
async def register_automation_trigger(
    req: TriggerCreate,
    current_user: User = Depends(require_permission("foundry:write")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new URL slug and token for a specific job definition (Admin Only)."""
    return await trigger_service.create_trigger(req.name, req.slug, req.job_definition_id, db)


@trigger_router.delete("/api/admin/triggers/{id}", tags=["Headless Automation"])
async def remove_automation_trigger(
    id: str,
    current_user: User = Depends(require_permission("foundry:write")),
    db: AsyncSession = Depends(get_db)
):
    """Delete an automation trigger (Admin Only)."""
    success = await trigger_service.delete_trigger(id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return {"status": "deleted"}


@trigger_router.patch("/api/admin/triggers/{id}", response_model=TriggerResponse, tags=["Headless Automation"])
async def update_automation_trigger(
    id: str,
    req: TriggerUpdate,
    current_user: User = Depends(require_permission("foundry:write")),
    db: AsyncSession = Depends(get_db)
):
    """Toggle is_active or update name on an automation trigger (Admin Only)."""
    return await trigger_service.update_trigger(id, req.is_active, db)


@trigger_router.post("/api/admin/triggers/{id}/regenerate-token", response_model=TriggerResponse, tags=["Headless Automation"])
async def regenerate_trigger_token(
    id: str,
    current_user: User = Depends(require_permission("foundry:write")),
    db: AsyncSession = Depends(get_db)
):
    """Rotate the secret token for an automation trigger (Admin Only)."""
    return await trigger_service.regenerate_token(id, db)

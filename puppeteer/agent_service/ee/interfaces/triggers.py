from fastapi import APIRouter
from fastapi.responses import JSONResponse

triggers_stub_router = APIRouter(tags=["Triggers"])

_EE_RESPONSE = JSONResponse(
    status_code=402,
    content={"detail": "This feature requires Axiom Enterprise Edition. See https://axiom.run/enterprise"}
)


@triggers_stub_router.post("/api/trigger/{slug}")
async def trigger_fire(slug: str): return _EE_RESPONSE

@triggers_stub_router.get("/api/admin/triggers")
async def triggers_list(): return _EE_RESPONSE

@triggers_stub_router.post("/api/admin/triggers")
async def triggers_create(): return _EE_RESPONSE

@triggers_stub_router.get("/api/admin/triggers/{trigger_id}")
async def trigger_get(trigger_id: str): return _EE_RESPONSE

@triggers_stub_router.put("/api/admin/triggers/{trigger_id}")
async def trigger_put(trigger_id: str): return _EE_RESPONSE

@triggers_stub_router.delete("/api/admin/triggers/{trigger_id}")
async def trigger_delete(trigger_id: str): return _EE_RESPONSE

@triggers_stub_router.post("/api/admin/triggers/{trigger_id}/regenerate-token")
async def trigger_regenerate_token(trigger_id: str): return _EE_RESPONSE

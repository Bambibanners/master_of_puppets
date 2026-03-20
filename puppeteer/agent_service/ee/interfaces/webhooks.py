from fastapi import APIRouter
from fastapi.responses import JSONResponse

webhooks_stub_router = APIRouter(tags=["Webhooks"])

_EE_RESPONSE = JSONResponse(
    status_code=402,
    content={"detail": "This feature requires Axiom Enterprise Edition. See https://axiom.run/enterprise"}
)


@webhooks_stub_router.get("/api/webhooks")
async def webhooks_get(): return _EE_RESPONSE

@webhooks_stub_router.post("/api/webhooks")
async def webhooks_post(): return _EE_RESPONSE

@webhooks_stub_router.get("/api/webhooks/{webhook_id}")
async def webhook_get(webhook_id: str): return _EE_RESPONSE

@webhooks_stub_router.put("/api/webhooks/{webhook_id}")
async def webhook_put(webhook_id: str): return _EE_RESPONSE

@webhooks_stub_router.delete("/api/webhooks/{webhook_id}")
async def webhook_delete(webhook_id: str): return _EE_RESPONSE

from fastapi import APIRouter
from fastapi.responses import JSONResponse

audit_stub_router = APIRouter(tags=["Audit"])

_EE_RESPONSE = JSONResponse(
    status_code=402,
    content={"detail": "This feature requires Axiom Enterprise Edition. See https://axiom.run/enterprise"}
)


@audit_stub_router.get("/admin/audit-log")
async def audit_log_get(): return _EE_RESPONSE

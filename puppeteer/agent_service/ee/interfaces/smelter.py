from fastapi import APIRouter
from fastapi.responses import JSONResponse

smelter_stub_router = APIRouter(tags=["Smelter"])

_EE_RESPONSE = JSONResponse(
    status_code=402,
    content={"detail": "This feature requires Axiom Enterprise Edition. See https://axiom.run/enterprise"}
)


@smelter_stub_router.get("/api/smelter/ingredients")
async def smelter_ingredients_get(): return _EE_RESPONSE

@smelter_stub_router.post("/api/smelter/ingredients")
async def smelter_ingredients_post(): return _EE_RESPONSE

@smelter_stub_router.get("/api/smelter/ingredients/{ingredient_id}")
async def smelter_ingredient_get(ingredient_id: str): return _EE_RESPONSE

@smelter_stub_router.put("/api/smelter/ingredients/{ingredient_id}")
async def smelter_ingredient_put(ingredient_id: str): return _EE_RESPONSE

@smelter_stub_router.delete("/api/smelter/ingredients/{ingredient_id}")
async def smelter_ingredient_delete(ingredient_id: str): return _EE_RESPONSE

@smelter_stub_router.post("/api/smelter/ingredients/{ingredient_id}/upload")
async def smelter_ingredient_upload(ingredient_id: str): return _EE_RESPONSE

@smelter_stub_router.post("/api/smelter/scan")
async def smelter_scan(): return _EE_RESPONSE

@smelter_stub_router.get("/api/smelter/config")
async def smelter_config_get(): return _EE_RESPONSE

@smelter_stub_router.put("/api/smelter/config")
async def smelter_config_put(): return _EE_RESPONSE

@smelter_stub_router.get("/api/smelter/mirror-health")
async def smelter_mirror_health(): return _EE_RESPONSE

@smelter_stub_router.get("/api/admin/mirror-config")
async def admin_mirror_config_get(): return _EE_RESPONSE

@smelter_stub_router.put("/api/admin/mirror-config")
async def admin_mirror_config_put(): return _EE_RESPONSE

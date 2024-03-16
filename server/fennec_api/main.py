from fastapi import FastAPI, APIRouter
from fennec_api.core.config import settings
from fennec_api.health.router import router as health_router
from fennec_api.auth.router import router as auth_router
from fennec_api.users.router import router as users_router

app = FastAPI()

router = APIRouter(prefix=settings.API_V1_PREFIX)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)

app.include_router(router)

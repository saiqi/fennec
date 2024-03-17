from fastapi import FastAPI, APIRouter
import sentry_sdk
from fennec_api.core.config import settings
from fennec_api.health.router import router as health_router
from fennec_api.auth.router import router as auth_router
from fennec_api.users.router import router as users_router


sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=settings.ENVIRONMENT,
)

app = FastAPI()

router = APIRouter(prefix=settings.API_V1_PREFIX)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)

app.include_router(router)

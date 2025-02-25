from fastapi import FastAPI, APIRouter
import sentry_sdk
from fennec_auth.config import settings
from fennec_auth.routers import auth_router


sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=settings.ENVIRONMENT,
)

app = FastAPI()

router_v1 = APIRouter(prefix=settings.API_V1_PREFIX)
router_v1.include_router(auth_router)

app.include_router(router_v1)

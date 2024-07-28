from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from arq import create_pool
import sentry_sdk
from fennec_api.core.config import settings
from fennec_api.core.arq import redis_settings
from fennec_api.core import queue
from fennec_api.health.router import router as health_router
from fennec_api.auth.router import router as auth_router
from fennec_api.users.router import router as users_router


sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=settings.ENVIRONMENT,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    queue.pool = await create_pool(redis_settings)
    yield
    await queue.pool.aclose()  # pyright: ignore


app = FastAPI(lifespan=lifespan)

router = APIRouter(prefix=settings.API_V1_PREFIX)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)

app.include_router(router)

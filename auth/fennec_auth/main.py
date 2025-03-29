from fastapi import FastAPI, APIRouter, Request, HTTPException, status
import sentry_sdk
from fennec_auth.config import settings
from fennec_auth.routers import auth_router, group_router, user_router
from fennec_auth.exceptions import GroupNotFound, AlreadyRegisteredGroup

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=settings.ENVIRONMENT,
)

app = FastAPI()


@app.exception_handler(GroupNotFound)
async def group_not_found_exception_handler(
    request: Request, exc: GroupNotFound
) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{exc.group_name} not found",
    )


@app.exception_handler(AlreadyRegisteredGroup)
async def already_registered_group_exception_handler(
    request: Request, exc: AlreadyRegisteredGroup
) -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{exc.group_name} is already registered",
    )


router_v1 = APIRouter(prefix=settings.API_V1_PREFIX)
router_v1.include_router(auth_router)
router_v1.include_router(group_router)
router_v1.include_router(user_router)

app.include_router(router_v1)

from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_auth.schemas import Token, GroupOut, GroupCreate
from fennec_auth.dependencies import get_session, get_current_internal_client
import fennec_auth.services as services
from fennec_auth.models import User, ClientApplication


group_router = APIRouter(prefix="/groups", tags=["admin"])


not_enough_permission_error = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
)


@group_router.get("", response_model=list[GroupOut], status_code=status.HTTP_200_OK)
async def list_groups(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_client: Annotated[
        User | ClientApplication, Depends(get_current_internal_client)
    ],
) -> Any:
    if not services.check_self_permission(current_client, role="read"):
        raise not_enough_permission_error
    return await services.list_groups(session)


@group_router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_client: Annotated[
        User | ClientApplication, Depends(get_current_internal_client)
    ],
    group_data: Annotated[GroupCreate, Body(...)],
) -> Any:
    if not services.check_self_permission(current_client, role="admin"):
        raise not_enough_permission_error
    return await services.create_group(session, group_data)


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/token", response_model=Token, status_code=status.HTTP_201_CREATED)
async def login_for_access_token(
    session: Annotated[AsyncSession, Depends(get_session)],
    grant_type: Annotated[str, Form(pattern=r"^password$|^client_credentials$")],
    client_id: Annotated[str, Form(...)],
    client_secret: Annotated[str, Form(...)],
    scopes: Annotated[
        str,
        Form(
            pattern=r"^[0-9a-zA-Z\-_]+:(read|write|admin)( [0-9a-zA-Z\-_]+:(read|write|admin))*$"
        ),
    ],
    username: Annotated[str | None, Form(...)] = None,
    password: Annotated[str | None, Form(...)] = None,
) -> Any:
    current_client: User | ClientApplication | None = None
    if grant_type == "password":
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing username or password",
            )
        current_client = await services.authenticate_user(
            session, user_name=username, password=password
        )
    else:
        current_client = await services.authenticate_client_application(
            session, client_id=client_id, client_secret=client_secret
        )

    if not current_client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not services.check_permissions(current_client, scopes=scopes.split(" ")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permission",
        )

    access_token = services.create_access_token(
        model=current_client, scopes=scopes.split(" ")
    )

    return {"access_token": access_token, "token_type": "bearer"}

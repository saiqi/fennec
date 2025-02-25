from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_auth.schemas import Token
from fennec_auth.dependencies import get_session
from fennec_auth.services import (
    authenticate_client_application,
    authenticate_user,
    check_permissions,
    create_access_token,
)
from fennec_auth.models import User, ClientApplication


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
        current_client = await authenticate_user(
            session, user_name=username, password=password
        )
    else:
        current_client = await authenticate_client_application(
            session, client_id=client_id, client_secret=client_secret
        )

    if not current_client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not check_permissions(current_client, scopes=scopes.split(" ")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permission",
        )

    access_token = create_access_token(model=current_client, scopes=scopes.split(" "))

    return {"access_token": access_token, "token_type": "bearer"}

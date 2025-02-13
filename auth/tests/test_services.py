from typing import AsyncGenerator
from unittest.mock import patch
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import fennec_auth.schemas as schemas
import fennec_auth.models as models
import fennec_auth.services as services
import fennec_auth.exceptions as exceptions
from fennec_auth.security import get_password_hash, verify_password


@pytest_asyncio.fixture()
async def existing_user(session: AsyncSession) -> AsyncGenerator[models.User, None]:
    user = models.User(
        first_name="Fleury",
        last_name="Dinallo",
        user_name="fleury",
        email="fleury@redstarfc.fr",
        role="read",
        password_hash=get_password_hash("password"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    yield user


@pytest_asyncio.fixture()
async def existing_group(session: AsyncSession) -> AsyncGenerator[models.Group, None]:
    group = models.Group(name="red-star")
    session.add(group)
    await session.commit()
    await session.refresh(group)
    yield group


@pytest_asyncio.fixture()
async def existing_client_application(
    session: AsyncSession,
) -> AsyncGenerator[models.ClientApplication, None]:
    client_application = models.ClientApplication(
        name="red-star-api",
        client_id="red-star-api",
        client_secret_hash=get_password_hash("secret"),
        is_active=True,
    )
    session.add(client_application)
    await session.commit()
    await session.refresh(client_application)
    yield client_application


@pytest_asyncio.fixture()
async def existing_alt_client_application(
    session: AsyncSession,
) -> AsyncGenerator[models.ClientApplication, None]:
    client_application = models.ClientApplication(
        name="red-star-auth",
        client_id="red-star-auth",
        client_secret_hash=get_password_hash("secret"),
        is_active=True,
    )
    session.add(client_application)
    await session.commit()
    await session.refresh(client_application)
    yield client_application


@pytest.mark.asyncio
async def test_list_groups(session: AsyncSession, existing_group: models.Group) -> None:
    groups = await services.list_groups(session)
    assert len(groups) == 1


@pytest.mark.asyncio
async def test_create_group_happy_path(session: AsyncSession) -> None:
    group_data = schemas.GroupCreate(name="besiktas")
    created_group = await services.create_group(session, group_data=group_data)

    db_result = await session.execute(
        select(models.Group).filter(models.Group.name == group_data.name)
    )
    db_group = db_result.scalar_one()
    assert db_group == created_group


@pytest.mark.asyncio
async def test_create_group_failed_when_name_exists(
    session: AsyncSession, existing_group: models.Group
) -> None:
    group_data = schemas.GroupCreate(name="red-star")
    with pytest.raises(exceptions.AlreadyRegisteredGroup):
        await services.create_group(session, group_data=group_data)


@pytest.mark.asyncio
async def test_list_users(session: AsyncSession, existing_user: models.User) -> None:
    users = await services.list_users(session)
    assert len(users) == 1


@pytest.mark.asyncio
async def test_create_user_happy_path(session: AsyncSession) -> None:
    user_data = schemas.UserCreate(
        first_name="Rino",
        last_name="Della Negra",
        user_name="rino",
        email="rino@redstarfc.fr",
        role="read",
    )
    with patch("fennec_auth.services.random_password") as random_password:
        random_password.return_value = "random"
        created_user = await services.create_user(session, user_data=user_data)
        assert created_user.is_active
        assert created_user.is_external_user
        assert created_user.has_temporary_password

        db_result = await session.execute(
            select(models.User).filter(models.User.id == created_user.id)
        )
        db_user = db_result.scalar_one()
        assert db_user.first_name == user_data.first_name
        assert db_user.last_name == user_data.last_name
        assert db_user.user_name == user_data.user_name
        assert db_user.email == user_data.email
        assert db_user.role == user_data.role
        assert verify_password(
            plain_password="random", hashed_password=db_user.password_hash
        )


@pytest.mark.asyncio
async def test_create_user_failed_when_email_exists(
    session: AsyncSession, existing_user: models.User
) -> None:
    user_data = schemas.UserCreate(
        first_name="Rino",
        last_name="Della Negra",
        user_name="rino",
        email="fleury@redstarfc.fr",
        role="read",
    )

    with pytest.raises(exceptions.AlreadyRegisteredUser):
        await services.create_user(session, user_data)


@pytest.mark.asyncio
async def test_create_user_failed_when_user_name_exists(
    session: AsyncSession, existing_user: models.User
) -> None:
    user_data = schemas.UserCreate(
        first_name="Rino",
        last_name="Della Negra",
        user_name="fleury",
        email="rino@redstarfc.fr",
        role="read",
    )

    with pytest.raises(exceptions.AlreadyRegisteredUser):
        await services.create_user(session, user_data)


@pytest.mark.asyncio
async def test_get_user_by_email(
    session: AsyncSession, existing_user: models.User
) -> None:
    fetched_user = await services.get_user_by_email(session, email=existing_user.email)
    assert fetched_user
    assert fetched_user.id == existing_user.id
    assert not await services.get_user_by_email(session, email="unknown@unknown.com")


@pytest.mark.asyncio
async def test_get_user_by_user_name(
    session: AsyncSession, existing_user: models.User
) -> None:
    fetched_user = await services.get_user_by_user_name(
        session, user_name=existing_user.user_name
    )
    assert fetched_user
    assert fetched_user.id == existing_user.id
    assert not await services.get_user_by_user_name(session, user_name="unknown")


@pytest.mark.asyncio
async def test_authenticate_user_happy_path(
    session: AsyncSession, existing_user: models.User
) -> None:
    authenticated_user = await services.authenticate_user(
        session, user_name=existing_user.user_name, password="password"
    )
    assert authenticated_user


@pytest.mark.asyncio
async def test_authenticate_user_failed_when_user_is_unknown(
    session: AsyncSession, existing_user: models.User
) -> None:
    assert not await services.authenticate_user(
        session, user_name="unknown", password="password"
    )


@pytest.mark.asyncio
async def test_authenticate_user_failed_when_password_mismatches(
    session: AsyncSession, existing_user: models.User
) -> None:
    assert not await services.authenticate_user(
        session, user_name=existing_user.user_name, password="wrongpassword"
    )


@pytest.mark.asyncio
async def test_update_user_groups_happy_path(
    session: AsyncSession, existing_user: models.User, existing_group: models.Group
) -> None:
    update_data = schemas.GroupUpdate(name=existing_group.name)
    updated_user = await services.update_groups(
        session, model=existing_user, update_data=update_data
    )
    assert updated_user.group_id == existing_group.id


@pytest.mark.asyncio
async def test_list_client_applications(
    session: AsyncSession, existing_client_application: models.ClientApplication
) -> None:
    client_applications = await services.list_client_applications(session)
    assert len(client_applications) == 1


@pytest.mark.asyncio
async def test_create_client_application_happy_path(session: AsyncSession) -> None:
    client_application_data = schemas.ClientApplicationCreate(name="besiktas-api")
    with patch("fennec_auth.services.random_client_secret") as random_client_secret:
        with patch("fennec_auth.services.random_client_id") as random_client_id:
            random_client_secret.return_value = "random"
            random_client_id.return_value = "besitkas-api"
            created_client_application = await services.create_client_application(
                session, client_application_data=client_application_data
            )

            db_result = await session.execute(
                select(models.ClientApplication).filter(
                    models.ClientApplication.name == client_application_data.name
                )
            )
            assert created_client_application.is_active

            db_client_application = db_result.scalar_one()
            assert db_client_application.name == client_application_data.name
            assert db_client_application.client_id == "besitkas-api"
            assert verify_password(
                plain_password="random",
                hashed_password=db_client_application.client_secret_hash,
            )


@pytest.mark.asyncio
async def test_create_client_application_failed_when_name_exists(
    session: AsyncSession, existing_client_application: models.ClientApplication
) -> None:
    client_application_data = schemas.ClientApplicationCreate(name="red-star-api")
    with pytest.raises(exceptions.AlreadyRegisteredClientApplication):
        await services.create_client_application(
            session, client_application_data=client_application_data
        )


@pytest.mark.asyncio
async def test_get_client_application_by_name(
    session: AsyncSession, existing_client_application: models.ClientApplication
) -> None:
    client_application = await services.get_client_application_by_name(
        session, name=existing_client_application.name
    )
    assert client_application


@pytest.mark.asyncio
async def test_authenticate_client_application_happy_path(
    session: AsyncSession, existing_client_application: models.ClientApplication
) -> None:
    authenticated_client_application = await services.authenticate_client_application(
        session, client_id=existing_client_application.client_id, client_secret="secret"
    )
    assert authenticated_client_application


@pytest.mark.asyncio
async def test_authenticate_client_application_failed_when_application_not_exists(
    session: AsyncSession,
) -> None:
    authenticated_client_application = await services.authenticate_client_application(
        session, client_id="unknown", client_secret="secret"
    )
    assert not authenticated_client_application


@pytest.mark.asyncio
async def test_authenticate_client_application_failed_when_secret_mismatches(
    session: AsyncSession, existing_client_application: models.ClientApplication
) -> None:
    authenticated_client_application = await services.authenticate_client_application(
        session,
        client_id=existing_client_application.client_id,
        client_secret="wrongsecret",
    )
    assert not authenticated_client_application


@pytest.mark.asyncio
async def test_update_user_groups_failed_when_group_not_exists(
    session: AsyncSession, existing_user: models.User
) -> None:
    update_data = schemas.GroupUpdate(name="unknown")
    with pytest.raises(exceptions.GroupNotFound):
        await services.update_groups(
            session, model=existing_user, update_data=update_data
        )


@pytest.mark.asyncio
async def test_update_user_status(
    session: AsyncSession, existing_user: models.User
) -> None:
    update_data = schemas.ActiveStatusUpdate(is_active=False)
    updated_user = await services.update_active_status(
        session, model=existing_user, update_data=update_data
    )
    assert not updated_user.is_active


@pytest.mark.asyncio
async def test_update_client_application_status(
    session: AsyncSession, existing_client_application: models.ClientApplication
) -> None:
    update_data = schemas.ActiveStatusUpdate(is_active=False)
    updated_client_application = await services.update_active_status(
        session, model=existing_client_application, update_data=update_data
    )
    assert not updated_client_application.is_active


@pytest.mark.asyncio
async def test_update_user_password(
    session: AsyncSession, existing_user: models.User
) -> None:
    update_data = schemas.PasswordUpdate(password="newpassword")
    updated_user = await services.update_user_password(
        session, user=existing_user, update_data=update_data
    )
    assert verify_password(
        plain_password="newpassword", hashed_password=updated_user.password_hash
    )


@pytest.mark.asyncio
async def test_reset_user_password(
    session: AsyncSession, existing_user: models.User
) -> None:
    with patch("fennec_auth.services.random_password") as random_password:
        random_password.return_value = "newrandompassword"
        updated_user = await services.reset_user_password(session, user=existing_user)
        assert verify_password(
            plain_password="newrandompassword",
            hashed_password=updated_user.password_hash,
        )


@pytest.mark.asyncio
async def test_add_permission_to_user_not_existing_permission(
    session: AsyncSession,
    existing_user: models.User,
    existing_client_application: models.ClientApplication,
) -> None:
    added_permission = await services.add_permission(
        session,
        model=existing_user,
        permission_data=schemas.PermissionUpdate(
            client_application=existing_client_application.name, role="read"
        ),
    )

    attached_user_permission = await session.execute(
        select(models.UserPermission).filter(
            models.UserPermission.user_id == existing_user.id,
            models.UserPermission.permission_id == added_permission.id,
        )
    )
    assert attached_user_permission.scalar_one()


@pytest.mark.asyncio
async def test_add_permission_to_user_existing_permission(
    session: AsyncSession,
    existing_user: models.User,
    existing_client_application: models.ClientApplication,
) -> None:
    added_permission = await services.add_permission(
        session,
        model=existing_user,
        permission_data=schemas.PermissionUpdate(
            client_application=existing_client_application.name, role="read"
        ),
    )
    attached_user_permission = await session.execute(
        select(models.UserPermission).filter(
            models.UserPermission.user_id == existing_user.id,
            models.UserPermission.permission_id == added_permission.id,
        )
    )
    assert attached_user_permission.scalar_one()


@pytest.mark.asyncio
async def test_add_permission_to_user_failed_when_client_application_not_exists(
    session: AsyncSession, existing_user: models.User
) -> None:
    with pytest.raises(exceptions.ClientApplicationNotFound):
        await services.add_permission(
            session,
            model=existing_user,
            permission_data=schemas.PermissionUpdate(
                client_application="unknown", role="read"
            ),
        )


@pytest.mark.asyncio
async def test_add_permission_to_user_failed_when_permission_already_attached(
    session: AsyncSession,
    existing_user: models.User,
    existing_client_application: models.ClientApplication,
) -> None:
    permission_data = schemas.PermissionUpdate(
        client_application=existing_client_application.name, role="read"
    )
    await services.add_permission(
        session,
        model=existing_user,
        permission_data=permission_data,
    )
    with pytest.raises(exceptions.AlreadyAttachedPermission):
        await services.add_permission(
            session, model=existing_user, permission_data=permission_data
        )


@pytest.mark.asyncio
async def test_add_permission_to_client_application_not_existing_permission(
    session: AsyncSession,
    existing_client_application: models.ClientApplication,
    existing_alt_client_application: models.ClientApplication,
) -> None:
    added_permission = await services.add_permission(
        session,
        model=existing_alt_client_application,
        permission_data=schemas.PermissionUpdate(
            client_application=existing_client_application.name, role="read"
        ),
    )

    attached_client_application_permission = await session.execute(
        select(models.ClientApplicationPermission).filter(
            models.ClientApplicationPermission.client_application_id
            == existing_alt_client_application.id,
            models.ClientApplicationPermission.permission_id == added_permission.id,
        )
    )
    assert attached_client_application_permission.scalar_one()


@pytest.mark.asyncio
async def test_add_permission_to_client_application_failed_when_client_application_not_exists(
    session: AsyncSession, existing_alt_client_application: models.ClientApplication
) -> None:
    with pytest.raises(exceptions.ClientApplicationNotFound):
        await services.add_permission(
            session,
            model=existing_alt_client_application,
            permission_data=schemas.PermissionUpdate(
                client_application="unknown", role="read"
            ),
        )


@pytest.mark.asyncio
async def test_add_permission_to_client_application_failed_when_permission_already_attached(
    session: AsyncSession,
    existing_client_application: models.ClientApplication,
    existing_alt_client_application: models.ClientApplication,
) -> None:
    permission_data = schemas.PermissionUpdate(
        client_application=existing_client_application.name, role="read"
    )
    await services.add_permission(
        session,
        model=existing_alt_client_application,
        permission_data=permission_data,
    )
    with pytest.raises(exceptions.AlreadyAttachedPermission):
        await services.add_permission(
            session,
            model=existing_alt_client_application,
            permission_data=permission_data,
        )


@pytest.mark.asyncio
async def test_remove_permission_to_user_happy_path(
    session: AsyncSession,
    existing_user: models.User,
    existing_client_application: models.ClientApplication,
) -> None:
    read_permission = models.Permission(
        client_application_id=existing_client_application.id, role="read"
    )
    session.add(read_permission)

    write_permission = models.Permission(
        client_application_id=existing_client_application.id, role="write"
    )
    session.add(write_permission)
    await session.commit()
    session.add_all(
        [
            models.UserPermission(
                user_id=existing_user.id, permission_id=read_permission.id
            ),
            models.UserPermission(
                user_id=existing_user.id, permission_id=write_permission.id
            ),
        ]
    )
    await session.commit()

    await services.remove_permission(
        session, model=existing_user, permission_id=read_permission.id
    )

    result = await session.execute(
        select(models.UserPermission).filter(
            models.UserPermission.user_id == existing_user.id
        )
    )
    assert len(result.scalars().all()) == 1

    await services.remove_permission(
        session, model=existing_user, permission_id=write_permission.id
    )
    result = await session.execute(
        select(models.UserPermission).filter(
            models.UserPermission.user_id == existing_user.id
        )
    )
    assert len(result.scalars().all()) == 0


@pytest.mark.asyncio
async def test_remove_permission_to_client_application_happy_path(
    session: AsyncSession,
    existing_alt_client_application: models.ClientApplication,
    existing_client_application: models.ClientApplication,
) -> None:
    read_permission = models.Permission(
        client_application_id=existing_client_application.id, role="read"
    )
    session.add(read_permission)

    write_permission = models.Permission(
        client_application_id=existing_client_application.id, role="write"
    )
    session.add(write_permission)
    await session.commit()

    session.add_all(
        [
            models.ClientApplicationPermission(
                client_application_id=existing_alt_client_application.id,
                permission_id=read_permission.id,
            ),
            models.ClientApplicationPermission(
                client_application_id=existing_alt_client_application.id,
                permission_id=write_permission.id,
            ),
            models.ClientApplicationPermission(
                client_application_id=existing_client_application.id,
                permission_id=read_permission.id,
            ),
            models.ClientApplicationPermission(
                client_application_id=existing_client_application.id,
                permission_id=write_permission.id,
            ),
        ]
    )
    await session.commit()

    await services.remove_permission(
        session, model=existing_alt_client_application, permission_id=read_permission.id
    )
    result = await session.execute(
        select(models.ClientApplicationPermission).filter(
            models.ClientApplicationPermission.client_application_id
            == existing_alt_client_application.id
        )
    )
    assert len(result.scalars().all()) == 1

    await services.remove_permission(
        session,
        model=existing_alt_client_application,
        permission_id=write_permission.id,
    )
    result = await session.execute(
        select(models.ClientApplicationPermission).filter(
            models.ClientApplicationPermission.client_application_id
            == existing_alt_client_application.id
        )
    )
    assert len(result.scalars().all()) == 0

    result = await session.execute(
        select(models.ClientApplicationPermission).filter(
            models.ClientApplicationPermission.client_application_id
            == existing_client_application.id
        )
    )
    assert len(result.scalars().all()) == 2


@pytest.mark.asyncio
async def test_list_client_application_permissions(
    session: AsyncSession,
    existing_alt_client_application: models.ClientApplication,
    existing_client_application: models.ClientApplication,
) -> None:
    read_permission = models.Permission(
        client_application_id=existing_client_application.id, role="read"
    )
    session.add(read_permission)

    write_permission = models.Permission(
        client_application_id=existing_client_application.id, role="write"
    )
    session.add(write_permission)
    await session.commit()

    session.add_all(
        [
            models.ClientApplicationPermission(
                client_application_id=existing_alt_client_application.id,
                permission_id=read_permission.id,
            ),
            models.ClientApplicationPermission(
                client_application_id=existing_alt_client_application.id,
                permission_id=write_permission.id,
            ),
            models.ClientApplicationPermission(
                client_application_id=existing_client_application.id,
                permission_id=read_permission.id,
            ),
            models.ClientApplicationPermission(
                client_application_id=existing_client_application.id,
                permission_id=write_permission.id,
            ),
        ]
    )
    await session.commit()

    permissions = await services.list_permissions(
        session, model=existing_alt_client_application
    )
    assert sorted([p.id for p in permissions]) == sorted(
        [write_permission.id, read_permission.id]
    )

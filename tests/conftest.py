import socket

import pytest
from environs import Env
from fastapi.testclient import TestClient
from pydantic import SecretStr
from pytest_mock import MockerFixture
from pytest_socket import socket_allow_hosts
from sqlalchemy import select

from app.apps.users.models import Users
from app.core.config import AppSettings, get_settings
from app.core.db_config import AsyncSessionMaker
from app.core.init_db import migrate_db_sync
from app.main import create_app


@pytest.fixture(autouse=True)
def set_test_settings(mocker: MockerFixture) -> None:
    mocker.patch(
        target='app.core.config.get_settings',
        return_value=AppSettings(
            SECRET_KEY=SecretStr('test'),
            IS_TEST=True,
        ),
    )


@pytest.fixture(autouse=True)
def migrate():
    env = Env()
    env.read_env('.env')
    socket_allow_hosts(allowed=['127.0.0.1', '127.0.1.1', '::1', socket.gethostbyname(env('DB_HOST'))])
    settings = get_settings()
    migrate_db_sync(settings.db_url.replace('+asyncpg', ''), echo=False)
    yield
    migrate_db_sync(settings.db_url.replace('+asyncpg', ''), 'base', echo=False)


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture()
async def normal_user_token_headers(client: TestClient):
    async with AsyncSessionMaker() as session:
        user = (await session.scalars(select(Users).where(Users.username == 'login-user'))).first()
        if not user:
            user = Users(username='login-user')
            user.hash_password('pass')
            session.add(user)
            await session.flush()
            await session.commit()

    return _get_auth_token_for_user(client=client, username='login-user', password='pass')


def _get_auth_token_for_user(client: TestClient, username: str, password: str) -> dict:
    data = {'username': username, 'password': password}
    r = client.post('api/v1/users/login', data=data)
    response = r.json()
    auth_token = response['access_token']
    headers = {'Authorization': f'Bearer {auth_token}'}
    return headers

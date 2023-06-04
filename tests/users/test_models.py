import pytest
from passlib.context import CryptContext
from pydantic import SecretStr
from pytest_mock import MockerFixture

from app.apps.users.models import Users
from app.lib.utils import pwd_context


@pytest.mark.asyncio
async def test_users_verify_password_returns_true_for_correct_pass():
    test_pass = pwd_context.hash('password')

    user = Users()
    user.username = 'test_user'
    user.hashed_pass = test_pass

    assert user.verify_password(SecretStr('password')) is True


@pytest.mark.asyncio
async def test_users_verify_password_returns_false_for_incorrect_pass():
    test_pass = pwd_context.hash('password_test')

    user = Users()
    user.username = 'test_user'
    user.hashed_pass = test_pass

    assert user.verify_password(SecretStr('password')) is False


@pytest.mark.asyncio
async def test_users_has_password_sets_value_to_model(mocker: MockerFixture):
    mocker.patch.object(CryptContext, 'hash', return_value='hashed_password')

    user = Users()
    user.username = 'test_user'

    user.hash_password('password')
    assert user.hashed_pass == 'hashed_password'

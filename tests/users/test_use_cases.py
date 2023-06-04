import pytest
from fastapi import HTTPException, Response
from jose import JWTError
from pydantic import SecretStr
from pytest_mock import MockerFixture
from starlette import status

from app.apps.users.dtos import JWTToken, RegistrationData
from app.apps.users.models import Users
from app.apps.users.use_cases import AuthenticateUserUseCase, GetUserFromTokenUseCase, RegisterUserUseCase
from app.lib.classes import BadRequestException


@pytest.mark.asyncio
async def test_register_user_use_case_creates_user_and_raises_error_if_its_exists():
    registration_data = RegistrationData(username='test_user', password='password', phone='123')
    user = await RegisterUserUseCase(registration_data).execute()
    assert isinstance(user, Users)
    assert user.username == 'test_user'

    with pytest.raises(BadRequestException) as e:
        await RegisterUserUseCase(registration_data).execute()
    assert 'User already exists' in str(e.value.detail)


@pytest.mark.asyncio
async def test_authenticate_user_use_case_success(mocker: MockerFixture):
    """Test success scenario of authenticate user use case"""
    await RegisterUserUseCase(RegistrationData(username='test_user', password='password', phone='123')).execute()

    async def _executable(*args, **kwargs):
        return 'test_token'

    mocker.patch.object(AuthenticateUserUseCase, '_create_access_token', new=_executable)

    use_case = AuthenticateUserUseCase(
        username='test_user',
        password=SecretStr('password'),
    )
    response = await use_case.execute()
    assert response.__class__ is Response


@pytest.mark.asyncio
async def test_authenticate_user_use_case_user_not_found(mocker: MockerFixture):
    """Test scenario when user not found"""

    async def _executable(*args, **kwargs):
        return None

    mocker.patch.object(AuthenticateUserUseCase, '_create_access_token', new=_executable)

    use_case = AuthenticateUserUseCase(username='non_existing_username', password=SecretStr('test_password'))
    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute()

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == 'User not found'


@pytest.mark.asyncio
async def test_authenticate_user_use_case_wrong_password(mocker: MockerFixture):
    """Test scenario when user provides wrong password"""
    await RegisterUserUseCase(RegistrationData(username='test_user', password='password', phone='123')).execute()

    async def _executable(*args, **kwargs):
        return None

    mocker.patch.object(AuthenticateUserUseCase, '_create_access_token', new=_executable)

    use_case = AuthenticateUserUseCase(
        username='test_user',
        password=SecretStr('wrong_password'),
    )
    with pytest.raises(HTTPException) as exc_info:
        await use_case.execute()

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == 'Wrong credentials'


@pytest.mark.asyncio
async def test_get_user_from_token_use_case_success(mocker):
    user = await RegisterUserUseCase(RegistrationData(username='test_user', password='password', phone='123')).execute()
    mock_payload = mocker.Mock(return_value={'sub': 'test_user'})
    mocker.patch('jose.jwt.decode', mock_payload)

    use_case = GetUserFromTokenUseCase(token='token')
    result = await use_case.execute()

    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_user_from_token_use_case_failure_jwt_error(mocker):
    mocker.patch('jose.jwt.decode', side_effect=JWTError)

    use_case = GetUserFromTokenUseCase(token='token')
    with pytest.raises(HTTPException) as e:
        await use_case.execute()

    assert e.value.status_code == 401
    assert e.value.detail == 'Token is corrupted or has expired.'
    assert e.value.headers == {'WWW-Authenticate': 'Bearer'}


@pytest.mark.asyncio
async def test_get_user_from_token_use_case_failure_decoded_with_no_username(mocker):
    mocker.patch('jose.jwt.decode', return_value={})

    use_case = GetUserFromTokenUseCase(token='token')
    with pytest.raises(HTTPException) as e:
        await use_case.execute()

    assert e.value.status_code == 401
    assert e.value.detail == 'Token is corrupted or has expired.'
    assert e.value.headers == {'WWW-Authenticate': 'Bearer'}


@pytest.mark.asyncio
async def test_get_user_from_token_use_case_user_not_found(mocker):
    mock_payload = mocker.Mock(return_value={'sub': 'user_test'})
    mocker.patch('jose.jwt.decode', mock_payload)

    use_case = GetUserFromTokenUseCase(token='token')
    with pytest.raises(HTTPException) as e:
        await use_case.execute()

    assert e.value.status_code == 401
    assert e.value.detail == 'Token is not valid.'
    assert e.value.headers == {'WWW-Authenticate': 'Bearer'}

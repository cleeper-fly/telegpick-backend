import pytest
from fastapi import HTTPException, status, Response
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app.apps.users.dtos import UserDTO
from app.apps.users.use_cases import AuthenticateUserUseCase, RegisterUserUseCase


@pytest.mark.asyncio
async def test_register_user(client: TestClient, mocker: MockerFixture):
    mocker.patch("app.apps.telegpick.use_cases.UserSendVerificationUseCase.execute")
    registration_data = {
        'id': 'b5fc0ced-c3b8-4124-aa6b-8179c75dfe57', 'email': 'test@test.com', 'username': 'test_user', 'password': 'test_password', 'phone': '123'
    }
    user_orm = mocker.MagicMock(**registration_data)
    user_dto = UserDTO.from_orm(user_orm)

    mocker.patch.object(RegisterUserUseCase, 'execute', return_value=user_orm)

    response = client.post('api/v1/users/register', json=registration_data)

    assert response.status_code == 200
    assert response.json() == dict(user_dto.dict())


@pytest.mark.asyncio
async def test_login_user(client: TestClient, mocker: MockerFixture):
    form_data = {
        'username': 'test_user',
        'password': 'test_password',
    }
    mocker.patch(
        'app.apps.users.use_cases.AuthenticateUserUseCase.execute',
        return_value=Response(content='Authentication successful')
    )
    response = client.post('api/v1/users/login', json=form_data)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_user_fail_with_bad_credentials(client: TestClient, mocker: MockerFixture):
    form_data = {
        'username': 'test_user',
        'password': 'wrong_password',
    }
    error_message = {'detail': 'Incorrect username or password'}
    mocker.patch.object(
        AuthenticateUserUseCase,
        'execute',
        side_effect=HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message['detail']),
    )

    response = client.post('api/v1/users/login', json=form_data)

    assert response.status_code == 400
    assert response.json() == error_message

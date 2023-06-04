import pytest
from fastapi import Cookie
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app.apps.telegpick.dtos import ListPicsDTO, PicsDTO
from app.apps.telegpick.models import Pics, Schedules
from app.apps.telegpick.use_cases import (
    CreatePicForUserUseCase,
    CreateScheduleForPicUseCase,
    DeletePicForUserUseCase,
    DeleteScheduleForPicUseCase,
    PatchPicForUserUseCase,
    PatchScheduleForPicUseCase,
)
from app.apps.users.dtos import UserDTO
from tests.telegpick.test_use_cases import session_maker


@pytest.fixture
def mock_delete_pic_use_case(client: TestClient, mocker: MockerFixture):
    return mocker.patch("app.apps.telegpick.use_cases.DeletePicForUserUseCase")


@pytest.fixture
def test_user(client: TestClient, mocker: MockerFixture):
    mocker.patch("app.apps.telegpick.use_cases.UserSendVerificationUseCase.execute")
    registration_data = {"email": "test@test.com", "username": "test_user", "password": "test_password", "phone": "123"}
    response = client.post("/api/v1/users/register", json=registration_data)
    assert response.status_code == 200
    user = UserDTO(**response.json())
    return user


@pytest.fixture
def auth_cookie(client, test_user):
    login_data = {"username": test_user.username, "password": "test_password"}
    login_response = client.post("/api/v1/users/login", json=login_data)
    assert login_response.status_code == 200
    auth_cookie = login_response.cookies
    return auth_cookie


@pytest.mark.asyncio
async def test_get_pics_endpoint(client: TestClient, mocker: MockerFixture, auth_cookie: Cookie):

    pics = [
        PicsDTO(**{"id": 1, "filename": "pic1.jpg"}),
        PicsDTO(**{"id": 2, "filename": "pic2.jpg"}),
        PicsDTO(**{"id": 3, "filename": "pic3.jpg"}),
    ]

    mocker.patch("app.apps.telegpick.use_cases.FetchPicsForUserUseCase.execute", return_value=pics)

    response = client.get("/api/v1/telegpick/pic/list", cookies=auth_cookie)

    assert response.status_code == 200

    response_json = response.json()
    assert response_json == ListPicsDTO(pics=pics).dict()


@pytest.mark.asyncio
async def test_create_pic_endpoint(client: TestClient, mocker: MockerFixture, auth_cookie: Cookie):
    mocker.patch.object(CreatePicForUserUseCase, "execute", return_value=PicsDTO())

    response = client.post("/api/v1/telegpick/pic/create", json={}, cookies=auth_cookie)

    assert response.status_code == 201
    assert response.json() == PicsDTO().dict()


@pytest.mark.asyncio
async def test_patch_pic_endpoint(client: TestClient, mocker: MockerFixture, auth_cookie: Cookie):
    mocker.patch.object(PatchPicForUserUseCase, "execute", return_value=PicsDTO())

    response = client.patch("/api/v1/telegpick/pic/update", json={}, cookies=auth_cookie)

    assert response.status_code == 200
    assert response.json() == PicsDTO().dict()


@pytest.mark.asyncio
async def test_delete_pic_endpoint(client: TestClient, mocker: MockerFixture, auth_cookie: Cookie, test_user: UserDTO):
    async with session_maker() as session:
        pic = Pics(user_id=test_user.id, filename='test.jpg')
        session.add(pic)
        await session.flush()
        pic_id = str(pic.id)

    mock = mocker.patch.object(DeletePicForUserUseCase, "execute", return_value=None)

    response = client.delete(
        f"/api/v1/telegpick/{pic_id}/delete",
        cookies=auth_cookie
    )
    assert response.status_code == 200
    assert response.json() == {'message': f'Successfully deleted pic {pic_id}!', 'details': None}
    mock.assert_called_once()


@pytest.mark.asyncio
async def test_create_schedule_endpoint(
    client: TestClient,
    mocker: MockerFixture,
    auth_cookie: Cookie,
    test_user: UserDTO,
):

    async with session_maker() as session:
        pic = Pics(user_id=test_user.id, filename='test.jpg')
        session.add(pic)
        await session.flush()

    mock = mocker.patch.object(CreateScheduleForPicUseCase, "execute", return_value=Schedules(pic_id=str(pic.id)))

    response = client.post(
        f"/api/v1/telegpick/{str(pic.id)}/schedule/create",
        json={"schedule": {}},
        cookies=auth_cookie
    )
    print(response.json())
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_patch_schedule_endpoint(
    client: TestClient,
    mocker: MockerFixture,
    auth_cookie: Cookie,
    test_user: UserDTO,
):
    async with session_maker() as session:
        pic = Pics(user_id=test_user.id, filename='test.jpg')
        session.add(pic)
        await session.flush()

    mock = mocker.patch.object(PatchScheduleForPicUseCase, "execute", return_value=Schedules(pic_id=str(pic.id)))

    response = client.patch(
        f"/api/v1/telegpick/{str(pic.id)}/schedule/update",
        json={"schedule": {}},
        cookies=auth_cookie
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_schedule_endpoint(
    client: TestClient,
    mocker: MockerFixture,
    auth_cookie: Cookie,
    test_user: UserDTO,
):
    async with session_maker() as session:
        pic = Pics(user_id=test_user.id, filename='test.jpg')
        session.add(pic)
        await session.flush()
        schedule = Schedules(pic_id=pic.id, day_time='16:00')
        session.add(schedule)
        await session.flush()
    pic_id = str(pic.id)
    schedule_id = str(schedule.id)

    mock = mocker.patch.object(DeleteScheduleForPicUseCase, "execute", return_value=None)

    response = client.delete(
        f"/api/v1/telegpick/{pic_id}/{schedule_id}/delete",
        cookies=auth_cookie
    )
    assert response.status_code == 200
    assert response.json() == {'message': f'Successfully deleted schedule {schedule_id}!', 'details': None}
    mock.assert_called_once()

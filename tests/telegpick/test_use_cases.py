import uuid
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, patch, mock_open
from uuid import UUID

import pytest
from fastapi import UploadFile
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import app.apps.telegpick.connectors.telegram
from app.apps.telegpick.dtos import PicsDTO, SchedulesDTO
from app.apps.telegpick.models import Pics, Schedules
from app.apps.telegpick.use_cases import (
    ChangeAvatarUseCase,
    CreatePicForUserUseCase,
    CreateScheduleForPicUseCase,
    DeletePicForUserUseCase,
    DeleteScheduleForPicUseCase,
    FetchPicsForUserUseCase,
    PatchPicForUserUseCase,
    PatchScheduleForPicUseCase,
    ProcessPicsTaskUseCase,
    BasePicWithUserUseCase, UploadPicOnDiskUseCase, UserSendVerificationUseCase,
)
from app.apps.users.models import Users
from app.core.db_config import AsyncSessionMaker
from app.lib.classes import BadRequestException

session_maker = AsyncSessionMaker


@pytest.fixture
async def pic():
    return PicsDTO(id=None, filename="test.jpg")


@pytest.fixture
async def user() -> Users:
    async with session_maker() as session:
        user = Users(username='test', hashed_pass='133', phone='123')
        session.add(user)
        await session.flush()
        await session.commit()
    return user


@pytest.mark.asyncio
async def test_fetch_pic_use_case_execute_with_existing_user():
    async with session_maker() as session:
        user = Users(username='test_user', hashed_pass='hashed_pass', phone='123')
        session.add(user)
        await session.flush()
        pics = [
            Pics(id=UUID('11111111-1111-1111-1111-111111111111'), user_id=user.id, filename="pic1.jpg"),
            Pics(id=UUID('22222222-2222-2222-2222-222222222222'), user_id=user.id, filename="pic2.jpg"),
        ]
        session.add_all(pics)
        await session.flush()
        await session.commit()

    async with session_maker() as session:
        use_case = FetchPicsForUserUseCase(user, 1, 2)
        result = await use_case.execute()

        assert len(result) == 2
        assert result[0].id == UUID('11111111-1111-1111-1111-111111111111')
        assert result[0].filename == "pic1.jpg"
        assert result[1].id == UUID('22222222-2222-2222-2222-222222222222')
        assert result[1].filename == "pic2.jpg"


@pytest.mark.asyncio
async def test_fetch_pic_use_case_execute_with_user_without_pics(user):
    use_case = FetchPicsForUserUseCase(user, 1, 10)
    result = await use_case.execute()
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_pic_use_case_execute(user, pic):
    use_case = CreatePicForUserUseCase(pic, user)
    created_pic = await use_case.execute()

    assert created_pic.id is not None
    assert created_pic.filename == "test.jpg"
    assert created_pic.user_id == user.id

    with pytest.raises(BadRequestException) as e:
        await CreatePicForUserUseCase(PicsDTO(id=created_pic.id), user).execute()

    assert 'Can\'t create already existing Pic' in str(e.value.detail)


@pytest.mark.asyncio
async def test_patch_pic_use_case_execute(user: Users) -> None:
    async with session_maker() as session:
        existing_pic = Pics(id=UUID('11111111-1111-1111-1111-111111111111'), user_id=str(user.id), filename='pic.jpg')
        session.add(existing_pic)
        await session.flush()
        await session.commit()

        updated_pic = PicsDTO(
            id=UUID('11111111-1111-1111-1111-111111111111'), user_id=str(user.id), filename='new_pic.jpg'
        )

        use_case = PatchPicForUserUseCase(updated_pic, user)
        patched_pic = await use_case.execute()

        assert patched_pic.id == UUID('11111111-1111-1111-1111-111111111111')
        assert patched_pic.filename == 'new_pic.jpg'


@pytest.mark.asyncio
async def test_delete_pic_use_case_execute_with_existing_pic(user):
    pic = Pics(id=UUID('11111111-1111-1111-1111-111111111111'), user_id=user.id, filename='pic1.jpg')
    async with session_maker() as session:
        session.add(user)
        session.add(pic)
        await session.commit()
    use_case = DeletePicForUserUseCase(pic_id='11111111-1111-1111-1111-111111111111', user=user)
    async with session_maker() as session:
        await use_case.execute()
    async with session_maker() as session:
        deleted_pic = await session.get(Pics, '11111111-1111-1111-1111-111111111111')
        assert deleted_pic is None


@pytest.mark.asyncio
async def test_create_schedule_use_case_execute(user):
    schedule_data = {
        'days_of_week': '0010000',
        'day_time': '09:00:00',
    }
    schedule = SchedulesDTO(**schedule_data)

    use_case = CreateScheduleForPicUseCase(pic_id='11111111-1111-1111-1111-111111111111', schedule=schedule)

    async with session_maker() as session:
        existing_pic = Pics(id=UUID('11111111-1111-1111-1111-111111111111'), user_id=str(user.id), filename='pic.jpg')
        session.add(existing_pic)
        await session.flush()
        await session.commit()
        created_schedule = await use_case.execute()

    assert created_schedule.pic_id == '11111111-1111-1111-1111-111111111111'
    assert created_schedule.days_of_week == '0010000'
    assert created_schedule.day_time == '09:00:00'
    assert created_schedule.id is not None


@pytest.mark.asyncio
async def test_patch_schedule_use_case_execute(user):
    async with session_maker() as session:
        pic_id = '123e4567-e89b-12d3-a456-426655440000'
        existing_pic = Pics(id=UUID('123e4567-e89b-12d3-a456-426655440000'), user_id=str(user.id), filename='pic.jpg')
        session.add(existing_pic)
        await session.flush()
        await session.commit()
        schedule_id = '11111111-1111-1111-1111-111111111111'
        schedule = Schedules(id=schedule_id, pic_id=pic_id, days_of_week='1000000', day_time='10:00')
        session.add(schedule)
        await session.flush()
        await session.commit()

    updated_schedule_data = {
        'id': schedule_id,
        'days_of_week': '0100000',
    }
    use_case = PatchScheduleForPicUseCase(pic_id, SchedulesDTO(**updated_schedule_data))
    updated_schedule = await use_case.execute()

    assert isinstance(updated_schedule, Schedules)
    assert updated_schedule.id == UUID(schedule_id)
    assert updated_schedule.pic_id == UUID(pic_id)
    assert updated_schedule.days_of_week == updated_schedule_data['days_of_week']
    assert updated_schedule.day_time == schedule.day_time


@pytest.mark.asyncio
async def test_delete_schedule_use_case_execute(user):
    async with session_maker() as session:
        pic_id = '123e4567-e89b-12d3-a456-426655440000'
        existing_pic = Pics(id=UUID('123e4567-e89b-12d3-a456-426655440000'), user_id=str(user.id), filename='pic.jpg')
        session.add(existing_pic)
        await session.flush()
        await session.commit()
        schedule_id = '11111111-1111-1111-1111-111111111111'
        schedule = Schedules(id=schedule_id, pic_id=pic_id, days_of_week='1000000', day_time='10:00')
        session.add(schedule)
        await session.flush()
        await session.commit()

    use_case = DeleteScheduleForPicUseCase(schedule_id, pic_id)
    await use_case.execute()

    async with session_maker() as session:
        deleted_schedule = await session.get(Schedules, schedule_id)
    assert deleted_schedule is None


@pytest.mark.asyncio
async def test_process_pics_task_use_case(user) -> None:
    pic_mock = MagicMock(filename='123')
    user_mock = MagicMock()

    use_case = ProcessPicsTaskUseCase(datetime.now())
    async with session_maker() as session:
        pic_id = UUID('123e4567-e89b-12d3-a456-426655440000')
        existing_pic = Pics(id=UUID('123e4567-e89b-12d3-a456-426655440000'), user_id=user.id, filename='pic.jpg')
        session.add(existing_pic)
        await session.flush()
        await session.commit()
        schedule_id = UUID('11111111-1111-1111-1111-111111111111')
        schedule = Schedules(id=schedule_id, pic_id=pic_id, days_of_week='1000000', day_time='10:00')
        session.add(schedule)
        await session.flush()
        await session.commit()
        q = (select(Pics).options(selectinload(Pics.schedules), selectinload(Pics.user))).limit(1)
        pic = (await session.scalars(q)).first()

    with patch('app.apps.telegpick.use_cases.ProcessPicsTaskUseCase._pic_for_change', return_value=True):
        with patch('app.apps.telegpick.use_cases.ChangeAvatarUseCase.execute', return_value=None):
            await use_case.execute()
            ProcessPicsTaskUseCase._pic_for_change.assert_called_once()
            ChangeAvatarUseCase.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_pic_fails_if_no_pic_found(user: Users) -> None:
    async with session_maker() as session:
        pic = PicsDTO(**{'id': uuid.uuid4()})
        use_case = PatchPicForUserUseCase(user=user, pic=pic)
        with pytest.raises(BadRequestException) as e:
            await use_case._get_pic_for_user_by_id(session)
        assert 'Pic not found' in str(e.value.detail)


@pytest.mark.asyncio
async def test_get_pic_fails_if_no_pic(user: Users) -> None:
    pic = PicsDTO()
    use_case = PatchPicForUserUseCase(user=user, pic=pic)
    with pytest.raises(BadRequestException) as e:
        await use_case.execute()
    assert 'No pic_id provided' in str(e.value.detail)


@pytest.mark.asyncio
async def test_pic_upload_failed(user: Users, mocker: MockerFixture) -> None:
    test_file = 'test_file.docx'
    use_case = UploadPicOnDiskUseCase(
        user=user,
        filename=test_file,
        file=UploadFile(filename=test_file, file=MagicMock()),
        timezone='+1'
    )

    with pytest.raises(BadRequestException) as e:
        await use_case.execute()
    assert 'There was an error uploading the file' in str(e.value.detail)


@pytest.mark.asyncio
async def test_pic_upload_faile(user: Users, mocker: MockerFixture) -> None:
    file_mock = mock.Mock(write=mock.Mock())
    open_mock = mock.Mock(return_value=file_mock)
    mocker.patch('builtins.open')
    patched = mocker.patch('app.apps.telegpick.use_cases.CreatePicForUserUseCase.execute')
    test_file = 'test_file.docx'
    use_case = UploadPicOnDiskUseCase(
        user=user,
        filename=test_file,
        file=UploadFile(filename=test_file, file=open_mock),
        timezone='+1'
    )
    await use_case.execute()
    patched.assert_called_once()


@pytest.mark.asyncio
async def test_send_verification_use_case(user: Users, mocker: MockerFixture) -> None:
    use_case = UserSendVerificationUseCase(user)
    patched = mocker.patch('app.apps.telegpick.connectors.telegram.TelegramConnector.send_code')
    await use_case.execute()
    patched.assert_called_once()
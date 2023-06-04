import datetime
import re
import uuid
from abc import ABC
from uuid import UUID

import pytz
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.apps.telegpick.connectors.telegram import TelegramConnector, TelegramException
from app.apps.telegpick.dtos import PicsDTO, SchedulesDTO
from app.apps.telegpick.models import Pics, Schedules
from app.apps.users.models import Users
from app.lib.classes import BadRequestException, SQLAlchemySessionBaseUseCase, alchemy_session_decorator


class BasePicWithUserUseCase(SQLAlchemySessionBaseUseCase, ABC):
    def __init__(self, pic: PicsDTO, user: Users) -> None:
        super().__init__()
        self.user: Users = user
        self.pic: PicsDTO = pic

    async def _get_pic_for_user_by_id(self, session: AsyncSession) -> Pics:
        q = select(Pics).where(and_(Pics.user_id == self.user.id, Pics.id == self.pic.id)).limit(1)
        res: None | Pics = (await session.scalars(q)).first()
        if not res:
            raise BadRequestException(detail='Pic not found')

        return res


class FetchPicsForUserUseCase(SQLAlchemySessionBaseUseCase):
    def __init__(self, user: Users, page: int, limit: int) -> None:
        super().__init__()
        self._user = user
        self._page = page
        self._limit = limit

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> list[PicsDTO]:
        query = (
            select(Pics)
            .join(Users)
            .options(selectinload(Pics.schedules))
            .where(Users.id == self._user.id)
            .order_by(Pics.id)
            .offset((self._page - 1) * self._limit)
            .limit(self._limit)
        )
        result = await session.execute(query)
        pics = [PicsDTO.from_orm(pic) for pic in result.scalars()]
        return pics


class CreatePicForUserUseCase(BasePicWithUserUseCase):
    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> Pics:
        if self.pic.id:
            raise BadRequestException(detail='Can\'t create already existing Pic')

        pic = Pics(
            user_id=self.user.id,
            **self.pic.dict(exclude_none=True),
        )
        session.add(pic)
        await session.flush()

        return pic


class PatchPicForUserUseCase(BasePicWithUserUseCase):
    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> Pics:
        if not self.pic.id:
            raise BadRequestException(detail='No pic_id provided')

        pic = await self._get_pic_for_user_by_id(session=session)
        pic_dict = self.pic.dict(exclude_none=True, exclude={'id'})
        q = update(Pics).where(and_(Pics.user_id == self.user.id, Pics.id == self.pic.id)).values(**pic_dict)
        await session.execute(q)
        await session.flush()
        return pic


class DeletePicForUserUseCase(SQLAlchemySessionBaseUseCase):
    def __init__(self, pic_id: str | UUID, user: Users) -> None:
        super().__init__()
        self.user: Users = user
        self.pic_id: str | UUID = pic_id

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> None:
        q = select(Pics).where(and_(Pics.user_id == self.user.id, Pics.id == self.pic_id)).limit(1)
        pic: None | Pics = (await session.scalars(q)).first()
        if not pic:
            raise BadRequestException(detail='Pic not found')

        await session.delete(pic)
        await session.flush()

        return None


class BaseScheduleWithUserUseCase(SQLAlchemySessionBaseUseCase, ABC):
    def __init__(self, pic_id: str, schedule: SchedulesDTO) -> None:
        super().__init__()
        self.pic_id = pic_id
        self.schedule = schedule

    async def _get_schedule_by_id(self, session: AsyncSession) -> Schedules:
        q = select(Schedules).where(and_(Schedules.pic_id == self.pic_id, Schedules.id == self.schedule.id)).limit(1)
        res: None | Schedules = (await session.scalars(q)).first()
        if not res:
            raise BadRequestException(detail='Schedule not found')

        return res


class CreateScheduleForPicUseCase(BaseScheduleWithUserUseCase):
    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> Schedules:
        if self.schedule.id:
            raise BadRequestException('Can\'t create already existing schedule')
        schedule = Schedules(
            pic_id=self.pic_id,
            **self.schedule.dict(exclude_none=True),
        )
        session.add(schedule)
        await session.flush()

        return schedule


class PatchScheduleForPicUseCase(BaseScheduleWithUserUseCase):
    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> Schedules:
        if not self.schedule.id:
            raise BadRequestException(detail='No pic_id provided')

        schedule = await self._get_schedule_by_id(session=session)
        schedule_dict = self.schedule.dict(exclude_none=True, exclude={'id'})
        q = update(Schedules).where(Schedules.id == schedule.id).values(**schedule_dict)
        await session.execute(q)
        await session.flush()

        return schedule


class DeleteScheduleForPicUseCase(SQLAlchemySessionBaseUseCase):
    def __init__(self, schedule_id: str | UUID, pic_id: str) -> None:
        super().__init__()
        self.pic_id: str = pic_id
        self.schedule_id: str | UUID = schedule_id

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> None:
        q = select(Schedules).where(and_(Schedules.pic_id == self.pic_id, Schedules.id == self.schedule_id)).limit(1)
        pic: None | Schedules = (await session.scalars(q)).first()
        if not pic:
            raise BadRequestException(detail='Pic not found')

        await session.delete(pic)
        await session.flush()

        return None


class ProcessPicsTaskUseCase(SQLAlchemySessionBaseUseCase):
    def __init__(self, task_time: datetime.datetime) -> None:
        super().__init__()
        self.task_time = task_time

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> None:
        q = select(Pics).options(selectinload(Pics.schedules), selectinload(Pics.user))
        result = await session.execute(q)
        for pic in result.scalars().all():
            for schedule in pic.schedules:
                if not await self._pic_for_change(schedule, pic):
                    continue
                await ChangeAvatarUseCase(pic.user, pic.filename).execute()

    async def _pic_for_change(self, schedule: Schedules, pic: Pics) -> bool:
        offset_match = re.match(r'^([+-])(\d{2}):(\d{2})$', pic.timezone)
        sign, hours, minutes = offset_match.groups()  # type: ignore
        offset = datetime.timedelta(hours=int(hours), minutes=int(minutes))
        if sign == '-':
            offset = -offset
        current_time = self.task_time + offset
        current_time = current_time.replace(microsecond=0)
        database_time = datetime.datetime.strptime(schedule.day_time, "%H:%M").time()
        return current_time.time() == database_time


class ChangeAvatarUseCase:
    def __init__(self, user: Users, filename: str):
        self.user = user
        self.filename = filename

    async def execute(self):
        await TelegramConnector(self.user).set_avatar(filename=self.filename)


class UploadPicOnDiskUseCase:
    def __init__(self, file: UploadFile, filename: str, timezone: str, user: Users) -> None:
        self.file = file
        self.filename = filename
        self.timezone = timezone
        self.user = user

    async def execute(self) -> None:
        from app.core.init_app import settings

        try:
            contents = self.file.file.read()
            filename = f'{self.filename}-{str(uuid.uuid4())}.{self.file.filename.split(".")[-1]}'
            with open(f'{settings.PICS_DIRECTORY}/{filename}', 'wb') as f:
                f.write(contents)
        except Exception:
            raise BadRequestException(detail='There was an error uploading the file')
        else:
            await CreatePicForUserUseCase(
                pic=PicsDTO(filename=filename, timezone=self.timezone), user=self.user
            ).execute()
        finally:
            self.file.file.close()


class ReturnPicFileByIdUseCase(SQLAlchemySessionBaseUseCase):
    def __init__(self, pic_id: str) -> None:
        super().__init__()
        self.pic_id = pic_id

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> FileResponse:
        from app.core.init_app import settings

        q = select(Pics).where(Pics.id == self.pic_id)
        pic = (await session.scalars(q)).first()
        if not pic:
            raise BadRequestException(detail='There was an error uploading the picture')
        pic_path = f"{settings.PICS_DIRECTORY}/{pic.filename}"
        return FileResponse(pic_path)


class UserSendVerificationUseCase:
    def __init__(self, user: Users) -> None:
        self.user = user

    async def execute(self) -> None:
        try:
            await TelegramConnector(self.user).send_code()
        except TelegramException:
            raise BadRequestException(detail='Error connecting to Telegram')
        except Exception:
            raise BadRequestException(detail='Error sending code')


class UserConfirmCodeUseCase(SQLAlchemySessionBaseUseCase):
    def __init__(self, code: str, user_id: str) -> None:
        super().__init__()
        self.code = code
        self.user_id = user_id

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> None:
        q = select(Users).where(Users.id == self.user_id)
        user = (await session.scalars(q)).first()
        if not user:
            raise BadRequestException(detail='No such user')
        try:
            await TelegramConnector(user).sign_in(self.code)
        except TelegramException as e:
            raise BadRequestException(detail='Error connecting to Telegram')
        except Exception as e:
            raise BadRequestException(detail='Error singing in')

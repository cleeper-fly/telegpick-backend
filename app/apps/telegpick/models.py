import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import DBBaseModel

if TYPE_CHECKING:
    from app.apps.users.models import Users


class Pics(DBBaseModel):
    __tablename__: str = 'pics'

    filename: Mapped[str] = mapped_column(String(length=(256)), nullable=False)
    schedules: Mapped[list['Schedules']] = relationship(back_populates='pic', cascade='all, delete')
    timezone: Mapped[str] = mapped_column(String(6), default='0')

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True)
    user: Mapped['Users'] = relationship(back_populates='pics')


class Schedules(DBBaseModel):
    __tablename__: str = 'schedules'

    days_of_week: Mapped[str] = mapped_column(String(length=(7)), default='0000000')
    day_time: Mapped[str] = mapped_column(String(length=(7)), default='00:00')

    pic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('pics.id'), index=True)
    pic: Mapped['Pics'] = relationship(back_populates='schedules')

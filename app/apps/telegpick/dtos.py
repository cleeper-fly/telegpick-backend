from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.config import get_settings
from app.core.pydantic_base import BaseModel, BaseModelORM

settings = get_settings()


class SchedulesDTO(BaseModelORM):
    id: UUID | str | None = None
    days_of_week: str | None = None
    day_time: str | None = None


class PicsDTO(BaseModelORM):
    id: UUID | str | None = None
    filename: str | None = None
    timezone: str | None = None
    schedules: list[SchedulesDTO] | None = None


class ListPicsDTO(BaseModel):
    pics: list[PicsDTO] = Field(default_factory=list)

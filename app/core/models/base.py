import uuid

from sqlalchemy import Column, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

meta_data = MetaData()
Base = DeclarativeBase


class DBBaseModel(Base):
    meta_data = meta_data
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, unique=True, primary_key=True, insert_default=uuid.uuid4, index=True
    )

    def __repr__(self) -> str:
        columns = ', '.join([f'{k}={repr(v)}' for k, v in self.__dict__.items() if not k.startswith('_')])
        return f'<{self.__class__.__name__}({columns})>'

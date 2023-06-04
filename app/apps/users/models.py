from typing import TYPE_CHECKING

from pydantic import SecretStr
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import DBBaseModel
from app.lib.utils import pwd_context

if TYPE_CHECKING:
    from app.apps.telegpick.models import Pics


class Users(DBBaseModel):
    __tablename__: str = 'users'
    username: Mapped[str] = mapped_column(String(length=128), nullable=False)
    hashed_pass: Mapped[str] = mapped_column(String(length=256), nullable=False)
    phone: Mapped[str] = mapped_column(String(length=16), nullable=False)
    phone_hash: Mapped[str] = mapped_column(String(length=256), nullable=True)
    pics: Mapped[list['Pics']] = relationship(back_populates='user', cascade='all, delete')

    def verify_password(self, password: SecretStr) -> bool:
        return pwd_context.verify(secret=password.get_secret_value(), hash=self.hashed_pass)

    def hash_password(self, password: str) -> None:
        self.hashed_pass = pwd_context.hash(secret=password)

from uuid import UUID

from pydantic import Field, SecretStr, validator

from app.core.pydantic_base import BaseModel, BaseModelORM


class ConfirmationData(BaseModel):
    code: str
    user_id: str


class JWTToken(BaseModel):
    access_token: str
    token_type: str


class JWTTokenData(BaseModel):
    username: str | None


class RegistrationData(BaseModel):
    username: str
    phone: str
    password: SecretStr = Field(min_length=8)

    @validator('username')
    def to_lowercase(cls, v: str) -> str:
        return v.lower()


class UserDTO(BaseModelORM):
    id: UUID
    username: str
    phone: str

    @validator("id")
    def validate_uuids(cls, value):
        if value:
            return str(value)
        return value


class UserLoginDTO(BaseModel):
    username: str
    password: str

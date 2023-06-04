from datetime import datetime, timedelta

from fastapi import HTTPException, Response, status
from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWTClaimsError
from pydantic import SecretStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.apps.users.dtos import JWTTokenData, RegistrationData
from app.apps.users.models import Users
from app.core.config import get_settings
from app.core.db_config import AsyncSessionMaker
from app.lib.classes import (
    AbstractUseCase,
    BadRequestException,
    SQLAlchemySessionBaseUseCase,
    alchemy_session_decorator,
)

settings = get_settings()


class RegisterUserUseCase(SQLAlchemySessionBaseUseCase):
    """
    Registering new user
    """

    def __init__(self, registration_data: RegistrationData) -> None:
        super().__init__()
        self._registration_data = registration_data

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> Users:
        q = select(Users).where(Users.username == self._registration_data.username).exists()

        if v := (await session.scalars(q.select())).first():
            raise BadRequestException(
                detail=f'User already exists {v}',
            )

        user = Users(username=self._registration_data.username, phone=self._registration_data.phone)
        user.hash_password(password=self._registration_data.password.get_secret_value())
        session.add(user)
        await session.flush()
        return user


class AuthenticateUserUseCase(SQLAlchemySessionBaseUseCase):
    """
    Authenticating a user via log/pass and generating an access token for him
    """

    def __init__(self, username: str, password: SecretStr) -> None:
        super().__init__()
        self._username = username.lower()
        self._password = password

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> Response:
        error: str | None = None

        q = select(Users).where(Users.username == self._username)
        user = (await session.scalars(q)).first()
        if not user:
            error = 'User not found'
        else:
            if not user.verify_password(password=self._password):
                error = 'Wrong credentials'

        if error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error,
                headers={'WWW-Authenticate': 'Bearer'},
            )

        token = await self._create_access_token(data={'sub': user.username})  # type: ignore
        response = Response(content='Authentication successful')
        response.set_cookie(key='access_token', value=token, httponly=True)
        return response

    @staticmethod
    async def _create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.EXPIRATION_MINUTES)
        to_encode.update({'exp': expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM)
        return encoded_jwt


class GetUserFromTokenUseCase(AbstractUseCase):
    """
    Looking for user from token.
    Not using `SQLAlchemySessionBaseUseCase` here, since we don't always need to create a session
    """

    def __init__(self, token: str) -> None:
        self._token = token
        self._session_maker: async_sessionmaker[AsyncSession] = AsyncSessionMaker

    async def execute(self) -> Users:
        exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={'WWW-Authenticate': 'Bearer'})
        try:
            payload = jwt.decode(self._token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.ALGORITHM])
            username: str | None = payload.get('sub')
            if username is None:
                exception.detail = 'Token is corrupted or has expired.'
                raise exception
        except (JWTError, ExpiredSignatureError, JWTClaimsError):
            exception.detail = 'Token is corrupted or has expired.'
            raise exception

        token_data = JWTTokenData(username=username)

        async with self._session_maker() as session:
            q = select(Users).where(Users.username == token_data.username)
            user: Users | None = (await session.scalars(q)).first()
            if user is None:
                exception.detail = 'Token is not valid.'
                raise exception

            return user


class UpdatePhoneHashUseCase(SQLAlchemySessionBaseUseCase):
    def __init__(self, user: Users, phone_hash: str):
        super().__init__()
        self.user = user
        self.phone_hash = phone_hash

    @alchemy_session_decorator
    async def execute(self, session: AsyncSession) -> None:
        q = update(Users).where(Users.id == self.user.id).values(**{'phone_hash': self.phone_hash})
        await session.execute(q)
        await session.flush()

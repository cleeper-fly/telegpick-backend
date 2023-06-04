from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db_config import AsyncSessionMaker
from app.core.pydantic_base import BaseModel


class AbstractUseCase(ABC):
    @abstractmethod
    async def execute(self) -> Any:
        pass


class SQLAlchemySessionBaseUseCase(ABC):
    def __init__(self) -> None:
        self._session_maker: async_sessionmaker[AsyncSession] = AsyncSessionMaker

    @abstractmethod
    async def execute(self, session: AsyncSession) -> Any:
        pass


SQLAlchemySessionBaseUseCaseType = TypeVar('SQLAlchemySessionBaseUseCaseType', bound=SQLAlchemySessionBaseUseCase)


def alchemy_session_decorator(
    _func: Callable[[SQLAlchemySessionBaseUseCaseType, AsyncSession], Coroutine] | None = None,
) -> Callable:
    """
    Decorator to use with SQLAlchemySessionBaseUseCase and it's children, usually on an execute method.
    Just so we won't be always doing `async with ... as session:` as well as skip adding additional indent
    """

    def decorator(_func):
        @wraps(_func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            self: SQLAlchemySessionBaseUseCase = args[0]
            async with self._session_maker() as session:
                async with session.begin():
                    return await _func(*args, **kwargs, session=session)

        return wrapper

    if _func is None:
        return decorator
    else:
        return decorator(_func)


class BadRequestException(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)


class MessageDTO(BaseModel):
    message: str
    details: Any = None

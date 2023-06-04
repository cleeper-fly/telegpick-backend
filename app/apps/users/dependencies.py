from fastapi import Depends, Request

from app.apps.users.models import Users
from app.apps.users.use_cases import GetUserFromTokenUseCase


async def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get('access_token')


async def get_current_user(token: str = Depends(get_token_from_cookie)) -> Users:
    return await GetUserFromTokenUseCase(token=token).execute()

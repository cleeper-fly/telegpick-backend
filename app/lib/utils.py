from decimal import Decimal
from functools import wraps
from typing import Any, Awaitable, Callable

import orjson
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext


def serialize_decimals(obj: Any) -> str:
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError


def orjson_dumps(v: Any) -> str:  # noqa: WPS111
    """ORJSON dumps with decimals to str by default"""
    return orjson.dumps(v, default=serialize_decimals).decode()


def async_wrap(func: Callable) -> Callable:
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    pool = ThreadPoolExecutor()

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Awaitable:
        future = pool.submit(func, *args, **kwargs)
        return asyncio.wrap_future(future)  # make it awaitable

    return wrapper


pwd_context = CryptContext(schemes=['bcrypt_sha256'], deprecated=['auto'], bcrypt_sha256__rounds=18)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/users/login')

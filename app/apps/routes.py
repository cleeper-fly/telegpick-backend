from types import MappingProxyType

from fastapi import APIRouter

from app.apps.telegpick.api.v1.api import router as telegpick_app_router
from app.apps.users.api.v1.api import router as user_app_router
from app.core.config import get_settings

config = get_settings()


v1_routers: tuple[APIRouter, ...] = (user_app_router, telegpick_app_router)


api_v1_to_routers_map: MappingProxyType[str, tuple[APIRouter, ...]] = MappingProxyType(
    {
        'v1': v1_routers,
    }
)

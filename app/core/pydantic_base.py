import orjson
from pydantic import BaseModel as PydanticBaseModel


def _orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class BaseModel(PydanticBaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = _orjson_dumps
        arbitrary_types_allowed = True


class BaseModelORM(BaseModel):
    class Config(BaseModel.Config):
        orm_mode = True

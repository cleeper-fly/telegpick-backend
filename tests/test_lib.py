import asyncio
from decimal import Decimal

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.classes import SQLAlchemySessionBaseUseCase, alchemy_session_decorator
from app.lib.utils import async_wrap, orjson_dumps, serialize_decimals


def test_serialize_decimals():
    decimal = Decimal('0.1234')
    assert serialize_decimals(decimal) == '0.1234'

    number = 123
    with pytest.raises(TypeError):
        serialize_decimals(number)


def test_orjson_dumps_with_decimal():
    data = {'price': Decimal('10.5')}
    expected_output = '{"price":"10.5"}'

    assert orjson_dumps(data) == expected_output


def test_orjson_dumps_with_float():
    data = {'price': 10.5}
    expected_output = '{"price":10.5}'

    assert orjson_dumps(data) == expected_output


def test_async_wrap():
    @async_wrap
    def test_function(a: int, b: int) -> int:
        return a + b

    async def test_async_wrap_decorator():
        result = await test_function(1, 2)
        assert result == 3

    asyncio.run(test_async_wrap_decorator())


@pytest.mark.asyncio
async def test_alchemy_session_decorator(mocker: MockerFixture):
    class TestUseCase(SQLAlchemySessionBaseUseCase):
        @alchemy_session_decorator
        async def execute(self, session: AsyncSession) -> None:
            pass

    test_use_case = TestUseCase()
    execute_mock = mocker.patch.object(TestUseCase, 'execute', mocker.AsyncMock(return_value=None))

    await test_use_case.execute()

    assert execute_mock.called

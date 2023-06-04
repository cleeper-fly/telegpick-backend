from uuid import UUID

import pytest

from app.core.models import DBBaseModel


@pytest.mark.asyncio
async def test_db_base_model():
    # create an instance of the DBBaseModel
    model = DBBaseModel()
    model.id = UUID('123e4567-e89b-12d3-a456-426655440000')

    # assert that the repr string is correct
    assert repr(model) == '<DBBaseModel(id=UUID(\'123e4567-e89b-12d3-a456-426655440000\'))>'

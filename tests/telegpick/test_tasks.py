from datetime import datetime, timedelta

from pytest_mock import MockerFixture

from app.apps.telegpick.tasks import process_all_pics_task


def test_process_all_pics_task(mocker: MockerFixture) -> None:
    current_time = datetime.now()
    tm = current_time - timedelta(
        minutes=current_time.minute % 10, seconds=current_time.second, microseconds=current_time.microsecond
    )
    mock = mocker.patch('app.apps.telegpick.tasks.ProcessPicsTaskUseCase.execute', return_value=True)
    process_all_pics_task()
    mock.assert_called_once()

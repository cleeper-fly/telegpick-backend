from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse, ORJSONResponse

from app.apps.telegpick.dtos import ListPicsDTO, PicsDTO, SchedulesDTO
from app.apps.telegpick.use_cases import (
    CreatePicForUserUseCase,
    CreateScheduleForPicUseCase,
    DeletePicForUserUseCase,
    DeleteScheduleForPicUseCase,
    FetchPicsForUserUseCase,
    PatchPicForUserUseCase,
    PatchScheduleForPicUseCase,
    ReturnPicFileByIdUseCase,
    UploadPicOnDiskUseCase,
)
from app.apps.users.dependencies import get_current_user
from app.apps.users.models import Users
from app.lib.classes import MessageDTO

router: APIRouter = APIRouter(
    prefix='/telegpick',
    tags=['telegpick'],
    default_response_class=ORJSONResponse,
)


@router.get('/pic/list', response_model=ListPicsDTO, status_code=status.HTTP_200_OK)
async def get_pics(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user: Users = Depends(get_current_user),
) -> ListPicsDTO:
    pics = await FetchPicsForUserUseCase(user=user, page=page, limit=limit).execute()
    return ListPicsDTO(pics=pics)


@router.post('/pic/create', response_model=PicsDTO, status_code=status.HTTP_201_CREATED)
async def create_pic(pic: PicsDTO, user: Users = Depends(get_current_user)) -> PicsDTO:
    return PicsDTO.from_orm(await CreatePicForUserUseCase(pic=pic, user=user).execute())


@router.patch('/pic/update', response_model='', status_code=status.HTTP_200_OK)
async def patch_pic(
    pic: PicsDTO,
    user: Users = Depends(get_current_user),
) -> PicsDTO:
    return PicsDTO.from_orm(await PatchPicForUserUseCase(pic=pic, user=user).execute())


@router.delete('/{pic_id}/delete', response_model=MessageDTO, status_code=status.HTTP_200_OK)
async def delete_pic(
    pic_id: str,
    user: Users = Depends(get_current_user),
) -> MessageDTO:
    await DeletePicForUserUseCase(pic_id=pic_id, user=user).execute()
    return MessageDTO(message=f'Successfully deleted pic {pic_id}!')


@router.post('/{pic_id}/schedule/create', response_model=SchedulesDTO, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule: SchedulesDTO, pic_id: str, user: Users = Depends(get_current_user)) -> SchedulesDTO:
    return SchedulesDTO.from_orm(await CreateScheduleForPicUseCase(pic_id=pic_id, schedule=schedule).execute())


@router.patch('/{pic_id}/schedule/update', response_model='', status_code=status.HTTP_200_OK)
async def patch_schedule(schedule: SchedulesDTO, pic_id: str) -> SchedulesDTO:
    return SchedulesDTO.from_orm(await PatchScheduleForPicUseCase(schedule=schedule, pic_id=pic_id).execute())


@router.delete('/{pic_id}/{schedule_id}/delete', response_model='', status_code=status.HTTP_200_OK)
async def delete_schedule(schedule_id: str, pic_id: str, user: Users = Depends(get_current_user)) -> MessageDTO:
    await DeleteScheduleForPicUseCase(pic_id=pic_id, schedule_id=schedule_id).execute()
    return MessageDTO(message=f'Successfully deleted schedule {schedule_id}!')


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    filename: str = Form(...),
    timezone: str = Form(...),
    user: Users = Depends(get_current_user),
) -> MessageDTO:
    await UploadPicOnDiskUseCase(file=file, filename=filename, timezone=timezone, user=user).execute()
    return MessageDTO(message=f'Successfully uploaded file {filename}!')


@router.get("/{pic_id}/picture")
async def get_picture(pic_id: str, user: Users = Depends(get_current_user)) -> FileResponse:
    return await ReturnPicFileByIdUseCase(pic_id).execute()

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
from pydantic import SecretStr
from starlette import status
from starlette.responses import Response

from app.apps.telegpick.use_cases import UserConfirmCodeUseCase, UserSendVerificationUseCase
from app.apps.users.dtos import ConfirmationData, RegistrationData, UserDTO, UserLoginDTO
from app.apps.users.use_cases import AuthenticateUserUseCase, RegisterUserUseCase
from app.lib.classes import MessageDTO

router: APIRouter = APIRouter(
    prefix='/users',
    tags=['users'],
    default_response_class=ORJSONResponse,
)


@router.post('/register', response_model=UserDTO)
async def register(
    registration_data: RegistrationData,
) -> UserDTO:
    user = await RegisterUserUseCase(registration_data=registration_data).execute()
    await UserSendVerificationUseCase(user=user).execute()
    return UserDTO.from_orm(obj=user)


@router.post('/confirm_code', response_model='', status_code=status.HTTP_200_OK)
async def confirm_code(
    confirmation_data: ConfirmationData,
) -> MessageDTO:
    await UserConfirmCodeUseCase(code=confirmation_data.code, user_id=confirmation_data.user_id).execute()
    return MessageDTO(message='Successfully signed in')


@router.post('/login')
async def login(login_data: UserLoginDTO) -> Response:
    return await AuthenticateUserUseCase(
        username=login_data.username,
        password=SecretStr(login_data.password),
    ).execute()

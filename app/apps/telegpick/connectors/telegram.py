from telethon import TelegramClient, functions
from telethon.tl.types import InputPhoto

from app.apps.users.models import Users
from app.apps.users.use_cases import UpdatePhoneHashUseCase


class TelegramException(Exception):
    pass


class TelegramConnector:
    def __init__(self, user: Users) -> None:
        from app.core.init_app import settings

        self.user = user
        self.api_id = settings.TELEGRAM_API_ID
        self.api_hash = settings.TELEGRAM_API_HASH
        self.pic_directory = settings.PICS_DIRECTORY
        self.sessions_directory = settings.SESSIONS_DIRECTORY
        self.session = str(user.id)
        self.phone = user.phone

    async def send_code(self) -> None:
        client = TelegramClient(f'{self.sessions_directory}/{self.session}', self.api_id, self.api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                code_request = await client.send_code_request(self.phone)
                await UpdatePhoneHashUseCase(self.user, code_request.phone_code_hash).execute()

        except Exception as e:
            raise TelegramException(f'Error sending code: {e}')

    async def sign_in(self, code: str) -> None:
        client = TelegramClient(f'{self.sessions_directory}/{self.session}', self.api_id, self.api_hash)
        try:
            await client.connect()
            await client.sign_in(phone=self.phone, code=code, phone_code_hash=self.user.phone_hash)
        except Exception as e:
            raise TelegramException(f'Error signing in: {e}')

    async def set_avatar(self, filename: str) -> None:
        client = TelegramClient(f'{self.sessions_directory}/{self.session}', self.api_id, self.api_hash)
        try:
            await client.connect()
            await self.delete_avatar(client)
            input_file = await client.upload_file(f'{self.pic_directory}/{filename}')
            result = await client(functions.photos.UploadProfilePhotoRequest(file=input_file))
        except Exception as e:
            raise TelegramException(f'Error setting avatar: {e}')
        finally:
            await client.disconnect()

    async def delete_avatar(self, client: TelegramClient = None) -> None:
        if not client:
            client = TelegramClient(f'{self.sessions_directory}/{self.session}', self.api_id, self.api_hash)
            try:
                await client.connect()
            except Exception as e:
                raise TelegramException(f'Error connecting to delete existing avatar: {e}')
        try:
            p = await client.get_profile_photos('me')
            in_scope = p[0]
            await client(
                functions.photos.DeletePhotosRequest(
                    id=[
                        InputPhoto(
                            id=in_scope.id, access_hash=in_scope.access_hash, file_reference=in_scope.file_reference
                        )
                    ]
                )
            )
        except Exception as e:
            raise TelegramException(f'Error deleting existing avatar: {e}')

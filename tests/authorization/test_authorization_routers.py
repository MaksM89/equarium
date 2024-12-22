from httpx import AsyncClient
from starlette import status
from starlette.datastructures import FormData

from src.schemas import UserSchema, UserResponceSchema

async def test_logger_add_records(client: AsyncClient, caplog):
    data = dict(username='New user', password='123455678')
    responce = await client.post('/register', json=data)
    for r in caplog.records:
        assert getattr(r, 'user_id') == 'unknown'
        assert hasattr(r, 'request_id')

async def test_register(client: AsyncClient, caplog):
    data = dict(username='New user', password='123455678')
    responce = await client.post('/register', json=data)
    assert status.HTTP_201_CREATED == responce.status_code
    assert 'id' in responce.json()
    assert any(map(lambda x: x.startswith('Register'), caplog.messages))

async def test_register_return_400(client: AsyncClient, users: list[UserSchema]):
    data = dict(username=users[0].fullname, password='123455678')
    responce = await client.post('/register', json=data)
    assert status.HTTP_400_BAD_REQUEST == responce.status_code

async def test_login_for_access_token_return_token(
    client: AsyncClient, users: list[UserSchema]
):
    data = FormData(dict(username=users[0].fullname, password='123'))
    responce = await client.post('/token', data=data)
    assert status.HTTP_200_OK == responce.status_code
    info = responce.json()
    assert len(info) == 2
    assert 'access_token' in responce.json()
    assert 'token_type' in responce.json()

async def test_login_for_access_token_return_401_for_unauthorized_user(
    client: AsyncClient, users: list[UserSchema]
):
    data = FormData(dict(username='not exists', password='123'))
    responce = await client.post('/token', data=data)
    assert status.HTTP_401_UNAUTHORIZED == responce.status_code

async def test_read_users_me_for_authorized_client(client_u1: AsyncClient, users: list[UserSchema]):
    responce = await client_u1.get('/me')
    assert status.HTTP_200_OK == responce.status_code
    responce_json = responce.json()
    user_info = UserResponceSchema.model_validate(responce_json)
    assert users[0].id == user_info.id
    assert users[0].fullname == user_info.fullname
    assert responce_json.get('hashed_password') is None

async def test_read_users_me_for_unauthorized_client_return_401(
        client: AsyncClient, users: list[UserSchema]):
    responce = await client.get('/me')
    assert status.HTTP_401_UNAUTHORIZED == responce.status_code

async def test_change_user_password(client_u1: AsyncClient, users: list[UserSchema]):
    data = dict(old_password='123', new_password='111')
    responce = await client_u1.patch('/me/change_password', json=data)
    assert status.HTTP_200_OK == responce.status_code
    assert responce.json().get('hashed_password') is None

async def test_change_user_password_return_401(client_u1: AsyncClient, users: list[UserSchema]):
    data = dict(old_password='wrong_password', new_password='111')
    responce = await client_u1.patch('/me/change_password', json=data)
    assert status.HTTP_401_UNAUTHORIZED == responce.status_code

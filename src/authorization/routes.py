from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from src.authorization import crud, logger
from src.authorization.dependencies import authenticate_user, create_access_token, get_current_user
from src.authorization.utils import verify_password
from src.database.connection import get_async_session
from src.database.models import User
from src.schemas import TokenSchema, UserResponceSchema, UserRegisterRequestSchema

router = APIRouter(tags=['Сервис авторизации'])


@router.post(
    '/register',
    status_code=status.HTTP_201_CREATED,
    summary='Зарегистрировать нового пользователя'
)
async def register(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        info: Annotated[UserRegisterRequestSchema, Body()]
):
    """Ручка для регистрации новых пользователей.

    Параметры:
    - :body **username** - имя пользователя (уникальное для всех пользователей)
    - :body **password** - пароль (хотя бы один символ)

    :return: id нового пользователя
    """
    user_schema = await crud.create_user(session, **info.model_dump())
    if user_schema is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'User name already exists')
    logger.info('Register user %s', info.username)
    return user_schema.model_dump(include={'id'})

@router.post(
    '/token',
    response_model=TokenSchema,
    summary='Получение токена'
)
async def login_for_access_token(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenSchema:
    """Ручка для получниея токена для пользователя.

    Параметры:
    - :form **username** - имя пользователя
    - :form **password** - пароль

    :return: токен и тип токена
    """
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token = create_access_token({"sub": str(user.id), 'username': user.fullname})
    return TokenSchema(access_token=access_token)

@router.get(
    '/me',
    response_model=UserResponceSchema,
    summary='Получение информации о себе'
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user

@router.patch(
    '/me/change_password',
    summary='Смена пароля пользователя'
)
async def change_user_password(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    old_password: Annotated[str, Body()],
    new_password: Annotated[str, Body()]
):
    """Ручка для смены пароля пользователя.
    В случае успеха нужно запросить токен заново.

    Параметры:
    - :body **old_password** - старый пароль
    - :body **new_password** - новый пароль
    """
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    await crud.change_user_password(session, current_user.id, new_password)
    return JSONResponse(dict(status='ok'))
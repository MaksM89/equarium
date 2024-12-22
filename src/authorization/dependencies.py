from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from src.authorization import logger
from src.authorization.utils import verify_password
from src.crud import get_user
from src.database.connection import get_async_session
from src.database.models import User
from src.settings import settings
from src.utils import credentials_exception, decode_payload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def authenticate_user(
        session: AsyncSession,  # Annotated[AsyncSession, Depends(get_async_session)],
        username: str, password: str):
    user = await get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(
        data: dict,
        expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({"exp": expire, 'created': now.isoformat()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    payload_schema = await decode_payload(token)
    if payload_schema is None:
        raise credentials_exception
    user = await get_user(session, payload_schema.sub)
    if user is None or user.password_set_time.replace(tzinfo=timezone.utc) > payload_schema.created:
        logger.error('User not exists or password changed')
        raise credentials_exception
    return user

from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import get_user
from src.database.connection import get_async_session
from src.database.models import User
from src.utils import decode_payload, credentials_exception

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
async def get_current_user(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        header_value: Annotated[str, Depends(api_key_header)]
) -> User:
    scheme, token = get_authorization_scheme_param(header_value)
    if not header_value or scheme.lower() != "bearer":
        raise credentials_exception
    payload_schema = await decode_payload(token)
    if payload_schema is None:
        raise credentials_exception
    user = await get_user(session, payload_schema.sub)
    if user is None:
        raise credentials_exception
    return user
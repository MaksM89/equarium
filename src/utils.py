import uuid
from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import HTTPException
from jwt import InvalidTokenError
from pydantic import ValidationError
from starlette import status

from src.schemas import JWTPayloadSchema
from src.settings import settings

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def decode_payload(token: str) -> JWTPayloadSchema | None:
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": False,
        "verify_iat": False,
        "verify_aud": False,
        "verify_iss": False,
        'require': ['exp'],
    }
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options=options)
        payload_schema = JWTPayloadSchema.model_validate(payload)
        return payload_schema
    except (InvalidTokenError, ValidationError):
        pass

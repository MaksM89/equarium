import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Literal, Annotated

from pydantic import BaseModel, Field, ConfigDict, PlainSerializer

from src.database.models import TransactionStatus

DecimalS = Annotated[Decimal, PlainSerializer(lambda x: f'{x:.2f}', return_type=str, when_used='json')]

class UserRegisterRequestSchema(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1) # simple security check

class UserResponceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    fullname: str
    balance: DecimalS = Field(max_digits=20, decimal_places=2, ge=0)


class UserSchema(UserResponceSchema):
    hashed_password: str


class JWTPayloadSchema(BaseModel):
    model_config = ConfigDict(extra='allow')
    sub: uuid.UUID
    username: str
    created: datetime


class TokenSchema(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'

class TransactionCreateSchema(BaseModel):
    to_user_id: uuid.UUID
    amount: DecimalS = Field(max_digits=20, decimal_places=2, gt=0)

class TransactionResponceSchema(BaseModel):
    id: int
    dt: datetime
    status: TransactionStatus

class TransactionSchema(TransactionCreateSchema, TransactionResponceSchema):
    model_config = ConfigDict(from_attributes=True)
    from_user_id: uuid.UUID

class TransactionPagesCountSchema(BaseModel):
    pages_count: int
class TransactonHistoryParamsSchema(BaseModel):
    page: int = 1
    dt_start: date | None = None
    dt_end: date | None = None
    status: TransactionStatus | None = None

class TransactionHistoryResponceSchema(BaseModel):
    date: datetime
    direction: Literal['income', 'outcome']
    amount: DecimalS
    status: TransactionStatus




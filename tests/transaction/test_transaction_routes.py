import math
from functools import reduce

from httpx import AsyncClient
from starlette import status

from src.database.models import TransactionStatus
from src.schemas import UserSchema, TransactionCreateSchema, TransactionSchema, TransactonHistoryParamsSchema
from src.settings import settings


async def test_create_transaction(client_u1: AsyncClient, users: list[UserSchema]):
    data = TransactionCreateSchema(to_user_id=users[1].id, amount=users[0].balance).model_dump(mode='json')
    responce = await client_u1.post('/transaction/create', json=data)
    assert status.HTTP_201_CREATED == responce.status_code
    jsn = responce.json()
    assert 'id' in jsn
    assert 'dt' in jsn
    assert jsn['status'] == TransactionStatus.CREATED

async def test_create_transaction_return_403(client_u1: AsyncClient, users: list[UserSchema]):
    data = TransactionCreateSchema(to_user_id=users[1].id, amount=users[0].balance + 1).model_dump(mode='json')
    responce = await client_u1.post('/transaction/create', json=data)
    assert status.HTTP_403_FORBIDDEN == responce.status_code

async def test_get_user_transactions_pagescount(
        client_u1: AsyncClient,
        users: list[UserSchema],
        transactions: list[TransactionSchema]
):
    result = await client_u1.get('/transaction/pagescount')
    assert status.HTTP_200_OK == result.status_code
    jsn = result.json()
    exp = math.ceil(
        reduce(
            lambda x, y: x + int(y.from_user_id == users[0].id or y.to_user_id == users[0].id),
            transactions,
            0
        ) / settings.RECORDS_IN_PAGE
    )
    assert exp == jsn['pages_count']

async def test_get_user_transaction_history(
        client_u1: AsyncClient,
        users: list[UserSchema],
        transactions: list[TransactionSchema]
):
    user_id = users[0].id
    dt_start = transactions[2].dt.date()
    dt_end = transactions[-2].dt.date()
    stts = TransactionStatus.DONE
    params = TransactonHistoryParamsSchema(
        page=1,
        dt_start=dt_start,
        dt_end=dt_end,
        status=stts
    )
    result = await client_u1.get('/transaction/history', params=params.model_dump(mode='json'))
    assert status.HTTP_200_OK == result.status_code
    cnt = 0
    for t in transactions:
        if user_id in (t.from_user_id, t.to_user_id) \
            and dt_start <= t.dt.date() <= dt_end \
            and stts == t.status:
            if cnt < settings.RECORDS_IN_PAGE:
                cnt += 1
            else:
                break
    assert cnt == len(result.json())

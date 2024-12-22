import math
import random
from functools import reduce

import pytest
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.database.models import Transaction, TransactionStatus, User
from src.schemas import UserSchema, TransactionSchema
from src.settings import settings
from src.transaction.crud import get_transactions, create_transaction, imitate_process_transaction, \
    get_user_transactions_pagecount


async def test_create_transaction(session: AsyncSession, users: list[UserSchema]):
    u1 = users[0]
    u2 = users[1]
    t = await create_transaction(session, u1.id, u2.id, u1.balance)
    res = await session.scalar(
        select(Transaction)
        .where(
            and_(
                Transaction.from_user_id==u1.id,
                Transaction.to_user_id==u2.id,
                Transaction.amount==u1.balance
            )
        )
    )
    assert res is not None
    assert res.id == t.id
    assert res.dt == t.dt
    assert res.status == t.status

async def test_get_transactions_return_all_records_in_decreasing_order(
        session: AsyncSession,
        users: list[UserSchema],
        transactions: list[TransactionSchema]
):
    for user in users:
        expected_transactions_count = await session.scalar(
            select(func.count(Transaction.id))
            .where(
                or_(Transaction.from_user_id==user.id,
                    Transaction.to_user_id==user.id)
            )
        )
        user_tr = await get_transactions(session, user.id)
        assert expected_transactions_count == len(user_tr)
        for i in range(1, len(user_tr)):
            assert user_tr[i - 1][0] >= user_tr[i][0]

async def test_get_transactions_can_filter_by_date(
        session: AsyncSession,
        users: list[UserSchema],
        transactions: list[TransactionSchema]
):
    for user in users:
        expected_dt = (await session.scalars(
            select(Transaction.dt)
            .select_from(Transaction)
            .where(
                or_(Transaction.from_user_id==user.id,
                    Transaction.to_user_id==user.id)
            ).order_by(Transaction.dt.desc())
        )).all()
        dt_start, dt_end = sorted(random.sample(expected_dt, k = 2))
        expected_transactions_count = len(list(filter(lambda x: dt_start <= x <= dt_end, expected_dt)))
        user_tr = await get_transactions(session, user.id, dt_start=dt_start, dt_end=dt_end)
        assert expected_transactions_count == len(user_tr)
        for i in range(len(user_tr)):
            assert dt_start <= user_tr[i][0] <= dt_end

async def test_get_transactions_can_filter_by_status(
        session: AsyncSession,
        users: list[UserSchema],
        transactions: list[TransactionSchema]
):
    for user in users:
        expected_statuses = (await session.scalars(
            select(Transaction.status)
            .select_from(Transaction)
            .where(
                or_(Transaction.from_user_id==user.id,
                    Transaction.to_user_id==user.id)
            )
        )).all()
        status = random.choice(tuple(set(expected_statuses)))
        expected_transactions_count = len(list(filter(lambda x: x == status, expected_statuses)))
        user_tr = await get_transactions(session, user.id, status=status)
        assert expected_transactions_count == len(user_tr)
        for i in range(len(user_tr)):
            assert user_tr[i][-1] == status

async def test_get_transactions_can_paginate(
        session: AsyncSession,
        users: list[UserSchema],
        transactions: list[TransactionSchema]
):
    settings.RECORDS_IN_PAGE = 1 # one row per page
    for user in users:
        user_tr = (await session.scalars(
            select(Transaction)
            .where(
                or_(Transaction.from_user_id==user.id,
                    Transaction.to_user_id==user.id)
            ).order_by(Transaction.dt.desc())
        )).all()
        for i in range(len(user_tr)):
            result = await get_transactions(session, user.id, page=i + 1)
            assert len(result) == 1
            result = result[0]
            assert user_tr[i].dt == result[0]
            assert user_tr[i].amount == abs(result[2])
            assert user_tr[i].status == result[3]

async def test_imitate_process_transaction_done(
        session: AsyncSession, users: list[UserSchema]):
    transaction = await create_transaction(session, users[0].id, users[1].id, users[0].balance)
    await imitate_process_transaction(session, transaction.id)
    User1 = aliased(User)
    right = (
        await session.execute(
            select(
                User.balance == 0,
                User1.balance == users[0].balance + users[1].balance,
                Transaction.status == TransactionStatus.DONE
            ).join_from(Transaction, User, onclause=Transaction.from_user_id == User.id)
            .join(User1, onclause=Transaction.to_user_id == User1.id)
            .where(Transaction.id == transaction.id)
        )
    ).first()
    assert all(right)

async def test_imitate_process_transaction_canceled(
        session: AsyncSession, users: list[UserSchema]):
    transaction = await create_transaction(session, users[0].id, users[1].id, users[0].balance + 1)
    await imitate_process_transaction(session, transaction.id)
    User1 = aliased(User)
    right = (
        await session.execute(
            select(
                User.balance == users[0].balance,
                User1.balance == users[1].balance,
                Transaction.status == TransactionStatus.CANCELED
            ).join_from(Transaction, User, onclause=Transaction.from_user_id == User.id)
            .join(User1, onclause=Transaction.to_user_id == User1.id)
            .where(Transaction.id == transaction.id)
        )
    ).first()
    assert all(right)

async def test_get_user_transactions_pagecount(
        session: AsyncSession, users: list[UserSchema], transactions: list[TransactionSchema]
):
    for user in users:
        exp = math.ceil(
            reduce(
                lambda x, y: x + int(y.from_user_id == user.id or y.to_user_id == user.id),
                transactions,
                0
            ) / settings.RECORDS_IN_PAGE
        )
        res = await get_user_transactions_pagecount(session, user.id)
        assert exp == res
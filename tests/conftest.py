import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import random

import pytest
from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

import src
from src.authorization.utils import get_password_hash
from src.database.models import User, Transaction, TransactionStatus
from src.schemas import UserSchema, TransactionSchema
from src.settings import settings

@pytest.fixture(scope='session', autouse=True)
async def engine():
    if'test' not in settings.DB_NAME:
        settings.DB_NAME = 'test_' + settings.DB_NAME
    # This is the most simplistic, one shot system that prevents the Engine from using any connection more than once
    async_engine = create_async_engine(url=settings.db_url, echo=True, future=True, poolclass=NullPool)
    from src.database.models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield async_engine

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_engine.dispose()


@pytest.fixture(scope='function')
async def session(engine):
    conn = await engine.connect()
    trans = await conn.begin_nested()
    SessionMaker = async_sessionmaker(
        # expire_on_commit=False,
        # autocommit=False,
        # autoflush=False,
        bind=conn,
        # class_=AsyncSession,
        # close_resets_only=False
    )
    async with SessionMaker() as async_session:
        yield async_session

    await trans.rollback()
    await conn.close()

@pytest.fixture
async def users(session: AsyncSession) -> list[UserSchema]:
    """Create two users"""
    user_list = []
    for username, password, balance in (
        ('Ivanov Ivan', '123', Decimal('1000.00')),
        ('Petrov Petr', '321', Decimal('1000.00'))
    ):
        user_list.append(
            User(
                id=uuid.uuid4(),
                fullname=username,
                hashed_password=password, #get_password_hash(password),
                balance=balance
            )
        )
    users_schemas = list(map(UserSchema.model_validate, user_list))
    session.add_all(user_list)
    await session.commit()
    return users_schemas

@pytest.fixture
async def transactions(session: AsyncSession, users: list[UserSchema]) -> list[TransactionSchema]:
    deltas = sorted(set(random.randrange(1, 100) for _ in range(11)))
    trans_cnt = len(deltas)
    transactions = []
    for i in range(trans_cnt):
        f, t = random.sample(range(len(users)), k=2)
        cur_v = (Decimal(random.random()) * users[f].balance).quantize(Decimal('1.00'))
        status = TransactionStatus(TransactionStatus._member_names_[random.randrange(0, 4)].lower())
        transactions.append(
            Transaction(
                id=i + 1,
                dt=datetime.now() - timedelta(minutes=deltas[i]),
                from_user_id=users[f].id,
                to_user_id=users[t].id,
                amount=cur_v,
                status=status
            )
        )
        if status == TransactionStatus.DONE:
            users[f].balance -= cur_v
            users[t].balance += cur_v
    transaction_schemas = list(map(TransactionSchema.model_validate, transactions))
    dbusers = (await session.scalars(select(User))).all()
    for dbuser in dbusers:
        for user in users:
            if dbuser.id == user.id:
                dbuser.balance = user.balance
                break
    session.add_all(transactions)
    await session.commit()
    return transaction_schemas

@pytest.fixture(autouse=True)
def get_password_hash_and_verify_fast(monkeypatch):
    f = lambda x: x
    g = lambda x, y: x == y
    monkeypatch.setattr(src.authorization.crud, 'get_password_hash', f)
    monkeypatch.setattr(src.authorization.dependencies, 'verify_password', g)
    monkeypatch.setattr(src.authorization.routes, 'verify_password', g)
    yield
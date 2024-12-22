import math
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from asyncpg.transaction import TransactionState
from sqlalchemy import select, union_all, literal, Row, desc, insert, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.database.models import Transaction, TransactionStatus, User
from src.schemas import TransactionResponceSchema
from src.settings import settings
from src.transaction import logger


async def create_transaction(
        session: AsyncSession,
        from_user_id: uuid.UUID,
        to_user_id: uuid.UUID,
        amount: Decimal
) -> TransactionResponceSchema:
    stmt = (
        insert(Transaction)
        .values(dict(from_user_id=from_user_id, to_user_id=to_user_id, amount=amount))
        .returning(Transaction.id, Transaction.dt, Transaction.status)
    )
    result = (await session.execute(stmt)).first()
    ret = TransactionResponceSchema.model_construct(
        id=result[0],
        dt=result[1],
        status=result[2]
    )
    await session.commit()
    return ret

async def imitate_process_transaction(session: AsyncSession, t_id: int):
    await session.execute(
        update(Transaction)
        .values(status=TransactionStatus.PROCESSED)
        .where(Transaction.id == t_id)
    )
    await session.commit()
    logger.info('Status transaction %d - %s', t_id, TransactionStatus.PROCESSED)
    User1 = aliased(User)
    params = (
        await session.execute(
            select(User.id, User.balance, Transaction.amount, User1.id, User1.balance)
            .join_from(Transaction, User, onclause=User.id==Transaction.from_user_id)
            .join(User1, onclause=Transaction.to_user_id==User1.id)
            .where(Transaction.id == t_id)
        )
    ).first()
    if None in params or params[1] < params[2]:
        await session.execute(
            update(Transaction)
            .values(status=TransactionStatus.CANCELED)
            .where(Transaction.id == t_id)
        )
        logger.error('Transaction %d was canceled', t_id)
    else:
        await session.execute(
            update(User)
            .values(balance=params[1] - params[2])
            .where(User.id == params[0])
        )
        await session.execute(
            update(User)
            .values(balance=params[2] + params[4])
            .where(User.id == params[3])
        )
        await session.execute(
            update(Transaction)
            .values(status=TransactionStatus.DONE)
            .where(Transaction.id == t_id)
        )
        logger.info('Successfully processed transaction %d', t_id)
    await session.commit()


async def get_user_transactions_pagecount(
        session: AsyncSession,
        user_id: uuid.UUID
) -> int:
    stmt = (
        select(func.count(Transaction.id))
        .where(
            or_(
                Transaction.from_user_id==user_id,
                Transaction.to_user_id==user_id
            )
        )
    )
    total = await session.scalar(stmt)
    return math.ceil(total / settings.RECORDS_IN_PAGE)


async def get_transactions(
        session: AsyncSession,
        user_id: uuid.UUID,
        *,
        page: int | None = None,
        dt_start: datetime | None = None,
        dt_end:datetime | None = None,
        status: TransactionState | None = None,
) -> Sequence[Row]:
    stmts = []
    for i, c in enumerate((Transaction.from_user_id, Transaction.to_user_id)):
        stmt = select(
            Transaction.dt.label('date'),
            literal('outcome' if i == 0 else 'income').label('direction'),
            (Transaction.amount * (2 * i - 1)).label('amount'), # sign -1 or 1
            Transaction.status.label('status')
        ).where(c == user_id)
        if isinstance(dt_start, datetime):
            stmt = stmt.where(Transaction.dt >= dt_start)
        if isinstance(dt_end, datetime):
            stmt = stmt.where(Transaction.dt <= dt_end)
        if status is not None:
            stmt = stmt.where(Transaction.status == status)
        stmts.append(stmt)
    stmt = select(union_all(*stmts).subquery()).order_by(desc('date'))
    if page is not None and page > 0:
        stmt = (
            stmt
            .offset((page - 1) * settings.RECORDS_IN_PAGE)
            .limit(settings.RECORDS_IN_PAGE)
        )
    result = (await session.execute(stmt)).all()
    return result

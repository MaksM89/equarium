from typing import Annotated

from fastapi import APIRouter, Depends, Body, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.crud import get_user
from src.database.connection import get_async_session
from src.database.models import User
from src.schemas import TransactionCreateSchema, TransactionResponceSchema, TransactionPagesCountSchema, \
    TransactonHistoryParamsSchema, TransactionHistoryResponceSchema
from src.transaction import crud, logger
from src.transaction.crud import imitate_process_transaction
from src.transaction.dependencies import get_current_user

router = APIRouter(prefix='/transaction', tags=['Сервис транзакций'])

@router.post(
    '/create',
    response_model=TransactionResponceSchema,
    status_code=status.HTTP_201_CREATED,
    summary='Создать транзакцию'
)
async def create_transaction(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        user: Annotated[User, Depends(get_current_user)],
        params: Annotated[TransactionCreateSchema, Body()],
        background_tasks: BackgroundTasks
):
    """Ручка для перевода денег.

    Параметры:
    - :body **to_user_id** - id пользователя, которому нужно перевести
    - :body **amount** - сумма
    """
    second_user = await get_user(session, params.to_user_id)
    if user.balance < params.amount or second_user is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Bad request parameters')
    result = await crud.create_transaction(session, user.id, **params.model_dump())
    logger.info('Transaction %d was created', result.id)
    background_tasks.add_task(imitate_process_transaction, session, result.id)
    return result

@router.get(
    '/pagescount',
    response_model=TransactionPagesCountSchema,
    summary='Получение количества страниц записей о транзакциях (без фильтров)'
)
async def get_user_transactions_pagecount(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        user: Annotated[User, Depends(get_current_user)],
):
    result = await crud.get_user_transactions_pagecount(session, user.id)
    return TransactionPagesCountSchema(pages_count=result)

@router.get(
    '/history',
    response_model=list[TransactionHistoryResponceSchema],
    summary='История движения средств на балансе пользователя'
)
async def get_user_transaction_history(
        session: Annotated[AsyncSession, Depends(get_async_session)],
        user: Annotated[User, Depends(get_current_user)],
        params: Annotated[TransactonHistoryParamsSchema, Query()]
):
    """Ручка для получния записей о транзакциях по балансу пользователя.

    Параметры:
    - :body **page** - номер страницы (пагинация)
    Фильтры:
    - :body **dt_start** - дата начала
    - :body **dt_end** - дата окончания (включительно)
    - :body **status** - статус транзации
    """
    result = await crud.get_transactions(session, user.id, **params.model_dump())
    logger.info('User %s has %d transactions on page %d', user.id, len(result), params.page)
    return result

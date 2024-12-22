import uuid

from sqlalchemy import update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.authorization import logger
from src.authorization.utils import get_password_hash
from src.database.models import User
from src.schemas import UserSchema

async def create_user(session: AsyncSession, username: str, password: str) -> UserSchema | None:
    hashed_password = get_password_hash(password)
    user = User(id=uuid.uuid4(), fullname=username, hashed_password=hashed_password, balance=1000.0)
    user_schema = UserSchema.model_construct(**user.as_dict())
    session.add(user)
    try:
        await session.commit()
        return user_schema
    except IntegrityError:
        logger.exception('Cannot create user')
        await session.rollback()

async def change_user_password(session: AsyncSession, user_id: uuid.UUID, new_password: str):
    hashed_password = get_password_hash(new_password)
    stmt = update(User).where(User.id == user_id).values(hashed_password=hashed_password, password_set_time=func.now())
    await session.execute(stmt)
    await session.commit()
    logger.info('User changed his passowrd')

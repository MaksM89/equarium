from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.authorization.crud import change_user_password, create_user
from src.database.models import User
from src.schemas import UserSchema

async def test_create_user(session: AsyncSession):
    user_schema = await create_user(session, 'Ivan', '123')
    assert user_schema is not None
    user = (await session.scalars(select(User))).first()
    assert UserSchema.model_validate(user) == user_schema

async def test_change_user_password(session: AsyncSession, users: list[UserSchema]):
    new_password = 'new_password'
    await change_user_password(session, users[0].id, new_password)
    new_hashed_password = (
        await session.scalar(
            select(User.hashed_password).where(User.id == users[0].id)
        )
    )
    assert users[0].hashed_password != new_hashed_password

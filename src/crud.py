import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User


async def get_user(
        session: AsyncSession,
        id_or_name: str | uuid.UUID
) -> User | None:
    if isinstance(id_or_name, str):
        stmt = select(User).where(User.fullname == id_or_name)
    elif isinstance(id_or_name, uuid.UUID):
        stmt = select(User).where(User.id == id_or_name)
    else:
        return
    user = (await session.scalars(stmt)).first()
    return user
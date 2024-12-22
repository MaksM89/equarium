from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.transaction.dependencies import get_current_user
from src.transaction.web import app
from src.database.connection import get_async_session
from src.database.models import User
from src.schemas import UserSchema


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_async_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://127.0.0.1:8000') as ac:
        yield ac
    app.dependency_overrides = {}

@pytest.fixture
async def client_u1(
        client: AsyncClient,
        users: list[UserSchema],
        session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    async def get_test_user1() -> User:
        stmt = select(User).where(User.id == users[0].id)
        user1 = (await session.scalars(stmt)).one()
        return user1

    app.dependency_overrides[get_current_user] = get_test_user1
    yield client
    app.dependency_overrides = {}

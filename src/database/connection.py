from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.settings import settings

engine = create_async_engine(settings.db_url, echo=True)
SessionMaker = async_sessionmaker(engine)


async def get_async_session():
    async with SessionMaker() as session:
        yield session
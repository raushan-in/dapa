from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from settings import settings

database_url = settings.DATABASE_URL.get_secret_value()

engine = create_async_engine(database_url, echo=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """
    Dependency function to provide an async database session.
    Ensures proper cleanup after use.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


class Scammer(SQLModel, table=True):
    """Scammer ORM Model."""

    id: int = Field(default=None, primary_key=True)
    scammer_mobile: str = Field(index=True, description="Scammer mobile number")
    scam_id: int = Field(description="Scam ID of the scam type")
    reporter_ordeal: str = Field(description="Summary of the scam")
    reporter_mobile: str = Field(description="Reporter mobile number")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of report creation"
    )

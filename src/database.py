import re
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends
from pydantic import validator
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from scams import scam_categories
from settings import settings

database_url = settings.DATABASE_URL.get_secret_value()

engine = create_async_engine(database_url, echo=settings.is_dev())

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

    @validator("scammer_mobile", "reporter_mobile", pre=True)
    def validate_mobile_number(cls, value: str) -> str:
        """Validate mobile numbers using a regex."""
        pattern = r"^\+\d{1,3}-?\d{6,14}$"  # E.164 format
        if not re.match(pattern, value):
            raise ValueError(f"Invalid mobile number: {value}")
        return value

    @validator("scam_id")
    def validate_scam_id(cls, value: int) -> int:
        """Validate if scam_id exists in scam_categories."""
        if value not in scam_categories.keys():
            raise ValueError(
                f"Invalid scam_id: {value}. Must be one of {list(scam_categories.keys())}."
            )
        return value

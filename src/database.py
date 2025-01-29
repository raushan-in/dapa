"""
This module sets up the database connection using SQLAlchemy and SQLModel.
It includes the creation of an asynchronous engine and session for database operations.
"""

import re
from contextlib import asynccontextmanager
from datetime import datetime

from typing import Optional
from pydantic import validator, root_validator, EmailStr
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
    """
    Creates the database and tables if they do not already exist.
    It should be called during the application startup to ensure the database schema is up-to-date.
    """
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
    reporter_mobile: Optional[str] = Field(
        default=None, description="Reporter mobile number"
    )
    reporter_email: Optional[EmailStr] = Field(
        default=None, description="Reporter email"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp of report creation"
    )

    @root_validator(pre=True)
    @classmethod
    def check_contact_info(cls, values):
        """Ensure at least one of reporter_mobile or reporter_email is provided."""
        mobile = values.get("reporter_mobile")
        email = values.get("reporter_email")

        if not mobile and not email:
            raise ValueError(
                "At least one of 'reporter_mobile' or 'reporter_email' must be provided."
            )

        return values

    @staticmethod
    def validate_mobile_number(value: str) -> str:
        """Validate mobile numbers using a regex."""
        pattern = r"^\+\d{1,3}-?\d{6,14}$"  # E.164 format
        if value and not re.match(pattern, value):
            raise ValueError(f"Invalid mobile number: {value}")
        return value

    @root_validator(pre=True)
    @classmethod
    def apply_validations(cls, values):
        """Apply individual field validations."""
        if values.get("reporter_mobile"):
            values["reporter_mobile"] = cls.validate_mobile_number(
                values["reporter_mobile"]
            )
        return values

    @validator("scam_id")
    @classmethod
    def validate_scam_id(cls, value: int) -> int:
        """Validate if scam_id exists in scam_categories."""
        if value not in scam_categories:
            raise ValueError(
                f"Invalid scam_id: {value}. Must be one of {list(scam_categories.keys())}."
            )
        return value

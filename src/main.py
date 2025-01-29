"""
This module initializes and configures the FastAPI application for the DAPA project.
It sets up the application title, summary, and includes the necessary routers.
"""

import uvicorn
from fastapi import FastAPI

from database import create_db_and_tables
from routes import bot_router
from settings import settings


async def lifespan(_app):
    """
    Manages the lifespan of the FastAPI application.
    This function is called during the startup and shutdown of the application.
    """
    await create_db_and_tables()
    yield


app = FastAPI(title="DAPA", summary="Digital Arrest Protection App", lifespan=lifespan)

# Endpoint router
app.include_router(bot_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=settings.is_dev()
    )

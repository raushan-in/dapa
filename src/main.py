import uvicorn
from fastapi import FastAPI

from database import create_db_and_tables
from routes import bot_router
from settings import settings


async def lifespan(app):
    await create_db_and_tables()
    yield


app = FastAPI(title="DAPA", summary="Digital Arrest Protection App", lifespan=lifespan)

# Endpoint router
app.include_router(bot_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=settings.is_dev()
    )

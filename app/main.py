from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

import app.db as db
from app.api.routes import router as api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    db.init(get_settings())
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)

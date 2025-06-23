from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

import app.db as db
from app.api.routes import router as api_router
from app.config import get_settings
from app.services.constants import AUDIO_BUCKET, SPECTROGRAM_BUCKET
from app.services.s3_storage import open_s3_stores


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    db.init(get_settings())

    async with open_s3_stores(AUDIO_BUCKET, SPECTROGRAM_BUCKET) as stores:
        fastapi_app.state.audio_store = stores[AUDIO_BUCKET]
        fastapi_app.state.spectrogram_store = stores[SPECTROGRAM_BUCKET]

        yield

    await db.destroy_engine()


app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(api_router)

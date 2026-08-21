import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import get_settings
from app.workers.woocommerce_sync import run_sync_loop

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop = asyncio.Event()
    task = None
    configured = settings.woo_url and settings.woo_key and settings.woo_secret
    if configured:
        task = asyncio.create_task(run_sync_loop(settings, stop))
    try:
        yield
    finally:
        if task:
            stop.set()
            await task


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(router)

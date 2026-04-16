import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings

# Absolute path so static files resolve correctly regardless of the working
# directory — needed for Vercel serverless and local dev alike.
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB init + auto-seed is handled lazily in get_db() via _ensure_db_ready().
    # Vercel's Python runtime does not reliably fire ASGI lifespan events, so
    # we keep this hook as a no-op to avoid duplicate work.
    yield


app = FastAPI(
    title="AU Politicians Interests Dashboard",
    description="Searchable dashboard tracking Australian federal politicians' disclosed interests.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
app.include_router(router)

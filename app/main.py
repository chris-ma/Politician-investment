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
    # Auto-create tables on every cold-start (checkfirst=True makes it a
    # no-op if they already exist, so this is safe to repeat indefinitely).
    # This replaces the `python scripts/init_db.py` step that Railway ran
    # before uvicorn — Vercel has no equivalent pre-start hook.
    try:
        from app.db.base import Base
        from app.db.models import Politician, InterestsSummary, RefreshRun  # noqa: F401
        from app.db.session import _get_engine

        Base.metadata.create_all(bind=_get_engine(), checkfirst=True)
        log.info("Database tables verified/created on startup")
    except Exception as exc:
        # Log the error but don't prevent the app from starting — the
        # dashboard will show an empty state and the error will be visible
        # in Vercel function logs.
        log.error("Could not initialise database on startup: %s", exc)
    yield


app = FastAPI(
    title="AU Politicians Interests Dashboard",
    description="Searchable dashboard tracking Australian federal politicians' disclosed interests.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
app.include_router(router)

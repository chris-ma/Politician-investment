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
    try:
        from app.db.base import Base
        from app.db.models import Politician, InterestsSummary, RefreshRun  # noqa: F401
        from app.db.session import _get_engine, SessionLocal
        from sqlalchemy import text

        # 1. Create tables (no-op if they already exist)
        Base.metadata.create_all(bind=_get_engine(), checkfirst=True)
        log.info("Database tables verified/created on startup")

        # 2. Auto-seed on first deploy — if politicians table is empty, populate it
        #    immediately so the dashboard has data without any manual steps.
        db = SessionLocal()
        try:
            count = db.execute(text("SELECT COUNT(*) FROM politicians")).scalar() or 0
            if count == 0:
                log.info("Politicians table is empty — running auto-seed...")
                from scripts.seed_2025 import seed_db
                house, senate = seed_db(db)
                log.info("Auto-seed complete: %d house, %d senate", house, senate)
        except Exception as exc:
            log.warning("Auto-seed failed: %s", exc)
        finally:
            db.close()

    except Exception as exc:
        log.error("Startup init failed: %s", exc)
    yield


app = FastAPI(
    title="AU Politicians Interests Dashboard",
    description="Searchable dashboard tracking Australian federal politicians' disclosed interests.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
app.include_router(router)

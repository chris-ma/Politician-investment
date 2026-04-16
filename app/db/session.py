import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.core.config import settings

log = logging.getLogger(__name__)

_engine = None
_SessionLocal = None
_db_ready = False


def _get_engine():
    global _engine
    if _engine is None:
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")
        _engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=_get_engine()
        )
    return _SessionLocal


# Exported for standalone scripts (seed_2025.py, init_db.py, etc.)
def SessionLocal():
    return _get_session_factory()()


def _ensure_db_ready():
    """
    Idempotent: create tables then auto-seed politicians on first cold start.
    Called from get_db() so it runs before any request touches the DB.
    Vercel serverless doesn't reliably fire ASGI lifespan events, so we
    cannot rely on the lifespan hook for initialisation.
    """
    global _db_ready
    if _db_ready:
        return
    try:
        import sys
        import os as _os

        # Ensure project root is on sys.path so scripts.seed_2025 is importable
        _root = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        if _root not in sys.path:
            sys.path.insert(0, _root)

        from app.db.base import Base
        from app.db.models import Politician, InterestsSummary, RefreshRun  # noqa: F401
        from sqlalchemy import text

        Base.metadata.create_all(bind=_get_engine(), checkfirst=True)
        log.info("DB tables verified/created")

        db = _get_session_factory()()
        try:
            count = db.execute(text("SELECT COUNT(*) FROM politicians")).scalar() or 0
            if count == 0:
                log.info("Politicians table empty — auto-seeding 48th Parliament data…")
                from scripts.seed_2025 import seed_db
                house, senate = seed_db(db)
                log.info("Auto-seed done: %d house, %d senate", house, senate)
            else:
                log.info("Politicians table has %d rows — skipping seed", count)
        except Exception as exc:
            log.error("Auto-seed failed: %s", exc, exc_info=True)
            db.rollback()
        finally:
            db.close()

        _db_ready = True
    except Exception as exc:
        log.error("DB init failed: %s", exc, exc_info=True)


def get_db():
    """
    FastAPI dependency. Yields a live Session, or None when DATABASE_URL is
    not configured — routes must handle the None case to avoid a 500.
    """
    if not settings.DATABASE_URL:
        yield None
        return
    _ensure_db_ready()
    db: Session = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()

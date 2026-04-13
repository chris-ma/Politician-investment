from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.core.config import settings

_engine = None
_SessionLocal = None


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


def get_db():
    """
    FastAPI dependency. Yields a live Session, or None when DATABASE_URL is
    not configured — routes must handle the None case to avoid a 500.
    """
    if not settings.DATABASE_URL:
        yield None
        return
    db: Session = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()

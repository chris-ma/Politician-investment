from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Engine and session factory are created lazily on the first request.
# This prevents the function from crashing at import time if DATABASE_URL
# is missing or malformed — a common cause of FUNCTION_INVOCATION_FAILED
# on Vercel cold-starts before environment variables are confirmed correct.
_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set. "
                "Add it in the Vercel project settings under Environment Variables."
            )
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
    """FastAPI dependency that yields a database session."""
    db: Session = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# NullPool is used instead of a persistent connection pool because this app
# runs on Vercel serverless functions.  In serverless, each function
# invocation is isolated — a persistent pool would leak connections across
# cold-start instances.  NullPool opens and closes a connection per request,
# which is exactly the right behaviour with a hosted Postgres service (Vercel
# Postgres/Neon, Supabase, etc.) that has a built-in pgBouncer pooler.
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

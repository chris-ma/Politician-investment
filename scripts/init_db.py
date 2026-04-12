#!/usr/bin/env python3
"""
Create all database tables if they don't exist.
Safe to run multiple times (uses checkfirst=True).

Usage:
    python scripts/init_db.py
"""
import sys
import os

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from app.db.base import Base
from app.db.session import engine

# Import models so Base.metadata is populated
from app.db.models import Politician, InterestsSummary, RefreshRun  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def init_db() -> None:
    log.info("Connecting to database: %s", engine.url)
    Base.metadata.create_all(bind=engine, checkfirst=True)
    log.info(
        "Tables created (or already existed): %s",
        list(Base.metadata.tables.keys()),
    )


if __name__ == "__main__":
    init_db()

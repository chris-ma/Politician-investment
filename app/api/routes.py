import logging
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.dashboard import get_dashboard_rows, get_summary_stats

log = logging.getLogger(__name__)
router = APIRouter()

_templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
templates = Jinja2Templates(directory=_templates_dir)

_EMPTY_STATS = {
    "total_politicians": 0,
    "last_refresh_status": None,
    "last_refresh_at": None,
    "last_refresh_message": None,
}


@router.get("/health")
def health():
    return {
        "status": "ok",
        "database_configured": bool(settings.DATABASE_URL),
    }


@router.get("/api/dashboard")
def api_dashboard(db: Session = Depends(get_db)):
    if db is None:
        return {"error": "DATABASE_URL is not configured"}
    return get_dashboard_rows(db)


@router.get("/api/summary")
def api_summary(db: Session = Depends(get_db)):
    if db is None:
        return {"error": "DATABASE_URL is not configured"}
    return get_summary_stats(db)


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    """Render the searchable dashboard."""
    # ── No database configured ──────────────────────────────────────────────
    if db is None:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "rows": [],
                "stats": _EMPTY_STATS,
                "setup_error": (
                    "DATABASE_URL is not set. "
                    "Go to Vercel → your project → Settings → Environment Variables "
                    "and add DATABASE_URL pointing to a PostgreSQL instance "
                    "(Vercel Postgres, Neon, Supabase, etc.), then redeploy."
                ),
            },
        )

    # ── Database available ──────────────────────────────────────────────────
    try:
        rows = get_dashboard_rows(db)
        stats = get_summary_stats(db)
        setup_error = None
    except Exception as exc:
        log.error("Dashboard DB query failed: %s", exc)
        rows = []
        stats = _EMPTY_STATS
        setup_error = f"Database error: {exc}"

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "rows": rows,
            "stats": stats,
            "setup_error": setup_error,
        },
    )

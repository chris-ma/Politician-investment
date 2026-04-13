import logging
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard import get_dashboard_rows, get_summary_stats

log = logging.getLogger(__name__)
router = APIRouter()

# Use abspath so Jinja2 resolves templates correctly inside the Vercel sandbox
_templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
templates = Jinja2Templates(directory=_templates_dir)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/api/dashboard")
def api_dashboard(db: Session = Depends(get_db)):
    """Return the latest known interests summary for every politician."""
    return get_dashboard_rows(db)


@router.get("/api/summary")
def api_summary(db: Session = Depends(get_db)):
    """Return high-level stats: total politicians stored and last refresh info."""
    return get_summary_stats(db)


@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    """Render the searchable dashboard."""
    try:
        rows = get_dashboard_rows(db)
        stats = get_summary_stats(db)
    except Exception as exc:
        log.error("Dashboard DB query failed: %s", exc)
        rows = []
        stats = {
            "total_politicians": 0,
            "last_refresh_status": "error",
            "last_refresh_at": None,
            "last_refresh_message": str(exc),
        }
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "rows": rows, "stats": stats},
    )

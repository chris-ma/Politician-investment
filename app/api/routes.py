import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard import get_dashboard_rows, get_summary_stats

router = APIRouter()

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
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
    rows = get_dashboard_rows(db)
    stats = get_summary_stats(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "rows": rows, "stats": stats},
    )

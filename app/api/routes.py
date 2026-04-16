import datetime
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
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


@router.get("/api/admin/seed")
def admin_seed(token: str = "", db: Session = Depends(get_db)):
    """
    One-time seed endpoint — populates the DB with 48th Parliament politicians.

    Protected by the ADMIN_SECRET environment variable.
    Call it once in your browser:
        https://your-app.vercel.app/api/admin/seed?token=YOUR_SECRET

    Safe to call multiple times (upserts by slug).
    """
    if not settings.ADMIN_SECRET:
        raise HTTPException(status_code=503, detail="ADMIN_SECRET is not configured on this server.")
    if token != settings.ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token.")
    if db is None:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    from app.seed_data import HOUSE_MEMBERS, SENATORS, upsert_politician as _upsert, POLITICIAN_INTERESTS
    from app.db.models import InterestsSummary, RefreshRun

    now = datetime.datetime.utcnow()
    house_added = 0
    senate_added = 0

    try:
        db.add(RefreshRun(
            status="success",
            started_at=now,
            completed_at=now,
            message="Seeded via /api/admin/seed with Open Politics 47th Parliament investment data.",
        ))

        for name, electorate, state, party in HOUSE_MEMBERS:
            p = _upsert(db, name, "house", electorate, party)
            d = POLITICIAN_INTERESTS.get((name, "house"), {})
            db.add(InterestsSummary(
                politician_id=p.id,
                source_type="open_politics" if d else "pending",
                self_properties=d.get("self_re"),
                self_shares=d.get("self_sh"),
                partner_properties=d.get("partner_re"),
                partner_shares=d.get("partner_sh"),
                children_properties=d.get("children_re"),
                children_shares=d.get("children_sh"),
                total_interests=d.get("total"),
                notes="Source: Open Politics 47th Parliament (openpolitics.au)." if d else "No public data found.",
                refreshed_at=now,
            ))
            house_added += 1

        for name, state, party in SENATORS:
            p = _upsert(db, name, "senate", state, party)
            d = POLITICIAN_INTERESTS.get((name, "senate"), {})
            db.add(InterestsSummary(
                politician_id=p.id,
                source_type="open_politics" if d else "pending",
                self_properties=d.get("self_re"),
                self_shares=d.get("self_sh"),
                partner_properties=d.get("partner_re"),
                partner_shares=d.get("partner_sh"),
                children_properties=d.get("children_re"),
                children_shares=d.get("children_sh"),
                total_interests=d.get("total"),
                notes="Source: Open Politics 47th Parliament (openpolitics.au)." if d else "No public data found.",
                refreshed_at=now,
            ))
            senate_added += 1

        db.commit()
        log.info("Seed complete: %d house, %d senate", house_added, senate_added)
        return JSONResponse({
            "status": "ok",
            "house_members": house_added,
            "senators": senate_added,
            "total": house_added + senate_added,
        })

    except Exception as exc:
        db.rollback()
        log.error("Seed failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Seed failed: {exc}")


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
        if not rows:
            # Tables exist but are empty — seed inline on first visit
            log.info("No politicians found — seeding 48th Parliament data…")
            from app.seed_data import seed_db
            seed_db(db)
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

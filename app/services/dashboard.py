"""
Database query helpers for the dashboard endpoints.
"""
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import text


def get_dashboard_rows(db: Session) -> list[dict]:
    """
    Return the latest interest summary per politician, joined with politician metadata.
    Uses a LATERAL JOIN subquery (PostgreSQL) to efficiently fetch the most recent
    interests_summary row per politician.
    """
    sql = text("""
        SELECT
            p.id,
            p.slug,
            p.name,
            p.chamber,
            p.electorate_or_state,
            p.party,
            p.aph_url,
            p.register_pdf_url,
            p.updated_at_text,
            s.self_properties,
            s.self_shares,
            s.partner_properties,
            s.partner_shares,
            s.children_properties,
            s.children_shares,
            s.total_interests,
            s.notes,
            s.refreshed_at,
            s.source_type
        FROM politicians p
        LEFT JOIN LATERAL (
            SELECT *
            FROM interests_summary
            WHERE politician_id = p.id
            ORDER BY refreshed_at DESC
            LIMIT 1
        ) s ON TRUE
        ORDER BY p.name ASC
    """)
    rows = db.execute(sql).mappings().all()
    return [dict(r) for r in rows]


def get_summary_stats(db: Session) -> dict[str, Any]:
    """Overall stats for the summary card."""
    count_sql = text("SELECT COUNT(*) FROM politicians")
    total = db.execute(count_sql).scalar() or 0

    run_sql = text("""
        SELECT status, completed_at, message
        FROM refresh_runs
        ORDER BY started_at DESC
        LIMIT 1
    """)
    run = db.execute(run_sql).mappings().first()

    return {
        "total_politicians": total,
        "last_refresh_status": run["status"] if run else None,
        "last_refresh_at": (
            run["completed_at"].isoformat() if run and run["completed_at"] else None
        ),
        "last_refresh_message": run["message"] if run else None,
    }

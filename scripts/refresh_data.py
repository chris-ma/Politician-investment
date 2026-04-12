#!/usr/bin/env python3
"""
Daily ETL: scrape APH register pages, download and parse PDFs, upsert to DB.

Usage:
    python scripts/refresh_data.py

Steps:
  1. Create a refresh_runs row with status "running".
  2. Fetch the House + Senate register HTML pages.
  3. Parse politician rows (name, electorate, party, PDF link, updated date).
  4. Upsert politician metadata into the politicians table.
  5. For each politician, download and parse their register PDF.
  6. Insert a new interests_summary row (append-only for history).
  7. Mark the refresh run as "success", "partial", or "failed".
"""
import sys
import os

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import io
import logging
import datetime
from typing import Optional

import httpx
import pdfplumber
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import Politician, InterestsSummary, RefreshRun

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("refresh_data")

# ── HTTP client configuration ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AusPoliticianDashboard/1.0; "
        "research/transparency use)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
    "Accept-Language": "en-AU,en;q=0.9",
}
HTTP_TIMEOUT = 60  # seconds

# ── PDF section detection patterns ─────────────────────────────────────────
# Matches "B. Real estate", "Real estate", "REAL ESTATE" as a standalone heading line
_RE_REAL_ESTATE = re.compile(
    r"^\s*(?:[A-Z]\.\s+)?real\s+estate\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Matches "D. Publicly listed companies", "Shares", "Shareholdings"
_RE_SHARES = re.compile(
    r"^\s*(?:[A-Z]\.\s+)?(?:publicly\s+listed\s+companies?|shares?|shareholdings?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Holder subsection markers (standalone lines in a section)
_RE_HOLDER_SELF = re.compile(r"^\s*self\s*$", re.IGNORECASE)
_RE_HOLDER_SPOUSE = re.compile(
    r"^\s*(?:spouse|partner|spouse[/\\]partner|husband|wife|de\s*facto)\s*$",
    re.IGNORECASE,
)
_RE_HOLDER_CHILDREN = re.compile(
    r"^\s*(?:dependent\s+)?children?\s*$",
    re.IGNORECASE,
)

# Lines to skip when counting items (blank, page markers, section headers)
_RE_SKIP_LINE = re.compile(
    r"^\s*$"
    r"|^---\s*PAGE\s*BREAK"
    r"|^\s*(?:real\s+estate|publicly\s+listed\s+companies?|shares?|shareholdings?)\s*$"
    r"|^\s*(?:register\s+of|interests\s+registered|member\s+of\s+parliament|senator\s+for)\b",
    re.IGNORECASE,
)

# Numbered list items: "1. 123 Main St..." or "1) ..."
_RE_NUMBERED_ITEM = re.compile(r"^\s*\d+[.)]\s+\S")


# ── Slug generation ────────────────────────────────────────────────────────

def make_slug(name: str, chamber: str) -> str:
    """
    Generate a stable unique slug.
    "Smith, John" + "house" → "house-smith-john"
    """
    clean = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    clean = re.sub(r"[\s-]+", "-", clean.strip("-"))
    return f"{chamber}-{clean}"


# ── URL resolution ─────────────────────────────────────────────────────────

def _resolve_url(href: str) -> str:
    if not href:
        return ""
    href = href.strip()
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return settings.APH_BASE_URL.rstrip("/") + href
    return settings.APH_BASE_URL.rstrip("/") + "/" + href


# ── Text extraction helpers ────────────────────────────────────────────────

def _extract_electorate(text: str, chamber: str) -> Optional[str]:
    """Extract electorate (House) or state (Senate) from entry text."""
    if chamber == "senate":
        m = re.search(
            r"\b(New South Wales|Victoria|Queensland|Western Australia|"
            r"South Australia|Tasmania|Australian Capital Territory|"
            r"Northern Territory|NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\b",
            text,
            re.IGNORECASE,
        )
        return m.group(1) if m else None
    else:
        # "Division of Mackellar" or "Electorate of ..."
        m = re.search(
            r"(?:Division|Electorate)\s+of\s+([A-Z][A-Za-z\s'-]+?)(?:\s{2,}|\(|,|$)",
            text,
        )
        if m:
            return m.group(1).strip()
        return None


def _extract_party(text: str) -> Optional[str]:
    """Extract party from text — looks for parenthetical or known party names."""
    # Parenthetical like "(Australian Labor Party)" or "(ALP)"
    m = re.search(r"\(([A-Za-z][^)]{2,80})\)", text)
    if m:
        candidate = m.group(1).strip()
        # Avoid capturing electorates or dates in parens
        if not re.search(r"\d{4}", candidate) and len(candidate) < 80:
            return candidate
    # Known party name substrings
    KNOWN_PARTIES = [
        "Australian Labor Party",
        "Liberal Party of Australia",
        "Liberal Party",
        "National Party of Australia",
        "National Party",
        "The Nationals",
        "Australian Greens",
        "Independent",
        "One Nation",
        "Centre Alliance",
        "Katter's Australian Party",
        "United Australia Party",
        "David Pocock",  # listed as independent
    ]
    for party in KNOWN_PARTIES:
        if party.lower() in text.lower():
            return party
    return None


def _extract_updated_date(text: str) -> Optional[str]:
    """Extract the most recent 'Updated: DD Month YYYY' date string."""
    m = re.search(
        r"[Uu]pdated:?\s*(\d{1,2}\s+\w+\s+\d{4})",
        text,
    )
    if m:
        return m.group(1)
    # Bare date like "15 March 2024"
    m = re.search(
        r"\b(\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"\s+\d{4})\b",
        text,
    )
    return m.group(1) if m else None


# ── HTML parsing ───────────────────────────────────────────────────────────

def _parse_list_item(li, chamber: str) -> Optional[dict]:
    """Parse a single <li> element into a politician entry dict."""
    text = li.get_text(separator=" ", strip=True)
    if not text or len(text) < 5:
        return None

    links = li.find_all("a", href=True)
    name = None
    aph_url = None
    register_pdf_url = None

    for a in links:
        href = a.get("href", "").strip()
        link_text = a.get_text(strip=True)

        lower_href = href.lower()
        if lower_href.endswith(".pdf") or "/getdoc/" in lower_href or "pdf" in lower_href:
            register_pdf_url = _resolve_url(href)
        elif (
            "/Senators_and_Members/Parliamentarian" in href
            or "/senators_and_members/" in href.lower()
            or "/members/" in href.lower()
            or "MPID=" in href
            or "mpid=" in href.lower()
        ):
            if link_text:
                name = link_text
                aph_url = _resolve_url(href)
        elif name is None and link_text and len(link_text) > 3:
            # Fallback: first meaningful link text is the name
            name = link_text
            aph_url = _resolve_url(href)

    if not name:
        return None

    return {
        "name": name.strip(),
        "electorate_or_state": _extract_electorate(text, chamber),
        "party": _extract_party(text),
        "aph_url": aph_url,
        "register_pdf_url": register_pdf_url,
        "updated_at_text": _extract_updated_date(text),
    }


def _parse_pdf_link_context(a_tag, chamber: str) -> Optional[dict]:
    """
    Fallback strategy: given an <a> tag pointing to a PDF, extract politician
    info from surrounding context (parent element text).
    """
    href = a_tag.get("href", "").strip()
    if not href:
        return None

    # Walk up the DOM to find a container with meaningful text
    container = a_tag.parent
    for _ in range(4):
        if container is None:
            return None
        text = container.get_text(separator=" ", strip=True)
        if len(text) > 20:
            break
        container = container.parent

    if not text or len(text) < 10:
        return None

    # First linked text in the container that isn't the PDF link
    name = None
    aph_url = None
    for a in (container.find_all("a", href=True) if container else []):
        link_href = a.get("href", "")
        link_text = a.get_text(strip=True)
        if "pdf" not in link_href.lower() and "/getdoc/" not in link_href.lower():
            if link_text and len(link_text) > 3:
                name = link_text
                aph_url = _resolve_url(link_href)
                break

    if not name:
        return None

    return {
        "name": name.strip(),
        "electorate_or_state": _extract_electorate(text, chamber),
        "party": _extract_party(text),
        "aph_url": aph_url,
        "register_pdf_url": _resolve_url(href),
        "updated_at_text": _extract_updated_date(text),
    }


def scrape_register_page(
    url: str, chamber: str, client: httpx.Client
) -> list[dict]:
    """
    Fetch an APH register page and return a list of politician entry dicts.
    Uses a multi-strategy approach resilient to APH site redesigns.
    """
    log.info("Fetching register page [%s]: %s", chamber, url)
    response = client.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    # Find main content area (try selectors in priority order)
    content = (
        soup.find("div", class_="section-wrapper")
        or soup.find("div", id="main-content")
        or soup.find("main")
        or soup.find("div", class_="container")
        or soup.body
    )

    politicians: list[dict] = []
    seen_names: set[str] = set()

    def _add(entry: Optional[dict]) -> None:
        if entry and entry.get("name"):
            key = entry["name"].lower().strip()
            if key not in seen_names:
                seen_names.add(key)
                politicians.append(entry)

    # Strategy 1: parse <ul>/<ol> list items
    for lst in content.find_all(["ul", "ol"]):
        for li in lst.find_all("li", recursive=False):
            _add(_parse_list_item(li, chamber))

    # Strategy 2: if strategy 1 found nothing, scan all PDF links
    if not politicians:
        log.info("List strategy found no entries — trying PDF link scan")
        for a_tag in content.find_all("a", href=re.compile(r"\.pdf", re.IGNORECASE)):
            _add(_parse_pdf_link_context(a_tag, chamber))

    # Strategy 3: look for <dl> definition lists or <table> rows
    if not politicians:
        log.info("PDF link strategy found no entries — trying table/dl scan")
        for row in content.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                fake_li = BeautifulSoup(
                    "<li>" + row.decode_contents() + "</li>", "lxml"
                ).find("li")
                if fake_li:
                    _add(_parse_list_item(fake_li, chamber))

        for dt in content.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if dd:
                combined = BeautifulSoup(
                    "<li>" + dt.decode_contents() + " " + dd.decode_contents() + "</li>",
                    "lxml",
                ).find("li")
                if combined:
                    _add(_parse_list_item(combined, chamber))

    log.info("Found %d entries on %s register page", len(politicians), chamber)
    return politicians


# ── PDF parsing ────────────────────────────────────────────────────────────

def _find_section_boundaries(lines: list[str]) -> list[tuple]:
    """
    Scan lines and return [(section_type, start_idx, end_idx), ...].
    section_type is "real_estate" or "shares".
    Sections end where the next section starts (or EOF).
    """
    SECTION_MATCHERS = [
        ("real_estate", _RE_REAL_ESTATE),
        ("shares", _RE_SHARES),
    ]

    results = []
    current_section: Optional[str] = None
    current_start = 0

    for i, line in enumerate(lines):
        for section_type, pattern in SECTION_MATCHERS:
            if pattern.match(line):
                if current_section:
                    results.append((current_section, current_start, i))
                current_section = section_type
                current_start = i + 1
                break

    if current_section:
        results.append((current_section, current_start, len(lines)))

    return results


def _count_by_holder(section_lines: list[str]) -> dict[str, int]:
    """
    Within a section, count interest items per holder type.

    Holder subsections are delimited by standalone 'Self' / 'Spouse/Partner' /
    'Children' heading lines. Lines are counted as items if they look like
    content (numbered items, or non-blank lines longer than 10 chars).
    """
    counts = {"self": 0, "partner": 0, "children": 0}
    current_holder = "self"  # default: assume self if no subsection header found

    for line in section_lines:
        stripped = line.strip()

        if _RE_SKIP_LINE.match(line):
            continue

        if _RE_HOLDER_SELF.match(stripped):
            current_holder = "self"
            continue
        if _RE_HOLDER_SPOUSE.match(stripped):
            current_holder = "partner"
            continue
        if _RE_HOLDER_CHILDREN.match(stripped):
            current_holder = "children"
            continue

        # Count the line as one item
        if _RE_NUMBERED_ITEM.match(line):
            counts[current_holder] += 1
        elif len(stripped) > 10:
            counts[current_holder] += 1

    return counts


def parse_pdf(pdf_bytes: bytes, politician_name: str) -> dict:
    """
    Extract interest counts from a PDF filing.
    Returns a dict compatible with InterestsSummary fields.
    """
    result = {
        "source_type": "pdf",
        "self_properties": 0,
        "self_shares": 0,
        "partner_properties": 0,
        "partner_shares": 0,
        "children_properties": 0,
        "children_shares": 0,
        "total_interests": 0,
        "notes": None,
    }
    errors: list[str] = []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = "\n\n--- PAGE BREAK ---\n\n".join(
                page.extract_text() or "" for page in pdf.pages
            )

        if not full_text.strip():
            result["notes"] = "PDF yielded no extractable text (may be image-only)"
            result["source_type"] = "unavailable"
            return result

        lines = full_text.splitlines()
        boundaries = _find_section_boundaries(lines)

        if not boundaries:
            result["notes"] = "No recognisable interest sections found in PDF"

        for section_type, start, end in boundaries:
            section_lines = lines[start:end]
            counts = _count_by_holder(section_lines)
            if section_type == "real_estate":
                result["self_properties"] = counts["self"]
                result["partner_properties"] = counts["partner"]
                result["children_properties"] = counts["children"]
            elif section_type == "shares":
                result["self_shares"] = counts["self"]
                result["partner_shares"] = counts["partner"]
                result["children_shares"] = counts["children"]

    except Exception as exc:
        errors.append(f"PDF parse error: {exc}")
        log.warning("PDF parse failed for %s: %s", politician_name, exc)
        result["source_type"] = "unavailable"

    result["total_interests"] = sum(
        result[k] or 0
        for k in (
            "self_properties", "self_shares",
            "partner_properties", "partner_shares",
            "children_properties", "children_shares",
        )
    )

    if errors:
        existing = result.get("notes") or ""
        result["notes"] = (existing + "; " + "; ".join(errors)).lstrip("; ")

    return result


# ── Database upserts ───────────────────────────────────────────────────────

def upsert_politician(db: Session, data: dict, chamber: str) -> Politician:
    """Upsert politician by slug, returning the persisted instance."""
    slug = make_slug(data["name"], chamber)
    politician = db.query(Politician).filter_by(slug=slug).first()

    if politician is None:
        politician = Politician(slug=slug, chamber=chamber)
        db.add(politician)

    politician.name = data["name"]
    politician.electorate_or_state = data.get("electorate_or_state")
    politician.party = data.get("party")
    politician.aph_url = data.get("aph_url")
    politician.register_pdf_url = data.get("register_pdf_url")
    politician.updated_at_text = data.get("updated_at_text")
    db.flush()
    return politician


def insert_summary(db: Session, politician: Politician, summary_data: dict) -> None:
    """Insert a new summary row (append-only — preserves history)."""
    summary = InterestsSummary(
        politician_id=politician.id,
        refreshed_at=datetime.datetime.utcnow(),
        source_type=summary_data.get("source_type", "unavailable"),
        total_interests=summary_data.get("total_interests"),
        self_properties=summary_data.get("self_properties"),
        self_shares=summary_data.get("self_shares"),
        partner_properties=summary_data.get("partner_properties"),
        partner_shares=summary_data.get("partner_shares"),
        children_properties=summary_data.get("children_properties"),
        children_shares=summary_data.get("children_shares"),
        notes=summary_data.get("notes"),
    )
    db.add(summary)


# ── Main ETL orchestration ─────────────────────────────────────────────────

def run_refresh() -> None:
    db: Session = SessionLocal()
    run = RefreshRun(status="running", started_at=datetime.datetime.utcnow())
    db.add(run)
    db.commit()
    log.info("Refresh run started (id=%s)", run.id)

    total = 0
    failed = 0
    errors_log: list[str] = []

    try:
        with httpx.Client(follow_redirects=True, timeout=HTTP_TIMEOUT) as client:
            for url, chamber in [
                (settings.APH_MEMBERS_URL, "house"),
                (settings.APH_SENATORS_URL, "senate"),
            ]:
                try:
                    entries = scrape_register_page(url, chamber, client)
                except Exception as exc:
                    log.error("Failed to scrape %s register: %s", chamber, exc)
                    errors_log.append(f"Scrape {chamber}: {exc}")
                    continue

                for entry in entries:
                    total += 1
                    name = entry.get("name", "unknown")
                    pdf_url = entry.get("register_pdf_url")

                    # Default summary if we can't get/parse the PDF
                    summary_data: dict = {
                        "source_type": "unavailable",
                        "total_interests": None,
                        "self_properties": None,
                        "self_shares": None,
                        "partner_properties": None,
                        "partner_shares": None,
                        "children_properties": None,
                        "children_shares": None,
                        "notes": "No PDF link found" if not pdf_url else None,
                    }

                    if pdf_url:
                        try:
                            log.debug("Downloading PDF for %s: %s", name, pdf_url)
                            resp = client.get(
                                pdf_url, headers=HEADERS, timeout=HTTP_TIMEOUT
                            )
                            resp.raise_for_status()
                            summary_data = parse_pdf(resp.content, name)
                        except Exception as exc:
                            failed += 1
                            note = f"PDF download/parse failed: {exc}"
                            log.warning("%-40s  %s", name, note)
                            errors_log.append(f"{name}: {note}")
                            summary_data["notes"] = note
                            summary_data["source_type"] = "unavailable"

                    try:
                        politician = upsert_politician(db, entry, chamber)
                        insert_summary(db, politician, summary_data)
                        db.commit()
                        log.debug("Saved: %s (%s)", name, chamber)
                    except Exception as exc:
                        db.rollback()
                        failed += 1
                        log.error("DB upsert failed for %s: %s", name, exc)
                        errors_log.append(f"DB {name}: {exc}")

        if failed == 0:
            status = "success"
        elif failed < total:
            status = "partial"
        else:
            status = "failed"

        message = f"Processed {total} politicians, {failed} failures."
        if errors_log:
            # Truncate to first 10 errors to keep message manageable
            message += " Errors: " + " | ".join(errors_log[:10])
            if len(errors_log) > 10:
                message += f" ... and {len(errors_log) - 10} more."

    except Exception as exc:
        status = "failed"
        message = str(exc)
        log.exception("Fatal error during refresh")

    run.completed_at = datetime.datetime.utcnow()
    run.status = status
    run.message = message
    db.commit()
    db.close()

    log.info("Refresh complete: status=%s  %s", status, message)


if __name__ == "__main__":
    run_refresh()

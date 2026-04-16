#!/usr/bin/env python3
"""
Seed the database with real Australian federal politicians from the 48th Parliament
(elected May 2025). Covers House of Representatives and Senate members.

This script populates politician metadata only. Interest counts are set to null
and source_type="pending" until the daily refresh script parses the PDF filings.

Usage:
    python scripts/seed_2025.py
"""
import sys
import os
import re
import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.models import Politician, InterestsSummary, RefreshRun

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

APH_BASE = "https://www.aph.gov.au"
APH_REGISTER_HOUSE = f"{APH_BASE}/Parliamentary_Business/Disclosures/Register_of_Members_Interests"
APH_REGISTER_SENATE = f"{APH_BASE}/Parliamentary_Business/Disclosures/Register_of_Senators_Interests"


def make_slug(name: str, chamber: str) -> str:
    clean = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    clean = re.sub(r"[\s-]+", "-", clean.strip("-"))
    return f"{chamber}-{clean}"


# ── House of Representatives ───────────────────────────────────────────────
# (name, electorate, state, party)
HOUSE_MEMBERS = [
    # ── Australian Labor Party ──────────────────────────────────────────────
    ("Anthony Albanese",       "Grayndler",      "NSW", "Australian Labor Party"),
    ("Jim Chalmers",           "Rankin",          "QLD", "Australian Labor Party"),
    ("Richard Marles",         "Corio",           "VIC", "Australian Labor Party"),
    ("Tanya Plibersek",        "Sydney",          "NSW", "Australian Labor Party"),
    ("Chris Bowen",            "McMahon",         "NSW", "Australian Labor Party"),
    ("Mark Dreyfus",           "Isaacs",          "VIC", "Australian Labor Party"),
    ("Jason Clare",            "Blaxland",        "NSW", "Australian Labor Party"),
    ("Clare O'Neil",           "Hotham",          "VIC", "Australian Labor Party"),
    ("Tony Burke",             "Watson",          "NSW", "Australian Labor Party"),
    ("Pat Conroy",             "Shortland",       "NSW", "Australian Labor Party"),
    ("Stephen Jones",          "Whitlam",         "NSW", "Australian Labor Party"),
    ("Amanda Rishworth",       "Kingston",        "SA",  "Australian Labor Party"),
    ("Catherine King",         "Ballarat",        "VIC", "Australian Labor Party"),
    ("Brendan O'Connor",       "Gorton",          "VIC", "Australian Labor Party"),
    ("Michelle Rowland",       "Greenway",        "NSW", "Australian Labor Party"),
    ("Matt Keogh",             "Burt",            "WA",  "Australian Labor Party"),
    ("Julie Collins",          "Franklin",        "TAS", "Australian Labor Party"),
    ("Madeleine King",         "Brand",           "WA",  "Australian Labor Party"),
    ("Kristy McBain",          "Eden-Monaro",     "NSW", "Australian Labor Party"),
    ("Josh Burns",             "Macnamara",       "VIC", "Australian Labor Party"),
    ("Mike Freelander",        "Macarthur",       "NSW", "Australian Labor Party"),
    ("Anne Aly",               "Cowan",           "WA",  "Australian Labor Party"),
    ("Peter Khalil",           "Wills",           "VIC", "Australian Labor Party"),
    ("Josh Wilson",            "Fremantle",       "WA",  "Australian Labor Party"),
    ("Patrick Gorman",         "Perth",           "WA",  "Australian Labor Party"),
    ("Sharon Claydon",         "Newcastle",       "NSW", "Australian Labor Party"),
    ("Fiona Phillips",         "Gilmore",         "NSW", "Australian Labor Party"),
    ("Emma McBride",           "Dobell",          "NSW", "Australian Labor Party"),
    ("Meryl Swanson",          "Paterson",        "NSW", "Australian Labor Party"),
    ("Brian Mitchell",         "Lyons",           "TAS", "Australian Labor Party"),
    ("Jerome Laxale",          "Bennelong",       "NSW", "Australian Labor Party"),
    ("Daniel Mulino",          "Fraser",          "VIC", "Australian Labor Party"),
    ("Cassandra Fernando",     "Holt",            "VIC", "Australian Labor Party"),
    ("Carina Garland",         "Chisholm",        "VIC", "Australian Labor Party"),
    ("Sam Rae",                "Hawke",           "VIC", "Australian Labor Party"),
    ("Louise Miller-Frost",    "Boothby",         "SA",  "Australian Labor Party"),
    ("Alicia Payne",           "Canberra",        "ACT", "Australian Labor Party"),
    ("Andrew Leigh",           "Fenner",          "ACT", "Australian Labor Party"),
    ("Marion Scrymgour",       "Lingiari",        "NT",  "Australian Labor Party"),
    ("Luke Gosling",           "Solomon",         "NT",  "Australian Labor Party"),
    ("Zaneta Mascarenhas",     "Swan",            "WA",  "Australian Labor Party"),
    ("Steve Georganas",        "Hindmarsh",       "SA",  "Australian Labor Party"),
    ("Tony Zappia",            "Makin",           "SA",  "Australian Labor Party"),
    ("Kate Thwaites",          "Jagajaga",        "VIC", "Australian Labor Party"),
    ("Lisa Chesters",          "Bendigo",         "VIC", "Australian Labor Party"),
    ("Peta Murphy",            "Dunkley",         "VIC", "Australian Labor Party"),
    ("Rob Mitchell",           "McEwen",          "VIC", "Australian Labor Party"),
    ("Maria Vamvakinou",       "Calwell",         "VIC", "Australian Labor Party"),
    ("Chris Hayes",            "Fowler",          "NSW", "Australian Labor Party"),
    ("Ed Husic",               "Chifley",         "NSW", "Australian Labor Party"),
    ("Andrew Charlton",        "Parramatta",      "NSW", "Australian Labor Party"),
    # ── Liberal Party of Australia ──────────────────────────────────────────
    ("Sussan Ley",             "Farrer",          "NSW", "Liberal Party of Australia"),
    ("Angus Taylor",           "Hume",            "NSW", "Liberal Party of Australia"),
    ("Dan Tehan",              "Wannon",          "VIC", "Liberal Party of Australia"),
    ("Andrew Hastie",          "Canning",         "WA",  "Liberal Party of Australia"),
    ("Julian Leeser",          "Berowra",         "NSW", "Liberal Party of Australia"),
    ("Bridget Archer",         "Bass",            "TAS", "Liberal Party of Australia"),
    ("Ted O'Brien",            "Fairfax",         "QLD", "Liberal Party of Australia"),
    ("James Stevens",          "Sturt",           "SA",  "Liberal Party of Australia"),
    ("Paul Fletcher",          "Bradfield",       "NSW", "Liberal Party of Australia"),
    ("Keith Wolahan",          "Menzies",         "VIC", "Liberal Party of Australia"),
    ("Aaron Violi",            "Casey",           "VIC", "Liberal Party of Australia"),
    ("Michael Sukkar",         "Deakin",          "VIC", "Liberal Party of Australia"),
    ("Phillip Thompson",       "Herbert",         "QLD", "Liberal Party of Australia"),
    ("Luke Howarth",           "Petrie",          "QLD", "Liberal Party of Australia"),
    ("Andrew Wallace",         "Fisher",          "QLD", "Liberal Party of Australia"),
    ("Karen Andrews",          "McPherson",       "QLD", "Liberal Party of Australia"),
    ("Scott Morrison",         "Cook",            "NSW", "Liberal Party of Australia"),
    ("Alex Hawke",             "Mitchell",        "NSW", "Liberal Party of Australia"),
    ("Trent Zimmerman",        "North Sydney",    "NSW", "Liberal Party of Australia"),
    ("Jason Wood",             "La Trobe",        "VIC", "Liberal Party of Australia"),
    ("Tim Wilson",             "Goldstein",       "VIC", "Liberal Party of Australia"),
    ("Katie Allen",            "Higgins",         "VIC", "Liberal Party of Australia"),
    # ── The Nationals ───────────────────────────────────────────────────────
    ("David Littleproud",      "Maranoa",         "QLD", "The Nationals"),
    ("Barnaby Joyce",          "New England",     "NSW", "The Nationals"),
    ("Michael McCormack",      "Riverina",        "NSW", "The Nationals"),
    ("Kevin Hogan",            "Page",            "NSW", "The Nationals"),
    ("Anne Webster",           "Mallee",          "VIC", "The Nationals"),
    ("Scott Buchholz",         "Wright",          "QLD", "The Nationals"),
    ("Michelle Landry",        "Capricornia",     "QLD", "The Nationals"),
    ("Mark Coulton",           "Parkes",          "NSW", "The Nationals"),
    ("Rick Wilson",            "O'Connor",        "WA",  "Liberal Party of Australia"),
    ("Rowan Ramsey",           "Grey",            "SA",  "Liberal Party of Australia"),
    # ── Australian Greens ───────────────────────────────────────────────────
    ("Elizabeth Watson-Brown", "Ryan",            "QLD", "Australian Greens"),
    # ── Independents ────────────────────────────────────────────────────────
    ("Zali Steggall",          "Warringah",       "NSW", "Independent"),
    ("Andrew Wilkie",          "Clark",           "TAS", "Independent"),
    ("Helen Haines",           "Indi",            "VIC", "Independent"),
    ("Monique Ryan",           "Kooyong",         "VIC", "Independent"),
    ("Kate Chaney",            "Curtin",          "WA",  "Independent"),
    ("Sophie Scamps",          "Mackellar",       "NSW", "Independent"),
    ("Allegra Spender",        "Wentworth",       "NSW", "Independent"),
    ("Kylea Tink",             "North Sydney",    "NSW", "Independent"),
    ("Zoe Daniel",             "Goldstein",       "VIC", "Independent"),
    ("David Pocock",           "Canberra",        "ACT", "Independent"),
    ("Bob Katter",             "Kennedy",         "QLD", "Katter's Australian Party"),
]

# ── Senate ─────────────────────────────────────────────────────────────────
# (name, state, party)
SENATORS = [
    # ── Australian Labor Party ──────────────────────────────────────────────
    ("Penny Wong",             "SA",  "Australian Labor Party"),
    ("Katy Gallagher",         "ACT", "Australian Labor Party"),
    ("Murray Watt",            "QLD", "Australian Labor Party"),
    ("Don Farrell",            "SA",  "Australian Labor Party"),
    ("Tim Ayres",              "NSW", "Australian Labor Party"),
    ("Raff Ciccone",           "VIC", "Australian Labor Party"),
    ("Nita Green",             "QLD", "Australian Labor Party"),
    ("Carol Brown",            "TAS", "Australian Labor Party"),
    ("Tony Sheldon",           "NSW", "Australian Labor Party"),
    ("Marielle Smith",         "SA",  "Australian Labor Party"),
    ("Anne Urquhart",          "TAS", "Australian Labor Party"),
    ("Jana Stewart",           "VIC", "Australian Labor Party"),
    ("Jess Walsh",             "VIC", "Australian Labor Party"),
    ("Anthony Chisholm",       "QLD", "Australian Labor Party"),
    ("Dorinda Cox",            "WA",  "Australian Labor Party"),
    ("Fatima Payman",          "WA",  "Independent"),
    # ── Liberal Party of Australia ──────────────────────────────────────────
    ("Michaelia Cash",         "WA",  "Liberal Party of Australia"),
    ("James Paterson",         "VIC", "Liberal Party of Australia"),
    ("Sarah Henderson",        "VIC", "Liberal Party of Australia"),
    ("Anne Ruston",            "SA",  "Liberal Party of Australia"),
    ("Hollie Hughes",          "NSW", "Liberal Party of Australia"),
    ("Andrew Bragg",           "NSW", "Liberal Party of Australia"),
    ("Dean Smith",             "WA",  "Liberal Party of Australia"),
    ("Maria Kovacic",          "NSW", "Liberal Party of Australia"),
    ("Jane Hume",              "VIC", "Liberal Party of Australia"),
    ("Paul Scarr",             "QLD", "Liberal Party of Australia"),
    ("David Van",              "VIC", "Independent"),
    # ── The Nationals ───────────────────────────────────────────────────────
    ("Bridget McKenzie",       "VIC", "The Nationals"),
    ("Matt Canavan",           "QLD", "The Nationals"),
    ("Perin Davey",            "NSW", "The Nationals"),
    ("Susan McDonald",         "QLD", "The Nationals"),
    ("Ross Cadell",            "NSW", "The Nationals"),
    ("Sam McMahon",            "NT",  "Country Liberal Party"),
    # ── Australian Greens ───────────────────────────────────────────────────
    ("Larissa Waters",         "QLD", "Australian Greens"),
    ("Sarah Hanson-Young",     "SA",  "Australian Greens"),
    ("Nick McKim",             "TAS", "Australian Greens"),
    ("Mehreen Faruqi",         "NSW", "Australian Greens"),
    ("Janet Rice",             "VIC", "Australian Greens"),
    ("Peter Whish-Wilson",     "TAS", "Australian Greens"),
    ("Barbara Pocock",         "SA",  "Australian Greens"),
    ("David Shoebridge",       "NSW", "Australian Greens"),
    # ── Others ──────────────────────────────────────────────────────────────
    ("David Pocock",           "ACT", "Independent"),
    ("Jacqui Lambie",          "TAS", "Jacqui Lambie Network"),
    ("Tammy Tyrrell",          "TAS", "Jacqui Lambie Network"),
    ("Pauline Hanson",         "QLD", "One Nation"),
    ("Malcolm Roberts",        "QLD", "One Nation"),
]


def upsert_politician(db, name: str, chamber: str, electorate_or_state: str, party: str) -> Politician:
    from sqlalchemy.exc import IntegrityError
    slug = make_slug(name, chamber)
    p = db.query(Politician).filter_by(slug=slug).first()
    if p is None:
        p = Politician(slug=slug, chamber=chamber)
        db.add(p)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            p = db.query(Politician).filter_by(slug=slug).first()
    p.name = name
    p.chamber = chamber
    p.electorate_or_state = electorate_or_state
    p.party = party
    p.aph_url = None
    p.register_pdf_url = None
    p.updated_at_text = None
    db.flush()
    return p


def seed_db(db) -> tuple[int, int]:
    """
    Seed the database with 48th Parliament politicians using an existing session.
    Returns (house_count, senate_count). Safe to call from the FastAPI lifespan.
    """
    run = RefreshRun(
        status="success",
        started_at=datetime.datetime.utcnow(),
        completed_at=datetime.datetime.utcnow(),
        message="Auto-seeded from 48th Parliament 2025 data on first startup.",
    )
    db.add(run)

    house_count = 0
    senate_count = 0

    for name, electorate, state, party in HOUSE_MEMBERS:
        p = upsert_politician(db, name, "house", electorate, party)
        db.add(InterestsSummary(
            politician_id=p.id,
            source_type="pending",
            notes="Interest data pending — trigger the Daily Data Refresh workflow to parse PDF filings.",
            refreshed_at=datetime.datetime.utcnow(),
        ))
        house_count += 1

    for name, state, party in SENATORS:
        p = upsert_politician(db, name, "senate", state, party)
        db.add(InterestsSummary(
            politician_id=p.id,
            source_type="pending",
            notes="Interest data pending — trigger the Daily Data Refresh workflow to parse PDF filings.",
            refreshed_at=datetime.datetime.utcnow(),
        ))
        senate_count += 1

    db.commit()
    return house_count, senate_count


def seed() -> None:
    """Standalone seed — creates its own DB session. Use for CLI / GitHub Actions."""
    db = SessionLocal()
    try:
        house_count, senate_count = seed_db(db)
        log.info("Seeded %d House members and %d Senators (%d total).",
                 house_count, senate_count, house_count + senate_count)
    finally:
        db.close()


if __name__ == "__main__":
    seed()

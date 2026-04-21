"""
Seed data for the 48th Australian Parliament (elected May 2025).
Lives inside app/ so it is always included in the Vercel lambda bundle.
"""
import re
import datetime
import logging

log = logging.getLogger(__name__)

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


def make_slug(name: str, chamber: str) -> str:
    clean = re.sub(r"[^a-z0-9\s-]", "", name.lower())
    clean = re.sub(r"[\s-]+", "-", clean.strip("-"))
    return f"{chamber}-{clean}"


# Investment data sourced from Open Politics 47th Parliament public category tables.
# Keys: (name, chamber)  — chamber is lowercase "house" or "senate"
# Values: dict with optional integer fields (missing key → None/unknown):
#   self_re, self_sh        → self real-estate count, self shareholdings count
#   partner_re, partner_sh  → partner equivalents (from profile_verified_counts where available)
#   children_re, children_sh → children equivalents
#   total                   → known_category_count_total
POLITICIAN_INTERESTS = {
    # ── Profile-verified breakdown (self / partner / children) ─────────────
    ("Alex Hawke",        "house"): dict(self_re=1, self_sh=0, partner_re=1, partner_sh=0, children_re=0, children_sh=0, total=5),
    ("Andrew Charlton",   "house"): dict(self_re=5, self_sh=21, partner_re=4, partner_sh=22, children_re=0, children_sh=0, total=19),
    ("Anne Aly",          "house"): dict(self_re=2, self_sh=0, partner_re=1, partner_sh=1, children_re=0, children_sh=0, total=5),
    ("Anthony Albanese",  "house"): dict(self_re=2, self_sh=0, partner_re=1, partner_sh=0, children_re=0, children_sh=0, total=6),
    ("Karen Andrews",     "house"): dict(self_re=7, self_sh=5, partner_re=6, partner_sh=5, children_re=0, children_sh=0, total=41),
    # ── Public category counts (aggregate mapped to self_*) ────────────────
    ("Aaron Violi",           "house"):  dict(self_re=1,  self_sh=5,  total=11),
    ("Alicia Payne",          "house"):  dict(self_re=2,  self_sh=2,  total=15),
    ("Allegra Spender",       "house"):  dict(self_sh=18,             total=44),
    ("Amanda Rishworth",      "house"):  dict(self_sh=13,             total=21),
    ("Andrew Bragg",          "senate"): dict(self_re=1,              total=7),
    ("Andrew Hastie",         "house"):  dict(self_re=2,              total=10),
    ("Andrew Leigh",          "house"):  dict(self_re=2,  self_sh=2,  total=7),
    ("Andrew Wallace",        "house"):  dict(self_sh=9,              total=21),
    ("Andrew Wilkie",         "house"):  dict(self_re=4,  self_sh=1,  total=24),
    ("Angus Taylor",          "house"):  dict(self_re=3,  self_sh=8,  total=29),
    ("Anne Ruston",           "senate"): dict(self_re=1,              total=3),
    ("Anne Urquhart",         "senate"): dict(total=5),
    ("Anne Webster",          "house"):  dict(total=3),
    ("Anthony Chisholm",      "senate"): dict(self_re=2,              total=2),
    ("Barbara Pocock",        "senate"): dict(total=11),
    ("Barnaby Joyce",         "house"):  dict(self_re=2,  self_sh=22, total=35),
    ("Bob Katter",            "house"):  dict(self_re=1,              total=2),
    ("Bridget McKenzie",      "senate"): dict(self_re=4,              total=4),
    ("Carina Garland",        "house"):  dict(self_re=1,  self_sh=1,  total=5),
    ("Carol Brown",           "senate"): dict(self_sh=1,              total=2),
    ("Cassandra Fernando",    "house"):  dict(self_sh=6,              total=9),
    ("Catherine King",        "house"):  dict(total=5),
    ("Chris Bowen",           "house"):  dict(total=4),
    ("Clare O'Neil",          "house"):  dict(self_re=2,              total=6),
    ("Dan Tehan",             "house"):  dict(self_re=2,  self_sh=1,  total=12),
    ("Daniel Mulino",         "house"):  dict(self_re=2,              total=2),
    ("David Pocock",          "house"):  dict(self_re=2,              total=11),
    ("David Pocock",          "senate"): dict(self_re=2,              total=11),
    ("Dean Smith",            "senate"): dict(self_re=2,  self_sh=12, total=14),
    ("Don Farrell",           "senate"): dict(self_re=3,              total=4),
    ("Dorinda Cox",           "senate"): dict(total=2),
    ("Ed Husic",              "house"):  dict(self_re=3,              total=3),
    ("Elizabeth Watson-Brown","house"):  dict(total=2),
    ("Emma McBride",          "house"):  dict(self_re=2,              total=3),
    ("Fatima Payman",         "senate"): dict(self_re=2,              total=2),
    ("Fiona Phillips",        "house"):  dict(total=4),
    ("James Paterson",        "senate"): dict(total=1),
    ("Jane Hume",             "senate"): dict(total=2),
    ("Jason Clare",           "house"):  dict(total=3),
    ("Jerome Laxale",         "house"):  dict(self_sh=17,             total=17),
    ("Jess Walsh",            "senate"): dict(total=4),
    ("Jim Chalmers",          "house"):  dict(self_re=2,              total=2),
    ("Josh Burns",            "house"):  dict(self_re=2,              total=2),
    ("Josh Wilson",           "house"):  dict(self_sh=10,             total=10),
    ("Julian Leeser",         "house"):  dict(self_re=2,              total=2),
    ("Julie Collins",         "house"):  dict(self_re=0,  self_sh=2,  total=10),
    ("Kate Chaney",           "house"):  dict(total=2),
    ("Kate Thwaites",         "house"):  dict(total=3),
    ("Katy Gallagher",        "senate"): dict(total=3),
    ("Kevin Hogan",           "house"):  dict(total=10),
    ("Kristy McBain",         "house"):  dict(self_re=8,  self_sh=2,  total=20),
    ("Larissa Waters",        "senate"): dict(total=4),
    ("Lisa Chesters",         "house"):  dict(total=6),
    ("Louise Miller-Frost",   "house"):  dict(self_re=8,              total=18),
    ("Luke Gosling",          "house"):  dict(total=2),
    ("Madeleine King",        "house"):  dict(self_re=7,  self_sh=1,  total=8),
    ("Maria Kovacic",         "senate"): dict(self_sh=3,              total=13),
    ("Marielle Smith",        "senate"): dict(total=5),
    ("Marion Scrymgour",      "house"):  dict(total=2),
    ("Mark Dreyfus",          "house"):  dict(self_sh=2,              total=5),
    ("Matt Keogh",            "house"):  dict(self_re=1,              total=19),
    ("Mehreen Faruqi",        "senate"): dict(total=6),
    ("Meryl Swanson",         "house"):  dict(self_re=8,  self_sh=15, total=33),
    ("Michael McCormack",     "house"):  dict(self_re=5,              total=9),
    ("Michelle Landry",       "house"):  dict(self_sh=2,              total=2),
    ("Michelle Rowland",      "house"):  dict(self_sh=2,              total=6),
    ("Mike Freelander",       "house"):  dict(self_sh=13,             total=21),
    ("Monique Ryan",          "house"):  dict(total=9),
    ("Murray Watt",           "senate"): dict(self_re=1,              total=5),
    ("Nick McKim",            "senate"): dict(self_sh=1,              total=1),
    ("Nita Green",            "senate"): dict(self_re=2,              total=4),
    ("Pat Conroy",            "house"):  dict(total=7),
    ("Patrick Gorman",        "house"):  dict(self_re=1,              total=1),
    ("Paul Scarr",            "senate"): dict(self_re=1,  self_sh=19, total=20),
    ("Pauline Hanson",        "senate"): dict(self_re=2,  self_sh=3,  total=5),
    ("Peter Whish-Wilson",    "senate"): dict(self_re=2,              total=4),
    ("Phillip Thompson",      "house"):  dict(self_re=2,  self_sh=1,  total=7),
    ("Raff Ciccone",          "senate"): dict(self_sh=1,              total=6),
    ("Rick Wilson",           "house"):  dict(self_re=8,  self_sh=40, total=52),
    ("Rob Mitchell",          "house"):  dict(self_re=8,              total=11),
    ("Ross Cadell",           "senate"): dict(self_re=2,  self_sh=1,  total=3),
    ("Sarah Hanson-Young",    "senate"): dict(self_re=1,              total=2),
    ("Sarah Henderson",       "senate"): dict(self_re=3,              total=14),
    ("Scott Buchholz",        "house"):  dict(self_re=4,  self_sh=3,  total=23),
    ("Sharon Claydon",        "house"):  dict(self_re=2,              total=2),
    ("Steve Georganas",       "house"):  dict(self_re=4,              total=9),
    ("Susan McDonald",        "senate"): dict(self_re=2,  self_sh=2,  total=5),
    ("Sussan Ley",            "house"):  dict(self_re=4,              total=4),
    ("Tammy Tyrrell",         "senate"): dict(self_re=1,              total=1),
    ("Tanya Plibersek",       "house"):  dict(self_re=7,              total=15),
    ("Ted O'Brien",           "house"):  dict(self_re=3,              total=21),
    ("Tim Ayres",             "senate"): dict(self_re=2,              total=6),
    ("Tim Wilson",            "house"):  dict(self_re=4,  self_sh=13, total=22),
    ("Tony Burke",            "house"):  dict(self_re=11,             total=11),
    ("Tony Sheldon",          "senate"): dict(self_sh=1,              total=1),
    ("Tony Zappia",           "house"):  dict(self_re=5,  self_sh=4,  total=11),
    ("Zali Steggall",         "house"):  dict(self_re=4,  self_sh=2,  total=11),
    ("Zaneta Mascarenhas",    "house"):  dict(self_sh=3,              total=9),
}


def upsert_politician(db, name: str, chamber: str, electorate_or_state: str, party: str):
    from sqlalchemy.exc import IntegrityError
    from app.db.models import Politician

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


def seed_db(db) -> tuple:
    """
    Seed the DB with 48th Parliament politicians using an existing session.
    Uses bulk add_all + single flush/commit to minimise round-trips.
    Returns (house_count, senate_count).
    """
    from app.db.models import Politician, InterestsSummary, RefreshRun

    now = datetime.datetime.utcnow()

    # Build all Politician objects (name stored so we can look up interests)
    politicians = []   # list of (Politician, name, chamber)
    for name, electorate, _state, party in HOUSE_MEMBERS:
        p = Politician(slug=make_slug(name, "house"), name=name, chamber="house",
                       electorate_or_state=electorate, party=party)
        politicians.append((p, name, "house"))
    for name, state, party in SENATORS:
        p = Politician(slug=make_slug(name, "senate"), name=name, chamber="senate",
                       electorate_or_state=state, party=party)
        politicians.append((p, name, "senate"))

    # One flush assigns all IDs
    db.add_all([p for p, _, _ in politicians])
    db.flush()

    summaries = []
    for p, name, chamber in politicians:
        d = POLITICIAN_INTERESTS.get((name, chamber), {})
        has_data = bool(d)
        summaries.append(InterestsSummary(
            politician_id=p.id,
            source_type="open_politics" if has_data else "pending",
            self_properties=d.get("self_re"),
            self_shares=d.get("self_sh"),
            partner_properties=d.get("partner_re"),
            partner_shares=d.get("partner_sh"),
            children_properties=d.get("children_re"),
            children_shares=d.get("children_sh"),
            total_interests=d.get("total"),
            notes=(
                "Source: Open Politics 47th Parliament public disclosures (openpolitics.au)."
                if has_data else
                "Interest data not yet available in public sources."
            ),
            refreshed_at=now,
        ))
    db.add_all(summaries)

    db.add(RefreshRun(
        status="success",
        started_at=now,
        completed_at=now,
        message="Seeded 48th Parliament politicians with Open Politics 47th Parliament investment data.",
    ))

    db.commit()
    return len(HOUSE_MEMBERS), len(SENATORS)


def apply_investment_data(db) -> int:
    """
    Insert fresh InterestsSummary rows with Open Politics data for all existing politicians.
    Does NOT require the politicians table to be empty — safe to call at any time.
    Returns the number of new summary rows inserted.
    """
    from app.db.models import Politician, InterestsSummary, RefreshRun
    from sqlalchemy import text

    now = datetime.datetime.utcnow()

    politicians = db.query(Politician).all()
    summaries = []
    for p in politicians:
        d = POLITICIAN_INTERESTS.get((p.name, p.chamber), {})
        summaries.append(InterestsSummary(
            politician_id=p.id,
            source_type="open_politics" if d else "pending",
            self_properties=d.get("self_re"),
            self_shares=d.get("self_sh"),
            partner_properties=d.get("partner_re"),
            partner_shares=d.get("partner_sh"),
            children_properties=d.get("children_re"),
            children_shares=d.get("children_sh"),
            total_interests=d.get("total"),
            notes=(
                "Source: Open Politics 47th Parliament public disclosures (openpolitics.au)."
                if d else
                "Interest data not yet available in public sources."
            ),
            refreshed_at=now,
        ))

    if summaries:
        db.add_all(summaries)
        db.add(RefreshRun(
            status="success",
            started_at=now,
            completed_at=now,
            message="Applied Open Politics 47th Parliament investment data to existing politicians.",
        ))
        db.commit()

    log.info("apply_investment_data: inserted %d summary rows", len(summaries))
    return len(summaries)

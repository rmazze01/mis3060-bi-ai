# =============================================================================
# Script:      hw03_executives.py
# Purpose:     Executive Events Pipeline (Item 5.02). For each of five
#              companies, find every Form 8-K filed in the past 12 months that
#              reports Item 5.02 (Departure of Directors or Certain Officers;
#              Election of Directors; Appointment of Certain Officers), extract
#              each departure/appointment event (one row per event), and save
#              them to hw03/executive_events.csv.
# Data source: SEC EDGAR 8-K filings (submissions API + EDGAR Archives)
# Author:      Rose Mazzeo (MIS3060, Villanova), generated with Claude Cowork
# Generated:   2026-09-24
#
# Third-party libraries: requests, beautifulsoup4
#   Install with:  pip install requests beautifulsoup4
# =============================================================================

import csv
import os
import re
import time
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# Shared setup
# -----------------------------------------------------------------------------

# Step 1: same User-Agent header as the earnings pipeline, sent on EVERY request.
USER_AGENT = "MIS3060 Villanova rmazze01@villanova.edu"
HEADERS = {"User-Agent": USER_AGENT}

REQUEST_PAUSE_SECONDS = 0.15  # SEC allows at most 10 requests per second
NOT_FOUND = "NOT_FOUND"
LOOKBACK_DAYS = 365

COMPANIES = [
    {"company": "Apple Inc.", "ticker": "AAPL", "cik": "0000320193"},
    {"company": "Microsoft Corporation", "ticker": "MSFT", "cik": "0000789019"},
    {"company": "NVIDIA Corporation", "ticker": "NVDA", "cik": "0001045810"},
    {"company": "JPMorgan Chase & Co.", "ticker": "JPM", "cik": "0000019617"},
    {"company": "Walmart Inc.", "ticker": "WMT", "cik": "0000104169"},
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "executive_events.csv")

CSV_COLUMNS = [
    "company", "ticker", "cik", "filing_date", "event_type",
    "person_name", "title", "effective_date",
]


def get(url, ticker):
    """Make one GET request with the User-Agent header, then pause.

    This is the only place the script calls requests.get(), so every request
    carries the header. Returns the Response on status 200, or None (with a
    printed warning) on any network error or non-200 status.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as exc:
        print(f"  WARNING [{ticker}]: request failed for {url} ({exc})")
        time.sleep(REQUEST_PAUSE_SECONDS)
        return None
    time.sleep(REQUEST_PAUSE_SECONDS)
    if response.status_code != 200:
        print(f"  WARNING [{ticker}]: status {response.status_code} for {url}")
        return None
    return response


def html_to_text(html):
    """Strip HTML to plain text: drop script/style, collapse whitespace."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


# -----------------------------------------------------------------------------
# Step 2: query the submissions API and filter for recent Item 5.02 8-Ks
# -----------------------------------------------------------------------------

def get_item_502_filings(cik, ticker):
    """Return 8-K filings with Item 5.02 filed within the past 12 months,
    newest first. Returns an empty list if there are none."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = get(url, ticker)
    if response is None:
        return []

    try:
        recent = response.json()["filings"]["recent"]
    except (ValueError, KeyError) as exc:
        print(f"  WARNING [{ticker}]: could not read submissions JSON ({exc})")
        return []

    cutoff = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    matches = []
    for i in range(len(recent["form"])):
        if recent["form"][i] != "8-K":  # exact match: excludes 8-K/A
            continue
        items = [item.strip() for item in recent["items"][i].split(",")]
        if "5.02" not in items:
            continue
        if recent["filingDate"][i] < cutoff:  # ISO dates compare correctly
            continue
        matches.append({
            "filing_date": recent["filingDate"][i],
            "report_date": recent["reportDate"][i],
            "accession": recent["accessionNumber"][i],
            "primary_document": recent["primaryDocument"][i],
        })

    matches.sort(key=lambda f: f["filing_date"], reverse=True)
    return matches


# -----------------------------------------------------------------------------
# Step 3: text extraction helpers
# -----------------------------------------------------------------------------

def isolate_item_502(text):
    """Return the text from 'Item 5.02' up to the next 'Item N.NN' heading or
    'SIGNATURE', whichever comes first. Falls back to the full text."""
    start = re.search(r"\bItem\s+5\.02\b", text, flags=re.IGNORECASE)
    if not start:
        return text
    rest = text[start.end():]
    end = re.search(r"\bItem\s+\d+\.\d{2}\b|\bSIGNATURES?\b", rest)
    return text[start.start(): start.end() + (end.start() if end else len(rest))]


ABBREVIATIONS = ["Mr.", "Ms.", "Mrs.", "Dr.", "Jr.", "Sr.", "Inc.", "Co.",
                 "Corp.", "No.", "U.S.", "St."]


def split_sentences(text):
    """Split text into sentences without breaking on 'Mr.', 'Inc.', or
    middle initials like 'A.'."""
    protected = text
    for abbr in ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", "<DOT>"))
    protected = re.sub(r"\b([A-Z])\.(?=\s+[A-Z])", r"\1<DOT>", protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", protected)
    return [p.replace("<DOT>", ".").strip() for p in parts if p.strip()]


# Event keywords. Each is (regex, event, attach_to_preceding_name).
EVENT_KEYWORDS = [
    (r"\bresign(?:s|ed|ing|ation)?\b", "departure", False),
    (r"\bretire(?:s|d|ment)?\b(?!\s+(?:plan|savings|benefit|account))", "departure", False),
    (r"\bstep(?:s|ped|ping)?\s+down\b", "departure", False),
    (r"\bdepart(?:s|ed|ing|ure)?\b", "departure", False),
    (r"\bterminated\b", "departure", False),
    (r"(?<!upon\s)\btermination\b", "departure", False),
    (r"\bwill\s+not\s+stand\s+for\s+re-?election\b", "departure", False),
    (r"\btransition(?:s|ed|ing)?\s+(?:out\s+of|from)\b", "departure", False),
    (r"\bwill\s+leave\b", "departure", False),
    (r"\bappoint(?:s|ed|ing|ment)?\b", "appointment", False),
    (r"\belect(?:s|ed|ion)?\b", "appointment", False),
    (r"\bnamed\b(?!\s+executive\s+officers?)", "appointment", False),
    (r"\bpromot(?:ed|ion)\b", "appointment", False),
    (r"\bhired\b", "appointment", False),
    (r"\bwill\s+join\b", "appointment", True),
    (r"\b(?:will\s+)?succe(?:ed|eds|eding)\b", "appointment", True),
]

# Capitalized words that are never part of a person's name.
STOP_WORDS = {
    "the", "a", "an", "on", "in", "of", "and", "for", "as", "to", "at", "by",
    "effective", "company", "companies", "corporation", "corp", "inc", "co",
    "registrant", "board", "directors", "director", "chief", "executive",
    "officer", "officers", "financial", "operating", "accounting", "technology",
    "legal", "people", "marketing", "president", "vice", "senior", "general",
    "counsel", "chair", "chairman", "chairwoman", "chairperson", "lead",
    "independent", "member", "committee", "compensation", "audit",
    "nominating", "governance", "item", "items", "form", "exhibit", "section",
    "report", "current", "securities", "exchange", "act", "agreement", "plan",
    "stock", "incentive", "annual", "meeting", "shareholders", "stockholders",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "apple", "microsoft",
    "nvidia", "jpmorgan", "chase", "walmart", "bank", "united", "states",
    "retirement", "resignation", "appointment", "departure", "transition",
    "letter", "offer", "employment", "press", "release", "following",
    "pursuant", "also", "mr", "ms", "mrs", "dr", "he", "she", "his", "her",
    "fiscal", "quarter", "year", "global", "international", "retail", "sam's",
    "club", "operations", "commercial", "investment", "consumer", "community",
    "asset", "wealth", "management", "cloud", "business", "group", "north",
    "america", "controller", "treasurer", "secretary", "principal", "strategy",
    "human", "resources", "corporate", "affairs", "communications", "products",
    "services", "worldwide", "platform", "engineering", "research", "prior",
    "since", "from", "with", "who", "this", "that", "there", "these", "such",
    "new", "interim", "ceo", "cfo", "coo", "cto", "planning", "analysis",
    "finance", "departure", "election", "appointed", "certain", "compensatory",
    "arrangements", "officers'", "if", "upon", "during", "after", "before",
}

HONORIFIC = r"\b(?:Mr|Ms|Mrs|Dr)\.\s+"
NAME_TOKEN = r"(?:[A-Z][a-zA-Z'\-]+|[A-Z]\.|Jr\.|Sr\.|II|III|IV)"
CAP_RUN = re.compile(NAME_TOKEN + r"(?:,?\s+" + NAME_TOKEN + r")*")


def find_full_names(sentence):
    """Return [(start, end, full_name)] for 2-4 word capitalized names that
    contain no stop words."""
    results = []
    for run in CAP_RUN.finditer(sentence):
        tokens = list(re.finditer(NAME_TOKEN, run.group(0)))
        group = []
        for tok in tokens + [None]:
            word = tok.group(0) if tok else None
            is_initial = word is not None and re.fullmatch(r"[A-Z]\.", word)
            is_stop = (word is None
                       or (not is_initial and word.lower().strip(".,") in STOP_WORDS)
                       or (word.isupper() and len(word) > 3 and word not in ("III",)))
            if not is_stop:
                group.append(tok)
                continue
            # close the current group
            while group and re.fullmatch(r"[A-Z]\.", group[0].group(0)):
                group.pop(0)  # a name can't start with an initial
            words = [g.group(0) for g in group]
            core = [w for w in words if w not in ("Jr.", "Sr.", "II", "III", "IV")]
            if 2 <= len(core) <= 4 and not re.fullmatch(r"[A-Z]\.", core[-1]):
                s = run.start() + group[0].start()
                e = run.start() + group[-1].end()
                results.append((s, e, " ".join(words).replace(" ,", ",")))
            group = []
    return results


def find_mentions(sentence, known_names):
    """All person mentions in a sentence: full names, plus 'Mr. Surname'
    references resolved to a known full name. Returns [(start, end, name)]."""
    mentions = find_full_names(sentence)
    covered = [(s, e) for s, e, _ in mentions]
    for m in re.finditer(HONORIFIC + r"([A-Z][a-zA-Z'\-]+)", sentence):
        if any(s <= m.start(1) < e for s, e in covered):
            continue
        surname = m.group(1)
        full = next((n for n in known_names if n.split()[-1].strip(",") == surname
                     or surname in n.split()), None)
        if full:
            mentions.append((m.start(), m.end(), full))
    return sorted(mentions)


def gap(a_start, a_end, b_start, b_end):
    """Character distance between two spans (0 if they overlap)."""
    if a_end <= b_start:
        return b_start - a_end
    if b_end <= a_start:
        return a_start - b_end
    return 0


TITLE_PATTERN = re.compile(
    r"(?:(?:Executive|Senior)\s+)?Vice\s+President(?:,?\s+(?:and\s+|of\s+|for\s+)?(?:[A-Z][A-Za-z&]+|&)){0,5}"
    r"|(?:President\s+and\s+)?Chief\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+Officer"
    r"|President(?:\s+and\s+Chief\s+[A-Z][a-z]+\s+Officer)?"
    r"|\b(?:CEO|CFO|COO|CTO|CAO|CIO)\b"
    r"|General\s+Counsel(?:\s+and\s+Corporate\s+Secretary)?"
    r"|(?:Executive\s+|Non-Executive\s+)?Chair(?:man|woman|person)?(?:\s+of\s+the\s+Board)?"
    r"|Lead\s+Independent\s+Director"
    r"|Principal\s+(?:Accounting|Financial|Executive)\s+Officer"
    r"|Corporate\s+Controller|Controller|Treasurer|Corporate\s+Secretary"
    r"|member\s+of\s+the\s+Board(?:\s+of\s+Directors)?"
    r"|\b(?:independent\s+)?[Dd]irector\b"
)


def clean_title(title):
    title = title.strip(" ,")
    if title.lower().startswith("member of the board") or title.lower().endswith("director") \
            and "lead" not in title.lower():
        return "Director"
    return title


def find_title(sentence, name_span, event):
    """Pick the title for a person in a sentence. For appointments prefer a
    title introduced by 'as' after the name ('appointed ... as CFO'); for
    departures prefer 'as <title>' / 'role as <title>'; otherwise take the
    title closest to the name."""
    titles = list(TITLE_PATTERN.finditer(sentence))
    if not titles:
        return None
    ns, ne = name_span
    as_titles = [t for t in titles
                 if re.search(r"\b(?:as|of|to)\s+(?:the\s+)?(?:\w+'s\s+|its\s+|our\s+|new\s+)*$",
                              sentence[max(0, t.start() - 40):t.start()])]
    if event == "appointment":
        after = [t for t in as_titles if t.start() >= ne]
        if after:
            return clean_title(after[0].group(0))
    elif as_titles:
        best = min(as_titles, key=lambda t: gap(ns, ne, t.start(), t.end()))
        return clean_title(best.group(0))
    best = min(titles, key=lambda t: gap(ns, ne, t.start(), t.end()))
    return clean_title(best.group(0))


MONTH_DATE = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})"


def find_effective_date(sentence, report_date):
    """Return the effective date as YYYY-MM-DD, or None."""
    m = re.search(r"\beffective\s+(?:as\s+of\s+)?(?:on\s+)?(?:the\s+close\s+of\s+business\s+on\s+)?"
                  + MONTH_DATE, sentence, flags=re.IGNORECASE)
    if m:
        try:
            return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}",
                                     "%B %d %Y").date().isoformat()
        except ValueError:
            pass
    if re.search(r"\beffective\s+immediately\b", sentence, flags=re.IGNORECASE):
        return report_date
    return None


def extract_events(section_text, report_date):
    """Return a list of events: dicts with event_type, person_name, title,
    effective_date. One entry per person; a person with both departure and
    appointment language is a single 'both' event."""
    sentences = split_sentences(section_text)

    known_names = []
    for sentence in sentences:
        for _, _, name in find_full_names(sentence):
            if name not in known_names:
                known_names.append(name)

    people = {}  # name -> {"events": set, "title": .., "effective": .., "order": int}
    for sentence in sentences:
        mentions = find_mentions(sentence, known_names)
        if not mentions:
            continue
        for pattern, event, prefer_preceding in EVENT_KEYWORDS:
            for kw in re.finditer(pattern, sentence, flags=re.IGNORECASE):
                candidates = mentions
                if prefer_preceding:
                    before = [m for m in mentions if m[1] <= kw.start()]
                    candidates = before or mentions
                ms, me, name = min(candidates,
                                   key=lambda m: gap(m[0], m[1], kw.start(), kw.end()))
                person = people.setdefault(name, {"events": set(), "title": None,
                                                  "effective": None,
                                                  "order": len(people)})
                person["events"].add(event)
                if person["title"] is None:
                    person["title"] = find_title(sentence, (ms, me), event)
                if person["effective"] is None:
                    person["effective"] = find_effective_date(sentence, report_date)

    events = []
    for name, info in sorted(people.items(), key=lambda kv: kv[1]["order"]):
        if info["events"] == {"departure", "appointment"}:
            event_type = "both"
        else:
            event_type = next(iter(info["events"]))
        events.append({
            "event_type": event_type,
            "person_name": name,
            "title": info["title"] or NOT_FOUND,
            "effective_date": info["effective"] or NOT_FOUND,
        })
    return events


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------

def main():
    rows = []

    for company in COMPANIES:
        name, ticker, cik = company["company"], company["ticker"], company["cik"]
        print(f"\n=== {name} ({ticker}) ===")

        filings = get_item_502_filings(cik, ticker)

        # Step 6: zero filings is valid data, not an error.
        if not filings:
            print(f"{ticker}: No executive events in past 12 months")
            continue

        for filing in filings:
            base = {
                "company": name,
                "ticker": ticker,
                "cik": cik,
                "filing_date": filing["filing_date"],
            }

            # Step 3: download the 8-K, strip HTML, isolate Item 5.02.
            cik_no_zeros = str(int(cik))
            accession_no_dashes = filing["accession"].replace("-", "")
            doc_url = (f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/"
                       f"{accession_no_dashes}/{filing['primary_document']}")
            response = get(doc_url, ticker)

            events = []
            if response is None:
                print(f"  WARNING [{ticker}]: could not download filing "
                      f"{filing['accession']}; recording NOT_FOUND and continuing")
            else:
                section = isolate_item_502(html_to_text(response.text))
                events = extract_events(section, filing["report_date"])

            # Compensation-only filings (or failed downloads) still get one row.
            if not events:
                events = [{"event_type": NOT_FOUND, "person_name": NOT_FOUND,
                           "title": NOT_FOUND, "effective_date": NOT_FOUND}]

            # Step 4 + 5: one row per event, printed as it is processed.
            for event in events:
                row = {**base, **event}
                print(f"{ticker} | {row['filing_date']} | {row['event_type']} | "
                      f"{row['person_name']} | {row['title']}")
                rows.append(row)

    # Step 7: save the CSV (header row is written even if there are no events).
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: (row.get(col) or NOT_FOUND) for col in CSV_COLUMNS})

    print(f"\nWrote {len(rows)} events to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

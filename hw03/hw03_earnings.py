# =============================================================================
# Script:      hw03_earnings.py
# Purpose:     Earnings Pipeline (Item 2.02). For each of five companies, find
#              the four most recent Form 8-K filings that report Item 2.02
#              (Results of Operations and Financial Condition), download the
#              earnings press release exhibit, extract the reporting period,
#              revenue, diluted EPS, and net income, and save them to
#              hw03/earnings_history.csv.
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

import requests
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# Shared setup
# -----------------------------------------------------------------------------

# Step 1: User-Agent header, defined once and sent on EVERY request (see get()).
USER_AGENT = "MIS3060 Villanova rmazze01@villanova.edu"
HEADERS = {"User-Agent": USER_AGENT}

REQUEST_PAUSE_SECONDS = 0.15  # SEC allows at most 10 requests per second
NOT_FOUND = "NOT_FOUND"
FILINGS_PER_COMPANY = 4

COMPANIES = [
    {"company": "Apple Inc.", "ticker": "AAPL", "cik": "0000320193"},
    {"company": "Microsoft Corporation", "ticker": "MSFT", "cik": "0000789019"},
    {"company": "NVIDIA Corporation", "ticker": "NVDA", "cik": "0001045810"},
    {"company": "JPMorgan Chase & Co.", "ticker": "JPM", "cik": "0000019617"},
    {"company": "Walmart Inc.", "ticker": "WMT", "cik": "0000104169"},
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "earnings_history.csv")

CSV_COLUMNS = [
    "company", "ticker", "cik", "filing_date", "period",
    "revenue_reported", "eps_diluted", "net_income",
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
# Extraction helpers (Step 5). Each returns the FIRST match in the document
# (earliest position across all patterns), or NOT_FOUND.
# -----------------------------------------------------------------------------

def earliest_match(patterns, text):
    """Return the regex match that starts earliest in text, or None."""
    best = None
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m and (best is None or m.start() < best.start()):
            best = m
    return best


PERIOD_PATTERNS = [
    # "fourth quarter fiscal 2024", "second quarter of 2025", "third-quarter 2024"
    r"\b(?:first|second|third|fourth)[\s-]quarter(?:\s+of)?(?:\s+fiscal)?(?:\s+year)?,?\s+(?:FY\s?)?\d{4}\b",
    # "fiscal 2024 fourth quarter"
    r"\bfiscal\s+(?:year\s+)?\d{4}\s+(?:first|second|third|fourth)\s+quarter\b",
    # "Q3 2024", "Q1 FY25", "Q3 FY2025"
    r"\bQ[1-4]\s*(?:FY\s?)?'?\d{2,4}\b",
    # "quarter ended September 30, 2024"
    r"\b(?:(?:first|second|third|fourth)\s+)?quarter\s+ended\s+[A-Za-z]+\s+\d{1,2},?\s+\d{4}\b",
]

MONEY = r"\$\s?([\d,]+(?:\.\d+)?)\s*(billion|million)\b"

REVENUE_PATTERNS = [
    # "revenue of $94.9 billion", "net sales were $3,210 million",
    # "Total revenues increased 5.5% to $169.6 billion"
    r"\b(?:revenues?|net\s+sales)\b[^$.]{0,60}" + MONEY,
]

NET_INCOME_PATTERNS = [
    # "net income of $12.9 billion", "Net income was $24.7 billion"
    r"\bnet\s+income\b[^$.]{0,40}" + MONEY,
]

EPS_PATTERNS = [
    # "diluted earnings per share of $1.64", "diluted EPS was $3.30",
    # "earnings per diluted share for the quarter were $0.78", "GAAP EPS of $0.57"
    r"\b(?:diluted\s+earnings\s+per\s+share|earnings\s+per\s+diluted\s+share|diluted\s+EPS|GAAP\s+EPS|loss\s+per\s+diluted\s+share)\b[^$]{0,60}?\$\s?(\(?-?\d+\.\d{2}\)?)",
    # "$1.64 per diluted share", "or $4.37 per share"
    r"\$\s?(\(?-?\d+\.\d{2}\)?)\s+per\s+(?:diluted\s+)?share\b",
]


def extract_period(text):
    m = earliest_match(PERIOD_PATTERNS, text)
    return m.group(0) if m else NOT_FOUND


def extract_money(patterns, text):
    """Return the amount and unit as reported, e.g. '94.9 billion'."""
    m = earliest_match(patterns, text)
    if not m:
        return NOT_FOUND
    return f"{m.group(1)} {m.group(2).lower()}"


def extract_eps(text):
    m = earliest_match(EPS_PATTERNS, text)
    if not m:
        return NOT_FOUND
    raw = m.group(1)
    negative = raw.startswith("(") or raw.startswith("-")
    number = raw.strip("()").lstrip("-")
    return f"-{number}" if negative else number


# -----------------------------------------------------------------------------
# EDGAR helpers
# -----------------------------------------------------------------------------

def get_item_202_filings(cik, ticker):
    """Step 2 + 3: query the submissions API, keep 8-K filings with Item 2.02,
    and return the four most recent (one per reportDate / quarter)."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = get(url, ticker)
    if response is None:
        return []

    try:
        recent = response.json()["filings"]["recent"]
    except (ValueError, KeyError) as exc:
        print(f"  WARNING [{ticker}]: could not read submissions JSON ({exc})")
        return []

    matches = []
    for i in range(len(recent["form"])):
        if recent["form"][i] != "8-K":  # exact match: excludes 8-K/A
            continue
        items = [item.strip() for item in recent["items"][i].split(",")]
        if "2.02" not in items:
            continue
        matches.append({
            "filing_date": recent["filingDate"][i],
            "report_date": recent["reportDate"][i],
            "accession": recent["accessionNumber"][i],
        })

    # Step 3: newest first, one filing per reportDate, stop at four.
    matches.sort(key=lambda f: f["filing_date"], reverse=True)
    selected, seen_report_dates = [], set()
    for filing in matches:
        if filing["report_date"] in seen_report_dates:
            continue
        seen_report_dates.add(filing["report_date"])
        selected.append(filing)
        if len(selected) == FILINGS_PER_COMPANY:
            break

    if len(selected) < FILINGS_PER_COMPANY:
        print(f"  NOTE [{ticker}]: only {len(selected)} Item 2.02 filing(s) found")
    return selected


def find_press_release_url(cik, accession, ticker):
    """Step 4: read the filing index page and return the URL of the EX-99.1
    .htm exhibit (or the first EX-99* .htm if there is no EX-99.1).
    Returns None if the index can't be read or no exhibit is found."""
    cik_no_zeros = str(int(cik))
    accession_no_dashes = accession.replace("-", "")
    folder_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{accession_no_dashes}"
    index_url = f"{folder_url}/{accession}-index.htm"

    response = get(index_url, ticker)
    if response is None:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    documents = []  # (type, file_name)
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        doc_type = cells[3].get_text(strip=True).upper()
        link = cells[2].find("a")
        file_name = link.get_text(strip=True) if link else cells[2].get_text(strip=True)
        if file_name.lower().endswith(".htm"):
            documents.append((doc_type, file_name))

    chosen = next((name for t, name in documents if t == "EX-99.1"), None)
    if chosen is None:
        chosen = next((name for t, name in documents if t.startswith("EX-99")), None)
    if chosen is None:
        return None
    return f"{folder_url}/{chosen}"


def format_money_for_print(value):
    return value if value == NOT_FOUND else f"${value}"


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------

def main():
    rows = []

    for company in COMPANIES:
        name, ticker, cik = company["company"], company["ticker"], company["cik"]
        print(f"\n=== {name} ({ticker}) ===")

        filings = get_item_202_filings(cik, ticker)

        for filing in filings:
            row = {
                "company": name,
                "ticker": ticker,
                "cik": cik,
                "filing_date": filing["filing_date"],
                "period": NOT_FOUND,
                "revenue_reported": NOT_FOUND,
                "eps_diluted": NOT_FOUND,
                "net_income": NOT_FOUND,
            }

            # Step 4: find and download the press release exhibit.
            exhibit_url = find_press_release_url(cik, filing["accession"], ticker)
            if exhibit_url is None:
                print(f"  WARNING [{ticker}]: no press release exhibit found for "
                      f"filing {filing['accession']} ({filing['filing_date']}); "
                      f"recording NOT_FOUND and continuing")
            else:
                response = get(exhibit_url, ticker)
                if response is not None:
                    text = html_to_text(response.text)
                    # Step 5 + 6: extract fields; misses stay NOT_FOUND.
                    row["period"] = extract_period(text)
                    row["revenue_reported"] = extract_money(REVENUE_PATTERNS, text)
                    row["eps_diluted"] = extract_eps(text)
                    row["net_income"] = extract_money(NET_INCOME_PATTERNS, text)

            # Step 7: print the row as it is processed.
            print(f"{ticker} | {row['period']} | "
                  f"Revenue: {format_money_for_print(row['revenue_reported'])} | "
                  f"EPS: {format_money_for_print(row['eps_diluted'])} | "
                  f"Net Income: {format_money_for_print(row['net_income'])}")

            rows.append(row)

    # Step 8: save the CSV (no blank cells: every missing field is NOT_FOUND).
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: (row.get(col) or NOT_FOUND) for col in CSV_COLUMNS})

    print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

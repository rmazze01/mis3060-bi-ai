# HW03 AI Usage Log

**Tool used:** Claude Cowork
**Scripts generated:** `hw03_earnings.py`, `hw03_executives.py`, `hw03_timeline.py`

---

## 1. Prompts sent to Claude Cowork

Specifications A and B are the full text of `hw03/specifications.md`. Both specifications rely on the same **Shared Setup** and **Constraints** sections, which were part of the same file and are included once below.

### Prompt 1: Specification A (Earnings Pipeline, Item 2.02) → `hw03_earnings.py`

~~~~text
## Specification A: Earnings Pipeline (Item 2.02)

**Script:** `hw03/hw03_earnings.py`
**Output:** `hw03/earnings_history.csv`

### Purpose

For each of the five companies, collect the four most recent quarterly earnings releases filed with the SEC on Form 8-K under Item 2.02 (Results of Operations and Financial Condition). Extract the headline figures from each release and save them to one CSV.

### Required Behavior

Do these steps in order, looping over the five companies:

1. **Set the User-Agent.** Every HTTP request uses the shared `User-Agent` header described above.

2. **Query the submissions API.** Request `https://data.sec.gov/submissions/CIK{cik}.json` using the 10-digit CIK. Loop through the `filings.recent` lists and keep only the filings where `form` is `"8-K"` and the split `items` list contains `"2.02"`.

3. **Select the four most recent filings.** Sort the matching filings by `filingDate` from newest to oldest. Take the first four, one per quarter: if two matching filings share the same `reportDate`, keep only the newer one and move on to the next filing. If a company has fewer than four, process however many exist and print a note saying how many were found.

4. **Find and download the earnings press release.**
   - Remove the dashes from the accession number to build the folder name. Build the filing index URL as:
     `https://www.sec.gov/Archives/edgar/data/{cik_no_leading_zeros}/{accession_no_dashes}/{accession_with_dashes}-index.htm`
   - Download the index page and read the document table. The earnings press release is the row whose **Type** column is `EX-99.1` and whose file name ends in `.htm`. If there is no `EX-99.1`, use the first `.htm` document whose type starts with `EX-99`.
   - Build that document's full URL (`https://www.sec.gov/Archives/edgar/data/{cik_no_leading_zeros}/{accession_no_dashes}/{file_name}`), download it, and strip the HTML to plain text as described in Shared Setup.
   - If no press release exhibit is found, print a warning and record the row with `"NOT_FOUND"` in every extracted field.

5. **Extract four fields from the plain text** using case-insensitive regular expressions. For each field, use the **first** match in the document, since the headline numbers appear near the top of a press release.
   - **`period`**: the fiscal period the release covers, such as "fourth quarter fiscal 2024", "second quarter of 2025", "Q3 2024", or "Q1 FY25". Look for patterns like `(first|second|third|fourth) quarter (of )?(fiscal )?(year )?\d{4}` and `Q[1-4] (FY)?\s?\d{2,4}`. Store the matched text as written.
   - **`revenue_reported`**: total quarterly revenue. Look for a phrase such as "revenue", "revenues", "net revenue", "total revenue", or "net sales" followed within a short distance by a dollar amount and a unit, for example "revenue of $94.9 billion" or "net sales were $3,210 million". Store the number and unit as reported, such as `94.9 billion` or `3,210 million`. Do not convert units.
   - **`eps_diluted`**: diluted earnings per share. Look for patterns such as "diluted earnings per share of $1.64", "diluted EPS of $1.64", "$1.64 per diluted share", or "earnings per diluted share of $1.64". Store just the number, such as `1.64`. If the number is shown as a loss in parentheses or with a minus sign, store it as a negative number.
   - **`net_income`**: quarterly net income. Look for "net income of $X million/billion" or "net income was $X million/billion". Store the number and unit as reported, such as `23.6 billion`.

6. **Handle missing fields.** If a regular expression finds no match, store the exact string `"NOT_FOUND"` in that field. Never leave a cell blank. A blank cell and a missing value are two different things.

7. **Print each row as it is processed** in exactly this format:
   ```
   [Ticker] | [Period] | Revenue: $X | EPS: $X | Net Income: $X
   ```
   For example: `AAPL | fourth quarter fiscal 2024 | Revenue: $94.9 billion | EPS: $1.64 | Net Income: $14.7 billion`. If a field is `NOT_FOUND`, print `NOT_FOUND` in its place without a dollar sign.

8. **Save the CSV.** After all five companies are processed, write every row to `hw03/earnings_history.csv` with these columns, in this order:
   `company`, `ticker`, `cik`, `filing_date`, `period`, `revenue_reported`, `eps_diluted`, `net_income`
   - `filing_date` is the `filingDate` from the submissions API (`YYYY-MM-DD`).
   - Rows are grouped by company in the order of the company list, newest filing first within each company.
   - After saving, print the total number of rows written and the full path to the file.

### Expected Output

- Up to 20 rows (5 companies × 4 filings).
- Console: one printed line per filing, plus any warnings and a final summary line.
- File: `hw03/earnings_history.csv`.
~~~~

### Prompt 2: Specification B (Executive Events Pipeline, Item 5.02) → `hw03_executives.py`

~~~~text
## Specification B: Executive Events Pipeline (Item 5.02)

**Script:** `hw03/hw03_executives.py`
**Output:** `hw03/executive_events.csv`

### Purpose

For each of the five companies, find every Form 8-K filed in the past 12 months under Item 5.02 (Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers). Extract each executive or director change it reports and save them to one CSV, with one row per event.

### Required Behavior

Do these steps in order, looping over the five companies:

1. **Set the User-Agent.** Every HTTP request uses the same shared `User-Agent` header as Specification A.

2. **Query and filter the submissions API.** Request `https://data.sec.gov/submissions/CIK{cik}.json` using the 10-digit CIK. Keep only filings that meet all three conditions:
   - `form` is exactly `"8-K"`
   - the split `items` list contains `"5.02"`
   - `filingDate` is within the past 12 months: on or after today's date minus 365 days, calculated when the script runs (not hard-coded)

3. **Download and extract events from each matching filing.**
   - Build the URL of the main 8-K document:
     `https://www.sec.gov/Archives/edgar/data/{cik_no_leading_zeros}/{accession_no_dashes}/{primaryDocument}`
   - Download it and strip the HTML to plain text as described in Shared Setup.
   - **Isolate the Item 5.02 section.** Take the text from the words "Item 5.02" up to the next heading that starts with "Item" followed by a number (such as "Item 9.01") or the word "SIGNATURE", whichever comes first. If "Item 5.02" can't be found, use the full document text.
   - Split the section into sentences, then look for event language:
     - **Departure** keywords: resign, resignation, retire, retirement, step down, depart, departure, terminated, termination, will not stand for re-election
     - **Appointment** keywords: appoint, appointed, appointment, elect, elected, named, promoted, hired, will join, will succeed
   - For each event found, extract:
     - **`event_type`**: `"departure"` if only departure language applies to that person, `"appointment"` if only appointment language applies, or `"both"` if the **same person** is leaving one role and taking another (for example, a CFO who is named CEO).
     - **`person_name`**: the person's full name: two to four capitalized words, which may include a middle initial and a suffix such as Jr. or III. Names often follow "Mr.", "Ms.", or "Dr.", or come right before a comma and a title. Store the name without the Mr./Ms./Dr. prefix.
     - **`title`**: the role involved, such as Chief Executive Officer, Chief Financial Officer, President, Chief Operating Officer, General Counsel, Chair of the Board, Director, or any "Chief ... Officer" or "Vice President ..." phrase. Store it as written in the filing.
     - **`effective_date`**: the date the change takes effect, normally a written date like "January 15, 2025" near the word "effective". Store it as `YYYY-MM-DD`. If the filing says "effective immediately", use the event date (`reportDate` from the submissions API).
   - Any field that can't be extracted is stored as the exact string `"NOT_FOUND"`, never left blank.

4. **One row per event.** If a filing reports more than one event (for example, one person departing and another being appointed), create a separate row for each one. If the same person and event appear in more than one sentence of a filing, record them only once.
   - Some Item 5.02 filings report only compensation or employment-agreement changes and no departure or appointment. For those, write one row with the filing's details and `"NOT_FOUND"` in `event_type`, `person_name`, `title`, and `effective_date`, so the filing is still accounted for.

5. **Print each event as it is processed** in exactly this format:
   ```
   [Ticker] | [Date] | [Event Type] | [Name] | [Title]
   ```
   where `[Date]` is the filing date. For example: `MSFT | 2025-03-14 | appointment | Jane A. Smith | Chief Financial Officer`.

6. **Report companies with no events.** If a company has no Item 5.02 8-K filings in the past 12 months, print exactly:
   ```
   [Ticker]: No executive events in past 12 months
   ```
   This is a valid result, not an error. Do not print a warning or stop the script, and do not add a row to the CSV for that company.

7. **Save the CSV.** After all five companies are processed, write every event row to `hw03/executive_events.csv` with these columns, in this order:
   `company`, `ticker`, `cik`, `filing_date`, `event_type`, `person_name`, `title`, `effective_date`
   - Rows are grouped by company in the order of the company list, newest filing first within each company.
   - If no company has any events, still create the file with just the header row.
   - After saving, print the total number of events written and the full path to the file.

### Expected Output

- Any number of rows, including zero, depending on what the five companies filed in the past 12 months.
- Console: one printed line per event, a "No executive events" line for each company with none, any warnings, and a final summary line.
- File: `hw03/executive_events.csv`.
~~~~

### Shared sections sent with both Specification A and B

<details>
<summary>Shared Setup</summary>

~~~~text
## Shared Setup (applies to both specifications)

### Companies

Both scripts process the same five companies. Store them at the top of each script as a list of dictionaries with the keys `company`, `ticker`, and `cik`:

| company | ticker | cik |
|---|---|---|
| Apple Inc. | AAPL | 0000320193 |
| Microsoft Corporation | MSFT | 0000789019 |
| NVIDIA Corporation | NVDA | 0001045810 |
| JPMorgan Chase & Co. | JPM | 0000019617 |
| Walmart Inc. | WMT | 0000104169 |

- When building the submissions API URL, pad the CIK with leading zeros to exactly 10 digits (for example, `320193` becomes `0000320193`).
- When building EDGAR Archives URLs (filing index pages and documents), use the CIK **without** leading zeros.
- In the output CSVs, write the CIK as the 10-digit zero-padded string so it is stored the same way in every row.

### HTTP requests

- Every HTTP request (to `data.sec.gov` and `www.sec.gov`) must send the header `User-Agent: MIS3060 Villanova rmazze01@villanova.edu`. Define this once as a constant and reuse it; do not send any request without it.
- SEC limits traffic to 10 requests per second. Pause at least 0.15 seconds after every request.
- If a request fails (network error or a status code other than 200), print a clear warning that names the ticker and the URL, then keep going with the next filing. One bad request must not crash the whole script.

### Libraries

Use `requests` for HTTP, `beautifulsoup4` for stripping HTML, `re` for text extraction, and `csv` (or `pandas`) for writing the output file. List any third-party libraries used in a comment at the top of the script.

### Reading the submissions API response

The submissions API returns JSON. The filings are under `filings` → `recent`, which holds parallel lists of equal length. Position `i` in each list describes the same filing. The fields needed are:

- `form`: the form type. Only keep filings where this is exactly `"8-K"`. Do not include amendments (`"8-K/A"`).
- `items`: a comma-separated string of item numbers, such as `"2.02,9.01"`. Split on commas and strip spaces before checking for an item number.
- `filingDate`: the date filed, formatted `YYYY-MM-DD`.
- `reportDate`: the date of the event being reported.
- `accessionNumber`: the filing ID, formatted like `0000320193-24-000123`.
- `primaryDocument`: the file name of the main 8-K document.

### Stripping HTML

To convert a downloaded HTML document to plain text, parse it with BeautifulSoup, remove all `<script>` and `<style>` tags, get the text with a space as the separator, replace non-breaking spaces with regular spaces, and collapse all runs of whitespace into single spaces.

### Script header

Each script must start with a comment block giving the script's name and purpose, the data source (SEC EDGAR 8-K filings), the author, and the date the script was generated.

### File locations

Build every output path relative to the script's own folder (use `os.path.dirname(os.path.abspath(__file__))`). That way the CSV always lands in `hw03/`, no matter which folder the script is run from.
~~~~

</details>

<details>
<summary>Constraints (both scripts)</summary>

~~~~text
## Constraints (both scripts)

- Each specification is **one Python script** that performs every step in a single run with no manual input needed.
- Label each step in the script with a section comment that matches the step numbers above.
- Only read public data from SEC EDGAR. Do not write any files other than the one CSV named in each specification.
- Use the exact column names, column order, print formats, and `"NOT_FOUND"` string shown above. They are graded as written.
~~~~

</details>

### Prompt 3: Timeline prompt → `hw03_timeline.py`

~~~~text
Write a Python script that reads `hw03/earnings_history.csv` and `hw03/executive_events.csv`. Do the following:
1. For each executive event in the events table, calculate the number of days between the executive event's `filing_date` and the nearest earnings filing date for the same company in the earnings table. Call this `days_to_nearest_earnings`. 2. Add a column `event_timing` that categorizes each executive event as: `'before earnings'` if the event came before the nearest earnings filing, `'after earnings'` if it came after, or `'same week'` if within 7 days of an earnings filing. 3. Save the combined table to `hw03/corporate_events_timeline.csv` with all columns from both source tables plus `days_to_nearest_earnings` and `event_timing`. 4. Print a summary: for each company, list any executive events and whether they occurred before or after the nearest earnings announcement. 5. Print a final count: how many events occurred before vs. after an earnings announcement across all five companies.
~~~~

---

## 2. Companies whose extractions required iteration (follow-up regex fixes)

**No follow-up regex fixes were needed** for the earnings figures I validated. Revenue and diluted EPS were extracted for all 20 earnings filings, and my known-answer check (5A) on Microsoft fiscal Q1 2026 matched the 8-K ($77,673 million revenue, $3.72 diluted EPS).

Extractions that would need iteration if I improved the pipeline:

- **Apple, NVIDIA, Walmart (net income):** `net_income` is `NOT_FOUND` for all 12 of their earnings rows. Their press releases report net income only in the financial tables, not in a sentence like "net income was $X billion," so the regex never matches. I left these as `NOT_FOUND` rather than fixing the pattern.
- **Walmart and NVIDIA (executive names):** the executives script picked up non-person phrases as names ("Non-Competition Agreements," "Covenant Not") and created a duplicate row ("Nora Johnson" for Suzanne Nora Johnson). Documented in `validation.md` (5D).
- **Apple (event type):** Tim Cook's row is labeled `departure`, but he also became Executive Chairman, so `both` would be more accurate (see `validation.md`, 5B).

During generation, the executives script was also fixed once before its first real run: a middle initial like "A." was treated as the word "a" and split names such as "Jane A. Doe." This was caught in testing, not on a specific company's filing.

---

## 3. Something the generated script did that I would not have thought to specify

**What it did:** In `hw03_executives.py`, Claude Cowork added logic to connect later references like "Mr. Maestri" back to the person's full name ("Luca Maestri") mentioned earlier in the filing, and to combine all the sentences about one person into a single event. That way the same person isn't counted several times just because the filing mentions them in more than one sentence. I specified "one row per event," but I wouldn't have thought about filings referring to people by last name only.

**Was it correct?** Partly. It worked on most filings (for example, Apple's April 2026 CEO change and JPMorgan's June 2026 leadership changes came out as one row per person). But the name-detection rule it relies on (a run of 2–4 capitalized words) also caught phrases that aren't people, like "Non-Competition Agreements," and it treated "Suzanne Nora Johnson" and "Nora Johnson" as two different people. It **needs adjustment**: a stricter check for what counts as a name, or matching partial names to full names already found.

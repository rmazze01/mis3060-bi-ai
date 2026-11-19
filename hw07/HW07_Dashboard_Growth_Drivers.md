# HW7: Where Did 2024 Growth Come From? A Two-Page Wildcat Dashboard
## MIS3060 Business Intelligence with AI | Villanova University
### Covers Weeks 11–12: data visualization principles and Power BI dashboards

> **Due:** *(instructor: set date)* | **Weight:** *(set in Brightspace)* | **Individual** | 
> **Submission:** push to your `mis3060-bi-ai` repo, folder `hw07/`, and paste the folder URL into Brightspace
> **Tools:** Power BI Desktop (Apporto; **no Power BI Service**) · Claude Desktop (script drafts, visual prototypes, formatting measure and alt-text drafts, design critique, summary draft) · VS Code (run the scripts) · Claude Code (review both scripts)

---

## The business question

Wildcat Capital's AUM grew in 2024. The managing director asks:

> **"Where did 2024 growth come from — markets or new money — and which client segments and regions drove it?"**

You will design and build a two-page Power BI report that answers this question, verify every number, have Claude critique the design, and write an audited executive summary.

This is not the ICE 12 page. ICE 12 was about fees and advisors; this report is about **AUM growth**.

## Starting point
- ICE12.pbix.pbix (add necessary measures based on ICE12 document: Ending AUM, Ending AUM LY, AUM YoY %, Ending Clients, Avg AUM per Client, Fee Yield (bps), Organic Growth Rate, AUM-Weighted Alpha, Alpha Signal, Top 10 Client Share) plus `Total Fees` and `Net Flows`
- One new measure you must add and reconcile:
```DAX
Market Change = ( [Ending AUM] - [Ending AUM LY] ) - [Net Flows]
```
  *Interpretation:* the part of the year's AUM change not explained by net new money (investment performance, plus fees and other cash effects). You must state this caveat on Page 1 (see Part B).



---

## Part A — Design plan (15 points)
Before opening Power BI, write `design_plan.md`. You will add one section to it later (item 6).
1. **Audience and question** in one sentence each; what the reader must conclude in 10 seconds
2. **A wireframe of each page** (photo of a sketch, or a PowerPoint/Figma image in `design/`), labeling every visual, its fields/measures, and the question it answers
3. **Visual choices**: for each visual, the Week 11 reasoning (data types, number of measures, analysis type)
4. **Interaction plan**: slicers (which dimension columns), edited interactions, the drill-through path, any tooltip
5. **Prototype with Claude** (before Power BI):
   - Write `scripts/00_make_extract.py` (Claude Desktop drafts, Claude Code reviews) that builds `data/growth_extract.csv`. Build it with pandas from the same source files your Assignment 6 script reads, not from Power BI:
     - **Grain:** one row per **year × client tier × region** (75 rows). Assign each client's AUM to the region of its advisor (`dim_advisor[region]`), using the same relationship as your Power BI model.
     - **`ending_aum`:** the balance on the December month-end snapshot of that year.
     - **`ending_aum_ly`:** the same balance one year earlier. For the first year in the data, leave it and `market_change` blank, but keep the row.
     - **`net_flows`:** net flows summed over the calendar year, using the same definition as your `Net Flows` measure.
     - **`market_change`:** `ending_aum − ending_aum_ly − net_flows`.
   - Add a short `data/README.md` that labels each column as a **balance** (a point-in-time snapshot that cannot be added across years) or a **flow** (summed over the year).
   - Record what Claude Code flagged in the script and what you changed in `README.md`.
   - Upload the CSV and its README to Claude Desktop and ask for **at least three** visual options for the flows-vs-market split, each available in Power BI Desktop. Save the images in `design/prototypes/`.
   - In `design_plan.md`, compare the options in Week 11 terms, say which one you will build and why, and note anything Claude got wrong (for example, adding balances across years).
6. **Add after you build Page 1:** a section showing your Claude-assisted formatting measure (Part B): Claude's draft, your final DAX, and what you changed and why.

## Part B — Page 1: Growth Drivers (25 points)
Required content (you choose the visuals and layout):
- KPI cards: **Ending AUM** (with AUM YoY % as its comparison), **Net Flows**, **Market Change**, **Organic Growth Rate**. A prior-year comparison on the other three cards is optional.
- A visual that splits 2024 AUM growth into **net flows vs. market change** (e.g., waterfall or stacked bar)
- The same split **by client tier** and **by region** (`dim_advisor[region]`)
- The **Market Change caveat** in a visible text box or subtitle on the page
- Slicer on `dim_date[year]` (saved with 2024 selected); a second slicer of your choice
- Insight titles; Week 11 principles applied (sorting, one accent, bars from zero, accessible color)
- **Alt text** on every visual; you may draft it with Claude, but every number in it must match the visual. Static alt text that matches earns most of the credit; **dynamic alt text with fx is required for full marks**.
- At least one **Claude-assisted formatting measure** (e.g., a Field value color measure or a dynamic insight title), documented in `design_plan.md` (Part A, item 6)

## Part C — Page 2: Segment Detail, a drill-through page (20 points)
- Drill-through from Page 1 on **client tier** (`dim_client[client_tier]`) with **Keep all filters** on, so the year and other slicer selections carry over; *optional:* also region
- Cards: Ending AUM, Ending Clients, Avg AUM per Client, Fee Yield (bps), AUM-Weighted Alpha with Alpha Signal
- An AUM trend for the segment, and the **top 10 clients** by Ending AUM with conditional formatting
- A dynamic subtitle naming the segment and year (SELECTEDVALUE); the back button works

## Part D — Verification (15 points)
1. Read every value you will reconcile from Power BI (from the cards, or from a DAX query in DAX query view) and save them in `reports/powerbi_values.csv`, in the same format as Assignment 6.
2. Extend your Assignment 6 script into `scripts/01_reconcile_kpis.py` (Claude Desktop drafts, Claude Code reviews). Reconcile, for **2024**: every Page 1 card at the firm level, the flows/market split for **each tier** and **each region**, and the Page 2 cards for **one tier** of your choice → `reports/kpi_reconciliation.csv` (same columns and tolerance as Assignment 6). Record what Claude Code flagged and what you changed in `README.md`.
3. **Extract check:** confirm that the 2024 rows of `data/growth_extract.csv` (summed to tier and to region) match the tier and region rows in `kpi_reconciliation.csv`. Report the result in `README.md`.
4. **Filter audit** in `README.md`: for each page, list every visual-, page- and report-level filter and every edited interaction, and confirm none changes a number silently.

## Part E — Design critique with Claude (10 points)
Give Claude Desktop a screenshot of each page, the audience and the question. Ask for a critique against the Week 11 checklist and the top three changes. In `claude/design_critique.md`, log **at least five** suggestions with your decision (**accept / adapt / reject**) and a reason, plus one claim Claude made about your page that was wrong. Save before/after screenshots of at least one change you accepted as `claude/before.png` and `claude/after.png`, and embed them in the log.

## Part F — Executive summary (15 points)
1. Give Claude your **verified** KPI values (paste the numbers; do not rely on a screenshot) and ask for a 150–200-word executive summary answering the business question
2. Edit it into `executive_summary.md` in your own voice
3. Add an **audit table**: every number and claim in the summary → the measure and the reconciliation row that supports it → correct / corrected. At least one sentence must state a limitation of the data or the Market Change measure (see the caveats under *Starting point*)

---

## Submission (`hw07/`)
- [ ] `README.md` (structure, how to run, Claude Code findings for both scripts, extract check, filter audit)
- [ ] `design_plan.md` (including the formatting-measure section) · `design/` (wireframes) · `design/prototypes/` (Claude prototypes)
- [ ] `scripts/00_make_extract.py` · `data/growth_extract.csv` · `data/README.md`
- [ ] `dashboard/hw07.pbix` · `dashboard/page1.png` · `dashboard/page2.png` (slicer and filter state visible in each screenshot; Page 2 shown after a drill-through)
- [ ] `scripts/01_reconcile_kpis.py` · `reports/powerbi_values.csv` · `reports/kpi_reconciliation.csv`
- [ ] `claude/design_critique.md` · `claude/before.png` · `claude/after.png` · `executive_summary.md`

> If your `.pbix` exceeds GitHub's 100 MB file limit, upload it to Brightspace and say so in `README.md`.

## Grading rubric *(indicative — set final weights in Brightspace)*
| Component | Pts | Full credit |
|---|---:|---|
| A Design plan | 15 | Audience and question clear; wireframes labeled; each visual choice justified with the Week 11 framework; interaction plan; extract script, CSV and data README correct (balances vs. flows labeled); Claude prototypes compared and a reasoned choice (4 of 15) |
| B Page 1: Growth Drivers | 25 | Required content; correct measures; Market Change caveat on the page; principles applied consistently; insight titles; accurate alt text (dynamic fx alt text for full marks); a Claude-assisted formatting measure documented in the design plan |
| C Page 2: Segment Detail | 20 | Drill-through works with Keep all filters on; required cards and table; conditional formatting; dynamic subtitle; back button |
| D Verification | 15 | Power BI values recorded; all required KPIs reconcile to pandas; extract check reported; filter audit complete and honest |
| E Claude critique | 10 | ≥ 5 suggestions with reasoned decisions; one Claude error identified; before/after evidence |
| F Executive summary | 15 | Answers the question; every number audited; a stated limitation |
| **Total** | **100** | |

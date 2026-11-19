# HW7 Design Plan: Where Did 2024 Growth Come From?

Written before opening Power BI. Numbers quoted here come from `data/growth_extract.csv` (pandas) and will be re-checked against Power BI in Part D.

## 1. Audience and question

- **Audience:** Wildcat Capital's managing director, who makes strategic decisions and wants a few numbers, a clear answer and the exceptions. This is not an analyst who will explore the data.
- **Question:** "Where did 2024 growth come from, markets or new money, and which client segments and regions drove it?"
- **What the reader must conclude in 10 seconds:** AUM grew $2.08B (+19.6%) in 2024, and almost all of it (about 96%) was market change. Net new money was only $78M (3.7%). Retail is the exception, where flows were about half of its growth. Northeast and Mid-Atlantic produced 65% of the dollar growth.

## 2. Wireframes

Wireframe images go in `design/` (`wireframe_page1.png`, `wireframe_page2.png`). Each box is labeled with its visual, fields and the question it answers. The layout they follow:

**Page 1: Growth Drivers** (16:9, top-left is most important, read left to right and top to bottom)

```
+--------------------------------------------------------------------------+
| Title (insight): "Markets, not new money, drove 2024 AUM growth"         |
| Subtitle: Year 2024 | All tiers and regions | Firm total                 |
+---------------------------------------------------------+----------------+
| KPI card: Ending AUM (+ AUM YoY %) | Net Flows |        | Slicer: year   |
|   Market Change | Organic Growth Rate                   | (2024 saved)   |
+---------------------------------------------------------+ Slicer: region |
| Waterfall: firm growth = net flows + market change      |                |
|  "How much of the growth was new money?"               |                |
+---------------------------+-----------------------------+----------------+
| 100% stacked bar by tier  | Stacked bar by region ($)   | Caveat text    |
| "Which tiers relied on    | "Which regions drove the    | box: Market    |
|  new money?"              |  dollars?"                  | Change note    |
+---------------------------+-----------------------------+----------------+
```

**Page 2: Segment Detail** (drill-through on client tier)

```
+--------------------------------------------------------------------------+
| Title: "Segment detail"  Subtitle: "Tier: UHNW | Year: 2024"   [Back]    |
+--------------------------------------------------------------------------+
| Cards: Ending AUM | Ending Clients | Avg AUM per Client | Fee Yield (bps)|
|        | AUM-Weighted Alpha + Alpha Signal                               |
+-----------------------------------+--------------------------------------+
| Line chart: Ending AUM trend      | Table: top 10 clients by Ending AUM  |
| for the segment                   | (conditional formatting: data bars)  |
+-----------------------------------+--------------------------------------+
```

## 3. Visual choices (framework: data types, number of measures, analysis type)

All three Page 1 breakdown visuals use the same two measures, `[Net Flows]` and `[Market Change]`, and the same colors. Both are flows (they add across a year), so adding them up within a year is valid. `Ending AUM` is a balance, so it is never added across years.

| Visual | Dimension | Measures | Analysis type | Why this visual |
|---|---|---|---|---|
| KPI cards (Card with a reference label) | none | 4 (Ending AUM with AUM YoY %, Net Flows, Market Change, Organic Growth Rate) | Overview, comparison with last year | The reader first needs "where are we now?" with a comparison. A card shows one number clearly, and a gauge would need a target that the data does not have |
| Waterfall, firm total | The two drivers (nominal, 2 values) | 1 (amount) | Composition of a change: part-to-whole | The question is how a total change splits into two parts. A waterfall shows both parts and the total in one picture, and it answers the managing director's first question directly |
| 100% stacked bar, by client tier | Client tier (nominal, 3 categories) | 2 (flows and market) | Composition: part-to-whole, comparing shares | The tier question is "which tier relied on new money?", which is about share, not size. UHNW is $1.58B of the growth and Retail is $86M, so a dollar bar would make Retail's 52% flows share invisible |
| Stacked bar, by region (dollars) | Region (nominal, 5 categories) | 2 (flows and market) | Composition and ranking | The region question is "which regions drove the dollars?", which is about size. Sorted from largest to smallest, so the ranking can be read by length. Labels carry the flow amounts, because the flow slice is thin |
| Text box | none | none | Caveat | Market Change is a residual (see below). It has to be visible on the page, not in a tooltip |

**Principles applied to every visual**
- **One accent color.** Net flows is the accent (blue) because the question is "markets or new money?" and new money is what the reader is looking for. Market change is grey. The same two colors are used on all three visuals, so the legend is learned once. The waterfall's total bar is a darker neutral.
- Blue and grey also work for color-blind readers, and the direct labels mean the meaning does not depend on color.
- Bars start at zero. The waterfall's market-change bar floats by design, but its axis also starts at zero.
- Sorted by value, gridlines light or off, no legend where direct labels do the job, display units in $M or $B with one decimal, and titles that state the finding.
- 7 objects on the page (cards, waterfall, two bars, caveat, two slicers), within the 5 ± 2 guideline when the cards are one visual.

**Visuals I considered and did not use**
- **Matrix heat map (tier × region).** It shows all 15 segments, but it is 15 numbers to decode, it needs conditional formatting to be readable, and the detail page already answers the tier question. It could be a later drill-down, not part of the Page 1 overview.
- **Line chart over time.** Net flows and market change are year-level flows, and the question is about one year, so a trend is not what is being asked.
- **Pie or donut.** The split is only two parts, but it has to be compared across 3 tiers and 5 regions, which angles do poorly.

## 4. Interaction plan

- **Slicers:** `dim_date[year]` (saved with 2024 selected) and `dim_advisor[region]` (the second slicer). Both are on dimension columns, not fact columns. They sync to Page 2, so the year and region carry through the drill-through.
- **Edited interactions:**
  - The year and region slicers filter the cards, waterfall and tier bar. The region slicer does not filter the region bar (set to None), which stays on all regions as a comparison; the region bar's subtitle says "all regions".
  - Clicking a bar in the tier or region chart filters the waterfall (Filter), so the reader can see one segment's split.
  - Clicking a bar does not change the KPI cards (None), which stay the firm total for the selected year. The page subtitle says "Firm total".
  - Every pair will be tested by clicking and checking that the page still tells the truth (see the filter audit in `README.md`).
- **Drill-through:** from Page 1 to Page 2 on `dim_client[client_tier]`, with Keep all filters on, so the year and region selections carry over. Optionally also on region.
- **Tooltip:** hovering a tier bar shows Ending AUM, Ending Clients and Organic Growth Rate (added to the Tooltips well; no tooltip page needed).
- **Page 2:** the back button returns to Page 1, and the subtitle names the segment and year with `SELECTEDVALUE`.

## 5. Prototypes with Claude

Claude Desktop drew four options from `data/growth_extract.csv` and `data/README.md` (images in `design/prototypes/`). I checked every number in them against the extract, and all of them matched.

| Option | What it answers | Week 11 assessment | Decision |
|---|---|---|---|
| 1. Waterfall, firm total | Markets or new money? | Part-to-whole of one change, 1 measure, 2 categories. The most direct answer to the headline question. The floating bar is the one place bars do not start at the baseline | **Build** (headline visual) |
| 2. 100% stacked bar by tier | Which tier relied on new money? | Part-to-whole, 3 categories, 2 measures. Shows share accurately, but hides dollar size (Claude said so itself) | **Build** (tier), with dollar totals in the tooltip |
| 3. Stacked bar by region, dollars | Which regions drove growth? | Composition and ranking, 5 categories. Size and ranking are easy to read. The flow slice is too thin to see in the small regions, so labels are needed | **Build** (region) |
| 4. Matrix heat map, tier × region | Which segments rely on new money? | 15 cells, two dimensions. Dense, and needs two values per cell | **Do not build** on Page 1; maybe a later drill-down |

The options are not four competing answers to one question. They are four cuts (firm, tier, region, tier × region), so I chose by question: Option 1 for the firm, Option 2 for tier and Option 3 for region. The reason for different forms for tier and region is that the two questions differ: tier is about share, and region is about dollars.

**What Claude got wrong or missed**
1. **The DAX was built on `growth_extract[...]` columns.** In the real model, the visuals must use the model's measures (`[Net Flows]`, `[Market Change]`, `[Ending AUM]`) with `dim_date`, `dim_client` and `dim_advisor`. A page built on the extract would make Part D's reconciliation against the extract circular, because it would be checking the extract against itself.
2. **The drawings show labels that Power BI may not draw natively.** Examples are "(96.3%)" on the waterfall bars, the "$1,581M total" at the end of each 100% bar, and two values stacked inside each matrix cell. I will test each in Power BI Desktop and use a tooltip or a measure for any that are not available.
3. **Two accent colors.** The prototypes used blue and orange together, plus grey, which splits attention. I will use one accent (net flows in blue, market change in grey).

Claude did avoid the main trap: it did not add `ending_aum` across years, and it labeled the series "Market change (residual)". Even so, the residual also contains advisory fees, so the caveat below has to be on the page.

## Market Change caveat (text box on Page 1)

"Market Change is the part of 2024's AUM change not explained by net flows: (Ending AUM − Ending AUM last year) − Net Flows. It includes investment performance, fees and other cash effects, and it is not a measured market return. No clients joined or left in 2024."

## 6. Claude-assisted formatting measure

_To be added after Page 1 is built: Claude's draft, my final DAX, and what I changed and why._

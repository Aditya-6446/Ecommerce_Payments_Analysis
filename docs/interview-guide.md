# Digital Payments Explorer: interview guide

This guide explains the project in plain language. Read the short pitch first, then practice the questions aloud. Use your own words in an interview and be clear that the original research was collaborative.

## The 45-second explanation

“Our original project listed a main payment service and two alternatives for each of 100 countries and territories. I turned that research snapshot into a reproducible analysis: I preserved the raw file, cleaned names and link formatting with a logged Python pipeline, reshaped the data into market, service and listing tables, and explored it with SQL, Excel, Power BI and an interactive Streamlit dashboard. The dataset contains 300 service listings and 191 retained service identities. The most important decision was to measure *mentions in the dataset*, not real-world market share. The source percentages lack documented evidence, so the dashboard labels them unverified and excludes them from rankings.”

## What problem does it solve?

The original CSV was useful research but hard to explore: each row mixed a market, three service roles, links and a percentage. Names and URL formats were inconsistent, and the percentages had no documented source, time period or denominator. The project makes the records searchable and comparable while showing exactly what is known and what still needs verification.

This is a **research explorer**, not a live payments monitor. It contains no individual transactions, revenue, user counts or measured adoption rates.

## The data, in one picture

```text
Original Test.csv (100 rows, 14 columns)
              |
              v
Python validation + documented cleaning
              |
              +--> Markets: 100 market records
              +--> Services: 191 retained service identities
              +--> Listings: 300 market/service/role records
              +--> Changes: every corrected name or URL format
              +--> Review: missing evidence and duplicate checks
              |
              +--> CSV + SQLite --> SQL analysis
              +--> Streamlit + Plotly dashboard
              +--> Excel workbook and Power BI report snapshots
```

Each original market row has one `Primary`, one `Alternative 1` and one `Alternative 2` listing. That is why 100 rows become 300 listing records. `Primary` means the original table's main-service column; it is **not** proof that the service leads that market.

`market_id` identifies the market; `service_id` identifies a cleaned service; `listing_id` identifies each market/role record. The market and service tables each have a one-to-many relationship with listings. This structure lets the same service appear in many markets without repeating its identity in the service table. The listings also retain useful display labels and the original service spelling for traceability.

## The five metrics you must understand

| Metric | Plain meaning | Full snapshot |
| --- | --- | ---: |
| Markets selected | Distinct market IDs among the current listings | 100 |
| Services listed | Distinct service IDs among the current listings | 191 |
| Service listings | Number of market/service/role records | 300 |
| Primary listings | Records in the original main-service position | 100 |
| Markets listed for a service | Distinct markets mentioning that service | PayPal: 47 |

The distinction between **listings** and **distinct markets** matters. Tanzania's source row names M-Pesa in two roles. Both listings remain visible, but Tanzania counts only once in M-Pesa's market coverage. In SQL, this is `COUNT(DISTINCT market_id)` rather than `COUNT(*)`. In Power BI, the equivalent is `DISTINCTCOUNT(Listings[Market ID])`. In Excel, a first-occurrence flag prevents the duplicate from inflating coverage.

PayPal is mentioned in 47 distinct market records: two `Primary` roles and 45 alternative roles. This says how often it occurs in this research table. It says nothing about PayPal's users, transactions, current availability or actual market share.

## How the cleaning works

1. Read the CSV as text so original strings are preserved. Require all expected columns, non-empty unique market names, and percentage syntax between 0% and 100%.
2. Assign stable IDs in source-row order and use ISO-3 country codes for the map. The displayed country names remain from the source.
3. Expand each row into three listing records. Trim extra spaces and apply only explicit spelling/capitalization aliases, such as `Goggle Pay` → `Google Pay` and `Paypal` → `PayPal`.
4. Normalize URL **syntax** (for example, add a missing `https://`) without claiming the link works or proves availability. Preserve original values in the raw file and log each change.
5. Keep potentially different products separate when the evidence does not justify a merge. For example, Google Pay and Google Wallet stay separate. EasyPay and Easypay use their supplied website hostnames as part of identity because the source domains differ.
6. Flag duplicate market/service pairs, preserve the original roles, and produce an explicit review queue.

The current audit records **9 name corrections** and **302 URL-format changes**. There are **102 review tasks**: 100 missing-share-evidence tasks, one repeated-service task and one general service/link-verification task.

## Why the original percentages are not in the ranking

All 100 original market-share values have no documented primary source, observation period or definition of “share.” A value might refer to users, transaction count, payment value, installs or something else. Comparing or averaging those percentages would suggest certainty the dataset does not support. The pipeline retains them as `reported_share`, marks them `Unverified`, leaves evidence fields blank and displays them only in research/data-review views. Missing evidence is not treated as zero.

If asked how to improve this, say: “I would verify a specific service and market against primary documentation, record the observation date and denominator, and only then compare like-for-like measurements. I would update the review queue one record at a time.”

## What each tool contributes

- **Python / pandas (`src/payments.py`)** performs repeatable validation, cleaning, reshaping, filtering and coverage calculations. `prepare_data.py` writes prepared CSV files, a summary and a SQLite database.
- **SQL (`sql/analysis.sql`)** independently checks the market/listing totals, distinct service coverage, role counts, market comparison and missing evidence.
- **Streamlit + Plotly (`streamlit_app.py`)** provide the interactive dashboard: sidebar filters, search, four metric cards, top-service bar chart, geographic coverage, a market comparison, raw listing table and CSV downloads. Its map uses ISO-3 codes. The visual design lives in `dashboard.css`.
- **Excel** provides an accessible workbook with an Overview market selector in cell E12, formula-based service coverage, and editable fields for source URLs, periods and definitions. Edits there do not automatically sync to Python or Power BI.
- **Power BI** provides a populated three-page report: Overview, Market comparison and Data review. The editable project contains related Markets, Services and Listings tables plus research tables, Power Query snapshot data and DAX measures. The `.pbix` is the ready-to-open report; the `.pbip` is the editable source project.
- **Tests** check the cleaning and identity rules, duplicate-aware counts, filtering, SQL results and dashboard interactions. Tests confirm the software's behavior; they do not validate the real-world payment claims in the source.

The dashboard runs locally from the repository. The GitHub README shows screenshots and downloadable files; GitHub Pages hosting for the separate portfolio does not automatically host this Python dashboard.

## A two-minute live demo

1. Open the dashboard and state the caveat: “These are source-table mentions, not market-share statistics.”
2. Point to 100 markets, 191 services and 300 listings. Explain why 100 source rows became 300 listings.
3. Filter to a market such as India. Show how the metrics, service chart, map and listing table respond.
4. Switch to **Compare markets** and select India, the United Kingdom and the United States. Explain that the roles are inherited from the source, not independently verified rankings.
5. Open **Data & methodology** and show the change audit and unverified-share queue. Explain why you did not average or rank the original percentages.

## Practice questions and honest answers

**What was your contribution?**  “The original data collection was collaborative. This repository turns that snapshot into a documented, reproducible analysis and interactive outputs. I can walk through the cleaning rules, data model, metrics, visualizations and limitations.” Only claim the parts you can personally explain and demonstrate.

**Why normalize into three tables?**  “Markets and services are reusable entities, while each listing is one occurrence of a service in a market and role. Separating them prevents repeated entity details and makes filtering and distinct counting easier.”

**Why not just count rows for coverage?**  “A service can appear twice in one market. Counting distinct market IDs avoids calling two mentions two markets.”

**Is PayPal the most popular payment service globally?**  “That is not supported. PayPal appears in the most distinct markets in this particular table, 47. Popularity would require dated, comparable user or transaction evidence.”

**Why keep questionable values or duplicate roles?**  “Removing them would hide what the source actually said. I preserve them, label uncertainty and separate analytical counts from a review queue.”

**How do you know cleaning did not change the meaning?**  “I use a small, explicit alias list, preserve the raw file, record cell-level before/after changes, keep ambiguous identities separate and test key totals.”

**What does a filter do?**  “It selects listing records by market, service, source role or search text. The cards and charts recompute from that selection. The methodology view continues to explain the full source snapshot.”

**How does Power BI avoid duplicate coverage?**  “Its related model filters the Listings table and a DAX distinct-count measure counts Market ID once for each service, even if a service has multiple roles in the same market.”

**What would you add with more time?**  “First, dated primary-source verification and a consistent definition of service type. Then automated link/source review and dated snapshots. Only after that would I explore adoption or market-share comparisons.”

**What is the project's main weakness?**  “The original source lacks provenance for its percentages and current availability claims. I made that weakness visible and kept the conclusions limited to what the records actually show.”

## Terms in plain English

- **Dataset snapshot:** a fixed copy of the original research at an unspecified collection date.
- **Listing:** one service named in one market and role.
- **Coverage:** how many distinct market rows mention a service.
- **Normalization:** separating markets, services and their listings into related tables.
- **Provenance:** where a value came from and how we can trace it to the original source.
- **Denominator:** the “out of what?” behind a percentage, such as total users or total transactions.
- **DAX:** Power BI's formula language for measures such as distinct market count.
- **Power Query:** Power BI's data preparation/import layer.
- **Audit trail:** a record of what changed during cleaning and why.

Before an interview, open the project once and practice explaining a filter, one SQL distinct-count query and one unverified-share example. Understanding those three examples matters more than memorizing every file name.

# Data dictionary

Prepared CSV files and SQLite tables use the same field names. Original strings remain in `data/raw/payments.csv` and the root `Test.csv`.

## Markets: one row per source country or territory

| Field | Meaning |
| --- | --- |
| `market_id` | Unique ID assigned in source-row order; regenerate with care if rows are reordered |
| `country` | Trimmed original market label |
| `iso3` | ISO-3 lookup code used by the map |
| `primary_service`, `primary_service_id` | Cleaned name and identity key for the source's main service |
| `alternative_1`, `alternative_2` | Cleaned names for the source's two alternatives |
| `reported_share` | Original percentage stored as a decimal fraction, with no verification inferred |
| `share_status` | `Unverified` in this snapshot |
| `share_source_url`, `share_period`, `share_definition` | Empty evidence fields; unavailable information is not zero |

## Services: one row per retained service identity

| Field | Meaning |
| --- | --- |
| `service_id` | Stable hash-based identity key generated from the cleaned service name; EasyPay/Easypay also uses the supplied hostname |
| `service` | Cleaned service label; not a verified classification or availability claim |

## Listings: one row per market and listed role

| Field | Meaning |
| --- | --- |
| `listing_id` | Unique market/role ID |
| `market_id`, `service_id` | References to Markets and Services |
| `country`, `iso3`, `service` | Denormalized labels for convenient analysis |
| `source_name` | Original service-name cell, before cleaning |
| `role` | `Primary`, `Alternative 1` or `Alternative 2`, taken from source column position |
| `website`, `review_url`, `screenshot_url` | Original references with normalized URL syntax; content and current availability are unverified |

The market/service pair is intentionally not unique because the source lists M-Pesa twice for Tanzania. `listing_id` remains unique.

## Audit tables

| Table | Fields | Purpose |
| --- | --- | --- |
| Changes | `market_id`, `country`, `field`, `original`, `cleaned`, `reason` | Cell-level trail for name and URL-format changes |
| Review | `market_id`, `country`, `issue`, `detail`, `next_step` | Missing-source and duplicate-record research tasks; global tasks may have an empty market ID |
| Service coverage (CSV) | `service_id`, `service`, `markets_listed`, `primary`, `alternative`, `listings` | Reproducible service coverage and role counts |
| Summary (JSON) | Source hash, source dimensions, prepared totals, changes and top-coverage service | Reconciliation and provenance |

## Relationships

`Markets.market_id` and `Services.service_id` each have a one-to-many relationship to Listings. Changes and Review retain source labels and IDs for inspection; the Power BI research tables are independent of overview filters.

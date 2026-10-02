# Methodology and provenance

## Source

The source is the original [`Test.csv`](../Test.csv) in this repository, preserved as [`data/raw/payments.csv`](../data/raw/payments.csv). It has 100 rows and 14 columns. The source records countries/territories, a main payment service, a market-share value, websites, review references, screenshot references and two alternative services.

The project does not document an original collection date, primary sources for the percentages, observation periods or measurement denominators. Supplied links are research references, not evidence that a service is currently available. “Research snapshot” describes this retained table; it does not imply a known observation date.

Baseline Git commit: `de7bddb60b6d734703471254ec6b90d57664c30e`.

Raw-file SHA-256: `8a36f7fc21fb058b83c600fa671c6d882a327073923d77d30cb76e4b48406649`.

## Preparation

1. Read source cells as strings, preserving supplied values.
2. Require populated, unique market names and the documented source columns. Validate percentage syntax and its 0–100% range.
3. Assign market IDs in source-row order and map country labels to ISO-3 codes for the geographic view. Display names remain the source names. ISO lookup aliases are identifiers, not geographic or political analysis.
4. Expand each row into three listing records, preserving the source's role order.
5. Trim whitespace and apply the explicit alias map in `src/payments.py`. Log each changed name.
6. Add missing `https://` schemes and normalize URL syntax. Preserve meaningful paths, queries and fragments. Log every change; do not claim link verification.
7. Build a service lookup. Keep Google Wallet separate from Google Pay. For the two differently named EasyPay/Easypay records, include the supplied hostname in the identity key.
8. Flag repeated market/service pairs without deleting original roles.
9. Retain original percentages as `reported_share`, label them `Unverified`, and leave source, period and definition fields empty.
10. Export CSV tables, a summary, coverage counts and SQLite tables.

## Metrics

| Metric | Definition |
| --- | --- |
| Markets selected | Distinct market IDs in the selected listing records |
| Services listed | Distinct service IDs in the selected listing records |
| Service listings | Number of listing records, including repeated roles |
| Primary listings | Records with the source role `Primary` |
| Markets listed / coverage | Distinct market IDs mentioning a service; repeated roles count once |
| Primary / alternative coverage | Distinct markets mentioning a service in that role group; the groups may overlap |
| Shares awaiting evidence | Market records with an original percentage and no documented verification |

Listing coverage is not an adoption rate or verified availability measure. Summing primary and alternative coverage can exceed total distinct coverage where the same service occurs in both roles in one market. The service table's `listings` total instead counts records.

## Consistency across outputs

Python and SQL count distinct market IDs. Excel flags the first occurrence of each market/service pair before aggregating coverage. Power BI uses a related Markets/Services/Listings model and `DISTINCTCOUNT` measures. The dashboard displays the first 12 services by coverage and name; Power BI's coverage chart includes ties at the ranking cutoff.

All original market-share percentages are excluded from coverage charts, rankings and headline aggregates. The workbook and data-review view display them only with their unverified status for research.

## Limits and next steps

Source roles and service names may reflect inconsistent definitions. The table mixes wallets, networks and payment schemes, and links may be stale. No service-type classification, collection date, adoption trend, fraud model or transaction conclusion is invented.

The next research step is to verify individual service identities and country availability, then supply primary evidence with a date and denominator for any market-share comparison. Update the review queue as evidence is collected rather than marking the entire table verified at once.

# Findings from the research snapshot

These findings describe the included source table. They do not establish current service availability, adoption, transaction volume or customer preferences.

## Coverage and listed roles

The original table contains 100 countries and territories, with one main service and two alternatives per row. Normalization produces 300 listing records and 191 service entries. The listed roles come from the source; “main service” does not imply verified leadership in that market.

| Service | Distinct markets mentioning it |
| --- | ---: |
| PayPal | 47 |
| Apple Pay | 14 |
| Revolut | 7 |
| Google Pay | 6 |
| Alipay | 4 |
| MobilePay | 4 |
| MTN Mobile Money | 4 |
| Orange Money | 4 |

PayPal is listed as the main service in two markets and as an alternative in 45. A useful follow-up is to verify those individual listings with dated service documentation. The dataset cannot explain why PayPal appears more often or quantify actual usage.

## Data quality changes the interpretation

- Tanzania lists M-Pesa in both the main and second-alternative positions. The listing table retains both records for traceability. Coverage uses distinct market/service pairs, so the duplicate does not inflate that service's market coverage.
- The pipeline documents nine spelling, capitalization or whitespace changes. For example, `Goggle Pay` becomes `Google Pay` and `Paypal` becomes `PayPal`.
- Google Wallet and Google Pay remain separate entries. EasyPay and Easypay also remain separate because the supplied domains differ. Those distinctions prevent unsupported identity merges.
- 302 URL-format changes add missing schemes or normalize syntax. The original links are retained in the raw file and change log. No availability or content verification is implied.

## Evidence is the next research priority

Every original market-share value is missing a primary source, observation period and measurement definition. A percentage could refer to users, payments, value, installs or another denominator; the table does not say which. Ranking countries or aggregating these percentages would therefore create an unsupported conclusion.

The source-review table contains 102 tasks: one evidence task per market, one duplicate-record task and one general service/link-verification task. The Excel Markets sheet provides editable fields for source URLs, periods and definitions. Until evidence is supplied and reviewed, the analytical views use listing counts only.

## Reproduce these findings

Run `python prepare_data.py` and inspect `data/processed/summary.json` and `service_coverage.csv`. Queries 1, 2, 3 and 5 in `sql/analysis.sql` reproduce the totals, coverage, role counts and evidence gaps. The dashboard, Excel workbook and Power BI report use this same prepared snapshot.

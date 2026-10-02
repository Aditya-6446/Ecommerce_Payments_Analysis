# Open and update the outputs

## Excel

Open `outputs/payments-analysis/Digital-Payments-Analysis.xlsx` in Excel. The Overview sheet has a market selector in **E12**. Choose a market to show its recorded main service and alternatives. Service analysis uses formulas over the Listings sheet, including a first-occurrence flag to avoid duplicate coverage counts.

The Markets sheet has highlighted input columns for primary-source URLs, measurement periods and definitions. Adding a note there is a research step; it does not automatically mark a record verified. Changes in the workbook do not sync back to the Python source, dashboard or Power BI.

The workbook is an exported analysis snapshot. After changing source data, rebuild/review the workbook and compare all totals before replacing the released file.

## Power BI

For immediate use, open `outputs/payments-analysis/Digital-Payments-Explorer.pbix`. It includes the loaded snapshot and three pages:

1. **Overview:** market, service and listing metrics; service coverage; market selection.
2. **Market comparison:** main service and two alternatives recorded for each selected market.
3. **Data review:** missing market-share evidence, name corrections, URL-format changes and research tasks.

For source editing, open `powerbi/Digital-Payments-Explorer.pbip` in Power BI Desktop. Keep the adjacent `.Report` and `.SemanticModel` folders together. If the project indicates incomplete data on first open, select **Refresh**. The prepared CSV snapshot is embedded in Power Query, so it does not depend on the original author's computer paths or a cloud login.

The semantic model has five tables and nine DAX measures. Markets and Services filter Listings through one-to-many relationships. Research tables are separate, so their total tasks do not silently change with an overview market selection.

The report's PBIR files support documented external editing. See [Microsoft's report-project documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) for the file structure and refresh workflow.

## Update the research source

1. Preserve a copy of the current raw file and record the new source's provenance and observation date.
2. Edit `data/raw/payments.csv` using the existing source schema. Do not replace missing evidence with guessed percentages.
3. Run `python prepare_data.py` and `python -m pytest -q`.
4. Review Changes, Review and summary totals. Check identities, accents, duplicate roles and country mappings.
5. With Power BI closed, run `python build_powerbi.py` to update the embedded model snapshot. Existing report layout files are preserved.
6. Reopen the project, refresh and verify the cards, coverage and comparison. Save a new PBIX from the checked project.
7. Rebuild/review Excel separately and replace the release workbook only after its formulas and chart agree with the new prepared data.
8. Update the findings and screenshots when the results change.

`build_powerbi.py` updates the included TMSL/BIM model format. If the project has been converted to TMDL in Power BI, the builder stops rather than overwriting native model changes. Preserve those edits and update the Power Query partitions in Power BI instead.

The original `Test.csv` and legacy `EDA_Report.html` remain historical artifacts. Data preparation writes derived outputs and does not modify those originals.

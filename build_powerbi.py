"""Build a portable Power BI project from the prepared, documented snapshot.

The data model embeds the prepared CSV snapshot, so opening the project does not
depend on personal filesystem paths or a cloud account. Report layout files are
only created when absent, preserving subsequent report customization.
"""

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
PBI = ROOT / "powerbi"
REPORT = PBI / "Digital-Payments.Report"
MODEL = PBI / "Digital-Payments.SemanticModel"
SCHEMA_BASE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"


def save(path, content, overwrite=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not path.exists():
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def literal(value):
    if isinstance(value, bool):
        text = str(value).lower()
    elif isinstance(value, (int, float)):
        text = f"{value}D"
    else:
        text = "'" + str(value).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": text}}}


def color(value):
    return {"solid": {"color": literal(value)}}


def field(table, prop, measure=False):
    return {"Measure" if measure else "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": prop}}


def projection(table, prop, measure=False):
    return {"field": field(table, prop, measure), "queryRef": f"{table}.{prop}", "nativeQueryRef": prop}


def visual(page, name, visual_type, pos, roles=None, title="", objects=None, sort=None):
    item = {"$schema": SCHEMA_BASE + "visualContainer/2.0.0/schema.json", "name": name,
            "position": dict(zip(["x", "y", "width", "height"], pos))}
    item["position"].update(z=0, tabOrder=0)
    config = {"visualType": visual_type,
              "visualContainerObjects": {
                  "title": [{"properties": {"show": literal(bool(title)), "text": literal(title),
                                              "fontColor": color("#17233C"), "fontSize": literal(12), "bold": literal(True)}}],
                  "background": [{"properties": {"show": literal(True), "color": color("#FFFFFF"), "transparency": literal(0)}}],
                  "border": [{"properties": {"show": literal(False)}}],
              }}
    if roles:
        config["query"] = {"queryState": {role: {"projections": fields} for role, fields in roles.items()}}
        if sort:
            config["query"]["sortDefinition"] = {"sort": [{"field": sort, "direction": "Descending"}], "isDefaultSort": False}
    if objects:
        config["objects"] = objects
    item["visual"] = config
    save(REPORT / "definition/pages" / page / "visuals" / name / "visual.json", item, overwrite=False)


def text(page, name, value, pos, size=20, tint="#17233C", bold=False):
    visual(page, name, "textbox", pos, objects={"general": [{"properties": {"paragraphs": [{"textRuns": [
        {"value": value, "textStyle": {"fontFamily": "Segoe UI", "fontSize": f"{size}pt", "color": tint,
                                       "fontWeight": "bold" if bold else "normal"}}
    ]}]}}]})


def card(page, name, measure, title, pos):
    visual(page, name, "card", pos, {"Values": [projection("Listings", measure, True)]}, title,
           objects={"labels": [{"properties": {"color": color("#315CDE"), "fontSize": literal(32)}}],
                    "categoryLabels": [{"properties": {"show": literal(False)}}]})


def model_table(name, filename, fields):
    df = pd.read_csv(ROOT / "data/processed" / filename, keep_default_na=False)
    csv = df.to_csv(index=False, lineterminator="\n")
    # M string escaping retains the CSV exactly, including accents, quotes and '#'.
    m = csv.replace("#", "#(#)").replace('"', '""').replace("\r", "#(cr)").replace("\n", "#(lf)")
    types = ", ".join('{"' + src + '", ' + ("type number" if dtype == "double" else "type text") + '}' for src, _, dtype in fields)
    source = ["let", f'    Source = Csv.Document(Text.ToBinary("{m}", TextEncoding.Utf8), [Delimiter=",", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
              '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
              f'    Typed = Table.TransformColumnTypes(Headers, {{{types}}}, "en-US")', "in", "    Typed"]
    columns = [{"name": dest, "dataType": dtype, "sourceColumn": src, "summarizeBy": "none"} for src, dest, dtype in fields]
    for col in columns:
        if col["dataType"] == "double":
            col["formatString"] = "0%"
    return {"name": name, "columns": columns, "partitions": [{"name": name, "mode": "import", "source": {"type": "m", "expression": source}}]}


def build():
    PBI.mkdir(exist_ok=True)
    listing_fields = [("listing_id", "Listing ID", "string"), ("market_id", "Market ID", "string"),
                      ("country", "Market", "string"), ("service_id", "Service ID", "string"),
                      ("service", "Service", "string"), ("role", "Listed role", "string"),
                      ("website", "Website", "string")]
    tables = [
        model_table("Listings", "listings.csv", listing_fields),
        model_table("Markets", "markets.csv", [("market_id", "Market ID", "string"), ("country", "Market", "string"),
                    ("iso3", "ISO3", "string"), ("primary_service", "Main service", "string"),
                    ("alternative_1", "Alternative 1", "string"), ("alternative_2", "Alternative 2", "string"),
                    ("reported_share", "Original share (unverified)", "double"), ("share_status", "Share status", "string")]),
        model_table("Services", "services.csv", [("service_id", "Service ID", "string"), ("service", "Service", "string")]),
        model_table("Review", "review.csv", [("market_id", "Market ID", "string"), ("country", "Market", "string"),
                    ("issue", "Issue", "string"), ("detail", "Detail", "string"), ("next_step", "Next step", "string")]),
        model_table("Changes", "changes.csv", [("country", "Market", "string"), ("field", "Field", "string"),
                    ("original", "Original", "string"), ("cleaned", "Cleaned", "string"), ("reason", "Reason", "string")]),
    ]
    measures = {
        "Market count": "DISTINCTCOUNT(Listings[Market ID])",
        "Service count": "DISTINCTCOUNT(Listings[Service ID])",
        "Listing count": "COUNTROWS(Listings)",
        "Primary listings": 'COALESCE(CALCULATE(COUNTROWS(Listings), KEEPFILTERS(Listings[Listed role] = "Primary")), 0)',
        "Markets listed": "DISTINCTCOUNT(Listings[Market ID])",
        "Top service coverage": "IF(RANKX(ALLSELECTED(Services), [Markets listed], , DESC, Skip) <= 12, [Markets listed])",
        "Unverified shares": 'COUNTROWS(FILTER(Markets, Markets[Share status] = "Unverified"))',
        "Name corrections": 'COUNTROWS(FILTER(Changes, Changes[Field] IN {"App Name", "Alternate1 Name", "Alternate2 Name"}))',
        "URL format changes": 'COUNTROWS(FILTER(Changes, NOT(Changes[Field] IN {"App Name", "Alternate1 Name", "Alternate2 Name"})))',
    }
    tables[0]["measures"] = [{"name": n, "expression": e, "formatString": "#,0"} for n, e in measures.items()]
    model = {"name": "Digital-Payments", "compatibilityLevel": 1604,
             "model": {"culture": "en-US", "defaultPowerBIDataSourceVersion": "powerBI_V3",
                       "tables": tables, "relationships": [
                           {"name": "Listings_Markets", "fromTable": "Listings", "fromColumn": "Market ID", "toTable": "Markets", "toColumn": "Market ID"},
                           {"name": "Listings_Services", "fromTable": "Listings", "fromColumn": "Service ID", "toTable": "Services", "toColumn": "Service ID"},
                       ], "annotations": [{"name": "DatasetMeaning", "value": "Historical research snapshot. Listing counts do not establish current availability or payment adoption."}]}}
    if (MODEL / "definition").exists():
        raise RuntimeError("This model has been converted to TMDL. Preserve the native edits and update its source partitions in Power BI.")
    save(MODEL / "model.bim", model)
    save(MODEL / "definition.pbism", {"version": "1.0", "settings": {}})
    save(PBI / "Digital-Payments-Explorer.pbip", {"version": "1.0", "artifacts": [{"report": {"path": "Digital-Payments.Report"}}],
                                               "settings": {"enableAutoRecovery": True}})
    save(REPORT / "definition.pbir", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
                                      "version": "4.0", "datasetReference": {"byPath": {"path": "../Digital-Payments.SemanticModel"}}})
    definition = REPORT / "definition"
    save(definition / "version.json", {"$schema": SCHEMA_BASE + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, overwrite=False)
    save(definition / "report.json", {"$schema": SCHEMA_BASE + "report/2.0.0/schema.json", "themeCollection": {
        "baseTheme": {"name": "CY24SU06", "reportVersionAtImport": "5.55", "type": "SharedResources"}}}, overwrite=False)
    pages = [("Overview", "Overview"), ("MarketComparison", "Market comparison"), ("DataReview", "Data review")]
    save(definition / "pages/pages.json", {"$schema": SCHEMA_BASE + "pagesMetadata/1.0.0/schema.json",
                                          "pageOrder": [p[0] for p in pages], "activePageName": "Overview"}, overwrite=False)
    for page, label in pages:
        save(definition / "pages" / page / "page.json", {"$schema": SCHEMA_BASE + "page/2.0.0/schema.json", "name": page,
             "displayName": label, "displayOption": "FitToPage", "width": 1280, "height": 720,
             "objects": {"background": [{"properties": {"color": color("#F6F7FA"), "transparency": literal(0)}}]}}, overwrite=False)
        text(page, "Heading", "Digital Payments Explorer", [32, 22, 1200, 58], 26, bold=True)
        text(page, "Context", "Original research snapshot · 100 countries and territories · Service listings and source review", [32, 82, 1200, 30], 11, "#738098")
        text(page, "Footnote", "Coverage counts dataset mentions. Current availability and market-share figures require dated primary sources.", [32, 678, 1200, 30], 10, "#738098")
    for i, (measure, title) in enumerate([("Market count", "Markets"), ("Service count", "Services listed"), ("Listing count", "Service listings"), ("Primary listings", "Primary listings")]):
        card("Overview", "Metric" + str(i + 1), measure, title, [32 + 310 * i, 132, 286, 104])
    visual("Overview", "ServiceCoverage", "clusteredBarChart", [32, 262, 740, 388],
           {"Category": [projection("Services", "Service")], "Y": [projection("Listings", "Top service coverage", True)]},
           "Most-listed services (distinct markets)",
           objects={"dataPoint": [{"properties": {"defaultColor": color("#315CDE")}}]}, sort=field("Listings", "Top service coverage", True))
    visual("Overview", "MarketFilter", "slicer", [796, 262, 420, 388],
           {"Values": [projection("Markets", "Market")]}, "Select markets")
    visual("MarketComparison", "MarketFilter", "slicer", [32, 134, 284, 508],
           {"Values": [projection("Markets", "Market")]}, "Select markets")
    visual("MarketComparison", "MarketTable", "tableEx", [344, 134, 872, 508],
           {"Values": [projection("Markets", n) for n in ["Market", "Main service", "Alternative 1", "Alternative 2"]]}, "Recorded main service and alternatives")
    for i, (measure, title) in enumerate([("Unverified shares", "Shares awaiting evidence"), ("Name corrections", "Name corrections"), ("URL format changes", "URL format changes")]):
        card("DataReview", "Metric" + str(i + 1), measure, title, [32 + 410 * i, 132, 386, 104])
    visual("DataReview", "ReviewTable", "tableEx", [32, 262, 1184, 388],
           {"Values": [projection("Review", n) for n in ["Market", "Issue", "Detail", "Next step"]]}, "Source gaps and records needing research")
    print("Built portable project:", PBI / "Digital-Payments-Explorer.pbip")


if __name__ == "__main__":
    build()

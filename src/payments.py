"""Prepare the original research table without inventing transaction data."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
import pycountry

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "payments.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
SOURCE_URL = "https://github.com/Aditya-6446/Ecommerce_Payments_Analysis/blob/main/Test.csv"
ALIASES = {
    "Goggle Pay": "Google Pay",
    "Paypal": "PayPal",
    "Line Pay": "LINE Pay",
    "Twint": "TWINT",
    "Mobile Pay": "MobilePay",
    "Google wallet": "Google Wallet",
}
COUNTRY_ALIASES = {
    "Turkey": "Türkiye",
    "Russia": "Russian Federation",
    "South Korea": "Korea, Republic of",
    "Taiwan": "Taiwan, Province of China",
    "Vietnam": "Viet Nam",
    "Czech Republic": "Czechia",
    "Ivory Coast": "Côte d'Ivoire",
    "DR Congo": "Congo, The Democratic Republic of the",
    "Macau": "Macao",
    "Bolivia": "Bolivia, Plurinational State of",
    "Venezuela": "Venezuela, Bolivarian Republic of",
    "Iran": "Iran, Islamic Republic of",
    "Tanzania": "Tanzania, United Republic of",
}
ROLE_COLUMNS = [
    ("Primary", "App Name", "App Website Link", "App Review Link", "App Screenshot Link"),
    ("Alternative 1", "Alternate1 Name", "Alternate1 Website", "Alternate1 Review", "Alternate1 Screenshot"),
    ("Alternative 2", "Alternate2 Name", "Alternate2 Website", "Alternate2 Review", "Alternate2 Screenshot"),
]
REQUIRED_COLUMNS = ["Country", "Market Share"] + [c for role in ROLE_COLUMNS for c in role[1:]]


@dataclass
class PreparedData:
    markets: pd.DataFrame
    services: pd.DataFrame
    listings: pd.DataFrame
    changes: pd.DataFrame
    review: pd.DataFrame
    summary: dict


def normalize_url(value: str) -> str:
    """Normalize syntax only; a well-formed URL is not evidence of availability."""
    value = str(value).strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, flags=re.I):
        value = "https://" + value
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"Unsupported URL: {value}")
    host = parts.netloc.lower()
    return urlunsplit((parts.scheme.lower(), host, parts.path, parts.query, parts.fragment))


def iso_code(country: str) -> str:
    return pycountry.countries.lookup(COUNTRY_ALIASES.get(country, country)).alpha_3


def prepare_data(raw_path: Path = RAW_PATH) -> PreparedData:
    raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    missing = set(REQUIRED_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if raw.empty:
        raise ValueError("The source dataset is empty.")
    countries = raw["Country"].str.strip()
    if countries.eq("").any() or countries.duplicated().any():
        raise ValueError("Country / territory names must be populated and unique.")
    market_rows, listing_rows, change_rows, review_rows = [], [], [], []
    for idx, row in raw.iterrows():
        market_id = f"M{idx + 1:03d}"
        country = row["Country"].strip()
        text_share = row["Market Share"].strip()
        if not re.fullmatch(r"\d+(?:\.\d+)?%", text_share):
            raise ValueError(f"Invalid source share for {country}: {text_share}")
        share = float(text_share[:-1]) / 100
        if not 0 <= share <= 1:
            raise ValueError(f"Source share outside 0–100%: {country}")
        record = {
            "market_id": market_id, "country": country, "iso3": iso_code(country),
            "primary_service": "", "primary_service_id": "", "reported_share": share,
            "share_status": "Unverified", "share_source_url": "", "share_period": "",
            "share_definition": "",
            "alternative_1": "", "alternative_2": "",
        }
        review_rows.append({
            "market_id": market_id, "country": country, "issue": "Market-share evidence missing",
            "detail": "Original share has no documented source, measurement period or denominator.",
            "next_step": "Find the original source and record its period and definition before comparison.",
        })
        for role_index, (role, name_col, website_col, review_col, screenshot_col) in enumerate(ROLE_COLUMNS):
            original_name = row[name_col]
            stripped = re.sub(r"\s+", " ", original_name.strip())
            name = ALIASES.get(stripped, stripped)
            if not name:
                raise ValueError(f"Missing service name: {country}, {role}")
            website = normalize_url(row[website_col])
            # Retain differently spelled EasyPay / Easypay records: their supplied domains differ.
            service_key = name if name.casefold() != "easypay" else name + " | " + urlsplit(website).hostname
            service_id = "S" + hashlib.sha256(service_key.encode("utf-8")).hexdigest()[:12]
            listing = {
                "listing_id": f"{market_id}-{role_index + 1}", "market_id": market_id,
                "country": country, "iso3": record["iso3"], "service_id": service_id,
                "service": name, "source_name": original_name, "role": role,
                "website": website, "review_url": normalize_url(row[review_col]),
                "screenshot_url": normalize_url(row[screenshot_col]),
            }
            listing_rows.append(listing)
            if role == "Primary":
                record.update(primary_service=name, primary_service_id=service_id)
            elif role == "Alternative 1":
                record["alternative_1"] = name
            else:
                record["alternative_2"] = name
            if name != original_name:
                change_rows.append({
                    "market_id": market_id, "country": country, "field": name_col,
                    "original": original_name, "cleaned": name,
                    "reason": "Trim whitespace / documented spelling or capitalization alias",
                })
            for field, cleaned in [(website_col, website), (review_col, listing["review_url"]), (screenshot_col, listing["screenshot_url"])]:
                if cleaned != row[field]:
                    change_rows.append({
                        "market_id": market_id, "country": country, "field": field,
                        "original": row[field], "cleaned": cleaned,
                        "reason": "Add missing https scheme / normalize URL syntax",
                    })
        market_rows.append(record)
    markets = pd.DataFrame(market_rows)
    listings = pd.DataFrame(listing_rows)
    services = listings[["service_id", "service"]].drop_duplicates().sort_values("service").reset_index(drop=True)
    # A country/service appearing twice is observable and must not inflate country coverage.
    duplicate_pairs = int(listings.duplicated(["market_id", "service_id"]).sum())
    for _, duplicate in listings[listings.duplicated(["market_id", "service_id"])].iterrows():
        review_rows.append({
            "market_id": duplicate["market_id"], "country": duplicate["country"],
            "issue": "Repeated service in the same market",
            "detail": f"{duplicate['service']} appears in more than one listed role. Coverage counts the market once.",
            "next_step": "Check the original research and replace the repeated alternative only with verified evidence.",
        })
    review_rows.append({
        "market_id": "", "country": "All markets", "issue": "Service and link verification pending",
        "detail": "Original rows include wallets, payment networks and payment schemes. Website, review and screenshot links are unverified.",
        "next_step": "Verify each service's identity, country availability and linked material against primary sources.",
    })
    changes = pd.DataFrame(change_rows, columns=["market_id", "country", "field", "original", "cleaned", "reason"])
    review = pd.DataFrame(review_rows)
    ranking = service_coverage(listings)
    summary = {
        "source_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "source_rows": len(raw), "source_columns": len(raw.columns),
        "markets": len(markets), "services": len(services), "listings": len(listings),
        "duplicate_market_service_listings": duplicate_pairs,
        "name_changes": int(changes["field"].isin([r[1] for r in ROLE_COLUMNS]).sum()),
        "url_changes": int((~changes["field"].isin([r[1] for r in ROLE_COLUMNS])).sum()),
        "shares_needing_evidence": int(markets["share_status"].eq("Unverified").sum()),
        "top_service": ranking.iloc[0]["service"],
        "top_service_markets": int(ranking.iloc[0]["markets_listed"]),
        "source": SOURCE_URL,
    }
    return PreparedData(markets, services, listings, changes, review, summary)


def filter_listings(listings: pd.DataFrame, countries=None, services=None, roles=None, search="") -> pd.DataFrame:
    result = listings.copy()
    for column, values in [("country", countries), ("service_id", services), ("role", roles)]:
        if values:
            result = result[result[column].isin(values)]
    if search.strip():
        needle = search.strip().casefold()
        mask = result[["country", "service"]].apply(lambda col: col.str.casefold().str.contains(needle, regex=False)).any(axis=1)
        result = result[mask]
    return result.reset_index(drop=True)


def service_coverage(listings: pd.DataFrame) -> pd.DataFrame:
    """Count dataset mentions, not payment adoption, users or transaction share."""
    if listings.empty:
        return pd.DataFrame(columns=["service_id", "service", "markets_listed", "primary", "alternative", "listings"])
    rows = []
    for (key, name), group in listings.groupby(["service_id", "service"], sort=False):
        rows.append({
            "service_id": key, "service": name, "markets_listed": group["market_id"].nunique(),
            "primary": group.loc[group["role"].eq("Primary"), "market_id"].nunique(),
            "alternative": group.loc[~group["role"].eq("Primary"), "market_id"].nunique(),
            "listings": len(group),
        })
    return pd.DataFrame(rows).sort_values(["markets_listed", "service"], ascending=[False, True]).reset_index(drop=True)


def write_outputs(data: PreparedData, directory: Path = PROCESSED_DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ["markets", "services", "listings", "changes", "review"]:
        getattr(data, name).to_csv(directory / f"{name}.csv", index=False, lineterminator="\n")
    service_coverage(data.listings).to_csv(directory / "service_coverage.csv", index=False, lineterminator="\n")
    (directory / "summary.json").write_text(json.dumps(data.summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with sqlite3.connect(directory / "payments.sqlite") as connection:
        for name in ["markets", "services", "listings", "changes", "review"]:
            getattr(data, name).to_sql(name, connection, if_exists="replace", index=False)
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS market_key ON markets(market_id)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS service_key ON services(service_id)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS listing_key ON listings(listing_id)")

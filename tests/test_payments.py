from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from src.payments import RAW_PATH, filter_listings, normalize_url, prepare_data, service_coverage, write_outputs


@pytest.fixture(scope="module")
def data():
    return prepare_data()


def test_source_rows_reconcile_and_keys_are_unique(data):
    assert len(data.markets) == 100
    assert len(data.listings) == 300
    assert data.listings.groupby("market_id").size().eq(3).all()
    assert data.markets.market_id.is_unique
    assert data.services.service_id.is_unique
    assert data.listings.listing_id.is_unique
    assert data.listings.market_id.isin(data.markets.market_id).all()
    assert data.listings.service_id.isin(data.services.service_id).all()
    assert data.markets.iso3.str.fullmatch(r"[A-Z]{3}").all()


def test_aliases_are_corrected_without_merging_distinct_services(data):
    assert "Goggle Pay" not in set(data.listings.service)
    assert data.listings[data.listings.source_name.eq("Goggle Pay")].service.eq("Google Pay").all()
    assert "Google Wallet" in set(data.listings.service)
    easy = data.listings[data.listings.service.str.casefold().eq("easypay")]
    assert easy.service_id.nunique() == 2
    assert "Banca Móvil BCP" in set(data.listings.service)


def test_market_shares_are_preserved_and_never_filled_as_verified(data):
    raw = pd.read_csv(RAW_PATH, dtype=str)
    expected = raw["Market Share"].str.rstrip("%").astype(float) / 100
    assert data.markets.reported_share.tolist() == expected.tolist()
    assert data.markets.share_status.eq("Unverified").all()
    assert data.markets.share_source_url.eq("").all()
    assert data.markets.share_period.eq("").all()


def test_country_and_literal_search_filters(data):
    india = filter_listings(data.listings, countries=["India"])
    assert len(india) == 3
    assert set(india.service) == {"PhonePe", "Google Pay", "Paytm"}
    assert filter_listings(data.listings, search="[missing]").empty
    assert filter_listings(data.listings, countries=["India"], search="PAYTM").service.tolist() == ["Paytm"]


def test_coverage_counts_distinct_markets_not_duplicate_listings(data):
    duplicated = pd.concat([data.listings, data.listings.iloc[[0]]], ignore_index=True)
    a = service_coverage(data.listings)
    b = service_coverage(duplicated)
    assert a[["service_id", "markets_listed"]].equals(b[["service_id", "markets_listed"]])
    assert service_coverage(data.listings.iloc[:0]).empty


def test_missing_or_duplicate_source_keys_fail_explicitly(tmp_path):
    raw = pd.read_csv(RAW_PATH, dtype=str)
    raw.loc[1, "Country"] = raw.loc[0, "Country"]
    target = tmp_path / "duplicate.csv"
    raw.to_csv(target, index=False)
    with pytest.raises(ValueError, match="unique"):
        prepare_data(target)
    raw.drop(columns="Market Share").to_csv(target, index=False)
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_data(target)


def test_exported_sql_results_match_analysis(data, tmp_path):
    write_outputs(data, tmp_path)
    with sqlite3.connect(tmp_path / "payments.sqlite") as db:
        assert db.execute("SELECT COUNT(*) FROM markets").fetchone()[0] == 100
        assert db.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 300
        name, count = db.execute("SELECT service, COUNT(DISTINCT market_id) AS n FROM listings GROUP BY service_id, service ORDER BY n DESC, service LIMIT 1").fetchone()
        assert name == data.summary["top_service"]
        assert count == data.summary["top_service_markets"]


def test_url_normalization_retains_meaningful_path_and_fragment():
    assert normalize_url(" apple.com/apple-pay/ ") == "https://apple.com/apple-pay/"
    assert normalize_url("https://example.com/review?q=abc#details") == "https://example.com/review?q=abc#details"

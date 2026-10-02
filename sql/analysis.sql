-- Run these queries against data/processed/payments.sqlite.
-- A listing is a dataset mention. It is not a payment or verified availability.

-- 1. Reconcile source markets and normalized listings.
SELECT (SELECT COUNT(*) FROM markets) AS markets,
       (SELECT COUNT(*) FROM services) AS services,
       COUNT(*) AS listings
FROM listings;

-- 2. Services named in the most distinct markets.
SELECT service, COUNT(DISTINCT market_id) AS markets_listed
FROM listings
GROUP BY service_id, service
ORDER BY markets_listed DESC, service
LIMIT 12;

-- 3. Listed role mix for each service; totals count listing records.
SELECT service,
       SUM(CASE WHEN role = 'Primary' THEN 1 ELSE 0 END) AS primary_listings,
       SUM(CASE WHEN role <> 'Primary' THEN 1 ELSE 0 END) AS alternative_listings
FROM listings
GROUP BY service_id, service
ORDER BY primary_listings + alternative_listings DESC, service;

-- 4. Compare the recorded services in three selected markets.
SELECT country,
       MAX(CASE WHEN role = 'Primary' THEN service END) AS primary_service,
       MAX(CASE WHEN role = 'Alternative 1' THEN service END) AS alternative_1,
       MAX(CASE WHEN role = 'Alternative 2' THEN service END) AS alternative_2
FROM listings
WHERE country IN ('India', 'United Kingdom', 'United States')
GROUP BY market_id, country
ORDER BY country;

-- 5. Record-level market-share evidence coverage.
-- Null/empty source, period and definition mean unavailable evidence.
SELECT share_status, COUNT(*) AS markets,
       SUM(CASE WHEN share_source_url IS NULL OR share_source_url = '' THEN 1 ELSE 0 END) AS missing_sources,
       SUM(CASE WHEN share_period IS NULL OR share_period = '' THEN 1 ELSE 0 END) AS missing_periods,
       SUM(CASE WHEN share_definition IS NULL OR share_definition = '' THEN 1 ELSE 0 END) AS missing_definitions
FROM markets
GROUP BY share_status;

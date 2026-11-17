-- Original schema stays intact. Snapshot scope is inclusive calendar dates.
-- Grain: one row per quote. Coverage never multiplies a premium or quote count.
CREATE VIEW analytics_quotes AS
SELECT q.*, c.name AS carrier, substr(q.created_at, 1, 10) AS created_date,
       substr(q.created_at, 1, 7) AS created_month,
       q.premium_cents / 100.0 AS annual_premium_usd,
       s.snapshot_date
FROM quotes q JOIN carriers c ON c.id = q.carrier_id
CROSS JOIN analytics_snapshot s
WHERE date(q.created_at) BETWEEN s.start_date AND s.snapshot_date;

-- Grain: one row per prospect, including those with no in-scope quote.
CREATE VIEW analytics_prospects AS
SELECT p.id AS prospect_id, COUNT(q.id) AS quote_count,
       MAX(CASE WHEN q.status = 'Accepted' THEN 1 ELSE 0 END) AS has_accepted_quote
FROM prospects p CROSS JOIN analytics_snapshot s
LEFT JOIN analytics_quotes q ON p.id = q.prospect_id
WHERE date(p.created_at) <= s.snapshot_date
GROUP BY p.id;

-- Canonical entire recorded coverage set, including notes and NULLs.
-- Hex encoding prevents delimiters in free-text notes from colliding.
-- Missing coverage is NULL, deliberately excluded from comparisons.
CREATE VIEW analytics_coverage_signatures AS
SELECT quote_id, group_concat(token, '|') AS coverage_signature
FROM (
    SELECT quote_id, printf('%d:%s:%s:%s', coverage_id,
           coalesce(CAST(limit_cents AS TEXT), 'NULL'),
           coalesce(CAST(deductible_cents AS TEXT), 'NULL'),
           CASE WHEN notes IS NULL THEN 'NULL' ELSE 'HEX' || hex(notes) END) AS token
    FROM quote_coverages ORDER BY quote_id, coverage_id
)
GROUP BY quote_id;

-- Conservative recorded-field comparability; not an underwriting equivalence claim.
CREATE VIEW analytics_comparable_quotes AS
WITH matched AS (
    SELECT q.*, s.coverage_signature,
           MIN(q.id) OVER (
             PARTITION BY prospect_id, quote_type, effective_date,
                          expiration_date, coverage_signature) AS comparison_group_id
    FROM analytics_quotes q
    JOIN analytics_coverage_signatures s ON s.quote_id = q.id
)
SELECT * FROM matched;

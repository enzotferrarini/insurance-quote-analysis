-- Grain: carrier within selected quote cohort; current status at snapshot.
-- Denominator: Presented + Accepted + Declined + Expired; Pending excluded.
-- Fixture: Alder 2/3; Birch 1/3; combined 3/6 (NOT mean of carrier shares).
-- NULL means no eligible denominator, not measured zero.
WITH filtered AS (
    SELECT * FROM analytics_quotes
    WHERE (:carrier_id IS NULL OR carrier_id = :carrier_id)
      AND (:product IS NULL OR quote_type = :product)
      AND (:month IS NULL OR created_month = :month)
)
SELECT carrier_id, carrier, COUNT(*) AS quote_count,
       SUM(status = 'Accepted') AS accepted_quotes,
       SUM(status IN ('Presented', 'Accepted', 'Declined', 'Expired')) AS non_pending_quotes,
       1.0 * SUM(status = 'Accepted') /
       NULLIF(SUM(status IN ('Presented', 'Accepted', 'Declined', 'Expired')), 0) AS accepted_quote_share
FROM filtered GROUP BY carrier_id, carrier ORDER BY carrier_id;

-- Grain: one quote in a group with >=2 distinct carriers AFTER filters.
-- Same prospect, product, effective date, expiry and entire recorded coverage set.
-- Date: in-scope created dates; all snapshot statuses included, not a live offer list.
-- Denominator: group quote count; no population savings or best-carrier inference.
-- Fixture: only quotes 1 and 2 qualify; $1,000 and $1,200; range $200.
WITH filtered AS (
    SELECT * FROM analytics_comparable_quotes
    WHERE (:carrier_id IS NULL OR carrier_id = :carrier_id)
      AND (:product IS NULL OR quote_type = :product)
      AND (:month IS NULL OR created_month = :month)
), eligible AS (
    SELECT comparison_group_id FROM filtered
    GROUP BY comparison_group_id HAVING COUNT(DISTINCT carrier_id) >= 2
)
SELECT f.*,
       DENSE_RANK() OVER (PARTITION BY f.comparison_group_id ORDER BY premium_cents) AS premium_rank,
       COUNT(*) OVER (PARTITION BY f.comparison_group_id) AS group_quote_count,
       (MAX(premium_cents) OVER (PARTITION BY f.comparison_group_id) -
        MIN(premium_cents) OVER (PARTITION BY f.comparison_group_id)) / 100.0 AS group_range_usd
FROM filtered f JOIN eligible e USING (comparison_group_id)
ORDER BY f.comparison_group_id, premium_rank, id;

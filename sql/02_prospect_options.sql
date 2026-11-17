-- Grain: one selected population. Denominator: distinct in-scope quoted prospects.
-- Date: quote creation period, inclusive snapshot; unquoted prospects excluded.
-- Fixture: 8 quotes / 4 quoted prospects = 2.0; unfiltered register has 5 prospects.
WITH filtered AS (
    SELECT * FROM analytics_quotes
    WHERE (:carrier_id IS NULL OR carrier_id = :carrier_id)
      AND (:product IS NULL OR quote_type = :product)
      AND (:month IS NULL OR created_month = :month)
)
SELECT COUNT(*) AS quote_count, COUNT(DISTINCT prospect_id) AS quoted_prospects,
       1.0 * COUNT(*) / NULLIF(COUNT(DISTINCT prospect_id), 0) AS quotes_per_quoted_prospect
FROM filtered;

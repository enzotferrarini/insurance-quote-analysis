-- Grain: one selected population of distinct prospects with in-scope quotes.
-- Numerator: distinct prospects with >=1 Accepted quote in the SAME filters.
-- Date: created cohort + snapshot status; no historical conversion or policy claim.
-- Fixture: prospects 1 and 3 / quoted prospects 1,2,3,4 = 2/4 = 0.5.
WITH filtered AS (
    SELECT * FROM analytics_quotes
    WHERE (:carrier_id IS NULL OR carrier_id = :carrier_id)
      AND (:product IS NULL OR quote_type = :product)
      AND (:month IS NULL OR created_month = :month)
)
SELECT COUNT(DISTINCT CASE WHEN status = 'Accepted' THEN prospect_id END) AS accepted_prospects,
       COUNT(DISTINCT prospect_id) AS quoted_prospects,
       1.0 * COUNT(DISTINCT CASE WHEN status = 'Accepted' THEN prospect_id END) /
       NULLIF(COUNT(DISTINCT prospect_id), 0) AS accepted_prospect_share
FROM filtered;

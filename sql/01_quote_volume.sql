-- Grain: created month / product / carrier. Count distinct quote IDs.
-- Date: in-scope creation dates, snapshot status; no acceptance-timing inference.
-- Fixture: Jan Auto Alder=3; Jan Auto Birch=2; Feb Home Alder=2; Feb Umbrella Birch=1.
WITH filtered AS (
    SELECT * FROM analytics_quotes
    WHERE (:carrier_id IS NULL OR carrier_id = :carrier_id)
      AND (:product IS NULL OR quote_type = :product)
      AND (:month IS NULL OR created_month = :month)
)
SELECT created_month, quote_type, carrier_id, carrier, COUNT(*) AS quote_count
FROM filtered GROUP BY created_month, quote_type, carrier_id, carrier
ORDER BY created_month, quote_type, carrier_id;

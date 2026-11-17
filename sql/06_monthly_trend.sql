-- Grain: one COMPLETE created month, zero-filled before LAG.
-- Date: month end <= snapshot date; no partial-month or acceptance-timing comparison.
-- Denominator: previous full calendar month's count; NULL for first/zero baseline.
-- Fixture: Jan=5, Feb=3; Feb previous=5 and change=-0.4.
WITH RECURSIVE months(month) AS (
    SELECT date(start_date, 'start of month') FROM analytics_snapshot
    UNION ALL
    SELECT date(month, '+1 month') FROM months, analytics_snapshot
    WHERE date(month, '+1 month') <= snapshot_date
), counts AS (
    SELECT substr(m.month, 1, 7) AS created_month, COUNT(q.id) AS quote_count
    FROM months m CROSS JOIN analytics_snapshot s
    LEFT JOIN analytics_quotes q ON q.created_month = substr(m.month, 1, 7)
      AND (:carrier_id IS NULL OR q.carrier_id = :carrier_id)
      AND (:product IS NULL OR q.quote_type = :product)
    WHERE date(m.month, '+1 month', '-1 day') <= s.snapshot_date
      AND m.month >= s.start_date
    GROUP BY m.month
), lagged AS (
    SELECT *, LAG(quote_count) OVER (ORDER BY created_month) AS previous_month_quotes
    FROM counts
)
SELECT *, 1.0 * (quote_count - previous_month_quotes) /
          NULLIF(previous_month_quotes, 0) AS month_over_month_change
FROM lagged
WHERE (:month IS NULL OR created_month = :month)
ORDER BY created_month;

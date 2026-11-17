-- READ ONLY: use examples/sample_data.sql in a separate empty database first.
-- Price sorting below does NOT establish equivalent coverage; use sql/05_comparable_premiums.sql for analytics.
-- Find all quotes for a prospect by email address
SELECT
    "quotes".*
FROM "quotes"
WHERE "prospect_id" = (
    SELECT "id"
    FROM "prospects"
    WHERE "email" = 'demo@example.invalid'
);

-- Display a clean quote comparison
SELECT *
FROM "quote_comparison"
WHERE "first_name" = 'Demo'
AND "last_name" = 'Prospect'
ORDER BY "annual_premium";

-- Find the least expensive auto quote
SELECT
    "carriers"."name" AS "carrier",
    ROUND(
        "quotes"."premium_cents" / 100.0,
        2
    ) AS "annual_premium"
FROM "quotes"
JOIN "carriers"
    ON "quotes"."carrier_id" = "carriers"."id"
WHERE "quotes"."prospect_id" = (
    SELECT "id"
    FROM "prospects"
    WHERE "email" = 'demo@example.invalid'
)
AND "quotes"."quote_type" = 'Auto'
ORDER BY "quotes"."premium_cents"
LIMIT 1;

-- Display all coverages included with the Fictional Alder quote
SELECT
    "coverages"."name",
    ROUND(
        "quote_coverages"."limit_cents" / 100.0,
        2
    ) AS "coverage_limit",
    ROUND(
        "quote_coverages"."deductible_cents" / 100.0,
        2
    ) AS "deductible",
    "quote_coverages"."notes"
FROM "quote_coverages"
JOIN "coverages"
    ON "quote_coverages"."coverage_id" = "coverages"."id"
JOIN "quotes"
    ON "quote_coverages"."quote_id" = "quotes"."id"
JOIN "carriers"
    ON "quotes"."carrier_id" = "carriers"."id"
JOIN "prospects"
    ON "quotes"."prospect_id" = "prospects"."id"
WHERE "carriers"."name" = 'Fictional Alder'
AND "prospects"."email" = 'demo@example.invalid'
AND "quotes"."quote_type" = 'Auto'
AND "quotes"."effective_date" = '2026-08-01'
ORDER BY "coverages"."name";

-- Count how many quotes each carrier has provided
SELECT
    "carriers"."name",
    COUNT("quotes"."id") AS "number_of_quotes"
FROM "carriers"
LEFT JOIN "quotes"
    ON "carriers"."id" = "quotes"."carrier_id"
GROUP BY "carriers"."id"
ORDER BY "number_of_quotes" DESC;

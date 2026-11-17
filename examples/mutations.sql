-- MUTATIONS: only run against a disposable example database.
PRAGMA foreign_keys = ON;
BEGIN;
-- Mark the Fictional Alder quote as presented
UPDATE "quotes"
SET "status" = 'Presented'
WHERE "id" = (
    SELECT "quotes"."id"
    FROM "quotes"
    JOIN "carriers"
        ON "quotes"."carrier_id" = "carriers"."id"
    JOIN "prospects"
        ON "quotes"."prospect_id" = "prospects"."id"
    WHERE "carriers"."name" = 'Fictional Alder'
    AND "prospects"."email" = 'demo@example.invalid'
    AND "quotes"."quote_type" = 'Auto'
    AND "quotes"."effective_date" = '2026-08-01'
);

-- Mark the prospect as quoted
UPDATE "prospects"
SET "status" = 'Quoted'
WHERE "email" = 'demo@example.invalid';

-- Remove quotes marked as expired after their expiration date
DELETE FROM "quotes"
WHERE "status" = 'Expired'
AND "expiration_date" < DATE('now');

-- Demonstration is rolled back intentionally.
ROLLBACK;

-- INSERTS ONLY: fictional examples; load into a new empty demo database.
-- Demonstrate typical database operations using fictional sample data.
-- Run this file after schema.sql on a new database.

-- Add a new prospect
INSERT INTO "prospects"
    (
        "first_name",
        "last_name",
        "email",
        "phone"
    )
VALUES
    (
        'Demo',
        'Prospect',
        'demo@example.invalid',
        '000-000-0000'
    );

-- Add insurance carriers
INSERT INTO "carriers" ("name")
VALUES
    ('Fictional Alder'),
    ('Fictional Birch');

-- Add two auto quotes for the prospect
INSERT INTO "quotes"
    (
        "prospect_id",
        "carrier_id",
        "quote_type",
        "premium_cents",
        "effective_date",
        "expiration_date"
    )
VALUES
    (
        (
            SELECT "id"
            FROM "prospects"
            WHERE "email" = 'demo@example.invalid'
        ),
        (
            SELECT "id"
            FROM "carriers"
            WHERE "name" = 'Fictional Alder'
        ),
        'Auto',
        149700,
        '2026-08-01',
        '2027-02-01'
    ),
    (
        (
            SELECT "id"
            FROM "prospects"
            WHERE "email" = 'demo@example.invalid'
        ),
        (
            SELECT "id"
            FROM "carriers"
            WHERE "name" = 'Fictional Birch'
        ),
        'Auto',
        135900,
        '2026-08-01',
        '2027-02-01'
    );

-- Add auto coverage types
INSERT INTO "coverages"
    (
        "name",
        "description"
    )
VALUES
    (
        'Bodily Injury Liability',
        'Pays for injuries caused to other people in an accident.'
    ),
    (
        'Property Damage Liability',
        'Pays for damage caused to another person''s property.'
    ),
    (
        'Comprehensive',
        'Pays for covered vehicle damage not caused by a collision.'
    ),
    (
        'Collision',
        'Pays for covered collision damage to the insured vehicle.'
    ),
    (
        'Uninsured Motorist Bodily Injury',
        'Pays for injuries caused by an uninsured or underinsured driver.'
    ),
    (
        'Medical Payments',
        'Pays eligible medical expenses after an auto accident.'
    ),
    (
        'Rental Reimbursement',
        'Helps pay for a rental vehicle after a covered loss.'
    ),
    (
        'Roadside Assistance',
        'Provides services such as towing and battery assistance.'
    );

-- Add coverages to the Fictional Alder quote
INSERT INTO "quote_coverages"
    (
        "quote_id",
        "coverage_id",
        "limit_cents",
        "deductible_cents",
        "notes"
    )
VALUES
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Bodily Injury Liability'
        ),
        25000000,
        NULL,
        '$250,000 per person and $500,000 per accident'
    ),
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Property Damage Liability'
        ),
        10000000,
        NULL,
        '$100,000 per accident'
    ),
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Comprehensive'
        ),
        NULL,
        50000,
        '$500 deductible'
    ),
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Collision'
        ),
        NULL,
        100000,
        '$1,000 deductible'
    ),
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Uninsured Motorist Bodily Injury'
        ),
        25000000,
        NULL,
        '$250,000 per person and $500,000 per accident'
    ),
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Medical Payments'
        ),
        500000,
        NULL,
        '$5,000 per person'
    ),
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Rental Reimbursement'
        ),
        NULL,
        NULL,
        '$50 per day, maximum of $1,500'
    ),
    (
        (
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
        ),
        (
            SELECT "id"
            FROM "coverages"
            WHERE "name" = 'Roadside Assistance'
        ),
        NULL,
        NULL,
        'Included'
    );


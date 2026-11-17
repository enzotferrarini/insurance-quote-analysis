# Data dictionary

The five original tables and `schema.sql` are preserved. Monetary values are annualized USD cents unless stated otherwise. IDs are invented integers. `NULL` means unknown/not applicable, never numeric zero. Primary keys are unique and non-null. Text dates must parse as ISO dates/timestamps; Python QA complements SQLite constraints.

| Table / row meaning | Column | SQLite type | Meaning / allowed values |
|---|---|---|---|
| prospects: one registered prospect | id | INTEGER PK | Synthetic prospect identifier |
| prospects | first_name, last_name | TEXT NOT NULL | Invented name labels |
| prospects | email | TEXT UNIQUE, nullable | Invented `example.invalid` address |
| prospects | phone | TEXT, nullable | Unused in analytics demo |
| prospects | status | TEXT NOT NULL | New, Quoting, Quoted, Accepted, Declined; default New |
| prospects | created_at | TEXT NOT NULL | Creation timestamp; default CURRENT_TIMESTAMP, explicitly populated by generator |
| carriers: one carrier | id | INTEGER PK | Carrier identifier |
| carriers | name | TEXT NOT NULL UNIQUE | Six names explicitly prefixed Fictional |
| quotes: one carrier quote for one prospect | id | INTEGER PK | Quote identifier; not a policy ID |
| quotes | prospect_id, carrier_id | INTEGER NOT NULL FK | References prospects.id and carriers.id |
| quotes | quote_type | TEXT NOT NULL | Auto, Home, Umbrella |
| quotes | premium_cents | INTEGER NOT NULL | Nonnegative annualized premium cents; divide by 100 to display USD |
| quotes | effective_date | TEXT NOT NULL | Proposed effective date, YYYY-MM-DD |
| quotes | expiration_date | TEXT, nullable | Quote expiration/validity date, not policy term; >= effective_date |
| quotes | status | TEXT NOT NULL | Pending, Presented, Accepted, Declined, Expired; default Pending |
| quotes | created_at | TEXT NOT NULL | Quote creation timestamp; default CURRENT_TIMESTAMP, explicitly populated |
| coverages: one reusable coverage definition | id | INTEGER PK | Coverage identifier |
| coverages | name | TEXT NOT NULL UNIQUE | Coverage label |
| coverages | description | TEXT, nullable | Definition; synthetic in demo |
| quote_coverages: one coverage on one quote | quote_id, coverage_id | INTEGER NOT NULL, composite PK/FK | References quotes.id / coverages.id; quote delete cascades |
| quote_coverages | limit_cents | INTEGER, nullable | Nonnegative coverage limit in cents |
| quote_coverages | deductible_cents | INTEGER, nullable | Nonnegative deductible in cents |
| quote_coverages | notes | TEXT, nullable | Additional terms; part of exact comparison signature |

## Analytics-only objects

`analytics_snapshot` is one row with `start_date` and `snapshot_date` as ISO date TEXT. The inclusive window controls the views. It is created only in new demo files; it does not modify the original database.

| View | Grain / fields |
|---|---|
| analytics_quotes | One quote in creation-date scope; original fields plus carrier, created_date, created_month, annual_premium_usd and snapshot_date |
| analytics_prospects | One prospect registered by snapshot, including zero quotes; prospect_id, quote_count and integer has_accepted_quote |
| analytics_coverage_signatures | One quote with at least one coverage; stable sorted signature of the entire coverage set, distinguishing NULL, zero and empty notes |
| analytics_comparable_quotes | One scoped quote with coverage; original fact fields, coverage_signature and comparison_group_id (minimum quote ID in its full group) |
| quote_comparison | Original convenience view; sorting its premium field does NOT guarantee equal coverage |

`05_comparable_premiums.sql` returns only groups with at least two visible carriers and adds `premium_rank` (dense rank, ties equal), `group_quote_count` and `group_range_usd`. Ranking is descriptive, not a recommendation. The one-row-per-prospect view is for whole-snapshot checks; filtered measures count distinct prospects from the filtered quote fact instead of summing this view.

## Export contract

All CSVs are UTF-8 with a header, one row per stated grain, empty fields for NULL, and decimal points for USD/rates. Integer IDs and cents must remain whole numbers when imported into other tools. `Quotes.csv`, `Prospects.csv`, `Carriers.csv`, `QuoteCoverages.csv`, `Coverages.csv`, `Snapshot.csv` and `ComparableQuotes.csv` retain the fields described above. `Date.csv` contains daily `date`, `year`, `month_number`, `year_month`, and integer `is_complete_month` (0/1). Analytical query CSVs preserve SQL column names. Rates are 0–1 fractions, formatted as percentages only for display.

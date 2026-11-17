# Metric definitions

The report covers quotes created from September 1, 2025 through August 31, 2026. Both dates are included. Statuses are recorded at the end of August 31; the database does not store a history of status changes.

| Question | Calculation | Row level |
|---|---|---|
| How much quoting occurs? | Count of quote IDs by creation month, product and carrier | Quote |
| How many prospects receive options? | Distinct quoted prospects; quote count divided by that count | Quoted prospect |
| What share of non-pending quotes is accepted? | Accepted / (Presented + Accepted + Declined + Expired) | Quote |
| What share of quoted prospects has an accepted quote? | Distinct prospects with at least one accepted quote / distinct quoted prospects | Quoted prospect |
| Where do comparable premiums differ? | Premium rank and range within each matching group | Quote within a comparison group |

## Filters and denominators

Carrier, product and month filters apply before counting quotes or distinct prospects. An accepted prospect must have an accepted quote inside the same selection. Unquoted prospects are excluded from the quote-based rates.

A missing denominator returns NULL. Zero accepted quotes with an eligible denominator returns zero. Subgroup prospect counts cannot be added together because the same person may appear in more than one group. Rates are recalculated from counts rather than averaged.

Pending quotes are excluded from accepted quote share as a reporting convention. Accepted quotes are not issued policies. Rates for newer cohorts also need care because those quotes have had less time to receive a decision.

## Premium comparisons

A group must have the same prospect, product, effective date, expiration date and complete set of coverage IDs, limits, deductibles and notes. At least two different carriers must remain after filtering. Quotes without coverage records are excluded. NULL, zero and empty notes are treated separately.

The query includes all quote statuses, so it describes recorded comparisons rather than currently available offers. Matching these fields does not establish that actual contracts have identical exclusions, endorsements or payment terms. The least expensive quote is not necessarily the best option.

## Monthly changes

Monthly LAG uses complete calendar months. Empty months are filled with zero before the calculation. Selecting one month preserves its actual preceding-month baseline. A first month or a zero baseline returns NULL for percentage change.

The [test fixture](fixture_expectations.md) contains the expected calculations for all five questions.

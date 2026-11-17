# Data quality

Synthetic data · snapshot 2026-08-31 · seed 42.

| Check | Expected | Actual | Result |
|---|---|---|---|
| Foreign keys enabled on loader connection | 1 | 1 | PASS |
| Unmatched foreign keys | 0 | 0 | PASS |
| SQLite integrity | ok | ok | PASS |
| prospects: loaded vs raw count | 100 | 100 | PASS |
| prospects: duplicate keys | 0 | 0 | PASS |
| prospects: missing required fields | 0 | 0 | PASS |
| carriers: loaded vs raw count | 6 | 6 | PASS |
| carriers: duplicate keys | 0 | 0 | PASS |
| carriers: missing required fields | 0 | 0 | PASS |
| coverages: loaded vs raw count | 5 | 5 | PASS |
| coverages: duplicate keys | 0 | 0 | PASS |
| coverages: missing required fields | 0 | 0 | PASS |
| quotes: loaded vs raw count | 329 | 329 | PASS |
| quotes: duplicate keys | 0 | 0 | PASS |
| quotes: missing required fields | 0 | 0 | PASS |
| quote_coverages: loaded vs raw count | 610 | 610 | PASS |
| quote_coverages: duplicate keys | 0 | 0 | PASS |
| quote_coverages: missing required fields | 0 | 0 | PASS |
| Invalid quote status | 0 | 0 | PASS |
| Invalid prospect status | 0 | 0 | PASS |
| Invalid product | 0 | 0 | PASS |
| Invalid premium cents | 0 | 0 | PASS |
| Invalid coverage cents | 0 | 0 | PASS |
| Invalid quote dates / ordering / expired status | 0 | 0 | PASS |
| Invalid prospect dates | 0 | 0 | PASS |
| One row per quote in analytical view | 329 | 329 | PASS |
| Quote 1: cents to USD | 1264.18 | 1264.18 | PASS |
| Quote 2: cents to USD | 1560.36 | 1560.36 | PASS |
| Quote 3: cents to USD | 1369.46 | 1369.46 | PASS |
| Quote 4: cents to USD | 1585.02 | 1585.02 | PASS |
| Quote 5: cents to USD | 1840.07 | 1840.07 | PASS |

## Reconciliation

SQL and pandas give the same quote counts for all 12 complete months and the same results for five filter selections. See [filter_reconciliation.csv](filter_reconciliation.csv).

## Premium extremes

- Auto: n=192, $1,085.95–$2,765.42.
- Home: n=89, $1,894.84–$3,817.73.
- Umbrella: n=48, $308.14–$768.77.

The generator bounds each base premium at 70–130% of its product baseline, then applies 80–120% variation. The lowest and highest premiums fall within those generated ranges. They have not been checked against actual insurance prices.

## Limits

The original SQLite schema is preserved. SQLite affinity does not enforce integer storage or calendar-date validity by itself; Python QA enforces these assumptions and invalid fixtures test detection. Every new SQLite connection must enable foreign keys. Current status has no event history. Exact recorded coverage equality does not establish contractual equivalence. Unquoted prospects are outside quote-based denominators.

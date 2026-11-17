# Eight-quote fixture, calculated independently

Snapshot February 28, 2026; creation window January–February 2026. Load `schema.sql` followed by `tests/fixtures/hand_calculated.sql` in a new in-memory test database. The test helper adds the snapshot and analytical views.

| Quote | Prospect | Carrier | Product | Month | Status | Annual USD |
|---|---|---|---|---|---|---|
| 1 | 1 | Alder | Auto | Jan | Accepted | 1,000 |
| 2 | 1 | Birch | Auto | Jan | Accepted | 1,200 |
| 3 | 1 | Alder | Auto | Jan | Pending | 900 |
| 4 | 2 | Alder | Auto | Jan | Presented | 1,500 |
| 5 | 2 | Birch | Auto | Jan | Expired | 1,400 |
| 6 | 3 | Alder | Home | Feb | Accepted | 2,000 |
| 7 | 3 | Alder | Home | Feb | Pending | 2,100 |
| 8 | 4 | Birch | Umbrella | Feb | Declined | 500 |

Prospect 5 has no quote. Prospect 2 and prospect 4 have no accepted quote. Quotes 1 and 2 share the entire coverage set, effective date and expiration. Quote 3 has a different deductible. Quotes 6 and 7 have only one distinct carrier and cannot form a cross-carrier comparison.

- 8 quotes, 4 quoted prospects, 5 registered prospects; 8 / 4 = **2 quotes per quoted prospect**.
- 3 accepted quotes; 8 − 2 pending = 6 eligible; **3 / 6 = 50% accepted quote share**.
- Only prospects 1 and 3 have accepted quotes; **2 / 4 = 50% accepted prospect share**. Counting accepted quotes as accepted prospects would incorrectly yield 75%.
- Alder: 5 quotes, 2 accepted / 3 eligible = **66.67%**. Birch: 3 quotes, 1 accepted / 3 eligible = **33.33%**.
- January: 5 quotes; February: 3. LAG = 5; change = (3 − 5) / 5 = **−40%**.
- One comparable group: quotes 1 and 2; **$200 range**, ranks 1 and 2. Quote 3's $900 is ineligible despite being cheaper.
- Premium sum at quote grain: **$10,600**; joining all coverage rows before summing would overstate it.
- Auto filter: 5 quotes, 2 quoted prospects, 1 accepted prospect; February: 3 quotes, 2 quoted prospects, 1 accepted prospect. No-match filter: 0 counts and NULL ratios.

Tests also cover all-pending data, equal-premium ties, complete-month zero filling, snapshot boundaries, coverage-note changes, NULL vs zero/empty notes, missing coverage, schema rejection and QA-only rejection of separate invalid examples.

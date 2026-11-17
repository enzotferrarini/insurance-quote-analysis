# Decision memo: what to check next

For an independent agency manager reviewing quotes created from 2025-09-01 through 2026-08-31. Statuses are recorded as of 2026-08-31. All records are fictional.

Before changing the quoting process, the first step would be to trace a small sample of prospects from their initial request to a final decision. This report can help frame that review, but the data was generated for the project. It cannot tell an agency which carrier to favor or whether its staff are following up effectively.

The sample contains 100 prospects, six fictional carriers and 329 quotes. It uses a fixed random seed (42), so the same inputs reproduce the same records. The analysis checks dates, required fields, relationships and currency units. SQL results were compared with hand-calculated examples and an independent pandas calculation.

## Quote volume does not tell the whole story

The 329 quotes belong to 90 prospects, giving 3.66 quotes per quoted prospect. Another 10 registered prospects have no quotes. That last group was put into the generator on purpose: every tenth prospect is left unquoted. It should not be read as evidence of a service problem.

With actual agency records, this would be a useful group to review. Some people might be waiting for a quote; others might have incomplete information, be ineligible, or have duplicate records. Request and follow-up dates would help separate those explanations before setting a target.

## Acceptance depends on what is being counted

There are 42 accepted quotes out of 286 non-pending quotes, an accepted quote share of 14.7%. At the prospect level, 42 of 90 people with quotes have at least one accepted option: 46.7%. Both calculations are useful, but they answer different questions. An accepted quote also does not confirm that a policy was issued.

Pending quotes are excluded from the quote-level rate by definition. The report has only current statuses, so it cannot show how long a decision took. More recent quotes have had less time to reach a decision. Differences between the fictional carriers come from the generated sample; carrier performance was not modeled.

## Compare the coverage before the price

There are 20 matching groups containing 60 quotes. The median difference between the lowest and highest annual premium in a group is $409.92, with group ranges from $144.29 to $874.94. Each group shares a prospect, product, dates and all recorded coverage details. Quotes with missing coverage are excluded.

These groups were deliberately constructed to test the comparison. The ranges are not estimates of customer savings. A real comparison would still need to account for exclusions, endorsements, eligibility and payment terms that this database does not capture.

## Next step

For a real process review, collect quote and response timestamps, status changes, complete coverage terms and linked issued-policy outcomes. Use a consistent follow-up window so newer prospects are not judged against older ones. Questions about revenue would also need issued premiums, commissions and acquisition costs. Once those records are available, the same queries could help identify cases worth reviewing and support a better-informed decision about what to change.

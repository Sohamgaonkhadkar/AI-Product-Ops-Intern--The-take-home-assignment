# Verification methodology

## Purpose and audit boundary

Verification is a separate evidence-gathering pass. It preserves every first-pass value, records a source-backed observation and any correction in a distinct ledger, and applies approved corrections only to a copied dataset. Automated/source-assisted checks, held-out ground truth, and human account/tenant QA are separate concepts. The final HTML is generated from the analysis artifact and corrected data; it is not the source of truth.

## Sample design and population gate

The full-population first-pass dataset is reconciled to all 100 manifest IDs before selecting a sample: 76 native `LIVE_AGENT` captures (Arena.ai web search/page inspection) plus 24 historical `PRIOR_CAPTURE` records; 97 research records are `COMPLETE` and 3 `PARTIAL`. No app is `NOT_RUN`. Historical records retain their label. This describes the available research workflow and does not claim a Tavily/OpenAI provider-backed run.

The final audit uses a greedy weighted max-coverage sample over all 100 `COMPLETE`/`PARTIAL` records, without replacement. Fixed seed: `20260924`; selected IDs in selection order:

`22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9`

It contains 14 `LIVE_AGENT` and 6 `PRIOR_CAPTURE` records, covers 10/10 manifest categories and 54/54 observed strata. This is a reproducible **coverage-oriented audit sample, not a probability sample**. Its rates must not be generalized to the 100-app population.

## First-pass verification results

Six critical groups were evaluated for each of the 20 selected apps (120 rows):

| Critical field | Correct | Checked / adjudicable | Accuracy | Unresolved / non-adjudicable |
|---|---:|---:|---:|---:|
| Authentication methods | 16 | 17 | 94.1% | 3 |
| Self-serve path | 17 | 18 | 94.4% | 2 |
| Credential access | 18 | 18 | 100.0% | 2 |
| API availability | 19 | 19 | 100.0% | 1 |
| MCP status | 15 | 16 | 93.8% | 4 |
| Buildability | 18 | 18 | 100.0% | 2 |

Some unresolved values overlap across fields; there are 106 adjudicable critical rows in total. Record accuracy is 13/15 fully adjudicable records (86.7%); 5 selected records are partial/unadjudicable. First-pass comparison found 3 critical-label mismatches and 9 supplemental value/scope changes. Field denominators exclude unresolved values and are reported separately; these figures do not estimate population accuracy.

ID84, Paygent Connect, remains a product-identity unresolved case by explicit instruction. Public search surfaced unrelated Paygent products, and no first-party source identifies the product intended by the manifest. Product-specific API/auth/MCP facts remain `UNKNOWN`; candidate Paygent/NMI evidence is not attributed to ID84.

## Independent source checks and provenance

For each selected app and each critical field (`auth_methods`, `self_serve_status`, `credential_access.status`, `api.available`, `mcp.status`, `buildability.verdict`):

1. Start a targeted lookup for the field. Search-result snippets identify possible sources only; open and inspect pages before using them as claim evidence.
2. Prefer first-party developer/API/auth/support/pricing/GitHub sources. Record URL, title, source type, observation, retrieval date/precision, verifier type, and evidence-capture status.
3. Compare the source observation with the unchanged raw first-pass value. Preserve both, the adjudicated value, correctness, reason, and any correction in the ledger.
4. When the same canonical page is reopened, call it `FRESH_REINSPECTION`, not alternate-source validation. A distinct relevant source is `ALTERNATIVE_SOURCE`; multiple sources supporting a finding are `MULTI_SOURCE`.
5. Preserve conflicts, access failures, truncation, and partial extraction. A bounded or inaccessible search does not establish `NO`; use `UNKNOWN`/`UNRESOLVED` where evidence is insufficient.
6. Apply only explicit evidence-backed changes to the corrected copy. Never overwrite `data/raw/final_full_research.json` or infer values for the post-correction file from the corrected dataset.

`data/evidence/final_sample_source_captures.json` retains first-pass, primary-verification, and post-recheck packet roles and `extraction_attempts`. Some captures are partial/chunk-limited; notably Freshdesk, Google NotebookLM Enterprise, and the Amazon repository page have uninspected later chunks. The tools exposed date-only retrieval precision; exact per-request timestamps were not available. The original 24 `PRIOR_CAPTURE` records have incomplete historical per-call retry detail, so retry totals for those records are not measurable. Reopening a source for verification/recheck is not a provider retry.

## Separate post-correction recheck

After the corrected dataset was written, 12 explicit observations were recorded and independently re-opened from the named public source pages: all 3 critical corrected rows and all 9 changed supplemental rows. All 12 are classified `FRESH_REINSPECTION`, with verifier type `automated_independent`; source observations are recorded in `data/evidence/final_post_recheck_input.json` and `data/evidence/final_post_recheck.json`, then joined by `scripts/run_verification.py`.

- Critical changed fields: 3/3 concordant; 0 conflicts, 0 unresolved.
- All changed rows: 12/12 concordant (3 critical + 9 supplemental); 0 conflicts, 0 unresolved.
- 103 other adjudicable critical rows were not rechecked. Fourteen critical sample rows were unresolved in the first pass; they are not treated as verified by this recheck.

This is source-page concordance with the explicitly reopened pages, not held-out truth, an independent human review, or a population accuracy estimate. Page extraction may be partial, and the date precision remains limited as stated above.

## Human verification status

**HUMAN VERIFICATION NOT POSSIBLE.** No authorized vendor tenant, account credentials, or human reviewer with account access was provided. No human page review, signup, credential creation, authenticated API operation, or MCP session is claimed. Public source checks do not prove that a specific tenant has a feature enabled or that a given role can create credentials.

`reports/human_qa.md` records the blocker and reasons. `data/evidence/human_qa_template.csv` has 120 rows (six critical fields × 20 selected apps), each marked `HUMAN VERIFICATION NOT POSSIBLE` with a reason and field-specific checklist. Reviewer/date/result/correction/notes are blank. ID84's identity-resolution warning is explicit. These are prepared checklists—not completed QA results. Update a row only after an authorized human actually performs that check; never place secrets or customer data in the template.

The earlier five-app engineering pilot remains separately documented; its metrics and account-review checklists are not pooled into the final sample.

## Accuracy definitions and guardrails

- **First-pass field accuracy:** adjudicable fields labeled `CORRECT` divided by adjudicable checked fields. Show unresolved values separately; never quietly remove an app from the manifest denominator.
- **First-pass record accuracy:** records matching across all adjudicable critical groups divided by fully adjudicable selected records; show partial/unadjudicable records separately.
- **Post-correction concordance:** corrected values agreeing with an explicit distinct second-pass observation divided by changed values actually rechecked. It is not automatically perfect and is not held-out ground truth.
- Keep critical-field metrics separate from record accuracy and supplemental changes.
- `UNKNOWN` means evidence does not establish a value. It is distinct from `NO`; API existence does not prove self-serve credentials, account access, or MCP availability.
- Freshdesk and Gorgias outbound webhook/HTTP automation remains distinct from a dedicated Webhooks API. An API reference does not prove credentials are self-serve; UNKNOWN is not a substitute for research.

## Observed error analysis

Only actual changed ledger rows are counted. The final audit records 3 critical mismatches and 9 supplemental changes. Causes, exact first-pass/corrected values, evidence URLs, post-recheck outcomes, and prevention steps are generated in `reports/final_error_analysis.md` and retained in `data/analysis/final_analysis.json`; no hypothetical error categories are counted as observed misses.

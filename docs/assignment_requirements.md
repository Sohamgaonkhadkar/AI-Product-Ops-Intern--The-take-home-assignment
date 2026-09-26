# Assignment requirements → implementation checklist

**Scope source:** `docs/assignment_source.md` and the canonical 100-app manifest `apps/apps.json`. This checklist reports the state of the final local artifacts. It does not infer human review, authenticated access, public publication, or deployment from generated files.

## Requirements and current state

| Assignment requirement | Implementation | Evidence / acceptance check | Status |
|---|---|---|---|
| Research the exact 100 apps across 10 categories | `apps/apps.json`; first-pass dataset and attempt traces under `data/raw/` | 100 unique manifest IDs, 100 records, 100 traces; 76 native `LIVE_AGENT` and 24 historical `PRIOR_CAPTURE`; 97 `COMPLETE`, 3 `PARTIAL`. | **First-pass reconciled; provenance mixed** |
| Preserve categories, descriptions, and claim-linked evidence | Normalized 100-row dataset; schema and quality checks | Raw first pass remains separate from the corrected copy; first-party source limitations and unknowns retained. | **Complete for available evidence; three partial records** |
| Capture authentication methods and credential path separately from API existence | `auth_methods`, `self_serve_status`, `credential_access` | API existence does not prove an obtainable credential or tenant entitlement. | **Researched; 20-app audit metrics reported with unresolved values** |
| Describe API interfaces/breadth without inventing counts | `api.available`, `api.types`, `api.breadth`, `api.details` | SOAP, REST, GraphQL, webhooks, SDKs, and other interfaces are distinguished where evidence supports it; no endpoint counts invented. Freshdesk/Gorgias outbound HTTP/webhook automation is not mislabeled as a dedicated Webhooks API. | **Complete for available evidence; limitations retained** |
| Record MCP only with first-party evidence and bounded negatives | `mcp.status`, `details`, `search_scope` | Unknown remains separate from `NO`; Amazon local educational sample is distinct from hosted product; ID84 unresolved. | **Complete for reviewed sources; product-specific unknowns remain** |
| Give buildability verdict and main blocker | `buildability.verdict`, `blocker`, `rationale`; deterministic rules | Derived analysis counts all 100 rows; only fully adjudicated sample rows receive positive triage. | **Complete for researched data; account-specific access untested** |
| Build pipeline with explicit provenance, errors, and retries | Research capture bundles, `final_full_attempts.json`, verification source packets | 7 native capture batches; 641 logged LIVE_AGENT attempts; 24 historical traces lack original per-call attempt counts. Date-only fetch precision and chunk/partial limits are explicit. | **Complete for preserved activity; historical retries unmeasurable** |
| Preserve raw-first-pass → verification → corrected dataset | `data/raw/final_full_research.json`, ledger input, `data/verified/final_dataset.json` | 100 raw records preserved; 129 verification ledger rows (120 critical, 9 supplemental); 3 critical mismatches and 9 supplemental changes. | **Complete** |
| Select and independently verify a 15–20-app sample after full research | `verification_sample_selection.json`, source capture, ledger, reports | 20 selected after population research; 14 LIVE_AGENT/6 PRIOR_CAPTURE; 10/10 categories; 54/54 strata; coverage—not probability—sample. First-pass field/record denominators and unresolved values are reported. | **Complete with scope limitation** |
| Record a separate post-correction recheck | `final_post_recheck_input.json`, `final_post_recheck.json`, verification runner | 12 explicit `FRESH_REINSPECTION` observations; 3/3 critical and 12/12 changed rows concordant; 103 other adjudicable critical rows not rechecked. | **Complete for changed rows; not held-out truth** |
| Perform or honestly block human QA | `reports/human_qa.md`, 120-row `human_qa_template.csv` | Every sampled critical-field row records `HUMAN VERIFICATION NOT POSSIBLE`, reason, and checklist; reviewer/result fields blank. | **Human QA not possible; blocker recorded, no pass claimed** |
| Analyze first-pass data, error patterns, categories, easy wins/outreach | `final_analysis.json`, analysis/error reports and CSVs | Metrics derive from corrected data; pilot metrics separate; UNKNOWN and unresolved states visible. | **Complete** |
| Generate an explanatory offline HTML case study | `case-study/index.html` | Includes 100-row matrix, source modes, patterns, verified/error examples, limitations, recheck metrics, and human-QA status; no remote assets. | **Complete locally; final regeneration/test status in final audit** |
| Run tests | `tests/`; standard-library `unittest` | `python -m unittest discover -s tests -v` | **Run result recorded in final audit only after execution** |
| Provide README and `.env.example` without secrets | `README.md`, `.env.example`, `.gitignore` | Optional configuration names only; no real key belongs in source control. | **Prepared locally** |
| Publish public source repository | Public-host remote and authorized account required | No local Git repository/remote, `gh` CLI, or repository credential is available. | **External access blocker; not published; no URL claimed** |
| Deploy case study and test public URL | Static HTML, `netlify.toml` and `vercel.json` prepared; Vercel selected by owner | Vercel CLI/account authorization is unavailable; no URL exists to test. | **External access blocker; not deployed; no URL claimed** |
| Create final audit | `reports/final_audit.md` | Records stage outcomes, 29 passing tests, HUMAN VERIFICATION NOT POSSIBLE, missing repository/deployment authorization, and no invented URLs. | **Complete; external release blockers documented** |

## Retained sample and facts

Sample selection order: **22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9** (seed `20260924`). It is a deterministic weighted coverage sample, not a probability sample.

ID84 (`Paygent Connect`) remains unresolved: unrelated candidate Paygent/NMI pages are not evidence for the product named by the manifest. Freshdesk and Gorgias outbound webhook/HTTP automation is not called a dedicated Webhooks API. The raw initial baseline is retained in `data/archive/pre_native_capture_reconciliation_2026-09-25/`.

## Ordered acceptance stages

1. **Research:** full 100-app first-pass reconciliation is complete; 76 records use native live-agent web captures and 24 are prior captures.
2. **Verification:** sample was selected after research; primary pass and 12-row post-correction recheck are complete, with stated limitations.
3. **Human QA:** account-dependent checks are explicitly recorded as not possible; no human pass is claimed.
4. **Analysis and error review:** generated from the corrected dataset and audit artifacts.
5. **Case study:** generated locally from final analysis and corrected data.
6. **Tests:** **Complete** — 29 tests passed.
7. **Source publication:** **Blocked** — no Git remote, `gh` CLI, or repository authorization is available.
8. **Deployment and public-URL checks:** **Blocked** — no hosting CLI/authorization; no public URL exists to test.
9. **Final audit:** **Complete** — `reports/final_audit.md` records the real publication/deployment blockers and does not invent URLs.

The overall project remains **INCOMPLETE** until public repository publication, deployment, and actual URL tests are completed; `reports/final_audit.md` is already recorded with the blockers. If authorized human tenant access remains unavailable, the recorded `HUMAN VERIFICATION NOT POSSIBLE` outcome is the honest result—not a completed QA claim.

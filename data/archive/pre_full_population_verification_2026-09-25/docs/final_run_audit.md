# Final run audit — 2026-09-24

## Outcome

**Overall project status: INCOMPLETE.** The required pipeline stages that can be executed from the available workspace have been run and checked. A provider-backed full 100-app research pass and human/account-dependent checks were not possible and are not represented as completed.

## Acceptance audit

| Requirement | Outcome | Audit evidence |
|---|---|---|
| Preserve the existing pilot, CRM IDs 2–10, Support IDs 11–20, raw captures, evidence and tests | PASS | Original files remain under `data/raw/`, `data/evidence/`, and pilot/CRM/Support reports. The final run assembles, rather than overwrites, those historical records. |
| Exact 100-app manifest and attempt reconciliation | PASS | `apps/apps.json`, `data/raw/final_full_research.json`, and `data/raw/final_full_attempts.json`: 100 unique manifest IDs, 100 records, 100 traces, zero blocking reconciliation/structure errors. |
| Honest full-research provenance | INCOMPLETE | Run mode `PRIOR_CAPTURE_ASSEMBLY_NO_PROVIDER_CREDENTIALS`; 24 `PRIOR_CAPTURE`, 0 `LIVE_AGENT`, 76 `NOT_RUN`. `TAVILY_API_KEY` and `OPENAI_API_KEY` are recorded `MISSING`. The run report records 463 unknown critical-field slots, 176 first-pass claim-linked evidence items, 107 trace source entries/unique URLs, 75 queries, 76 missing-credential trace events and 7 historical source failures/limits. Per-call historical retry counts are not measurable. |
| Preserve `RAW FIRST PASS → VERIFICATION → CORRECTED VERIFIED DATASET` | PASS | Raw: `data/raw/final_full_research.json/.csv`; distinct verification inputs/source capture; corrected output: `data/verified/final_dataset.json/.csv`; joined ledger preserves first-pass value, checked value, reason, correction, evidence and recheck. |
| Dataset-wide quality gates | PASS WITH WARNINGS | Every raw and corrected record validates; no blocking logical/structural errors. Raw quality: 89 `PASS`, 11 `WARN`, 0 `FAIL`. Corrected quality: 92 `PASS`, 8 `WARN`, 0 `FAIL`. The corrected warnings are repeated-evidence-URL warnings for IDs 3, 4, 5, 6, 9, 16, 20 and 92. They are retained, not silently fixed. |
| Deterministic 15–20-app sample | PASS WITH SCOPE LIMIT | 20 of 24 eligible prior captures; greedy weighted max-coverage, seed `20260924`; selected IDs: `22, 49, 92, 4, 13, 61, 15, 14, 1, 9, 3, 5, 16, 6, 12, 8, 11, 2, 10, 19`. Coverage: 6/10 manifest categories. Four categories have no eligible source capture, so the sample is not representative of all 100 apps. |
| Six critical groups independently checked for every sample app | PASS WITH UNRESOLVED SLOTS | 120 ledger rows (six per app), 116 adjudicable and 4 unresolved. Accuracy: auth 19/20; self-serve 18/19 with one unresolved; credential access 20/20; API availability 20/20; MCP 15/17 with three unresolved; buildability 20/20. Record accuracy: 13/16 fully adjudicable records; four partial/unadjudicable. Same-URL second looks are labeled fresh reinspection. |
| Distinct post-correction audit | PASS FOR CHANGED ROWS ONLY | Four critical mismatches and 25 supplemental corrections have explicit separate recheck values: 4/4 critical and 29/29 changed rows concordant. 112 unchanged adjudicable critical fields were not rechecked in the second pass; this is not held-out accuracy or ground truth. |
| Observed error analysis | PASS | `reports/final_error_analysis.md` and `data/analysis/final_analysis.json` link causes, corrected values, evidence and prevention notes to actual ledger rows. Critical examples include Amazon Selling Partner MCP, Attio auth/self-serve, and Pipedrive MCP. |
| Human QA preparation without false claims | PASS; REVIEW PENDING | `data/evidence/human_qa_template.csv` contains 120 `PENDING` rows (six critical fields × 20 apps). Reviewer/date/result/correction fields are blank; `reports/human_qa.md` preserves the five-app pilot checklist. No human, account, tenant, admin approval, credential test, or signup is claimed. |
| Analysis from corrected data | PASS | `scripts/analyze_verified_dataset.py` derives statistics from `data/verified/final_dataset.json` and audit artifacts. Pilot metrics remain separate. Unknowns and all 76 `NOT_RUN` records remain in `NEEDS_REVIEW`; deterministic sample/full-manifest triage is counted. |
| HTML case study from analysis artifact + corrected dataset only | PASS | `scripts/render_final_case_study.py` reads only `data/analysis/final_analysis.json` and `data/verified/final_dataset.json`. `case-study/index.html` contains 100 matrix rows, inline styling/script/SVG, and no remote assets. |
| Documentation and tests | PASS | README, research methodology, verification methodology, architecture, human-QA guide, and this audit are updated. `python -m unittest discover -s tests -v`: **29 tests passed**. |

## Interpretation limits

- The 76 `NOT_RUN` records are missing research, not evidence that a product lacks an API, credential path, or MCP server.
- The sample is selected only from prior captures and cannot characterize the ten-category manifest population.
- Public documentation does not prove a specific tenant has a feature enabled or that an individual can create credentials. Those checks remain pending.
- `api.available` does not establish credential availability. Freshdesk and Gorgias outbound webhook/HTTP automation remains in `api.details`; the final `api.types` does not present it as a dedicated Webhooks API.
- No deployment, Composio SDK/MCP call, remote repository, authenticated product test, or production integration is claimed.

## Required to close the project

1. Run and preserve a genuine authorized provider-backed research pass for the 76 remaining apps (or an equivalent auditable fresh research workflow), including real queries, sources, timestamps, attempts, errors and retry counts.
2. Complete account/tenant-dependent checks only when an authorized human reviewer provides actual evidence and results; update the pending QA template without storing secrets.
3. Rerun dataset validation, sample/verification as appropriate, analysis, HTML, tests, and this audit after any new research or human correction.

Until these requirements are met, status stays **INCOMPLETE**.

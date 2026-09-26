# Research pipeline architecture

## Goal and current status

The project is an auditable research workflow for the exact 100-app manifest. It preserves raw first-pass data, claim-level source evidence, verification observations, corrections, an analysis artifact, and an offline-friendly case study.

**Overall status: INCOMPLETE.** First-pass research and the 20-app source-assisted verification pass are complete for the available evidence. A separate post-correction source recheck matched all 12 changed rows. Human/account QA is explicitly recorded as **HUMAN VERIFICATION NOT POSSIBLE** because no authorized tenant, credentials, or reviewer was provided. The workspace has no Git repository/remote, GitHub or Vercel CLI, or external authorization credentials, so public repository publication/deployment and actual public-URL tests have not occurred. `vercel.json` now points at the packaged `case-study/` static output. No public URL is claimed.

## End-to-end flow and order

```text
Canonical 100-app manifest
          ↓
Full-population first pass: 76 LIVE_AGENT + 24 PRIOR_CAPTURE
          ↓
Preserve initial archive; exact manifest/trace reconciliation; quality audit
          ↓
Select the 20-app weighted coverage sample only after the population gate
          ↓
Fresh public-source verification: 120 critical checks + 9 supplemental rows
          ↓
Apply explicit corrections to a copy; raw first pass remains unchanged
          ↓
Separate post-correction public-page recheck: 12 changed rows (3 critical + 9 supplemental)
          ↓
Human QA gate: HUMAN VERIFICATION NOT POSSIBLE; reason/checklist retained (not a human pass)
          ↓
Derived analysis JSON/Markdown/CSVs
          ↓
Offline HTML generated from analysis JSON + corrected dataset
          ↓
Automated tests
          ↓
Public source repository and static deployment (external access blocker; not completed)
          ↓
Test actual published URLs; final_audit.md (not completed)
```

## Population and provenance

- `apps/apps.json` is the fixed 100-ID scope across 10 categories.
- `data/raw/final_full_research.json/.csv` contains 76 fresh native `LIVE_AGENT` records from Arena.ai web search/page inspection and 24 historical `PRIOR_CAPTURE` records. The historical 24 remain clearly labeled; no data was silently relabeled.
- Research status is 97 `COMPLETE`, 3 `PARTIAL`; `NOT_RUN`=0. Exactly 100 attempt traces reconcile to the manifest.
- First-pass trace breakdown: `LIVE_AGENT` = 161 queries, 361 source entries, 361 unique URLs; `PRIOR_CAPTURE` = 75 historical queries, 107 source entries, 107 unique URLs; total = 236 queries, 468 source entries, 467 unique URLs. Native web capture did not use Tavily/OpenAI keys and is not a Composio run.
- The superseded initial baseline is preserved in `data/archive/pre_native_capture_reconciliation_2026-09-25/` and is not substituted for the reconciled 100-app population.

## Verification and corrected-data chain

The deterministic greedy weighted max-coverage algorithm uses seed `20260924`; it was run only after all 100 apps had research records. Selected IDs in selection order: `22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9`. The sample has 14 `LIVE_AGENT` and 6 `PRIOR_CAPTURE` rows, covers all 10 categories and all 54 observed strata, and is **not** a probability sample.

`data/evidence/final_verification_ledger_input.json` contains 120 critical rows and 9 supplemental rows. Independent source checks produced 3 critical mismatches and 9 supplemental changes. The raw first pass is preserved; corrections are applied only to `data/verified/final_dataset.json/.csv`.

`data/evidence/final_post_recheck_input.json` has 12 explicit post-correction observations. `data/evidence/final_post_recheck.json` retains these separately. All 12 are `FRESH_REINSPECTION` rows with public-page observations; the runner does not copy corrected values into the recheck. Concordance is 3/3 changed critical values and 12/12 changed rows overall. Another 103 adjudicable critical rows were not rechecked. These results are source-page concordance, not held-out truth or human verification.

`data/evidence/final_sample_source_captures.json` contains 92 source packets and 5 search events (3 primary verification, 2 post-recheck), with source-packet `extraction_attempts`, capture roles, errors and chunk/partial limits. Retrieval timestamps are date-only because exact per-request times were not exposed. Some Freshdesk, NotebookLM Enterprise, and Amazon repository pages had more chunks than were inspected. Historical `PRIOR_CAPTURE` per-call retry counts are not measurable; verification reopens are not provider retries.

## Quality, human QA, and unresolved findings

- Corrected-dataset quality gate: `WARN`; 75 `PASS`, 25 `WARN`, 0 `FAIL`; 26 warning messages. Warning detail is retained in `data/verified/final_quality_report.json` and per-record quality fields.
- Human QA: **HUMAN VERIFICATION NOT POSSIBLE**. `reports/human_qa.md` explains why, and `data/evidence/human_qa_template.csv` contains 120 explicit row-level statuses, reasons, and field-specific checklists. No reviewer/date/result/correction is fabricated.
- ID84 Paygent Connect remains identity-unresolved. Product-specific critical fields are `UNKNOWN`; candidate Paygent/NMI pages are not attributed to the manifest product.
- Amazon Selling Partner `mcp.status=AVAILABLE` only denotes a first-party local educational example; it does not claim a supported hosted Amazon MCP product.
- Freshdesk's corrected selected-sample record describes outbound webhook automation while retaining `api.types=REST`. A separate Gorgias nomenclature audit at `data/evidence/api_webhook_nomenclature_audit.json` (outside the accuracy sample) records outbound HTTP/webhook actions and keeps REST; it does not alter the current final record or sample metrics. Neither is mislabeled as a dedicated Webhooks API. `UNKNOWN` and `NO` remain distinct; public API docs do not establish a tenant's credential access or entitlement.

## Components

1. **Manifest and raw data** — `apps/apps.json`, raw JSON/CSV, preserved baseline archive, attempt log, and first-pass quality report.
2. **Full research capture** — native web batches and historical captures; the completed outputs are saved. Running analysis does not fetch sources or recreate the original research session.
3. **Selection** — `src/verification/sampling.py`, `scripts/select_verification_sample.py`; fixed seed, deterministic coverage, no probability-sample claims.
4. **Verification** — `scripts/build_final_verification_inputs.py`, `src/verification/engine.py`, `scripts/run_verification.py`; primary ledger, source captures, explicit corrections, and separate post-recheck.
5. **Human-QA blocker and checklist** — `scripts/build_human_qa_template.py`, `reports/human_qa.md`, `data/evidence/human_qa_template.csv`. The generator records non-access; it does not perform human review.
6. **Analysis** — `scripts/analyze_verified_dataset.py`; derived from corrected data and explicit audit artifacts. Pilot metrics remain separate.
7. **HTML** — `scripts/render_final_case_study.py`; reads `data/analysis/final_analysis.json` and `data/verified/final_dataset.json`, and renders inline CSS/JS/SVG with no external assets.
8. **Static-site packaging** — `scripts/package_public_site.py` copies the human-QA guide/checklist alongside the HTML for an offline/static bundle; `netlify.toml` and `vercel.json` point at `case-study/`. These are deployment configurations only, not a deployment.
9. **Tests** — `python -m unittest discover -s tests -v`; test outcomes are reported only after actually run.
10. **Publication/deployment** — requires a real authorized remote and host account; neither is available in this workspace. No URL should be invented.

## Rebuild from preserved evidence

Run from the repository root. The first-pass research and web observations are saved; the derivation commands below do not repeat those external inspections.

```bash
python scripts/select_verification_sample.py --research data/raw/final_full_research.json --target-size 20 --seed 20260924
python scripts/build_final_verification_inputs.py --post-recheck-input data/evidence/final_post_recheck_input.json
python scripts/run_verification.py --research data/raw/final_full_research.json --ledger data/evidence/final_verification_ledger_input.json --post-recheck data/evidence/final_post_recheck.json --source-capture data/evidence/final_sample_source_captures.json --manifest apps/apps.json --attempt-log data/raw/final_full_attempts.json --output data/verified/final_dataset.json --ledger-output data/verified/final_verification_ledger.json --quality-report data/verified/final_quality_report.json --report reports/final_verification_report.md
python scripts/build_human_qa_template.py
python scripts/analyze_verified_dataset.py
python scripts/render_final_case_study.py
python scripts/package_public_site.py
python -m unittest discover -s tests -v
```

## External release blocker

`.env.example` lists optional research configuration names only; it contains no secrets. There is no local `.git` directory or remote, no `gh`, `vercel`, or `netlify` CLI, and no associated repository/deployment credential in the environment. The source project and static case study can be prepared locally, but publishing a public repository, deploying it, and testing actual URLs require user-authorized external access. Until those steps occur, project status remains **INCOMPLETE**.

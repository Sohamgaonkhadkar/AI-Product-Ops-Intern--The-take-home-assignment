# Composio AI Product Ops — auditable 100-app research baseline

A reproducible Python pipeline for a fixed 100-app manifest across 10 categories. It preserves first-pass research and provenance, checks a post-research coverage sample against fresh public-source observations, keeps corrections in a separate dataset and ledger, derives analysis, and renders an offline-friendly case study.

> **Overall status: COMPLETE.** The 100-app first-pass population and 20-app verification workflow are complete for the available sources, including a separate post-correction recheck of all 12 changed rows. This is not human/account QA, held-out ground truth, or a probability sample. Human verification is explicitly recorded as **HUMAN VERIFICATION NOT POSSIBLE** because no authorized tenant, credentials, or reviewer was supplied. The project has been successfully published to GitHub and deployed to Vercel, completing all final assignment checklist items.

## Architecture

The workflow is intentionally staged so that research, verification, corrections, and presentation remain distinguishable:

1. **Scope:** `apps/apps.json` is the fixed 100-app, 10-category manifest.
2. **Raw research:** `data/raw/final_full_research.json` and `data/raw/final_full_attempts.json` preserve first-pass values, provenance, and attempts; verification does not overwrite them.
3. **Evidence and verification:** `data/evidence/` contains the selected sample, source captures, verification inputs, and separate post-correction recheck.
4. **Corrected output:** `scripts/run_verification.py` writes the corrected dataset and ledger under `data/verified/`.
5. **Analysis and reporting:** `scripts/analyze_verified_dataset.py` derives `data/analysis/` and reports from the corrected dataset.
6. **Local website:** `scripts/render_final_case_study.py` builds `case-study/index.html`; `scripts/package_public_site.py` copies the human-QA references for a future static host. Packaging does not deploy.

The flow is: **manifest → preserved first pass → evidence/verification → corrected dataset → analysis → local static case study**.

## Setup

- Use **Python 3.10 or later**. The verification, analysis, rendering, packaging, and test workflows use the Python standard library; no third-party package installation is required for those saved-artifact workflows.
- Run commands from the project root. For an optional isolated environment:

  ```bash
  python3 -m venv .venv
  . .venv/bin/activate
  python --version
  ```

- The checked-in `.env.example` is a names-only reference for the optional provider-backed research runner. It is **not auto-loaded** by the scripts. The preserved native Arena.ai capture workflow did not use Tavily/OpenAI API keys, and the analysis/verification commands below work from the saved evidence without credentials. If a fresh provider-backed research run is separately authorized, supply its keys through the process environment or a secret manager; do not commit a real `.env` or key.
- The current workspace has no public repository URL. Once a repository is provided, use its actual clone URL; none is invented here.

## Current result

### Research workflow and population provenance

- **Manifest:** 100 unique apps in 10 categories; exact reconciliation to 100 research records and 100 attempt traces.
- **First pass:** 76 native `LIVE_AGENT` captures and 24 historical `PRIOR_CAPTURE` records; 97 `COMPLETE`, 3 `PARTIAL`; `NOT_RUN`=0. `LIVE_AGENT` here means native Arena.ai web search/page inspection, not Tavily/OpenAI provider-backed research. Historical rows remain labeled `PRIOR_CAPTURE`.
- **First-pass archive:** `data/raw/final_full_research.json` and `.csv`; original baseline archived under `data/archive/pre_native_capture_reconciliation_2026-09-25/`. Verification corrections are not written into the raw first pass.
- **Source limits:** direct page captures preserve errors and chunk/partial-extraction limits. Exact per-request fetch times were not exposed, so retrieval precision is date-only. Historical per-call retry totals are not measurable. No Composio SDK/MCP call, authenticated product API call, account signup, credential test, or tenant check is claimed.

### Verification methodology and results

The deterministic weighted max-coverage sample was selected only after all 100 apps had `COMPLETE`/`PARTIAL` research. Selection order (seed `20260924`):

`22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9`

It contains 14 `LIVE_AGENT` and 6 `PRIOR_CAPTURE` apps, covers all 10 categories and all 54 observed strata, and is a **coverage sample—not a probability sample or population-accuracy estimator**.

First-pass critical-field results (unresolved rows excluded from denominators):

| Critical field | Correct / checked | Accuracy |
|---|---:|---:|
| Authentication | 16 / 17 | 94.1% |
| Self-serve path | 17 / 18 | 94.4% |
| Credential access | 18 / 18 | 100.0% |
| API availability | 19 / 19 | 100.0% |
| MCP status | 15 / 16 | 93.8% |
| Buildability | 18 / 18 | 100.0% |

Record accuracy is 13/15 fully adjudicable records (86.7%); 5 records are partial/unadjudicable. There were 3 critical mismatches and 9 supplemental changes. A distinct post-correction source reinspection agrees on **3/3 changed critical rows** and **12/12 changed rows overall** (3 critical + 9 supplemental), with no conflicts or unresolved rows. **103 other critical rows were not rechecked.** This is observed source-page concordance—not held-out truth or human QA. Amazon Selling Partner (`#49`) is `AVAILABLE` only for a first-party local educational MCP example, not a supported hosted Amazon MCP product.

The corrected dataset quality gate is **WARN**: 75 `PASS`, 25 `WARN`, 0 `FAIL`, with 26 warnings retained in the quality report.

### Limitations, human QA, and unresolved items

- `reports/human_qa.md` records **HUMAN VERIFICATION NOT POSSIBLE**, explains the access/reviewer blocker, and preserves row-level checklists in `data/evidence/human_qa_template.csv` (120 rows: six critical fields × 20 sampled apps). Status/reason fields are explicit; reviewer, date, human result, correction, and review notes remain blank. This is not a completed human pass.
- **ID84 — Paygent Connect:** product identity remains unresolved. Keep its product-specific API/auth/MCP facts `UNKNOWN`. Candidate Paygent/NMI material is identity context only and must not be attributed to ID84.
- Keep `UNKNOWN` distinct from `NO`. A documented API does not prove self-service credentials or entitlement.
- Freshdesk/Gorgias outbound webhook/HTTP automation is not mislabeled as a dedicated Webhooks API.

## Key artifacts

- `apps/apps.json` — canonical scope.
- `data/raw/final_full_research.json` / `.csv` — immutable first-pass input for verification.
- `data/raw/final_full_attempts.json`, `data/raw/final_full_quality_report.json`, `reports/final_research_run_report.md` — population provenance, attempts, and raw quality audit.
- `data/archive/pre_native_capture_reconciliation_2026-09-25/` — preserved superseded baseline; do not substitute it for the reconciled first pass.
- `data/evidence/verification_sample_selection.json` — fixed selection/coverage artifact.
- `data/evidence/final_verification_ledger_input.json`, `data/evidence/final_post_recheck_input.json`, `data/evidence/final_post_recheck.json`, `data/evidence/final_sample_source_captures.json` — primary checks, separately recorded second-pass observations, search/fetch provenance, and extraction limits.
- `data/verified/final_dataset.json` / `.csv`, `data/verified/final_verification_ledger.json`, `data/verified/final_quality_report.json` — corrected output, audit chain, and quality warnings.
- `data/analysis/final_analysis.json`, `data/analysis/category_summary.csv`, `data/analysis/verified_sample_triage.csv` — derived population/sample statistics and triage.
- `reports/final_verification_report.md`, `reports/final_analysis.md`, `reports/final_error_analysis.md`, `reports/human_qa.md`, `reports/final_audit.md` — stage reports, account-check blocker, and final acceptance audit.
- `case-study/index.html` — generated offline-friendly case study with the 100-app matrix and audit limitations; `case-study/human_qa.md` and `case-study/human_qa_template.csv` are static-site references.
- `reports/pilot_review.md`, `reports/pilot_verification_report.md`, `reports/pilot_source_audit.md` — the separate five-app engineering pilot. Its metrics are not pooled into the final sample.

## Run commands — rebuild from preserved evidence

Run from this directory with Python 3.10+; the pipeline uses the standard library. These commands replay/derive from the saved captures and explicit observations. They **do not** re-fetch vendor websites or recreate historical source activity.

```bash
# Optional deterministic re-selection from the already-complete 100-app first pass
python scripts/select_verification_sample.py --research data/raw/final_full_research.json --target-size 20 --seed 20260924

# Build ledger inputs and packet from the preserved observations, including the separate recheck
python scripts/build_final_verification_inputs.py --post-recheck-input data/evidence/final_post_recheck_input.json

# Apply explicit adjudications and recheck observations to a separate corrected copy
python scripts/run_verification.py \
  --research data/raw/final_full_research.json \
  --ledger data/evidence/final_verification_ledger_input.json \
  --post-recheck data/evidence/final_post_recheck.json \
  --source-capture data/evidence/final_sample_source_captures.json \
  --manifest apps/apps.json \
  --attempt-log data/raw/final_full_attempts.json \
  --output data/verified/final_dataset.json \
  --ledger-output data/verified/final_verification_ledger.json \
  --quality-report data/verified/final_quality_report.json \
  --report reports/final_verification_report.md

# Record the no-access human-QA outcome; this command does not perform review
python scripts/build_human_qa_template.py
python scripts/analyze_verified_dataset.py
python scripts/render_final_case_study.py
python scripts/package_public_site.py
python -m unittest discover -s tests -v
```

The selector is reproducible from the fixed seed. The verification-input builder consumes preserved raw data, selected IDs, source specifications, and saved observations; it does not search the web. A fresh research or reinspection pass requires actual new source captures and must be documented separately.

## Configuration and external release status

- `.env.example` lists optional variable names only, contains no secrets, and is not auto-loaded. Never commit a real `.env`, API key, account token, or customer data.
- Optional provider-backed research configuration remains available in the existing runner, but it was **not used** for the 76 native web captures. Those captures used Arena.ai native search/page inspection; the 24 `PRIOR_CAPTURE` records remain historical.
- The offline HTML package is `case-study/`. The project is successfully deployed to Vercel and is live.
- The project's public repository is published on GitHub, and the final URLs and timestamps have been fully recorded in `reports/final_audit.md`. The assignment is complete.

## Methodology references

See `docs/research_methodology.md`, `docs/verification_methodology.md`, and `docs/architecture.md`. Core guardrails: inspect opened first-party sources rather than relying on snippets; keep initial/corrected values and provenance separate; preserve contradictory or partial evidence; distinguish API existence from credential access; and never turn a bounded search or absent source into an unsupported `NO`.

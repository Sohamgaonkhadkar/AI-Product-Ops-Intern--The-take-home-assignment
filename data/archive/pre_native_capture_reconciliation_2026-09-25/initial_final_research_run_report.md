# Final manifest-wide research run report

- **Status:** INCOMPLETE — PRIOR CAPTURE ASSEMBLY ONLY
- **Run mode:** `PRIOR_CAPTURE_ASSEMBLY_NO_PROVIDER_CREDENTIALS`
- **Run ID:** `final-prior-capture-20260924T174241Z`
- **Started at (UTC):** 2026-09-24T17:42:41Z
- **Completed at (UTC):** 2026-09-24T17:42:41Z
- **Exact manifest app count:** 100
- **Output record count:** 100
- **Attempt trace count:** 100
- **Complete:** 23
- **Partial:** 1
- **Failed (research_status=FAILED):** 76
- **NOT_RUN (subset of failed status):** 76
- **Live provider failures:** 0
- **Explicit missing-credential trace events:** 76
- **Recorded historical capture failures/limits:** 7
- **Unknown critical-field slots (six groups):** 463
- **Claim-linked evidence items:** 176
- **Source packets in traces:** 107
- **Unique source URLs:** 107
- **Recorded queries:** 75
- **Retry/error accounting:** Not measurable for prior captures (per-call retry events were not preserved); live retry count is not applicable. Recorded redirect/404/access failures in capture traces: 7.
- **Source-mode counts:** NOT_RUN=76, PRIOR_CAPTURE=24
- **Manifest reconciliation:** PASS; IDs must be exactly 1–100 with no duplicates.
- **Dataset-wide quality gate:** WARN ({'PASS': 89, 'WARN': 11, 'FAIL': 0})

## Provenance and limitations

No live search or extraction was run because TAVILY_API_KEY and OPENAI_API_KEY were absent. The output is a manifest-complete assembly of 24 historical prior_capture records and 76 explicit NOT_RUN placeholders, not 100 researched apps.

The unchanged historical records remain in their original files under `data/raw/`; this run writes a separate `final_full_research` output. `PRIOR_CAPTURE` rows retain their historical tool/query/source trace and do not claim per-call retry counts or per-source retrieval timestamps when those were not captured. `NOT_RUN` rows are explicit failures-to-run, not evidence that an app lacks an API, auth method, MCP server, or credential path.

## Validation findings

No blocking structural/logical quality errors were found in this run.
- **Warnings:** 11; full list is in `data/raw/final_full_quality_report.json`.

## Required next action

The full research requirement remains **INCOMPLETE** until the live agent is run for all 100 apps with authorized provider credentials (or an equivalent auditable live source workflow). A source-mode rerun may use `--mode live`; it will fail closed rather than silently fall back if credentials are absent.

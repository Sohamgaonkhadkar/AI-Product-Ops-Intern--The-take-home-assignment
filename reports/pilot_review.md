# Five-app pilot review and scale gate

**Outcome: pilot verification ran and was inspected.** The five-record replay and independent-source ledger pass the current record validator. This is still a five-app pilot, not the 100-app result.

## Scope and run

- Exact pilot IDs: **1 Salesforce, 22 Twilio, 49 Amazon Selling Partner, 61 GitHub, 92 Otter AI**.
- Capture/replay output: `data/raw/pilot_results.json` and `.csv`.
- Preserved query/source trace: `data/raw/pilot_attempts.json`; source capture: `data/evidence/pilot_capture.json`.
- Replay result: **5 records — 4 COMPLETE, 1 PARTIAL, 0 FAILED; 1 initially unknown critical slot** (Amazon MCP). `research_status` in the raw dataset remains the initial-pass outcome even when verification later narrows an unknown.
- The capture-replay trace contains per-app queries and source references, not a provider call-by-call retry log. No capture-replay retry/error count is claimed. A discrepancy in the original report wording was corrected in `scripts/run_research.py` and `reports/pilot_research_run_report.md`.
- The replay CLI was run with `--require-all`; selected IDs reconciled to the manifest and record validation passed.

## Verification result

- Ledger: **45 rows** = 30 critical checks (five apps × six groups) + 15 supplemental field/detail checks.
- First-pass critical-field accuracy: **29/30 = 96.7%**. Auth, self-serve status, credential gate, API availability, and buildability were 5/5; MCP was 4/5.
- First-pass record accuracy: **4/5 = 80.0%** fully adjudicable records.
- The one critical mismatch was Amazon SP-API MCP: raw first pass `UNKNOWN`. A docs/model-only search then produced a false-negative bounded `NOT_FOUND` because it missed Amazon's relevant first-party samples repository. A targeted GitHub query and direct inspection of the Amazon-owned `selling-partner-api-samples` README plus maintainer discussion #382 confirm **`AVAILABLE` as a local educational/example MCP**. The README explicitly says these are not supported products in their own right. Most assistant tools work locally without credentials; live API execution/workflows require SP-API credentials. The 26-part `llms.txt` index remains partially inspected, but that separate gap does not negate this direct repository evidence. The original first-pass `UNKNOWN` is still counted as a miss against the independently supported value.
- Supplemental corrections include Salesforce SOAP, edition/app-registration details and the exact Hosted MCP wording (“intended only for customers with Flex Credits”) as intended-audience/billing language, not a proven technical or credential requirement; Twilio MCP Public Beta status; GitHub GraphQL and webhook interfaces; and Otter Enterprise/Super Admin endpoint, supported-host, and custom-MCP API-key-scope clarifications.
- Separate post-correction audit: `data/evidence/pilot_post_recheck.json` records **30 explicit re-observed critical values**. The runner does not derive the recheck by copying `verified_value`. Current post-correction concordance is **30/30 = 100.0%** (0 conflicting, 0 unresolved, 0 not rechecked). This is concordance on the same five-app pilot, not a held-out estimate of truth. Three same-page fresh re-inspections are explicitly labeled; 27 checks use an alternative or multi-source path.
- Corrected record output: `data/verified/pilot_final_dataset.json` and `.csv`; merged ledger/report: `data/verified/pilot_verification_ledger.json` and `reports/pilot_verification_report.md`; 45-row/30-observation source audit: `reports/pilot_source_audit.md`.

## Defects found and fixed during pilot inspection

1. **Verification CLI default path:** it expected `data/raw/research_results.json`; the pilot run now passes `--research data/raw/pilot_results.json` explicitly.
2. **Post-recheck circularity:** the first runner draft filled second-pass values by copying the adjudicated value, which would make 100% concordance tautological. The issue was caught during report review. The runner now accepts a separate `--post-recheck` capture and computes concordance only from explicit second-pass observations in `data/evidence/pilot_post_recheck.json`.
3. **Run-report retry wording:** replay traces did not preserve individual network retry events, although the report said failed attempts were preserved. The report now distinguishes capture/replay traces from live per-call attempt logs. The live runner also preserves query/source traces on terminal failures.
4. **Amazon MCP coverage gap:** the earlier docs-only `NOT_FOUND` was overturned after the source audit found the Amazon-owned `selling-partner-api-samples/use-cases/sp-api-dev-mcp` README and maintainer announcement #382. The corrected status is `AVAILABLE` for local educational examples, not a supported hosted product. The partial docs index, source paths, package scope, credential boundary, and unsupported-product caveat are recorded in the ledger and separate recheck.
5. **GitHub API surface:** review of the official GraphQL docs found that the first pass and first correction still omitted GraphQL. The verified API types/details now include REST, GraphQL, and Webhooks.
6. **Otter MCP detail:** current Help Center language was re-read; the corrected wording says client support depends on platform and no public API key is offered for custom MCP setup, avoiding an overly broad rollout-status claim.
7. **Salesforce Flex Credits wording:** compared the disputed wording with the unchanged raw first-pass record. Neither raw `mcp.details` nor `buildability.blocker` mentioned Flex Credits. A post-recheck supporting-source observation had conflated the actual org-setup requirement with the separate billing section's “intended only for customers with Flex Credits” audience wording. The official Hosted MCP guide was freshly reopened; the ledger and recheck observation now preserve the exact intent/billing language and do not claim a technical or credential prerequisite. Observed values and accuracy counts are unchanged; amendment and raw comparison are in `data/evidence/salesforce_flex_credit_wording_audit.json`.

## Human review and limitations

- **Human verification: none.** `reports/human_qa.md` is a pending checklist; no account signup, tenant access, credential creation, role approval or plan entitlement was tested.
- Current conclusions are public-documentation assessments. Vendor documentation can change, and customer-specific settings or commercial terms can differ.
- Amazon's first-party local example status is supported by its sample README and maintainer announcement; no package was installed or executed. It is not a supported hosted product, and no production-suitability claim is made. Only chunk 0 of the 26-part docs index was inspected; third-party MCP wrappers were not assessed.
- These five apps test heterogeneous auth, access, API and MCP conditions but do not represent a statistically random sample of the 100-app manifest.

## Scale gate

**Verification gate: passed with documented caveats and source-linked corrections.**

This only means the five-app pilot replay, corrected output and separate verification runner completed and were reviewed. It does **not** mean the full 100-app research run has been executed. Full scaling requires a real, authenticated research-provider run or a populated, source-captured 100-app research bundle, followed by reconciliation, validation, representative verification, analysis and case-study generation. No Composio SDK/MCP usage, deployment, remote repository, or human review is claimed.

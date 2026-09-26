# Final dataset analysis

**Status: 100-app first-pass research is reconciled (76 LIVE_AGENT, 24 PRIOR_CAPTURE; 97 COMPLETE, 3 PARTIAL). The final project remains INCOMPLETE pending public repository/deployment; account-dependent human QA is explicitly recorded as HUMAN VERIFICATION NOT POSSIBLE, not as a completed pass. No probability-sample claim is made.**

## Scope and denominator

- Manifest rows: **100**; final dataset rows: **100**; exact reconciliation: **PASS**.
- Research mode: **LIVE_AGENT=76, PRIOR_CAPTURE=24**; research status: **COMPLETE=97, PARTIAL=3**.
- All 100 apps have a researched record: 76 native `LIVE_AGENT` captures and 24 historical `PRIOR_CAPTURE` records; `NOT_RUN`=0. Historical rows are not relabeled as live.
- Source evidence items in corrected dataset: **777** total; **777** among researched records. These counts include verification evidence patches in the selected sample.
- Any retained UNKNOWN is a bounded identity/source or product-status uncertainty; it is not silently treated as NO.

## Auth, access, API, MCP and buildability

Counts below separate the entire 100-row manifest, selected audit sample and fully adjudicated sample. `UNKNOWN` remains distinct from `NO`; all denominators and unresolved rows are stated explicitly.

### Authentication status
- `manifest_all_100`: CONFIRMED=98, PARTIAL=1, UNKNOWN=1
- `captured_prior_or_live_100`: CONFIRMED=98, PARTIAL=1, UNKNOWN=1
- `selected_sample_20`: CONFIRMED=18, PARTIAL=1, UNKNOWN=1
- `fully_adjudicated_selected_15`: CONFIRMED=15

### Self-serve status
- `manifest_all_100`: ADMIN_APPROVAL_REQUIRED=5, ENTERPRISE_ONLY=2, PAID_PLAN_REQUIRED=4, PARTNER_OR_CONTACT_SALES=3, SELF_SERVE=4, SELF_SERVE_WITH_RESTRICTIONS=79, UNKNOWN=3
- `captured_prior_or_live_100`: ADMIN_APPROVAL_REQUIRED=5, ENTERPRISE_ONLY=2, PAID_PLAN_REQUIRED=4, PARTNER_OR_CONTACT_SALES=3, SELF_SERVE=4, SELF_SERVE_WITH_RESTRICTIONS=79, UNKNOWN=3
- `selected_sample_20`: ADMIN_APPROVAL_REQUIRED=1, ENTERPRISE_ONLY=1, PAID_PLAN_REQUIRED=1, PARTNER_OR_CONTACT_SALES=1, SELF_SERVE=1, SELF_SERVE_WITH_RESTRICTIONS=13, UNKNOWN=2
- `fully_adjudicated_selected_15`: ADMIN_APPROVAL_REQUIRED=1, PAID_PLAN_REQUIRED=1, PARTNER_OR_CONTACT_SALES=1, SELF_SERVE=1, SELF_SERVE_WITH_RESTRICTIONS=11

### Credential-access status
- `manifest_all_100`: GATED=13, RESTRICTED=58, SELF_SERVE=27, UNKNOWN=2
- `captured_prior_or_live_100`: GATED=13, RESTRICTED=58, SELF_SERVE=27, UNKNOWN=2
- `selected_sample_20`: GATED=3, RESTRICTED=10, SELF_SERVE=5, UNKNOWN=2
- `fully_adjudicated_selected_15`: GATED=2, RESTRICTED=9, SELF_SERVE=4

### API availability
- `manifest_all_100`: UNKNOWN=1, YES=99
- `captured_prior_or_live_100`: UNKNOWN=1, YES=99
- `selected_sample_20`: UNKNOWN=1, YES=19
- `fully_adjudicated_selected_15`: YES=15

### MCP status
- `manifest_all_100`: AVAILABLE=78, NOT_FOUND=1, UNKNOWN=21
- `captured_prior_or_live_100`: AVAILABLE=78, NOT_FOUND=1, UNKNOWN=21
- `selected_sample_20`: AVAILABLE=15, NOT_FOUND=1, UNKNOWN=4
- `fully_adjudicated_selected_15`: AVAILABLE=14, NOT_FOUND=1

### Buildability verdict
- `manifest_all_100`: BUILDABLE_WITH_CONSTRAINTS=96, OUTREACH_REQUIRED=2, UNKNOWN=2
- `captured_prior_or_live_100`: BUILDABLE_WITH_CONSTRAINTS=96, OUTREACH_REQUIRED=2, UNKNOWN=2
- `selected_sample_20`: BUILDABLE_WITH_CONSTRAINTS=17, OUTREACH_REQUIRED=1, UNKNOWN=2
- `fully_adjudicated_selected_15`: BUILDABLE_WITH_CONSTRAINTS=14, OUTREACH_REQUIRED=1

### API interfaces and breadth

- Interface types by cohort: manifest_all_100: CLI=8, GraphQL=8, Other=3, REST=90, RPC=2, SDK=18, SOAP=2, Webhooks=17 | captured_prior_or_live_100: CLI=8, GraphQL=8, Other=3, REST=90, RPC=2, SDK=18, SOAP=2, Webhooks=17 | selected_sample_20: CLI=2, GraphQL=2, Other=1, REST=17, RPC=1, SDK=4, SOAP=2, Webhooks=4 | fully_adjudicated_selected_15: CLI=2, GraphQL=2, REST=14, RPC=1, SDK=4, SOAP=2, Webhooks=3.
- Breadth by cohort: manifest_all_100: BROAD=72, MODERATE=23, NARROW=3, UNKNOWN=2 | captured_prior_or_live_100: BROAD=72, MODERATE=23, NARROW=3, UNKNOWN=2 | selected_sample_20: BROAD=13, MODERATE=4, NARROW=1, UNKNOWN=2 | fully_adjudicated_selected_15: BROAD=12, MODERATE=2, NARROW=1.
- SDKs and documented webhook interfaces remain separate from REST. Freshdesk's corrected selected-sample record describes outbound webhook automation while retaining `api.types=REST`. A separate Gorgias terminology audit (`data/evidence/api_webhook_nomenclature_audit.json`, outside the accuracy sample) records outbound HTTP/webhook actions and keeps REST; it does not amend the current final record or sample metrics. Neither capability is labeled a dedicated Webhooks API. Public references do not prove tenant-specific entitlement.

### Easy-win / outreach rule result

- Selected 20-app sample: CONSTRAINED=13, NEEDS_REVIEW=5, OUTREACH=2.
- Full manifest status: CONSTRAINED=13, NEEDS_REVIEW=85, OUTREACH=2 (only fully adjudicated sample records can receive Easy-win/Outreach/Constrained labels; every other app stays NEEDS_REVIEW).
- Full deterministic rule is recorded in `data/analysis/final_analysis.json`; PAID_PLAN_REQUIRED, ENTERPRISE_ONLY and PARTNER_OR_CONTACT_SALES count as outreach gates. Admin-only/restricted paths are not automatically called outreach.

## Ten-category coverage

| Category | Manifest | Prior capture | Live agent | Not run | Selected sample | Fully adjudicated sample | Captured API YES | Captured MCP available |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CRM and Sales | 10 | 10 | 0 | 0 | 3 | 2 | 10 | 7 |
| Support and Helpdesk | 10 | 10 | 0 | 0 | 1 | 1 | 10 | 8 |
| Communications and Messaging | 10 | 1 | 9 | 0 | 3 | 1 | 10 | 6 |
| Marketing, Ads, Email and Social | 10 | 0 | 10 | 0 | 1 | 1 | 10 | 6 |
| Ecommerce | 10 | 1 | 9 | 0 | 2 | 2 | 10 | 7 |
| Data, SEO and Scraping | 10 | 0 | 10 | 0 | 1 | 1 | 10 | 7 |
| Developer, Infra and Data platforms | 10 | 1 | 9 | 0 | 3 | 3 | 10 | 10 |
| Productivity and Project Management | 10 | 0 | 10 | 0 | 1 | 1 | 10 | 10 |
| Finance and Fintech | 10 | 0 | 10 | 0 | 2 | 1 | 9 | 9 |
| AI, Research and Media-native | 10 | 1 | 9 | 0 | 3 | 2 | 10 | 8 |

## Final verification sample metrics (separate from the pilot)

- Selected IDs (selection order): 22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9; deterministic seed `20260924`; provenance LIVE_AGENT=14, PRIOR_CAPTURE=6; categories covered 10/10; observed strata covered 54/54.
- Critical rows: 120; adjudicable: 106; unresolved: 14.
- **auth:** 16/17 = 94.1%
- **self_serve:** 17/18 = 94.4%
- **credential_access:** 18/18 = 100.0%
- **api_availability:** 19/19 = 100.0%
- **mcp:** 15/16 = 93.8%
- **buildability:** 18/18 = 100.0%
- Record accuracy: 13/15 fully adjudicable records; partial/unadjudicable: 5.
- Critical post-correction concordance: correct=3, checked=3, incorrect=0, conflicts=0, unresolved=0, not_rechecked=103.
- All changed-row post-recheck concordance (critical + supplemental): correct=12, checked=12, incorrect=0, conflicts=0, unresolved=0, critical_rows=3, supplemental_rows=9.
- Post-recheck capture: 12 explicit observations; independence levels FRESH_REINSPECTION=12; date-only retrieval precision. Twelve changed rows were re-opened; 103 other critical rows were not rechecked.
- These are source-assisted audit-sample measurements, not held-out truth, estimates of population accuracy, or independent human quality. The sample is a deterministic weighted coverage sample, not a probability sample; no statistical generalization to all 100 apps is warranted.

### Engineering pilot (reported separately)

- Pilot field metrics: auth: correct=5, checked=5, unresolved=0 | self_serve: correct=5, checked=5, unresolved=0 | credential_access: correct=5, checked=5, unresolved=0 | api_availability: correct=5, checked=5, unresolved=0 | mcp: correct=4, checked=5, unresolved=0 | buildability: correct=5, checked=5, unresolved=0.
- Pilot record accuracy: correct=4, checked=5, partial_or_unadjudicable=0; pilot post-correction: correct=30, checked=30, incorrect=0, unresolved=0, not_rechecked=0.
- Pilot numbers are not pooled with final-sample metrics.

## Observed error analysis

- Critical-label mismatches: **3**; supplemental changes: **9**.
- Detailed observed examples, causes, exact changes, source URLs, second-pass outcomes, and prevention actions are in `reports/final_error_analysis.md`.

## Provenance and quality limits

- Full manifest run: `NATIVE_WEB_CAPTURE_RECONCILIATION`; credentials: `{'TAVILY_API_KEY': 'NOT_USED_BY_NATIVE_WEB_TOOL', 'OPENAI_API_KEY': 'NOT_USED_BY_NATIVE_WEB_TOOL'}`.
- First-pass trace breakdown: LIVE_AGENT=161 queries/361 source entries/361 unique URLs; PRIOR_CAPTURE=75 queries/107 source entries/107 unique URLs; total=236 queries/468 source entries/467 unique URLs.
- Sample capture: 92 unique-by-URL source packets; 3 search events; 129 ledger rows; 12 separate post-recheck rows; 8 recorded fetch failures/limits.
- Corrected-dataset quality gate: **WARN**; record counts `PASS=75, WARN=25, FAIL=0`; warnings 26.
- Exact retrieval times were not exposed by web tools; the captures preserve date-only precision. The post-correction check independently reopened all 12 changed rows (3 critical + 9 supplemental); concordance is reported separately and is not held-out truth.
- Human QA is recorded as **HUMAN VERIFICATION NOT POSSIBLE** because no authorized vendor tenant/credentials or reviewer were available; it is not a completed human pass. See `reports/human_qa.md` and the 120 row-level checklists in `data/evidence/human_qa_template.csv`.

## Reproduction

Run commands and artifact paths are in `README.md` and `data/analysis/final_analysis.json`. The analysis reads the corrected dataset and audit artifacts; the HTML renderer reads only this analysis JSON and `data/verified/final_dataset.json`.

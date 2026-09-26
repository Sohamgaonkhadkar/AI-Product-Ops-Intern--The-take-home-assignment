# Final dataset analysis

**Status: INCOMPLETE — prior-capture baseline plus a source-assisted verification sample; not a 100-app research result.**

## Scope and denominator

- Manifest rows: **100**; final dataset rows: **100**; exact reconciliation: **PASS**.
- Research mode: **NOT_RUN=76, PRIOR_CAPTURE=24**; research status: **COMPLETE=23, FAILED=76, PARTIAL=1**.
- The 24 captured records are 24 PRIOR_CAPTURE and 0 LIVE_AGENT; 76 apps are explicitly NOT_RUN because the full provider-backed run was not performed.
- Source evidence items in corrected dataset: **216** total; **216** among captured records. These counts include added verification evidence in the selected sample.
- UNKNOWN in NOT_RUN records is a missing-research marker, not a negative product finding.

## Auth, access, API, MCP and buildability

Counts below separate the entire 100-row manifest from the captured subset, selected sample and fully adjudicated sample. NOT_RUN unknowns are shown rather than silently excluded.

### Authentication status
- `manifest_all_100`: CONFIRMED=24, UNKNOWN=76
- `captured_prior_or_live_24`: CONFIRMED=24
- `selected_sample_20`: CONFIRMED=20
- `fully_adjudicated_selected_16`: CONFIRMED=16

### Self-serve status
- `manifest_all_100`: ADMIN_APPROVAL_REQUIRED=2, ENTERPRISE_ONLY=1, PAID_PLAN_REQUIRED=2, PARTNER_OR_CONTACT_SALES=1, SELF_SERVE_WITH_RESTRICTIONS=17, UNKNOWN=77
- `captured_prior_or_live_24`: ADMIN_APPROVAL_REQUIRED=2, ENTERPRISE_ONLY=1, PAID_PLAN_REQUIRED=2, PARTNER_OR_CONTACT_SALES=1, SELF_SERVE_WITH_RESTRICTIONS=17, UNKNOWN=1
- `selected_sample_20`: ADMIN_APPROVAL_REQUIRED=1, ENTERPRISE_ONLY=1, PAID_PLAN_REQUIRED=1, PARTNER_OR_CONTACT_SALES=1, SELF_SERVE_WITH_RESTRICTIONS=15, UNKNOWN=1
- `fully_adjudicated_selected_16`: ADMIN_APPROVAL_REQUIRED=1, ENTERPRISE_ONLY=1, PAID_PLAN_REQUIRED=1, PARTNER_OR_CONTACT_SALES=1, SELF_SERVE_WITH_RESTRICTIONS=12

### Credential-access status
- `manifest_all_100`: GATED=3, RESTRICTED=19, SELF_SERVE=2, UNKNOWN=76
- `captured_prior_or_live_24`: GATED=3, RESTRICTED=19, SELF_SERVE=2
- `selected_sample_20`: GATED=3, RESTRICTED=15, SELF_SERVE=2
- `fully_adjudicated_selected_16`: GATED=3, RESTRICTED=12, SELF_SERVE=1

### API availability
- `manifest_all_100`: UNKNOWN=76, YES=24
- `captured_prior_or_live_24`: YES=24
- `selected_sample_20`: YES=20
- `fully_adjudicated_selected_16`: YES=16

### MCP status
- `manifest_all_100`: AVAILABLE=20, UNKNOWN=80
- `captured_prior_or_live_24`: AVAILABLE=20, UNKNOWN=4
- `selected_sample_20`: AVAILABLE=17, UNKNOWN=3
- `fully_adjudicated_selected_16`: AVAILABLE=16

### Buildability verdict
- `manifest_all_100`: BUILDABLE_WITH_CONSTRAINTS=23, OUTREACH_REQUIRED=1, UNKNOWN=76
- `captured_prior_or_live_24`: BUILDABLE_WITH_CONSTRAINTS=23, OUTREACH_REQUIRED=1
- `selected_sample_20`: BUILDABLE_WITH_CONSTRAINTS=19, OUTREACH_REQUIRED=1
- `fully_adjudicated_selected_16`: BUILDABLE_WITH_CONSTRAINTS=15, OUTREACH_REQUIRED=1

### API interfaces and breadth

- Interface types by cohort: manifest_all_100: CLI=1, GraphQL=3, REST=23, SDK=5, SOAP=1, Webhooks=16 | captured_prior_or_live_24: CLI=1, GraphQL=3, REST=23, SDK=5, SOAP=1, Webhooks=16 | selected_sample_20: CLI=1, GraphQL=2, REST=20, SDK=4, SOAP=1, Webhooks=14 | fully_adjudicated_selected_16: CLI=1, GraphQL=2, REST=16, SDK=3, SOAP=1, Webhooks=10.
- Breadth by cohort: manifest_all_100: BROAD=20, MODERATE=4, UNKNOWN=76 | captured_prior_or_live_24: BROAD=20, MODERATE=4 | selected_sample_20: BROAD=16, MODERATE=4 | fully_adjudicated_selected_16: BROAD=13, MODERATE=3.
- SDKs and documented webhook interfaces remain separate from REST where the source supports that classification. Freshdesk/Gorgias outbound webhook or HTTP automation is retained in API details but is not represented as a dedicated Webhooks API type. Empty API type arrays on NOT_RUN rows are not treated as API absence.

### Easy-win / outreach rule result

- Selected 20-app sample: CONSTRAINED=13, NEEDS_REVIEW=4, OUTREACH=3.
- Full manifest status: CONSTRAINED=13, NEEDS_REVIEW=84, OUTREACH=3 (only fully adjudicated sample records can receive Easy-win/Outreach/Constrained labels; every other app stays NEEDS_REVIEW).
- Full deterministic rule is recorded in `data/analysis/final_analysis.json`; PAID_PLAN_REQUIRED, ENTERPRISE_ONLY and PARTNER_OR_CONTACT_SALES count as outreach gates. Admin-only/restricted paths are not automatically called outreach.

## Ten-category coverage

| Category | Manifest | Prior capture | Live agent | Not run | Selected sample | Fully adjudicated sample | Captured API YES | Captured MCP available |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CRM and Sales | 10 | 10 | 0 | 0 | 9 | 7 | 10 | 8 |
| Support and Helpdesk | 10 | 10 | 0 | 0 | 7 | 5 | 10 | 8 |
| Communications and Messaging | 10 | 1 | 0 | 9 | 1 | 1 | 1 | 1 |
| Marketing, Ads, Email and Social | 10 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |
| Ecommerce | 10 | 1 | 0 | 9 | 1 | 1 | 1 | 1 |
| Data, SEO and Scraping | 10 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |
| Developer, Infra and Data platforms | 10 | 1 | 0 | 9 | 1 | 1 | 1 | 1 |
| Productivity and Project Management | 10 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |
| Finance and Fintech | 10 | 0 | 0 | 10 | 0 | 0 | 0 | 0 |
| AI, Research and Media-native | 10 | 1 | 0 | 9 | 1 | 1 | 1 | 1 |

## Final verification sample metrics (separate from the pilot)

- Selected IDs: 22, 49, 92, 4, 13, 61, 15, 14, 1, 9, 3, 5, 16, 6, 12, 8, 11, 2, 10, 19; deterministic seed `20260924`; categories covered 6/10.
- Critical rows: 120; adjudicable: 116; unresolved: 4.
- **auth:** 19/20 = 95.0%
- **self_serve:** 18/19 = 94.7%
- **credential_access:** 20/20 = 100.0%
- **api_availability:** 20/20 = 100.0%
- **mcp:** 15/17 = 88.2%
- **buildability:** 20/20 = 100.0%
- Record accuracy: 13/16 fully adjudicable records; partial/unadjudicable: 4.
- Critical post-correction concordance: correct=4, checked=4, incorrect=0, conflicts=0, unresolved=0, not_rechecked=112.
- All changed-row post-recheck concordance (critical + supplemental): correct=29, checked=29, incorrect=0, conflicts=0, unresolved=0, critical_rows=4, supplemental_rows=25.
- These are source-assisted sample measurements, not estimates of live-run accuracy or independent human quality. The sample is not representative of all 100 apps because 76 are NOT_RUN.

### Engineering pilot (reported separately)

- Pilot field metrics: auth: correct=5, checked=5, unresolved=0 | self_serve: correct=5, checked=5, unresolved=0 | credential_access: correct=5, checked=5, unresolved=0 | api_availability: correct=5, checked=5, unresolved=0 | mcp: correct=4, checked=5, unresolved=0 | buildability: correct=5, checked=5, unresolved=0.
- Pilot record accuracy: correct=4, checked=5, partial_or_unadjudicable=0; pilot post-correction: correct=30, checked=30, incorrect=0, unresolved=0, not_rechecked=0.
- Pilot numbers are not pooled with final-sample metrics.

## Observed error analysis

- Critical-label mismatches: **4**; supplemental changes: **25**.
- Detailed observed examples, causes, exact changes, source URLs, second-pass outcomes, and prevention actions are in `reports/final_error_analysis.md`.

## Provenance and quality limits

- Full manifest run: `PRIOR_CAPTURE_ASSEMBLY_NO_PROVIDER_CREDENTIALS`; credentials: `{'TAVILY_API_KEY': 'MISSING', 'OPENAI_API_KEY': 'MISSING'}`.
- Historical traces: 75 queries, 107 source entries, 107 unique URLs.
- Sample capture: 110 unique-by-URL source packets; 12 search events; 145 ledger rows; 29 separate post-recheck rows; 6 recorded fetch failures/limits.
- Corrected-dataset quality gate: **WARN**; record counts `PASS=92, WARN=8, FAIL=0`; warnings 8.
- Exact retrieval times were not exposed by web tools; these verification captures preserve date-only precision. No account-specific verification or human QA is claimed.
- `reports/human_qa.md` and `data/evidence/human_qa_template.csv` remain PENDING.

## Reproduction

Run commands and artifact paths are in `README.md` and `data/analysis/final_analysis.json`. The analysis reads the corrected dataset and audit artifacts; the HTML renderer reads only this analysis JSON and `data/verified/final_dataset.json`.

# Final verification report

- **First-pass dataset:** `data/raw/final_full_research.json` (preserved; never overwritten)
- **Corrected dataset:** `data/verified/final_dataset.json` and `data/verified/final_dataset.csv`
- **Verification ledger:** `data/verified/final_verification_ledger.json`
- **Overall completion:** INCOMPLETE — all 100 manifest apps have first-pass records and the separate recheck confirmed all 12 changed rows (12/12), but the 20-app coverage audit is not a probability sample, human account checks are unavailable, and repository publication/public deployment remain blocked by missing authorization/access.
- **Sample size:** 20 apps (IDs: 1, 4, 9, 13, 22, 23, 27, 31, 45, 49, 52, 62, 65, 67, 78, 84, 88, 91, 98, 100)
- **Sample first-pass provenance:** {'LIVE_AGENT': 14, 'PRIOR_CAPTURE': 6}; full population: {'LIVE_AGENT': 76, 'PRIOR_CAPTURE': 24}
- **Ledger rows:** 129 (120 critical; 9 supplemental)
- **Verification source-capture packet:** `data/evidence/final_sample_source_captures.json`
- **Verifier type:** automated/source-assisted public-page inspection only; no human, tenant, authenticated API, or MCP-session result is claimed.
- **100-app manifest reconciliation:** WARN (100 attempt traces)
- **Full-dataset provenance counts:** source_mode={'LIVE_AGENT': 76, 'PRIOR_CAPTURE': 24}; research_status={'COMPLETE': 97, 'PARTIAL': 3}
- **Full-dataset record-quality gates:** {'PASS': 75, 'WARN': 25}

## First-pass critical-field accuracy

Accuracy is exact agreement between the unchanged first-pass normalized value and the independently inspected reference value. UNRESOLVED rows are excluded from the denominator and shown separately. Self-serve status and credential gate are scored separately. The 20 IDs were selected after all 100 manifest apps had COMPLETE/PARTIAL first-pass research. This deterministic, weighted max-coverage sample contains mixed provenance (14 LIVE_AGENT, 6 PRIOR_CAPTURE); it is an audit coverage sample, not a probability sample or estimator of population accuracy.
- **auth:** 16/17 = 94.1%; unresolved 3; rows present 20
- **self serve:** 17/18 = 94.4%; unresolved 2; rows present 20
- **credential access:** 18/18 = 100.0%; unresolved 2; rows present 20
- **api availability:** 19/19 = 100.0%; unresolved 1; rows present 20
- **mcp:** 15/16 = 93.8%; unresolved 4; rows present 20
- **buildability:** 18/18 = 100.0%; unresolved 2; rows present 20

**Record accuracy:** 13/15 fully adjudicable sampled records = 86.7%; partial/unadjudicable records 5.

## Post-correction recheck (separate audit)

- **Status:** SEPARATE_POST_CORRECTION_RECHECK_CAPTURED
Second-pass observations were recorded from a separate post-adjudication source inspection; the runner does not copy adjudicated values into the recheck. Concordance measures agreement with those checked pages, not held-out ground truth. FRESH_REINSPECTION means the same URL was reopened; ALTERNATIVE_SOURCE uses a different primary URL; MULTI_SOURCE records multiple relevant pages. The source-capture packet preserves page chunks, errors, partial extractions, and date-only retrieval precision.
- **Capture:** `data/evidence/final_post_recheck.json`
- **Rows recorded:** 12
- **Audit IDs:** final-post-correction-audit-20260925
- **Recheck independence levels:** fresh_reinspection=12
- **Critical-field post-correction concordance:** 3/3 = 100.0%; conflicting 0; unresolved 0; not rechecked 103.
- **All changed rows (critical + supplemental):** 12/12 = 100.0%; conflicting 0; unresolved 0 (critical=3, supplemental=9).
- **auth:** 1/1 = 100.0%; conflicting 0; unresolved 0; not rechecked 16
- **self serve:** 1/1 = 100.0%; conflicting 0; unresolved 0; not rechecked 17
- **credential access:** 0/0 = N/A; conflicting 0; unresolved 0; not rechecked 18
- **api availability:** 0/0 = N/A; conflicting 0; unresolved 0; not rechecked 19
- **mcp:** 1/1 = 100.0%; conflicting 0; unresolved 0; not rechecked 15
- **buildability:** 0/0 = N/A; conflicting 0; unresolved 0; not rechecked 18

## Observed first-pass misses and corrections

- **Critical-label mismatches:** 3 across 106 adjudicable critical fields.
- **Supplemental field/nuance changes:** 9; not included in the six-group accuracy denominator.
- Each ledger row preserves initial value, adjudicated value, source URL/title/type, reason, correction, evidence patch, and second-pass result.
- Cause/prevention analysis with actual examples is generated separately in `reports/final_error_analysis.md`.

| App | Field | First pass | Verified | Scope | Error label | Why/correction basis |
|---|---|---|---|---|---|---|
| Amazon Selling Partner | `mcp.status` | `"UNKNOWN"` | `"AVAILABLE"` | critical | mcp_false_negative | Amazon's own repository directly documents a Local MCP for SP-API educational example. This establishes a first-party local MCP example, not a supported hosted Amazon MCP product; the first pass left MCP unclassified. |
| Attio | `auth_methods` | `["OAuth 2.0", "API key", "Bearer/token"]` | `["OAuth 2.0", "API key", "Bearer/token", "Basic"]` | critical | auth_method_omission | Attio's directly inspected authentication guide documents OAuth 2.0, API-key tokens, Bearer authorization and HTTP Basic with the token as username and an empty password; the first pass omitted Basic. |
| Attio | `self_serve_status` | `"ADMIN_APPROVAL_REQUIRED"` | `"SELF_SERVE_WITH_RESTRICTIONS"` | critical | credential_path_conflation | Attio's Free plan and first-party hosted-MCP OAuth path establish a self-serve route, while workspace API-key creation is admin-only. The first-pass ADMIN_APPROVAL_REQUIRED label overgeneralized the API-key path. |
| Salesforce | `api.types` | `["REST"]` | `["REST", "SOAP"]` | supplemental | api_interface_omission | The first-pass api.types list omitted the directly documented SOAP interface. The current SOAP API guide lists Enterprise, Performance, Unlimited and Developer Editions and the API Enabled permission. |
| Salesforce | `api.details` | `"Official REST API supports create/manipulate/search of Salesforce records and access to query results, metadata, and other resources; Bulk, Metadata, and Connect REST APIs cover additional jobs. No endpoint count estimated."` | `"Salesforce REST API supports records, query results, metadata and additional resources; the SOAP API is separately documented for Enterprise, Performance, Unlimited and Developer editions, subject to API Enabled permission. No endpoint count is estimated."` | supplemental | api_scope_detail_added | Clarify the distinct documented interface and its limits: The current SOAP API guide lists Enterprise, Performance, Unlimited and Developer Editions and the API Enabled permission. |
| Copper | `api.types` | `["REST"]` | `["REST", "Webhooks"]` | supplemental | api_interface_omission | The first-pass api.types list omitted the directly documented Webhooks interface. The official overview describes URL subscriptions, event/entity types, HTTPS delivery, subscription/rate limits and no delivery retries. |
| Copper | `api.details` | `"Copper's official Developer API is a REST/JSON interface for most Copper resources, using API-key headers or OAuth. Detailed resource coverage includes core CRM entities, but this assessment does not infer unlisted APIs or count endpoints; plan entitlement remains unresolved."` | `"Copper's Developer API is a RESTful JSON interface for most CRM resources. The separate documented Webhooks interface supports subscriptions for near-real-time create/update/delete notifications on supported entities, HTTPS endpoints, up to 100 active subscriptions and stated delivery limits; this is not described as a general REST Webhooks API."` | supplemental | api_scope_detail_added | Clarify the distinct documented interface and its limits: The official overview describes URL subscriptions, event/entity types, HTTPS delivery, subscription/rate limits and no delivery retries. |
| Freshdesk | `api.details` | `"The official REST v2 reference documents ticket CRUD, conversations/replies, contacts, companies, agents, ticket fields/forms, and other helpdesk resources. API quotas are plan-based. The separate official MCP surface is an API-key-authenticated agent interface, not a separate REST API type."` | `"The official REST v2 reference documents ticket CRUD, conversations/replies, contacts, companies, agents, ticket fields/forms and other helpdesk resources; quotas are plan-based. Freshdesk automation rules also support outbound webhook actions to external URLs for ticket events. This is webhook-enabled automation, not a separately documented Webhooks API, so api.types remains REST."` | supplemental | outbound_webhook_capability_clarified | Clarify the directly documented outbound HTTP/webhook behavior without mislabeling it as a dedicated Webhooks API or adding Webhooks to api.types. |
| Amazon Selling Partner | `mcp.details` | `"No first-party MCP status assigned in the pilot first pass; targeted official-source MCP search is required before classifying absence."` | `"Amazon's selling-partner-api-samples repository contains a first-party Local MCP for SP-API educational example. It is explicitly not a supported product in its own right and is not a hosted Amazon MCP service. Most local developer-assistance tools work without SP-API credentials; tools that execute live SP-API requests or workflows require SP-API credentials."` | supplemental | mcp_scope_omission | The first-pass detail did not distinguish the first-party local educational sample from a supported hosted Amazon MCP product or state which tools require SP-API credentials. |
| Amazon Selling Partner | `mcp.search_scope` | `"Incomplete in first pass; not evidence of no MCP."` | `"Opened Amazon's first-party Local MCP for SP-API README. It documents installation/client setup and states the repository example is educational and unsupported as a product; some developer tools are local while live SP-API calls require credentials. No Amazon-hosted MCP service is inferred."` | supplemental | source_scope_detail_added | Replace the incomplete first-pass MCP search note with the directly inspected first-party example and its limitations. |
| Copper | `mcp.search_scope` | `"Opened Copper's developer/API documentation, API-key and OAuth guides, pricing page, and targeted official-domain MCP searches; no official MCP page/repository was verified, and no exhaustive first-party repo/catalog audit was completed."` | `"Opened Copper's official Developer API landing page, authentication/OAuth material and webhook overview, and ran a targeted official-domain MCP search. The opened pages establish REST, OAuth/API-key and webhook surfaces but do not establish MCP ownership or absence. Search was bounded; status remains UNKNOWN."` | supplemental | bounded_search_limitation_documented | Record the actual bounded source scope while preserving UNKNOWN rather than treating an empty search as NOT_FOUND. |
| NotebookLM | `mcp.search_scope` | `"Opened Google Cloud NotebookLM Enterprise notebook/source API, setup and licensing documentation and ran a targeted first-party Google Cloud search for NotebookLM MCP/Model Context Protocol. The returned official materials did not establish a product-specific MCP; status remains UNKNOWN, not NO."` | `"Opened Google Cloud NotebookLM Enterprise API, setup and licensing documentation and ran a targeted first-party Google Cloud search for NotebookLM MCP/Model Context Protocol. Search results included generic Google Cloud MCP references but no NotebookLM Enterprise-specific endpoint/setup; generic services are not attributed to NotebookLM. Status remains UNKNOWN, not NO."` | supplemental | bounded_search_limitation_documented | Update the search-scope note with the fresh targeted official-source search and explicitly keep generic Google Cloud MCP references separate. |

## Field-level provenance

See `data/verified/final_verification_ledger.json` for every sample initial value, verified value, source URL/title, method, reason, correction, verifier type, evidence patch, and joined post-recheck. `data/raw/final_full_research.json` remains unchanged.

## Human verification status

No human inspection, signup, authenticated tenant test, admin approval, or credential test is claimed. The final sample's required human/account checks are recorded as HUMAN VERIFICATION NOT POSSIBLE in `reports/human_qa.md` and `data/evidence/human_qa_template.csv`: no authorized vendor tenant/credentials or reviewer were provided. This is not a completed human QA pass; the row-level checklists are retained for a future authorized review.

## Final quality-gate audit

- **Status:** WARN; warnings: 26; blocking errors: 0.
- The complete corrected-dataset warning list is retained in `data/verified/final_quality_report.json` and each record's `quality_gate` field. The first-pass run audit remains separate in `data/raw/final_full_quality_report.json`.

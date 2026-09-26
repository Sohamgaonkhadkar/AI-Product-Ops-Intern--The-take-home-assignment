# Observed verification errors and corrections

This report includes only rows actually changed by the final sample verification ledger. Critical label mismatches are separated from supplemental detail/scope changes; no hypothetical error is counted.

- Critical first-pass mismatches: **3**.
- Supplemental observed changes: **9**.
- Critical post-correction recheck: `correct=3, checked=3, incorrect=0, conflicts=0, unresolved=0, not_rechecked=103`.
- All changed rows rechecked: `correct=12, checked=12, incorrect=0, conflicts=0, unresolved=0, critical_rows=3, supplemental_rows=9`.

## API interface omission (`api_interface_omission`) — 2 row(s)

**Observed cause:** The first-pass api.types list omitted the directly documented SOAP interface. The current SOAP API guide lists Enterprise, Performance, Unlimited and Developer Editions and the API Enabled permission.

**Prevention:** Enumerate separately documented interfaces and webhooks/SOAP/GraphQL/SDK distinctions; do not assume the REST guide is the complete API surface.

## API scope/detail completeness change (`api_scope_detail_added`) — 2 row(s)

**Observed cause:** Clarify the distinct documented interface and its limits: The current SOAP API guide lists Enterprise, Performance, Unlimited and Developer Editions and the API Enabled permission.

**Prevention:** Add an interface-completeness checklist to supplemental API review and ensure `api.types` changes are reflected in `api.details` with their exact limits.

## Authentication-method omission (`auth_method_omission`) — 1 row(s)

**Observed cause:** Attio's directly inspected authentication guide documents OAuth 2.0, API-key tokens, Bearer authorization and HTTP Basic with the token as username and an empty password; the first pass omitted Basic.

**Prevention:** Inspect the dedicated authentication guide and enumerate every documented wire-level method (including alternate HTTP authorization schemes) before normalizing the list.

## Bounded MCP-search limitation clarified (`bounded_search_limitation_documented`) — 2 row(s)

**Observed cause:** Record the actual bounded source scope while preserving UNKNOWN rather than treating an empty search as NOT_FOUND.

**Prevention:** Use bounded-scope language for inconclusive official searches and keep UNKNOWN unless authoritative evidence supports availability or a scoped NOT_FOUND classification.

## Credential-path conflation (`credential_path_conflation`) — 1 row(s)

**Observed cause:** Attio's Free plan and first-party hosted-MCP OAuth path establish a self-serve route, while workspace API-key creation is admin-only. The first-pass ADMIN_APPROVAL_REQUIRED label overgeneralized the API-key path.

**Prevention:** Model API-key, OAuth/MCP, and admin-issued paths separately; determine the record-level self-serve label from all viable documented paths rather than one credential route.

## First-pass MCP false negative / unresolved value (`mcp_false_negative`) — 1 row(s)

**Observed cause:** Amazon's own repository directly documents a Local MCP for SP-API educational example. This establishes a first-party local MCP example, not a supported hosted Amazon MCP product; the first pass left MCP unclassified.

**Prevention:** Add a targeted first-party MCP discovery checklist and inspect first-party repositories/indexes; distinguish local examples, hosted products, and unsupported samples in separate fields.

## MCP product-versus-sample scope omission (`mcp_scope_omission`) — 1 row(s)

**Observed cause:** The first-pass detail did not distinguish the first-party local educational sample from a supported hosted Amazon MCP product or state which tools require SP-API credentials.

**Prevention:** Separate MCP presence from product support/hosting and credential requirements; quote repository caveats in the claim rather than collapsing them into a single availability label.

## Outbound webhook capability clarified (`outbound_webhook_capability_clarified`) — 1 row(s)

**Observed cause:** Clarify the directly documented outbound HTTP/webhook behavior without mislabeling it as a dedicated Webhooks API or adding Webhooks to api.types.

**Prevention:** Keep outbound webhook/HTTP automation distinct from a product's dedicated webhook-management API; verify both the main REST reference and automation guide before describing it.

## Search/evidence scope note updated (`source_scope_detail_added`) — 1 row(s)

**Observed cause:** Replace the incomplete first-pass MCP search note with the directly inspected first-party example and its limitations.

**Prevention:** Persist search/opened-page scope in the first-pass record and update it only from directly inspected pages; retain partial extraction limitations.

## Row-level examples

| App | Field | First pass | Verified | Type | Cause / evidence basis | Correction | Source(s) | Post-recheck |
|---|---|---|---|---|---|---|---|---|
| Amazon Selling Partner | `mcp.status` | `"UNKNOWN"` | `"AVAILABLE"` | `mcp_false_negative` | Amazon's own repository directly documents a Local MCP for SP-API educational example. This establishes a first-party local MCP example, not a supported hosted Amazon MCP product; the first pass left MCP unclassified. | Set AVAILABLE for the documented first-party local example and preserve the explicit unsupported-product/hosted-service limitation. | [1](https://github.com/amzn/selling-partner-api-samples/blob/main/use-cases/sp-api-dev-mcp/README.md) | CORRECT (FRESH_REINSPECTION) |
| Attio | `auth_methods` | `["OAuth 2.0", "API key", "Bearer/token"]` | `["OAuth 2.0", "API key", "Bearer/token", "Basic"]` | `auth_method_omission` | Attio's directly inspected authentication guide documents OAuth 2.0, API-key tokens, Bearer authorization and HTTP Basic with the token as username and an empty password; the first pass omitted Basic. | Add the directly documented Basic method while preserving the first-pass value in the raw dataset. | [1](https://docs.attio.com/rest-api/guides/authentication) | CORRECT (FRESH_REINSPECTION) |
| Attio | `self_serve_status` | `"ADMIN_APPROVAL_REQUIRED"` | `"SELF_SERVE_WITH_RESTRICTIONS"` | `credential_path_conflation` | Attio's Free plan and first-party hosted-MCP OAuth path establish a self-serve route, while workspace API-key creation is admin-only. The first-pass ADMIN_APPROVAL_REQUIRED label overgeneralized the API-key path. | Change to SELF_SERVE_WITH_RESTRICTIONS and retain the admin-only API-key condition. | [1](https://attio.com/pricing), [2](https://docs.attio.com/mcp/overview), [3](https://attio.com/help/reference/apps/generating-an-api-key) | CORRECT (FRESH_REINSPECTION) |
| Salesforce | `api.types` | `["REST"]` | `["REST", "SOAP"]` | `api_interface_omission` | The first-pass api.types list omitted the directly documented SOAP interface. The current SOAP API guide lists Enterprise, Performance, Unlimited and Developer Editions and the API Enabled permission. | Add SOAP while preserving all first-pass API types. | [1](https://developer.salesforce.com/docs/platform/api/guide/sforce-api-quickstart-intro.html), [2](https://developer.salesforce.com/docs/platform/api-rest/guide/intro-what-is-rest-api.html) | CORRECT (FRESH_REINSPECTION) |
| Salesforce | `api.details` | `"Official REST API supports create/manipulate/search of Salesforce records and access to query results, metadata, and other resources; Bulk, Metadata, and Connect REST APIs cover additional jobs. No endpoint count estimated."` | `"Salesforce REST API supports records, query results, metadata and additional resources; the SOAP API is separately documented for Enterprise, Performance, Unlimited and Developer editions, subject to API Enabled permission. No endpoint count is estimated."` | `api_scope_detail_added` | Clarify the distinct documented interface and its limits: The current SOAP API guide lists Enterprise, Performance, Unlimited and Developer Editions and the API Enabled permission. | Update API detail to explain the added interface; the raw first-pass detail remains unchanged. | [1](https://developer.salesforce.com/docs/platform/api/guide/sforce-api-quickstart-intro.html), [2](https://developer.salesforce.com/docs/platform/api-rest/guide/intro-what-is-rest-api.html) | CORRECT (FRESH_REINSPECTION) |
| Copper | `api.types` | `["REST"]` | `["REST", "Webhooks"]` | `api_interface_omission` | The first-pass api.types list omitted the directly documented Webhooks interface. The official overview describes URL subscriptions, event/entity types, HTTPS delivery, subscription/rate limits and no delivery retries. | Add Webhooks while preserving all first-pass API types. | [1](https://developer.copper.com/webhooks/overview.html), [2](https://developer.copper.com/) | CORRECT (FRESH_REINSPECTION) |
| Copper | `api.details` | `"Copper's official Developer API is a REST/JSON interface for most Copper resources, using API-key headers or OAuth. Detailed resource coverage includes core CRM entities, but this assessment does not infer unlisted APIs or count endpoints; plan entitlement remains unresolved."` | `"Copper's Developer API is a RESTful JSON interface for most CRM resources. The separate documented Webhooks interface supports subscriptions for near-real-time create/update/delete notifications on supported entities, HTTPS endpoints, up to 100 active subscriptions and stated delivery limits; this is not described as a general REST Webhooks API."` | `api_scope_detail_added` | Clarify the distinct documented interface and its limits: The official overview describes URL subscriptions, event/entity types, HTTPS delivery, subscription/rate limits and no delivery retries. | Update API detail to explain the added interface; the raw first-pass detail remains unchanged. | [1](https://developer.copper.com/webhooks/overview.html), [2](https://developer.copper.com/) | CORRECT (FRESH_REINSPECTION) |
| Freshdesk | `api.details` | `"The official REST v2 reference documents ticket CRUD, conversations/replies, contacts, companies, agents, ticket fields/forms, and other helpdesk resources. API quotas are plan-based. The separate official MCP surface is an API-key-authenticated agent interface, not a separate REST API type."` | `"The official REST v2 reference documents ticket CRUD, conversations/replies, contacts, companies, agents, ticket fields/forms and other helpdesk resources; quotas are plan-based. Freshdesk automation rules also support outbound webhook actions to external URLs for ticket events. This is webhook-enabled automation, not a separately documented Webhooks API, so api.types remains REST."` | `outbound_webhook_capability_clarified` | Clarify the directly documented outbound HTTP/webhook behavior without mislabeling it as a dedicated Webhooks API or adding Webhooks to api.types. | Update the corrected narrative/scope; raw first-pass text remains unchanged. | [1](https://support.freshdesk.com/support/solutions/articles/132589-using-webhooks-in-automation-rules), [2](https://support.freshdesk.com/support/solutions/articles/50000009511-automation-examples-using-webhooks), [3](https://developer.freshdesk.com/api/) | CORRECT (FRESH_REINSPECTION) |
| Amazon Selling Partner | `mcp.details` | `"No first-party MCP status assigned in the pilot first pass; targeted official-source MCP search is required before classifying absence."` | `"Amazon's selling-partner-api-samples repository contains a first-party Local MCP for SP-API educational example. It is explicitly not a supported product in its own right and is not a hosted Amazon MCP service. Most local developer-assistance tools work without SP-API credentials; tools that execute live SP-API requests or workflows require SP-API credentials."` | `mcp_scope_omission` | The first-pass detail did not distinguish the first-party local educational sample from a supported hosted Amazon MCP product or state which tools require SP-API credentials. | Update the corrected narrative/scope; raw first-pass text remains unchanged. | [1](https://github.com/amzn/selling-partner-api-samples/blob/main/use-cases/sp-api-dev-mcp/README.md) | CORRECT (FRESH_REINSPECTION) |
| Amazon Selling Partner | `mcp.search_scope` | `"Incomplete in first pass; not evidence of no MCP."` | `"Opened Amazon's first-party Local MCP for SP-API README. It documents installation/client setup and states the repository example is educational and unsupported as a product; some developer tools are local while live SP-API calls require credentials. No Amazon-hosted MCP service is inferred."` | `source_scope_detail_added` | Replace the incomplete first-pass MCP search note with the directly inspected first-party example and its limitations. | Update the corrected narrative/scope; raw first-pass text remains unchanged. | [1](https://github.com/amzn/selling-partner-api-samples/blob/main/use-cases/sp-api-dev-mcp/README.md) | CORRECT (FRESH_REINSPECTION) |
| Copper | `mcp.search_scope` | `"Opened Copper's developer/API documentation, API-key and OAuth guides, pricing page, and targeted official-domain MCP searches; no official MCP page/repository was verified, and no exhaustive first-party repo/catalog audit was completed."` | `"Opened Copper's official Developer API landing page, authentication/OAuth material and webhook overview, and ran a targeted official-domain MCP search. The opened pages establish REST, OAuth/API-key and webhook surfaces but do not establish MCP ownership or absence. Search was bounded; status remains UNKNOWN."` | `bounded_search_limitation_documented` | Record the actual bounded source scope while preserving UNKNOWN rather than treating an empty search as NOT_FOUND. | Update the corrected narrative/scope; raw first-pass text remains unchanged. | [1](https://developer.copper.com/), [2](https://developer.copper.com/webhooks/overview.html), [3](https://developer.copper.com/introduction/oauth/quickstart.html) | CORRECT (FRESH_REINSPECTION) |
| NotebookLM | `mcp.search_scope` | `"Opened Google Cloud NotebookLM Enterprise notebook/source API, setup and licensing documentation and ran a targeted first-party Google Cloud search for NotebookLM MCP/Model Context Protocol. The returned official materials did not establish a product-specific MCP; status remains UNKNOWN, not NO."` | `"Opened Google Cloud NotebookLM Enterprise API, setup and licensing documentation and ran a targeted first-party Google Cloud search for NotebookLM MCP/Model Context Protocol. Search results included generic Google Cloud MCP references but no NotebookLM Enterprise-specific endpoint/setup; generic services are not attributed to NotebookLM. Status remains UNKNOWN, not NO."` | `bounded_search_limitation_documented` | Update the search-scope note with the fresh targeted official-source search and explicitly keep generic Google Cloud MCP references separate. | Update the corrected narrative/scope; raw first-pass text remains unchanged. | [1](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks), [2](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm), [3](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-licensing) | CORRECT (FRESH_REINSPECTION) |

No person performed these checks. This is automated/source-assisted verification and is not a human review record.

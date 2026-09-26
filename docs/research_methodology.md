# Research methodology and field decision rules

## Scope and unit of research

One record represents one app in the assignment manifest. Research is about a developer's ability to build an agent-callable integration, not merely whether a marketing page mentions an API. The app name/category/source hint comes from `apps/apps.json`. App-level conclusions must be grounded in claim-specific evidence and carry their own uncertainty.

## Evidence protocol

1. Search the official developer site and official API/auth/support/pricing sources first. The assignment's URL is a discovery hint, not automatic proof.
2. Open the source page where possible. A search snippet is a lead only; it is not evidence for a final claim.
3. Attach evidence to a specific field and claim. The claim should state exactly what the page supports; keep a concise excerpt or observation and retrieval timestamp.
4. Prefer current first-party sources. Record source title, canonical URL, source type, and access date. Do not turn a generic home page into evidence for OAuth, free credentials, API breadth, or MCP.
5. If evidence is inaccessible, preserve the URL and record an access limitation; do not pretend it was read. If sources disagree, preserve both claims and document which is more authoritative/current and why.
6. Third-party/community evidence is secondary and labeled as such. It cannot alone establish a sensitive negative or a first-party MCP claim.

Priority: official developer docs/API reference → official auth docs → official support/plan docs → first-party GitHub → official product/pricing pages → reputable secondary sources → community.

## Provenance and capture modes

Keep the first-pass record, evidence/capture trace, verification observations, and corrected record as separate artifacts. Do not overwrite raw first-pass values. The final manifest must retain one record and one attempt trace per manifest app, including apps that were not researched.

- `PRIOR_CAPTURE` means a historical capture is being replayed/assembled; it is not a fresh run.
- `LIVE_AGENT` means genuine current first-pass research using a live agent tool, with the actual tool, queries, source URLs/titles/types, retrieval dates/precision, extraction attempts, errors, retries, and final records preserved as observed. For the 76 rows in this baseline, this was native Arena.ai `web_search`/`fetch_page`, not a Tavily/OpenAI provider-backed execution. Do not collapse the specific tool/provenance into the enum alone.
- `NOT_RUN` is an explicit placeholder when no research attempt was made. All product facts remain `UNKNOWN`; this does not mean NO or NOT_FOUND.
- `LIVE_AGENT_WEB_REINSPECTION` identifies fresh verification-source inspection and does not change a `PRIOR_CAPTURE` first-pass label.
- Preserve query/source/attempt data separately from claim-level evidence. Search snippets are discovery only. Do not invent missing timestamps, attempts, retries, or sources; label inherited/missing trace fields and timestamp precision explicitly.
- If required provider credentials are absent, fail closed, keep live-capable architecture, preserve all manifest IDs, and report the blocker. Do not substitute a capture replay and call it live research.

## Field rules

### Category and one-line description

Use the assignment's category unchanged. Describe the app's core product in one factual sentence, ideally from an official product/about page; if unavailable, use `Unknown` and explain the gap. Do not infer a feature just from the app name.

### Authentication (`auth_status`, `auth_methods`)

Controlled values: `OAuth 2.0`, `API key`, `Bearer/token`, `Basic`, `Service account`, `Custom`, `Other`.

- Record a method only when official auth/API docs (or a first-party implementation guide) identify it for the relevant API.
- Multiple documented methods may coexist; list all supported methods and cite each claim.
- Distinguish authentication from authorization/scopes, session login, and API-key management.
- Do not infer API auth from an SDK sample or a generic login page when the official docs specify otherwise.
- `CONFIRMED`: relevant method(s) supported by direct evidence. `PARTIAL`: some flow is known but coverage is incomplete or alternatives are unclear. `UNKNOWN`: no reliable method identified; leave `auth_methods` empty rather than guessing.

### Self-serve and credential access

`self_serve_status` is one of `SELF_SERVE`, `SELF_SERVE_WITH_RESTRICTIONS`, `PAID_PLAN_REQUIRED`, `ADMIN_APPROVAL_REQUIRED`, `PARTNER_OR_CONTACT_SALES`, `ENTERPRISE_ONLY`, `UNKNOWN`.

- Establish a credential-creation path from docs/support/pricing/admin instructions, not from API docs alone.
- `SELF_SERVE`: a developer/admin can create credentials without paid-plan, sales, partner, or external approval; free or trial availability should be stated when evidenced.
- `SELF_SERVE_WITH_RESTRICTIONS`: credentials can be obtained but material restrictions apply (limited scopes, review for certain uses, trial/plan limits, or API access limitations).
- `PAID_PLAN_REQUIRED`: the documented credential/API access needed for the relevant integration requires a paid subscription.
- `ADMIN_APPROVAL_REQUIRED`: an org/workspace administrator must authorize the integration or issue credentials.
- `PARTNER_OR_CONTACT_SALES`: explicit partner approval, application, contact-sales, or commercial onboarding is required.
- `ENTERPRISE_ONLY`: relevant API access is explicitly limited to an enterprise tier; retain the access path and supporting evidence.
- `UNKNOWN`: evidence does not establish credential access. Never equate "public API docs" with freely obtainable credentials.
- If requirements vary by API, plan, or use case, name the exact condition and use the most restrictive status that blocks the evaluated general-purpose build, while documenting alternatives/conflicts.

The `credential_access` sub-object separately captures a plain-language path and plan/gate so an enum cannot hide nuance.

### API availability, type, and breadth

`api.available` is `YES`, `NO`, or `UNKNOWN` (rather than a boolean so unknown is not silently treated as false). Interface types: `REST`, `GraphQL`, `SDK`, `Webhooks`, `SOAP`, `RPC`, `CLI`, `Other`.

- Count an interface only when official documentation describes it for the app/API. SDKs/webhooks/CLI are not silently called REST endpoints.
- Distinguish a documented standalone Webhooks API or webhook-management API from outbound webhook/HTTP automation. Freshdesk's corrected selected-sample record describes outbound automation while retaining `api.types=REST`. A separate Gorgias terminology audit in `data/evidence/api_webhook_nomenclature_audit.json` (outside the 20-app accuracy sample) records outbound HTTP/webhook actions and keeps REST; it does not alter the current final Gorgias record or sample metrics. Neither is counted as a dedicated Webhooks API type.
- `NO` requires affirmative evidence that there is no public/developer API relevant to the product, or an authoritative product statement of non-availability. If coverage was not enough to establish absence, use `UNKNOWN`.
- Do not invent endpoint counts. Qualitative breadth is based on distinct documented resource/domain areas and supported operations, not page count.
- `BROAD`: docs cover multiple core resource families and meaningful read/write or equivalent operations across them.
- `MODERATE`: useful integration surface, but restricted to a subset of core resources, use cases, or operations.
- `NARROW`: a focused/single-purpose or materially limited surface.
- `UNKNOWN`: evidence is too sparse to assess. Every non-unknown breadth judgment must name the documented resource areas and limitation in `api.details`.

### MCP (`mcp.status`)

Values: `AVAILABLE`, `NOT_FOUND`, `UNKNOWN`.

- `AVAILABLE` only with direct first-party evidence: official MCP documentation, first-party server/repository, or a clearly documented first-party MCP integration. Capture repository ownership or official docs path. A third-party wrapper is not first-party availability and should be described separately in notes if relevant.
- `NOT_FOUND` means targeted inspection of the official developer docs/product documentation and the relevant first-party repository/index (where one is discoverable) found no first-party MCP offer. It is a bounded search result, **not proof no MCP can exist**. Record exactly what was inspected in `search_scope`; confidence may remain medium/low.
- `UNKNOWN` when the official-source search was incomplete, pages were inaccessible, ownership/status is unclear, or first-party versus third-party could not be resolved.
- An API or an LLM assertion is never sufficient evidence for MCP.

### Buildability (`buildability`)

Verdicts: `BUILDABLE_NOW`, `BUILDABLE_WITH_CONSTRAINTS`, `OUTREACH_REQUIRED`, `NOT_REALISTIC_TODAY`, `UNKNOWN`.

Apply in order and record a short rationale that references the component facts:

1. `OUTREACH_REQUIRED` when the relevant integration is gated by explicit partner/contact-sales/enterprise approval and no self-serve path adequate for a general integration is documented.
2. `NOT_REALISTIC_TODAY` when authoritative evidence indicates no relevant API or a technical restriction makes an agent toolkit infeasible; do not use merely because evidence is missing.
3. `UNKNOWN` when API, credentials, or key requirements remain too uncertain to make a defensible assessment.
4. `BUILDABLE_WITH_CONSTRAINTS` when a usable API/credential path exists but material scope, plan, admin approval, rate/permission, limited-surface, unusual-auth, or user-consent constraints shape the integration.
5. `BUILDABLE_NOW` when there is a usable documented API, practical credential path, adequate breadth for core agent actions, and no major approval/access barrier. This is a research verdict, not a guarantee of implementation effort.

`blocker` names the main documented obstacle; use `None identified in reviewed sources` only when the sources adequately cover access and API conditions. If unknown, say what remains unknown instead of asserting no blocker.

### Confidence and record completion

Confidence summarizes evidence quality, not model certainty:
- `HIGH`: direct, current first-party sources cover the decisive claim(s), with no unresolved conflict.
- `MEDIUM`: mostly first-party but some key nuance is indirect, conditional, or incompletely documented.
- `LOW`: evidence is sparse, inaccessible, secondary, or conflicting.

`research_status`: `COMPLETE` means required fields were assessed and important claims have evidence or explicit unknown rationale; `PARTIAL` means some fields/evidence remain incomplete; `FAILED` means no usable app-level research could be completed. A research record can be complete while one field is `UNKNOWN` if the search was documented and the unknown is genuinely unresolved.

## Easy wins vs. outreach: analysis rule

For aggregate presentation, apply the implemented deterministic rule only to records marked `AUTO_VERIFIED` with all six critical facts resolved and a non-empty documented `auth_methods` value:

- **Easy win:** API `YES`; credential access `SELF_SERVE`; auth is documented; API breadth is `BROAD` or `MODERATE`; buildability `BUILDABLE_NOW`; no explicit partner/contact-sales, enterprise-only, or paid-plan gate.
- **Outreach:** explicit `PARTNER_OR_CONTACT_SALES`, `ENTERPRISE_ONLY`, `PAID_PLAN_REQUIRED`, or `OUTREACH_REQUIRED`.
- **Constrained:** a fully verified known combination that meets neither Easy-win nor Outreach.
- **Needs review:** `MIXED`, `NOT_CHECKED`, any unresolved/`UNKNOWN` critical value, or missing auth methods. Incomplete records stay counted as `NEEDS_REVIEW`; they are never automatically classified as Easy-win or Outreach.

API `NO` by itself is not an outreach path. Admin approval/restricted credentials alone do not automatically count as sales outreach.

Publish the rule and number of unknown/unclassified cases with the result. Do not rank apps by subjective enthusiasm.

## Schema and validation

`schemas/research-record.schema.json` is the strict field contract. The app-level record follows the requested shape while adding explicit tri-state fields, credential-path detail, MCP search scope, buildability rationale, claim-to-source links, source conflicts, and limitations. The additions prevent absence-of-evidence from being presented as a negative. Every important claim has its own evidence item; a single generic URL cannot certify every field.

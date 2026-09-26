# Human QA status — 2026-09-25

## Outcome

**HUMAN VERIFICATION NOT POSSIBLE.** No authorized vendor tenant, account credentials, or human reviewer with account access was provided in the workspace. No signup, API call, MCP session, credential creation, package installation, or human review was performed. This is a recorded blocker—not a completed human QA pass and not a claim that product documentation is wrong.

The automated/source-assisted page checks are separate from human/tenant QA. For the final sample, `data/evidence/human_qa_template.csv` contains **120 rows** (six critical checks × 20 apps). Every row is explicitly marked `HUMAN VERIFICATION NOT POSSIBLE`, with a reason, concrete checklist, current public-source value, and source links. Reviewer, date, human result, correction, and review notes remain blank. No secret belongs in the template.

The final sample is the reproducible, post-research coverage sample (seed `20260924`): **22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9**. Its first-pass records have mixed provenance (14 `LIVE_AGENT`, 6 `PRIOR_CAPTURE`); it is not a probability sample. Full first-pass provenance remains 76 `LIVE_AGENT` and 24 `PRIOR_CAPTURE`.

## Reasons that require specific care

- **ID84 — Paygent Connect:** product identity is unresolved. The Paygent Japan and NMI pages in the CSV are explicitly *candidate identity context only*, not evidence attributable to ID84. Do not select an account or test a candidate product until the user or a first-party identity link resolves which product the manifest means. All six product-specific critical fields remain `UNKNOWN`.
- **ID27 — Telegram:** the current source review confirmed only the TDLib self-hosted HTTP Bot API requirement (`api_id`/`api_hash`). Official Telegram core pages returned HTTP 403; cloud bot-token onboarding, account/plan gates, and first-party MCP facts are not fully established. Do not turn these unknowns into `NO`.
- **ID23 — Zoho Cliq authentication:** the current REST/OAuth page extraction rendered a navigation shell and “No Results Found.” Its old raw OAuth/bearer observation remains historical first-pass evidence, not a fresh detailed-auth confirmation.
- **ID9 — Copper MCP and ID91 — NotebookLM Enterprise MCP:** bounded official-source research did not establish product-specific availability or absence. Keep `UNKNOWN`; generic search results or a missing result do not establish `NO`.
- **ID98 — Mermaid CLI:** a local CLI is documented, but no human reviewed an installation/render in a clean Node.js environment. This is a package/runtime check, not an account entitlement.
- Other rows still need an authorized human to confirm applicable tenant edition, plan, role, permissions, approvals, and product-specific setup. Public API documentation does not prove that a target tenant has access.

## Final-sample checklist

The CSV supplies field-specific steps on every row. In brief:

| Field | Required human check (only with authorization) |
|---|---|
| `auth_methods` | Confirm the documented method applies to the relevant API/version and any target-organization authentication policy. Never paste a secret. |
| `self_serve_status` | Confirm the actual signup/trial/plan route, regional limits, payment, admin, partner, or sales gates; distinguish product signup from API/MCP entitlement. |
| `credential_access.status` | Confirm the real role, credential-generation/consent path, scopes, expiry, and approval gates; record no key, password, OAuth code, or token. |
| `api.available` | Confirm API enablement for the target tenant/edition/plan, required permissions, developer-token/access levels, and relevant quotas. A public reference alone is insufficient. |
| `mcp.status` | Confirm first-party endpoint, setup, account/plan/client prerequisites, and tool access. Keep `UNKNOWN` when evidence does not establish presence or absence. |
| `buildability.verdict` | Re-evaluate API, auth, plan, role, approval, policy, security, and runtime constraints in the actual environment; claim no build/test unless executed. |

## Earlier five-app engineering pilot

The earlier pilot checklist remains part of the project and has the same outcome: **HUMAN VERIFICATION NOT POSSIBLE** for all five app-specific checks below. No pilot account was supplied. The authorized reviewer should perform only the checks relevant to the intended tenant and record evidence/results in a future update.

| App | Specific human check and checklist | Status / reason |
|---|---|---|
| Salesforce | Check the target org's edition and `API Enabled` permission; confirm External Client App/OAuth setup in that tenant. Ask the org owner/account team about Hosted MCP intended audience (“intended only for customers with Flex Credits”) and billing. Do not infer a technical prerequisite from that wording alone. Evidence: [Supported Editions and Required Permissions](https://developer.salesforce.com/docs/platform/api-rest/guide/intro-rest-compatible-editions.html), [OAuth and External Client Apps](https://developer.salesforce.com/docs/platform/api-rest/guide/intro-oauth-and-connected-apps.html), [Hosted MCP Billing](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide). | **HUMAN VERIFICATION NOT POSSIBLE** — no authorized Salesforce org owner/reviewer or tenant was provided. |
| Twilio | In an authorized trial account, confirm signup verification, regional/recipient restrictions, product units, credential-creation path, and upgrade requirements. Do not infer production cost or enablement from trial status. Evidence: [Twilio trial account](https://www.twilio.com/docs/usage/trials), [API keys in Console](https://www.twilio.com/docs/iam/api-keys/keys-in-console), [Twilio MCP Public Beta](https://www.twilio.com/docs/ai/mcp). | **HUMAN VERIFICATION NOT POSSIBLE** — no authorized Twilio account/reviewer was provided. |
| Amazon Selling Partner | In an authorized Solution Provider Portal, confirm public developer-profile/role review, app listing, private-app route, and PII security-review needs. If evaluating the local educational MCP example, review security/support posture and test only with approved credentials. No package was installed or run in this project. Evidence: [Public developer registration](https://developer-docs.amazon.com/sp-api/docs/register-as-a-public-developer), [Production application registration](https://developer-docs.amazon.com/sp-api/docs/onboarding-step-7-register-your-first-production-application), [Local MCP sample](https://github.com/amzn/selling-partner-api-samples/blob/main/use-cases/sp-api-dev-mcp/README.md). | **HUMAN VERIFICATION NOT POSSIBLE** — no authorized selling-partner account/reviewer was provided. |
| GitHub | Check the target organization’s PAT/OAuth/MCP policies, SAML SSO requirements, app installation approval, and plan requirements for selected tools. Evidence: [PAT management and organization approval](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens), [GitHub MCP Server setup](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp-in-your-ide/set-up-the-github-mcp-server). | **HUMAN VERIFICATION NOT POSSIBLE** — no authorized GitHub organization/reviewer was provided. |
| Otter AI | In an authorized Enterprise workspace, confirm Public API enablement, API-key access, Super Admin role/enablement for workspace endpoints, and supported MCP client/plan behavior. Evidence: [Otter Public API](https://help.otter.ai/hc/en-us/articles/36130822688279-Otter-ai-Public-API), [Super Admin APIs](https://help.otter.ai/hc/en-us/articles/39661865499799-Super-Admin-APIs), [Otter MCP Server](https://help.otter.ai/hc/en-us/articles/35287607569687-Otter-MCP-Server). | **HUMAN VERIFICATION NOT POSSIBLE** — no authorized Otter Enterprise workspace/reviewer was provided. |

## Reviewer record and boundary

No reviewer, date, human result, or correction is recorded. The project contains no claim of human verification, tenant signup, authorized API/MCP operation, or account-specific entitlement. If access is later supplied, update only the relevant row after the person actually performs the check; retain unknowns, explain any correction, and never store credentials or customer data.

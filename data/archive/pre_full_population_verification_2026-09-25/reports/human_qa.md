# Human QA preparation — final sample and engineering pilot

**Status: PENDING. No person has inspected these records or tested an app account in this workspace.** All completed verification so far is automated/source-assisted public-document review. Do not treat this checklist or its blank template as completed review.

## Final selected sample: pending human checks

- Selected IDs: **22, 49, 92, 4, 13, 61, 15, 14, 1, 9, 3, 5, 16, 6, 12, 8, 11, 2, 10, 19** (20 apps; seed `20260924`).
- This selection is from the 24 `PRIOR_CAPTURE` records only and is **not representative of all 100 manifest apps**; 76 apps remain `NOT_RUN`.
- `data/evidence/human_qa_template.csv` contains 120 blank `PENDING` rows: six critical fields for each selected app. It pre-populates the preserved first-pass value, current verified value, field-specific account/tenant action, and official evidence URLs/titles. `reviewer`, `review_date`, `human_result`, `correction`, and `review_notes` are blank.
- A row may be changed from `PENDING` only after a person actually performs the check. Record reviewer, date, app ID/name, field, evidence inspected, result, and any correction. Do not infer results from a public API page or from the automated verification ledger.

### Check instructions

For each assigned row, use an authorized tenant and the least-privileged access available. Confirm the current plan/edition, permissions, account role, credential path, and relevant API/MCP feature only when those are material to the claim. Record source links or non-sensitive evidence. Never commit passwords, API keys, refresh tokens, seller/customer data, or other secrets. If the reviewer lacks access, record `UNRESOLVED` and state the missing authorization; do not substitute a guess.

The template covers:

- **Authentication methods:** whether documented API methods apply to the target API/version and org policy.
- **Self-serve status:** current signup/trial/plan availability and any admin, paid, partner, or sales gate.
- **Credential access:** actual role and credential-generation path, including scope/approval restrictions.
- **API availability:** whether API access is enabled for the target tenant/edition/plan.
- **MCP:** current first-party endpoint/setup and client/provider-plan requirements; an unknown result is not proof of absence.
- **Buildability:** whether actual tenant permissions and operating constraints preserve the published verdict/blocker.

## Earlier five-app pilot checks retained

The following pilot-specific account checks remain pending and should be performed only by an authorized account owner/reviewer:

| App | Pending human check | Evidence to inspect | Status |
|---|---|---|---|
| Salesforce | Confirm the target org's edition and `API Enabled` permission; confirm External Client App/OAuth setup can be completed in that tenant. Ask the org owner/account team whether the customer is within Hosted MCP's documented intended audience (“intended only for customers with Flex Credits”) and what usage billing applies. Do not treat that audience wording alone as proof of a technical or credential prerequisite. | [Supported Editions and Required Permissions](https://developer.salesforce.com/docs/platform/api-rest/guide/intro-rest-compatible-editions.html); [OAuth and External Client Apps](https://developer.salesforce.com/docs/platform/api-rest/guide/intro-oauth-and-connected-apps.html); [Hosted MCP Billing](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide) | PENDING |
| Twilio | In an authorized trial account, confirm current signup verification, regional/recipient restrictions, available product units, and upgrade path. Do not use trial status to infer production cost or account-specific enablement. | [Twilio trial account](https://www.twilio.com/docs/usage/trials); [API keys in Console](https://www.twilio.com/docs/iam/api-keys/keys-in-console); [Twilio MCP Public Beta](https://www.twilio.com/docs/ai/mcp) | PENDING |
| Amazon Selling Partner | Confirm the current public developer-profile approval, role approval, app-listing requirements and private-app exception in the authorized Solution Provider Portal. For any requested PII role, confirm the exact security review. If considering the first-party local example MCP, have an authorized developer review its support/security posture and test it with approved credentials; no package was installed or run here. The 26-part docs index remains partially inspected, but the separate first-party samples repo establishes that a local example exists. | [Register as a Public SP-API Developer](https://developer-docs.amazon.com/sp-api/docs/register-as-a-public-developer); [Production Application Registration](https://developer-docs.amazon.com/sp-api/docs/onboarding-step-7-register-your-first-production-application); [Local MCP for SP-API sample README](https://github.com/amzn/selling-partner-api-samples/blob/main/use-cases/sp-api-dev-mcp/README.md); [SP-API Welcome](https://developer-docs.amazon.com/sp-api/docs/welcome) | PENDING |
| GitHub | Check the target organization’s PAT, OAuth/MCP policies, SAML SSO requirements, app installation approval and subscription requirements for any selected MCP tools. | [PAT management and organization approval](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens); [GitHub MCP Server setup](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp-in-your-ide/set-up-the-github-mcp-server) | PENDING |
| Otter AI | In an authorized Enterprise workspace, confirm Public API enablement, API-key access, Super Admin role/enablement for workspace endpoints, and supported MCP client/plan behavior. Do not infer account entitlement from public docs. | [Otter Public API](https://help.otter.ai/hc/en-us/articles/36130822688279-Otter-ai-Public-API); [Super Admin APIs](https://help.otter.ai/hc/en-us/articles/39661865499799-Super-Admin-APIs); [Otter MCP Server](https://help.otter.ai/hc/en-us/articles/35287607569687-Otter-MCP-Server) | PENDING |

## Reviewer record

| Reviewer | Date | App ID/name | Field | Evidence inspected | Human result | Correction | Status |
|---|---|---|---|---|---|---|---|
| — | — | — | — | No human review has been recorded. | — | — | PENDING |

## Boundary

Public documentation establishes what a vendor documents; it does not establish that a particular tenant has a feature enabled, that a specific user can create credentials without admin approval, or what commercial terms apply to an account. Those checks remain pending. No human verification, account signup, authenticated tenant/API test, admin approval, or credential test is claimed.

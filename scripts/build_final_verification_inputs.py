#!/usr/bin/env python3
"""Build primary source-verification inputs for the post-research 20-app sample.

This builder consumes the reconciled 100-app first-pass dataset and its already
selected full-population coverage sample. It preserves mixed first-pass
provenance (LIVE_AGENT and PRIOR_CAPTURE), records direct official-source
reinspections separately, and leaves the post-correction recheck empty until a
second, post-correction source pass has actually been performed.

It never searches the web itself, changes the raw dataset, or infers a recheck
value from the adjudicated value. Use --post-recheck-input only after the
separate follow-up inspections have been performed and explicitly recorded.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-09-25"
SELECTION_PATH = "data/evidence/verification_sample_selection.json"
RAW_PATH = "data/raw/final_full_research.json"
ATTEMPTS_PATH = "data/raw/final_full_attempts.json"
LEDGER_PATH = "data/evidence/final_verification_ledger_input.json"
POST_PATH = "data/evidence/final_post_recheck.json"
CAPTURE_PATH = "data/evidence/final_sample_source_captures.json"
MANIFEST_PATH = "apps/apps.json"


def source(
    key: str,
    url: str,
    title: str,
    source_type: str,
    observation: str,
    *,
    status: str = "SUCCESS_DIRECT_PAGE_INSPECTION",
    chunks: tuple[int, ...] = (0,),
    has_more: bool = False,
    warnings: tuple[str, ...] = (),
) -> dict:
    """Describe an actually opened source and the limits of its extraction."""
    return {
        "key": key,
        "source_url": url,
        "source_title": title,
        "source_type": source_type,
        "observation": observation,
        "retrieved_on": DATE,
        "timestamp_precision": "DATE_ONLY; fetch_page does not expose a per-request timestamp",
        "status": status,
        "chunks": list(chunks),
        "has_more": has_more,
        "warnings": list(warnings),
    }


# Directly inspected first-party sources for the final sample. Observations are
# intentionally narrow and do not treat an API page as proof of account access.
SOURCES: dict[str, dict] = {
    # 22 · Twilio
    "twilio_api": source("twilio_api", "https://www.twilio.com/docs/usage/requests-to-twilio", "Twilio API requests | Twilio", "official_auth_docs", "Twilio documents raw HTTP, SDK and CLI requests; API-key SID/secret or Account SID/Auth Token are sent using HTTP Basic authentication. API keys can be created in Console or through the documented API.", has_more=True, warnings=("The page is chunked; the opened authentication/API-key section was visible in the inspected chunk." ,)),
    "twilio_trial": source("twilio_trial", "https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account", "Get started with your Twilio free trial account | Twilio", "official_support", "Twilio says a trial can be started without a credit card, lasts 30 days, includes product-specific free units, and requires email and phone verification; Console credentials become visible after signup.", has_more=True, warnings=("Trial terms and available product units can vary; no trial account was created." ,)),
    "twilio_mcp": source("twilio_mcp", "https://www.twilio.com/docs/ai/mcp", "Twilio MCP server | Twilio", "official_docs", "Twilio documents a hosted public-beta MCP at mcp.twilio.com/docs, with no account/authentication required, read-only API/documentation search and retrieval, and no live API execution in the current release.", has_more=True, warnings=("The page is chunked; the public-beta, auth, scope and setup sections were visible." ,)),

    # 84 · Product identity unresolved. These are candidate context only.
    "paygent_candidate": source("paygent_candidate", "https://www.paygent.co.jp/", "Paygent official homepage (page title not preserved)", "official_product", "The opened Paygent Japan homepage describes Japanese payment services. It does not establish that this is the manifest's 'Paygent Connect' or link that name to NMI.", warnings=("Candidate identity context only; no product-specific facts are attributed to app ID 84." ,)),
    "nmi_candidate": source("nmi_candidate", "https://secure.networkmerchants.com/gw/merchants/resources/integration/integration_portal.php", "NMI gateway integration portal", "official_api_docs", "The NMI portal describes NMI gateway integrations. It does not identify the manifest's 'Paygent Connect' as an NMI product or link it to Paygent Japan.", warnings=("Candidate identity context only; do not transfer candidate-product API/auth/MCP facts to app ID 84." ,)),
    "paygent_search_candidate": source("paygent_search_candidate", "https://paygent.tech/", "Site Not Found | Framer", "search_candidate_page", "The exact-name web search surfaced paygent.tech, but direct inspection returned 'Site Not Found'. It did not establish the identity of 'Paygent Connect'.", status="SUCCESS_PAGE_INSPECTED_SITE_NOT_FOUND", warnings=("Search result was a discovery lead only; the failed page is not product evidence." ,)),

    # 49 · Amazon Selling Partner API
    "amazon_auth": source("amazon_auth", "https://developer-docs.amazon.com/sp-api/docs/authorize-public-applications", "Authorize Public Applications", "official_auth_docs", "Amazon documents public-app authorization using Login with Amazon OAuth 2.0, seller consent, authorization-code exchange and refresh/access tokens. Private-app self-authorization is a separate path."),
    "amazon_public_dev": source("amazon_public_dev", "https://developer-docs.amazon.com/sp-api/docs/register-as-a-public-developer", "Register as a Public SP-API Developer", "official_docs", "Public developers submit a developer profile, request roles and list public applications in the Selling Partner Appstore; Amazon review/approval applies. The page expressly distinguishes private internal applications.", has_more=True, warnings=("The page continues across chunks; the registration and review sections needed for this claim were visible." ,)),
    "amazon_onboarding": source("amazon_onboarding", "https://developer-docs.amazon.com/sp-api/docs/onboarding-overview", "Onboarding as a Developer", "official_api_docs", "Amazon describes SP-API as a REST API spanning seller/vendor workflows such as catalog, listings, pricing, orders, shipping, fulfillment and inventory, with public and private application routes.", has_more=True, warnings=("The onboarding page continues across chunks; the API surface and public/private application distinction were visible." ,)),
    "amazon_local_mcp": source("amazon_local_mcp", "https://github.com/amzn/selling-partner-api-samples/blob/main/use-cases/sp-api-dev-mcp/README.md", "selling-partner-api-samples/use-cases/sp-api-dev-mcp/README.md · amzn/selling-partner-api-samples", "official_github", "Amazon's repository calls this a Local MCP for SP-API educational example, not a supported product. It documents local developer tools; SP-API credentials are needed only for live SP-API execution/workflows.", has_more=True, warnings=("GitHub extraction was chunked; the educational-example, credential scope and setup text were visible in chunk 0." ,)),

    # 98 · Mermaid CLI
    "mermaid_cli": source("mermaid_cli", "https://github.com/mermaid-js/mermaid-cli/blob/master/README.md", "mermaid-js/mermaid-cli README", "official_github", "The official Mermaid CLI README documents local npm installation and rendering Mermaid syntax to output formats; this is a local CLI, not evidence of a hosted product API.", has_more=True, warnings=("The opened README is chunked; the installation/rendering instructions were visible." ,)),
    "mermaid_ecosystem": source("mermaid_ecosystem", "https://mermaid.js.org/ecosystem/integrations-community.html", "Community integrations | Mermaid", "official_docs", "Mermaid's official ecosystem page lists 'MCP Server Mermaid' under community integrations. This is not first-party Mermaid CLI MCP documentation."),

    # 4 · Attio
    "attio_auth": source("attio_auth", "https://docs.attio.com/rest-api/guides/authentication", "Authenticating requests - Attio Docs", "official_auth_docs", "Attio documents OAuth 2.0, workspace API-key tokens, Bearer authorization and HTTP Basic using the token as username with a blank password."),
    "attio_rest": source("attio_rest", "https://docs.attio.com/rest-api/overview", "REST API overview - Attio Docs", "official_api_docs", "Attio's first-party REST API documents workspace records, objects, lists and related resources and operations."),
    "attio_mcp": source("attio_mcp", "https://docs.attio.com/mcp/overview", "Attio MCP - Attio Docs", "official_docs", "Attio documents the hosted MCP endpoint https://mcp.attio.com/mcp, user OAuth, workspace-scoped read/search/create/update tools, and confirmation for writes."),
    "attio_pricing": source("attio_pricing", "https://attio.com/pricing", "Plans & Pricing | Attio", "official_pricing", "Attio lists a Free plan without a credit card and shows API/webhook and MCP availability in its plan matrix."),
    "attio_admin_key": source("attio_admin_key", "https://attio.com/help/reference/apps/generating-an-api-key", "Generate an API key | Attio Help Center", "official_support", "Attio says workspace API keys are available on all plans, but only workspace admins can create/manage them; keys can be scoped."),

    # 13 · Freshdesk
    "freshdesk_api": source("freshdesk_api", "https://developer.freshdesk.com/api/", "Freshdesk API reference", "official_api_docs", "The REST v2 reference documents tickets, conversations, contacts, companies, agents, ticket fields/forms and other resources; its authentication section identifies personal API keys with Basic auth and agent-role permissions.", has_more=True, warnings=("The API reference is highly chunked; the authentication and REST resource index were directly inspected." ,)),
    "freshdesk_key": source("freshdesk_key", "https://support.freshdesk.com/support/solutions/articles/215517-how-to-find-your-api-key", "How To Find Your API Key : Freshdesk Support", "official_support", "Freshdesk's key help page describes verified-agent access to the personal key and role-based API action permissions; current plan distinctions exclude Free from API/key functionality."),
    "freshdesk_pricing": source("freshdesk_pricing", "https://www.freshworks.com/freshdesk/pricing/", "Freshdesk Customer Support Software Pricing & Plans | Freshworks", "official_pricing", "The current Freshdesk pricing page lists Growth, Pro and Enterprise paid plans, self-serve trials and MCP action add-ons; it does not by itself establish API-key feature availability on every plan." , has_more=True),
    "freshdesk_mcp": source("freshdesk_mcp", "https://support.freshdesk.com/support/solutions/articles/50000012670-model-context-protocol-mcp-integration-in-freshdesk", "Model Context Protocol (MCP) integration in Freshdesk : Freshdesk Support", "official_support", "Freshworks says Freshdesk MCP became generally available September 10, 2026, documents https://<subdomain>.freshdesk.com/mcp, API-key-only authentication, and Growth/Pro/Enterprise plan limits/action allowances.", has_more=True, warnings=("The support article is chunked; the GA date, endpoint, auth and plan matrix were visible in chunk 0." ,)),
    "freshdesk_webhook": source("freshdesk_webhook", "https://support.freshdesk.com/support/solutions/articles/132589-using-webhooks-in-automation-rules", "Using webhooks in automation rules that run on ticket updates : Freshdesk Support", "official_support", "The directly inspected Freshdesk article documents outbound Trigger Webhook actions and Trigger API actions in ticket automation rules, including callback URLs, HTTP methods and API-key authentication; this supports webhook-enabled automation, not a dedicated Webhooks API.", has_more=True, chunks=(0,), warnings=("The current guide spans three chunks; chunk 0 contains the Trigger Webhook/Trigger API distinction, eligible plans and setup. A separate later URL refetch redirected to support login and is recorded as a capture failure, not as claim evidence." ,)),
    "freshdesk_webhook_examples": source("freshdesk_webhook_examples", "https://support.freshdesk.com/support/solutions/articles/50000009511-automation-examples-using-webhooks", "Examples for Automations using Webhooks : Freshdesk Support", "official_support", "Freshdesk's official examples configure outbound webhook automation using POST/PUT requests and Freshdesk API-key authentication; this is an automation action, not a standalone Webhooks API.", has_more=True, chunks=(0,), warnings=("The page spans two chunks; chunk 0 contains the automation examples and plan matrix." ,)),

    # 31 · Google Ads
    "google_ads_quickstart": source("google_ads_quickstart", "https://developers.google.com/google-ads/api/docs/get-started/make-first-call", "Quick start | Google Ads API | Google for Developers", "official_api_docs", "Google's quick start documents Google Ads API calls, Cloud project/OAuth or service-account configuration, manager-account developer token, customer account access and access-level constraints.", has_more=True, warnings=("The quick-start page is chunked; prerequisites and authentication summary were visible." ,)),
    "google_ads_access": source("google_ads_access", "https://developers.google.com/google-ads/api/docs/api-policy/access-levels", "Google Ads API access levels", "official_docs", "Google distinguishes test/basic/standard API access and describes developer-token applications/review and production quotas."),
    "google_ads_mcp": source("google_ads_mcp", "https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server", "Google Ads MCP server: Developer integration guide | Google Ads API | Google for Developers", "official_docs", "Google documents a first-party Google Ads MCP server; the current release is read-only, stdio transport, and supports OAuth 2.0 or service-account credentials.", has_more=True, warnings=("The MCP guide is chunked; overview/auth/scope text was visible." ,)),

    # 78 · Coda / Superhuman Docs
    "superhuman_api": source("superhuman_api", "https://docs.superhuman.com/developers/apis/v1", "Superhuman Docs API (v1) Reference Documentation", "official_api_docs", "The current API reference describes a REST API for folders/docs/pages/tables/rows, permissions, formulas, controls and analytics; the product is identified as formerly Coda.", has_more=True, warnings=("The API reference is chunked; REST overview/resource coverage was visible." ,)),
    "superhuman_mcp": source("superhuman_mcp", "https://help.superhuman.com/hc/en-us/articles/46210076980365-Connect-to-the-Superhuman-Docs-MCP", "Connect to the Superhuman Docs MCP", "official_support", "Superhuman Docs documents a first-party MCP endpoint and OAuth setup; it also retains a legacy Coda endpoint with a planned deprecation path."),
    "superhuman_security": source("superhuman_security", "https://help.superhuman.com/hc/en-us/articles/46210118248205-Security-recommendations-for-the-Docs-MCP", "Security recommendations for the Superhuman Docs MCP", "official_support", "The security guide documents OAuth 2 PKCE and MCP-restricted personal access tokens, with read/write scope controls and workspace/folder access limits."),
    "superhuman_settings": source("superhuman_settings", "https://help.superhuman.com/hc/en-us/articles/46210093335949-Manage-your-Superhuman-Docs-account-settings", "Manage your Superhuman Docs account settings", "official_support", "The account settings guide documents API-token generation and settings-based access; no workspace was created or used."),
    "superhuman_pricing": source("superhuman_pricing", "https://superhuman.com/plans/docs?source=coda.io", "Superhuman Docs plans", "official_pricing", "The plan page lists Free and paid tiers; MCP is limited on Free while the REST API is available with workspace-role constraints."),

    # 67 · Snowflake
    "snowflake_api": source("snowflake_api", "https://docs.snowflake.com/en/developer-guide/sql-api/intro", "Introduction to SQL REST API | Snowflake Documentation", "official_api_docs", "Snowflake documents the SQL REST API for submitting statements, polling/canceling and retrieving results, including DDL/DML and deployment-related operations."),
    "snowflake_auth": source("snowflake_auth", "https://docs.snowflake.com/en/developer-guide/sql-api/authenticating", "Authenticating to the server | Snowflake Documentation", "official_auth_docs", "The SQL API docs list OAuth, key-pair JWT and workload-identity-federation authentication; requests use Bearer tokens and account/user configuration." , has_more=True),
    "snowflake_mcp": source("snowflake_mcp", "https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp", "Snowflake-managed MCP servers", "official_docs", "Snowflake documents a managed MCP server object scoped to a database/schema, OAuth/External OAuth, RBAC and tool grants; connected tools may expose SQL or Cortex operations."),
    "snowflake_trial": source("snowflake_trial", "https://www.snowflake.com/en/snowflake-trial/", "Snowflake Trial", "official_pricing", "Snowflake's product-site trial page offers a 30-day trial and $400 in credits for the AI Data Cloud option."),

    # 52 · SE Ranking
    "seranking_api": source("seranking_api", "https://seranking.com/api/data/getting-started/", "SE Ranking Data API: Getting Started", "official_api_docs", "The Data API setup guide documents API-key creation and request authentication using an Authorization token/API-key header."),
    "seranking_api_help": source("seranking_api_help", "https://help.seranking.com/hc/en-us/articles/22447958135068-Getting-Started-with-SE-Ranking-s-API", "Getting Started with SE Ranking's API", "official_support", "SE Ranking says a standalone API package can be purchased/trialed separately; a 14-day API trial includes 100,000 credits and API key access depends on account/subaccount entitlement."),
    "seranking_mcp": source("seranking_mcp", "https://seranking.com/api/integrations/mcp/", "MCP Server - SE Ranking API Documentation", "official_docs", "SE Ranking documents the hosted Streamable HTTP MCP at https://api.seranking.com/mcp, OAuth 2.1 with dynamic client registration and API-key fallback; subaccounts need the master account's key.", has_more=True, warnings=("The MCP guide is chunked; endpoint/auth/setup and subaccount sections were visible in chunk 0." ,)),
    "seranking_pricing": source("seranking_pricing", "https://seranking.com/api-pricing.html", "SE Ranking API pricing", "official_pricing", "SE Ranking lists trial and paid API routes; credits, product/API entitlement and plan-generation restrictions remain material."),

    # 27 · Telegram
    "telegram_tdlib": source("telegram_tdlib", "https://github.com/tdlib/telegram-bot-api/blob/master/README.md", "telegram-bot-api/README.md at master · GitHub", "official_github", "The official TDLib repository calls the Bot API an HTTP API and says a self-hosted local Bot API server requires api_id/api_hash. The README does not settle standard cloud BotFather token access, plan gates or first-party MCP availability.", has_more=True, warnings=("The README is chunked; the HTTP API and local-server credential requirements were visible in chunk 0." ,)),

    # 91 · NotebookLM Enterprise / Gemini Notebook Enterprise
    "notebooklm_api": source("notebooklm_api", "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks", "Create and manage notebooks (API) | Gemini Notebook Enterprise | Google Cloud Documentation", "official_api_docs", "Google Cloud documents REST operations to create, retrieve, list, delete and share Gemini Notebook Enterprise notebooks/sources using Google Cloud OAuth Bearer tokens and project/IAM configuration.", has_more=True, warnings=("The API guide is chunked; REST operations and Bearer-auth examples were visible." ,)),
    "notebooklm_setup": source("notebooklm_setup", "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm", "Set up Gemini Notebook Enterprise | Google Cloud Documentation", "official_docs", "Setup requires organizational identity configuration, a Cloud project/API, and assigned administrative/user roles; NotebookLM Enterprise is distinct from consumer NotebookLM.", has_more=True),
    "notebooklm_licensing": source("notebooklm_licensing", "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-licensing", "Gemini Notebook Enterprise licensing | Google Cloud Documentation", "official_docs", "Google's licensing guide describes enterprise licensing and a minimum 15-license subscription, with a 14-day trial tier."),

    # 45 · Adobe Commerce
    "adobe_api": source("adobe_api", "https://developer.adobe.com/commerce/webapi/get-started/", "Get started with Web APIs | Adobe Commerce", "official_api_docs", "Adobe documents the Commerce Web API framework and REST/GraphQL use; feature/auth scope differs between PaaS Magento/Commerce and SaaS Commerce as a Cloud Service."),
    "adobe_auth_paas": source("adobe_auth_paas", "https://developer.adobe.com/commerce/webapi/rest/authentication/", "Authentication | Adobe Commerce", "official_auth_docs", "Adobe's PaaS authentication page describes administrator-registered integrations, ACL permissions and token/OAuth authentication; it is explicitly a PaaS path."),
    "adobe_auth_saas": source("adobe_auth_saas", "https://developer.adobe.com/commerce/webapi/get-started/authentication/", "Authentication for Adobe Commerce as a Cloud Service", "official_auth_docs", "The SaaS path uses Adobe Developer Console and IMS OAuth 2 Bearer tokens and requires the relevant Commerce as a Cloud Service license/environment."),
    "adobe_mcp_tools": source("adobe_mcp_tools", "https://developer.adobe.com/commerce/extensibility/developer-agent/tools-overview", "AI developer tools for Commerce extensibility", "official_docs", "Adobe documents first-party Commerce development MCPs for App Builder/extensibility and a separate storefront dropins MCP; these are development/documentation workflows, not a general merchant runtime data-plane MCP."),
    "adobe_mcp_setup": source("adobe_mcp_setup", "https://developer.adobe.com/commerce/extensibility/developer-agent/coding-tools", "Commerce development MCPs and skills", "official_docs", "Adobe's setup guide documents prerequisites, installation and IDE configuration for development MCP tools; it does not establish live arbitrary store data actions."),

    # 88 · Brex
    "brex_api": source("brex_api", "https://developer.brex.com/docs", "Brex Developer API", "official_api_docs", "Brex publishes REST API references for financial resources; production use and tokens are scoped to authorized account capabilities."),
    "brex_auth": source("brex_auth", "https://developer.brex.com/docs/authentication", "Authentication - Brex Developer API", "official_auth_docs", "Brex's API authentication documentation describes Bearer-token credentials and admin-provisioned/scoped tokens."),
    "brex_mcp": source("brex_mcp", "https://developer.brex.com/docs/mcp", "Brex MCP", "official_docs", "Brex documents https://api.brex.com/mcp as a beta MCP; account/card admin must accept the Developer API agreement and enable the beta, after which users can OAuth-connect. API tokens are admin-managed; tools inherit user capabilities.", has_more=True),

    # 65 · Supabase
    "supabase_api": source("supabase_api", "https://supabase.com/docs/guides/api", "Supabase APIs", "official_api_docs", "Supabase documents project APIs including an auto-generated REST Data API from PostgreSQL schemas."),
    "supabase_keys": source("supabase_keys", "https://supabase.com/docs/guides/getting-started/api-keys", "API Keys | Supabase Docs", "official_auth_docs", "Supabase documents publishable and secret project API keys, with RLS/server-side security distinctions."),
    "supabase_mcp": source("supabase_mcp", "https://supabase.com/docs/guides/ai-tools/mcp", "Supabase MCP Server | Supabase Docs", "official_docs", "Supabase documents the hosted https://mcp.supabase.com/mcp server, browser OAuth/dynamic client registration, project scoping, read-only mode and feature-group restrictions; some functions can write/execute SQL.", has_more=True, warnings=("The MCP guide is chunked; endpoint/auth/tools/scope sections were visible in chunk 0." ,)),
    "supabase_pricing": source("supabase_pricing", "https://supabase.com/pricing", "Supabase Pricing", "official_pricing", "Supabase lists a $0 Free plan and paid tiers; project/storage/usage limits and add-ons vary by plan."),

    # 1 · Salesforce
    "salesforce_rest": source("salesforce_rest", "https://developer.salesforce.com/docs/platform/api-rest/guide/intro-what-is-rest-api.html", "About REST API - Salesforce Developers", "official_api_docs", "Salesforce documents REST API resources and distinguishes other interfaces including SOAP."),
    "salesforce_soap": source("salesforce_soap", "https://developer.salesforce.com/docs/platform/api/guide/sforce-api-quickstart-intro.html", "About SOAP API | SOAP API Developer Guide | Salesforce Developers", "official_api_docs", "Salesforce directly documents SOAP API availability for Enterprise, Performance, Unlimited and Developer Editions, subject to API Enabled permission; a free Developer Edition is available for test/development."),
    "salesforce_mcp": source("salesforce_mcp", "https://developer.salesforce.com/docs/ai/agentforce/guide/mcp.html", "Salesforce MCP Solutions", "official_docs", "Salesforce developer documentation lists first-party MCP server options for Salesforce orgs; no org was connected or MCP call made."),
    "salesforce_dev": source("salesforce_dev", "https://developer.salesforce.com/signup", "Salesforce Developer Edition sign-up", "official_product", "Salesforce documents a free Developer Edition org for testing/development; this does not guarantee API entitlements in every production org."),

    # 23 · Zoho Cliq. REST/OAuth renderer currently exposes a navigation shell.
    "zoho_api": source("zoho_api", "https://www.zoho.com/cliq/help/restapi/v3/introduction/", "Introduction | Zoho Cliq | API Documentation", "official_api_docs", "The official API page exposes a V3 REST API documentation index and resource/authentication sections, but its extracted body displays 'No Results Found'; do not claim detailed endpoint/auth content from this shell.", status="SUCCESS_PARTIAL_DOCUMENTATION_SHELL", warnings=("The page extraction exposed navigation but not the body; OAuth details are not inferred from the navigation alone." ,)),
    "zoho_mcp": source("zoho_mcp", "https://www.zoho.com/cliq/help/platform/zoho-cliq-mcp.html", "Guide to Zoho Cliq's MCP Server", "official_support", "Zoho's first-party guide states its official Cliq MCP server supports chat/channel/message/reminder workflows." , has_more=True, warnings=("The page is chunked; the first-party server and tool-scope section was directly inspected in chunk 1." ,)),
    "zoho_mcp_setup": source("zoho_mcp_setup", "https://www.zoho.com/cliq/help/platform/configure-zoho-cliq-mcp.html", "Configuring Your Zoho MCP Server", "official_support", "Zoho documents a self-serve console flow to create/configure a Cliq MCP server, choose tools, and generate a unique secure MCP URL; configured services require valid authenticated credentials.", has_more=True, warnings=("The setup guide is chunked; prerequisites and unique-URL setup were visible in chunk 1." ,)),
    "zoho_pricing": source("zoho_pricing", "https://www.zoho.com/cliq/pricing.html", "Cliq - Chat Pricing | Free Chat plans for all Teams size", "official_pricing", "Zoho lists a Free plan at $0 with Try Now/Get Started and paid tiers; this page does not establish every API/MCP tool entitlement.", has_more=True),

    # 100 · Grain
    "grain_api_support": source("grain_api_support", "https://support.grain.com/en/articles/15507288-grain-api", "Grain API | Grain Support", "official_support", "Grain's support article documents API PAT, WAT and OAuth2 methods, plan/role gates and a Public-Api-Version header requirement; it labels 2025-10-31 current."),
    "grain_developer_overview": source("grain_developer_overview", "https://developers.grain.com/overview.html", "Overview — Grain Developers", "official_api_docs", "Grain's developer overview presents a versioned REST API and example header; its current-version example conflicts with the support article."),
    "grain_versions": source("grain_versions", "https://developers.grain.com/versions.html", "Versions — Grain Developers", "official_api_docs", "Grain's developer versions page labels 2026-10-01 current and 2025-10-31 deprecated; 2026-10-01 is future-dated relative to the 2026-09-25 retrieval date."),
    "grain_mcp_release": source("grain_mcp_release", "https://grain.com/release-note/06-18-2025", "Grain MCP release note", "official_product", "Grain's first-party release note identifies hosted MCP at https://api.grain.com/_/mcp; pricing lists Basic MCP on Free and Advanced MCP on Business/Enterprise. Detailed MCP authentication remained inaccessible."),
    "grain_pricing": source("grain_pricing", "https://grain.com/pricing", "Grain Pricing", "official_pricing", "Grain pricing lists Basic MCP on Free, Personal API on Starter, and Workspace API/Advanced MCP on Business/Enterprise; API entitlement and role restrictions vary."),

    # 62 · Vercel
    "vercel_api": source("vercel_api", "https://vercel.com/docs/rest-api", "Vercel REST API", "official_api_docs", "Vercel documents a REST API/SDK for account, project, deployment and related platform resources."),
    "vercel_token": source("vercel_token", "https://vercel.com/docs/rest-api/authentication/create-an-auth-token", "Create an Auth Token | Vercel REST API", "official_auth_docs", "Vercel documents user auth-token creation and Bearer authentication; the token value is returned only once and can be project/team-scoped."),
    "vercel_mcp": source("vercel_mcp", "https://vercel.com/docs/agent-resources/vercel-mcp", "Vercel MCP", "official_docs", "Vercel documents a first-party hosted MCP at https://mcp.vercel.com using OAuth; beta availability and client/team permissions apply."),
    "vercel_pricing": source("vercel_pricing", "https://vercel.com/pricing", "Vercel Pricing", "official_pricing", "Vercel lists Hobby at $0 for personal use, Pro and Enterprise; team/resource permissions remain account- and plan-dependent."),

    # 9 · Copper
    "copper_api": source("copper_api", "https://developer.copper.com/", "Getting started - Copper Developer API", "official_api_docs", "Copper describes a RESTful JSON Developer API for most Copper resources."),
    "copper_auth": source("copper_auth", "https://developer.copper.com/introduction/authentication.html", "Authentication - Copper Developer API", "official_auth_docs", "Copper's API documentation describes API-key authentication and owner-email/account context."),
    "copper_requests": source("copper_requests", "https://developer.copper.com/introduction/requests.html", "Requests - Copper Developer API", "official_api_docs", "Copper documents authenticated developer API requests and REST/JSON calls."),
    "copper_oauth": source("copper_oauth", "https://developer.copper.com/introduction/oauth/quickstart.html", "OAuth2.0 Quickstart Guide - Copper Developer API", "official_auth_docs", "Copper's OAuth quickstart requires app registration and client credentials obtained via its partners contact; the user consents and the API uses a Bearer access token."),
    "copper_pricing": source("copper_pricing", "https://www.copper.com/pricing", "Copper Pricing", "official_pricing", "Copper lists a self-serve trial/pricing path; the opened pricing extraction did not resolve API entitlement by plan."),
    "copper_webhooks": source("copper_webhooks", "https://developer.copper.com/webhooks/overview.html", "Overview - Copper Developer API", "official_api_docs", "Copper documents webhook subscriptions for near-real-time create/update/delete events on CRM entities, HTTPS notification URLs, a 100-subscription limit and notification limits. This is a documented webhook interface, not a claim of a general REST Webhooks API."),

    # Out-of-sample API nomenclature audit only; not part of sample accuracy.
    "gorgias_http": source("gorgias_http", "https://developers.gorgias.com/docs/receive-and-respond-to-tickets-from-a-third-party-app.md", "Integrate with a new channel - Gorgias Developers", "official_docs", "Gorgias says HTTP integrations send requests to external endpoints when tickets/messages are created or updated; this is outbound HTTP/webhook capability, not a dedicated Webhooks API."),
    "gorgias_sync": source("gorgias_sync", "https://developers.gorgias.com/docs/sync-gorgias-data-with-a-database.md", "Sync Gorgias data with a database - Gorgias Developers", "official_docs", "Gorgias's first-party tutorial demonstrates outbound HTTP integrations/webhook actions to third-party endpoints, not a standalone Webhooks API."),
}

CORE_FIELDS = [
    ("auth_methods", "auth"),
    ("self_serve_status", "self_serve"),
    ("credential_access.status", "credential_access"),
    ("api.available", "api"),
    ("mcp.status", "mcp"),
    ("buildability.verdict", "buildability"),
]
METRIC_GROUP = {
    "auth_methods": "auth",
    "self_serve_status": "self_serve",
    "credential_access.status": "credential_access",
    "api.available": "api_availability",
    "mcp.status": "mcp",
    "buildability.verdict": "buildability",
}

# Direct fresh source selected for each critical field. Supporting sources are
# attached below where more than one page is needed for a defensible conclusion.
CORE_SOURCE_KEYS: dict[tuple[int, str], str | None] = {
    (22, "auth_methods"): "twilio_api", (22, "self_serve_status"): "twilio_trial", (22, "credential_access.status"): "twilio_trial", (22, "api.available"): "twilio_api", (22, "mcp.status"): "twilio_mcp", (22, "buildability.verdict"): "twilio_mcp",
    (84, "auth_methods"): None, (84, "self_serve_status"): None, (84, "credential_access.status"): None, (84, "api.available"): None, (84, "mcp.status"): None, (84, "buildability.verdict"): None,
    (49, "auth_methods"): "amazon_auth", (49, "self_serve_status"): "amazon_public_dev", (49, "credential_access.status"): "amazon_public_dev", (49, "api.available"): "amazon_onboarding", (49, "mcp.status"): "amazon_local_mcp", (49, "buildability.verdict"): "amazon_public_dev",
    (98, "auth_methods"): "mermaid_cli", (98, "self_serve_status"): "mermaid_cli", (98, "credential_access.status"): "mermaid_cli", (98, "api.available"): "mermaid_cli", (98, "mcp.status"): "mermaid_ecosystem", (98, "buildability.verdict"): "mermaid_cli",
    (4, "auth_methods"): "attio_auth", (4, "self_serve_status"): "attio_pricing", (4, "credential_access.status"): "attio_admin_key", (4, "api.available"): "attio_rest", (4, "mcp.status"): "attio_mcp", (4, "buildability.verdict"): "attio_mcp",
    (13, "auth_methods"): "freshdesk_api", (13, "self_serve_status"): "freshdesk_pricing", (13, "credential_access.status"): "freshdesk_key", (13, "api.available"): "freshdesk_api", (13, "mcp.status"): "freshdesk_mcp", (13, "buildability.verdict"): "freshdesk_mcp",
    (31, "auth_methods"): "google_ads_quickstart", (31, "self_serve_status"): "google_ads_access", (31, "credential_access.status"): "google_ads_access", (31, "api.available"): "google_ads_quickstart", (31, "mcp.status"): "google_ads_mcp", (31, "buildability.verdict"): "google_ads_access",
    (78, "auth_methods"): "superhuman_security", (78, "self_serve_status"): "superhuman_pricing", (78, "credential_access.status"): "superhuman_security", (78, "api.available"): "superhuman_api", (78, "mcp.status"): "superhuman_mcp", (78, "buildability.verdict"): "superhuman_security",
    (67, "auth_methods"): "snowflake_auth", (67, "self_serve_status"): "snowflake_trial", (67, "credential_access.status"): "snowflake_mcp", (67, "api.available"): "snowflake_api", (67, "mcp.status"): "snowflake_mcp", (67, "buildability.verdict"): "snowflake_mcp",
    (52, "auth_methods"): "seranking_api_help", (52, "self_serve_status"): "seranking_pricing", (52, "credential_access.status"): "seranking_api_help", (52, "api.available"): "seranking_api", (52, "mcp.status"): "seranking_mcp", (52, "buildability.verdict"): "seranking_api_help",
    (27, "auth_methods"): "telegram_tdlib", (27, "self_serve_status"): "telegram_tdlib", (27, "credential_access.status"): "telegram_tdlib", (27, "api.available"): "telegram_tdlib", (27, "mcp.status"): "telegram_tdlib", (27, "buildability.verdict"): "telegram_tdlib",
    (91, "auth_methods"): "notebooklm_api", (91, "self_serve_status"): "notebooklm_licensing", (91, "credential_access.status"): "notebooklm_setup", (91, "api.available"): "notebooklm_api", (91, "mcp.status"): "notebooklm_api", (91, "buildability.verdict"): "notebooklm_setup",
    (45, "auth_methods"): "adobe_auth_paas", (45, "self_serve_status"): "adobe_auth_saas", (45, "credential_access.status"): "adobe_auth_paas", (45, "api.available"): "adobe_api", (45, "mcp.status"): "adobe_mcp_tools", (45, "buildability.verdict"): "adobe_api",
    (88, "auth_methods"): "brex_mcp", (88, "self_serve_status"): "brex_mcp", (88, "credential_access.status"): "brex_mcp", (88, "api.available"): "brex_api", (88, "mcp.status"): "brex_mcp", (88, "buildability.verdict"): "brex_mcp",
    (65, "auth_methods"): "supabase_keys", (65, "self_serve_status"): "supabase_pricing", (65, "credential_access.status"): "supabase_mcp", (65, "api.available"): "supabase_api", (65, "mcp.status"): "supabase_mcp", (65, "buildability.verdict"): "supabase_mcp",
    (1, "auth_methods"): "salesforce_rest", (1, "self_serve_status"): "salesforce_soap", (1, "credential_access.status"): "salesforce_soap", (1, "api.available"): "salesforce_rest", (1, "mcp.status"): "salesforce_mcp", (1, "buildability.verdict"): "salesforce_soap",
    (23, "auth_methods"): "zoho_api", (23, "self_serve_status"): "zoho_pricing", (23, "credential_access.status"): "zoho_mcp_setup", (23, "api.available"): "zoho_api", (23, "mcp.status"): "zoho_mcp", (23, "buildability.verdict"): "zoho_mcp_setup",
    (100, "auth_methods"): "grain_api_support", (100, "self_serve_status"): "grain_pricing", (100, "credential_access.status"): "grain_api_support", (100, "api.available"): "grain_api_support", (100, "mcp.status"): "grain_mcp_release", (100, "buildability.verdict"): "grain_versions",
    (62, "auth_methods"): "vercel_token", (62, "self_serve_status"): "vercel_pricing", (62, "credential_access.status"): "vercel_token", (62, "api.available"): "vercel_api", (62, "mcp.status"): "vercel_mcp", (62, "buildability.verdict"): "vercel_mcp",
    (9, "auth_methods"): "copper_auth", (9, "self_serve_status"): "copper_pricing", (9, "credential_access.status"): "copper_oauth", (9, "api.available"): "copper_api", (9, "mcp.status"): "copper_api", (9, "buildability.verdict"): "copper_oauth",
}

SUPPORTING_SOURCE_KEYS: dict[tuple[int, str], list[str]] = {
    (22, "auth_methods"): ["twilio_trial"],
    (4, "self_serve_status"): ["attio_mcp", "attio_admin_key"],
    (4, "buildability.verdict"): ["attio_admin_key", "attio_pricing"],
    (13, "self_serve_status"): ["freshdesk_key", "freshdesk_mcp"],
    (13, "buildability.verdict"): ["freshdesk_api", "freshdesk_pricing"],
    (31, "self_serve_status"): ["google_ads_quickstart"],
    (31, "buildability.verdict"): ["google_ads_mcp", "google_ads_quickstart"],
    (78, "self_serve_status"): ["superhuman_mcp", "superhuman_api"],
    (78, "credential_access.status"): ["superhuman_settings", "superhuman_mcp"],
    (67, "self_serve_status"): ["snowflake_mcp"],
    (67, "auth_methods"): ["snowflake_api"],
    (52, "auth_methods"): ["seranking_mcp"],
    (52, "self_serve_status"): ["seranking_api_help"],
    (52, "credential_access.status"): ["seranking_mcp"],
    (27, "mcp.status"): ["telegram_tdlib"],
    (91, "self_serve_status"): ["notebooklm_setup"],
    (91, "mcp.status"): ["notebooklm_setup"],
    (45, "self_serve_status"): ["adobe_api", "adobe_auth_paas"],
    (45, "credential_access.status"): ["adobe_auth_saas"],
    (45, "mcp.status"): ["adobe_mcp_setup"],
    (88, "self_serve_status"): ["brex_api"],
    (88, "credential_access.status"): ["brex_api"],
    (65, "auth_methods"): ["supabase_mcp"],
    (65, "credential_access.status"): ["supabase_keys"],
    (1, "self_serve_status"): ["salesforce_soap"],
    (1, "credential_access.status"): ["salesforce_rest"],
    (23, "auth_methods"): ["zoho_mcp_setup"],
    (23, "self_serve_status"): ["zoho_mcp_setup"],
    (23, "credential_access.status"): ["zoho_pricing"],
    (100, "auth_methods"): ["grain_developer_overview"],
    (100, "api.available"): ["grain_developer_overview", "grain_versions"],
    (100, "mcp.status"): ["grain_pricing"],
    (100, "buildability.verdict"): ["grain_api_support", "grain_mcp_release"],
    (62, "self_serve_status"): ["vercel_mcp"],
    (62, "credential_access.status"): ["vercel_mcp"],
    (9, "self_serve_status"): ["copper_auth", "copper_oauth"],
    (9, "credential_access.status"): ["copper_auth", "copper_requests"],
    (9, "api.available"): ["copper_webhooks"],
    (9, "mcp.status"): ["copper_webhooks"],
    (9, "buildability.verdict"): ["copper_webhooks", "copper_pricing"],
}

UNRESOLVED = {
    (84, "auth_methods"), (84, "self_serve_status"), (84, "credential_access.status"), (84, "api.available"), (84, "mcp.status"), (84, "buildability.verdict"),
    (27, "auth_methods"), (27, "self_serve_status"), (27, "credential_access.status"), (27, "mcp.status"), (27, "buildability.verdict"),
    (23, "auth_methods"),
    (9, "mcp.status"),
    (91, "mcp.status"),
}

VERIFIED_OVERRIDES = {
    (4, "auth_methods"): ["OAuth 2.0", "API key", "Bearer/token", "Basic"],
    (4, "self_serve_status"): "SELF_SERVE_WITH_RESTRICTIONS",
    (49, "mcp.status"): "AVAILABLE",
}

CRITICAL_REASONS = {
    (4, "auth_methods"): ("Attio's directly inspected authentication guide documents OAuth 2.0, API-key tokens, Bearer authorization and HTTP Basic with the token as username and an empty password; the first pass omitted Basic.", "auth_method_omission", "Add the directly documented Basic method while preserving the first-pass value in the raw dataset."),
    (4, "self_serve_status"): ("Attio's Free plan and first-party hosted-MCP OAuth path establish a self-serve route, while workspace API-key creation is admin-only. The first-pass ADMIN_APPROVAL_REQUIRED label overgeneralized the API-key path.", "credential_path_conflation", "Change to SELF_SERVE_WITH_RESTRICTIONS and retain the admin-only API-key condition."),
    (49, "mcp.status"): ("Amazon's own repository directly documents a Local MCP for SP-API educational example. This establishes a first-party local MCP example, not a supported hosted Amazon MCP product; the first pass left MCP unclassified.", "mcp_false_negative", "Set AVAILABLE for the documented first-party local example and preserve the explicit unsupported-product/hosted-service limitation."),
}

UNRESOLVED_REASONS = {
    84: "The manifest identity is unresolved. Public search and opened Paygent Japan/NMI first-party pages do not establish which product 'Paygent Connect' denotes. Keep every product-specific critical field UNKNOWN; candidate-product evidence is context only.",
    27: "The official TDLib README confirms the HTTP Bot API and a local server requiring api_id/api_hash, but opened Telegram core pages returned HTTP 403. The cloud bot-token path, account/plan gates and first-party MCP facts are not fully established; retain UNKNOWN/PARTIAL and do not infer NO.",
    23: "The current Zoho Cliq REST/OAuth page extraction exposed navigation and 'No Results Found' rather than the authentication body. First-party MCP setup and the official API index were inspected, but the precise API auth-method set could not be independently confirmed from the current page capture; retain the first-pass list as unresolved.",
    9: "Copper's official REST/auth/webhook sources and a targeted official-domain MCP search did not establish MCP ownership or absence. Keep UNKNOWN rather than converting a bounded search into NOT_FOUND.",
    91: "Google Cloud's NotebookLM Enterprise API/setup/license pages and targeted official-domain MCP search did not establish a product-specific NotebookLM MCP. Generic Google Cloud MCP services are not attributed to NotebookLM; keep UNKNOWN rather than NO.",
}

# Additional API-interface checks are supplemental; the Webhooks enum represents
# a documented webhook interface, not an assertion that every vendor has a
# standalone REST Webhooks API.
API_TYPE_ADDITIONS = {
    1: {
        "type": "SOAP", "source": "salesforce_soap", "supporting": ["salesforce_rest"],
        "claim": "Salesforce documents SOAP API as a separate programmatic interface for supported editions.",
        "observation": "The current SOAP API guide lists Enterprise, Performance, Unlimited and Developer Editions and the API Enabled permission.",
        "details": "Salesforce REST API supports records, query results, metadata and additional resources; the SOAP API is separately documented for Enterprise, Performance, Unlimited and Developer editions, subject to API Enabled permission. No endpoint count is estimated.",
    },
    9: {
        "type": "Webhooks", "source": "copper_webhooks", "supporting": ["copper_api"],
        "claim": "Copper documents a webhook subscription interface for near-real-time CRM create/update/delete notifications.",
        "observation": "The official overview describes URL subscriptions, event/entity types, HTTPS delivery, subscription/rate limits and no delivery retries.",
        "details": "Copper's Developer API is a RESTful JSON interface for most CRM resources. The separate documented Webhooks interface supports subscriptions for near-real-time create/update/delete notifications on supported entities, HTTPS endpoints, up to 100 active subscriptions and stated delivery limits; this is not described as a general REST Webhooks API.",
    },
}

DETAIL_UPDATES: dict[tuple[int, str], dict] = {
    (13, "api.details"): {
        "value": "The official REST v2 reference documents ticket CRUD, conversations/replies, contacts, companies, agents, ticket fields/forms and other helpdesk resources; quotas are plan-based. Freshdesk automation rules also support outbound webhook actions to external URLs for ticket events. This is webhook-enabled automation, not a separately documented Webhooks API, so api.types remains REST.",
        "source": "freshdesk_webhook", "supporting": ["freshdesk_webhook_examples", "freshdesk_api"],
        "claim": "Freshdesk's first-party support guides describe outbound webhook automation to external endpoints, not a dedicated Webhooks API.",
        "observation": "The automation article and examples configure outbound HTTP/webhook actions; the developer REST API remains a separately documented surface.",
        "reason": "Clarify the directly documented outbound HTTP/webhook behavior without mislabeling it as a dedicated Webhooks API or adding Webhooks to api.types.",
        "error_type": "outbound_webhook_capability_clarified",
    },
    (49, "mcp.details"): {
        "value": "Amazon's selling-partner-api-samples repository contains a first-party Local MCP for SP-API educational example. It is explicitly not a supported product in its own right and is not a hosted Amazon MCP service. Most local developer-assistance tools work without SP-API credentials; tools that execute live SP-API requests or workflows require SP-API credentials.",
        "source": "amazon_local_mcp", "supporting": [],
        "claim": "Amazon's repository documents a local educational MCP example, not a supported hosted product; live SP-API execution requires credentials.",
        "observation": "The README's Important and tool descriptions distinguish local developer assistance from live SP-API execution/workflows.",
        "reason": "The first-pass detail did not distinguish the first-party local educational sample from a supported hosted Amazon MCP product or state which tools require SP-API credentials.",
        "error_type": "mcp_scope_omission",
    },
    (49, "mcp.search_scope"): {
        "value": "Opened Amazon's first-party Local MCP for SP-API README. It documents installation/client setup and states the repository example is educational and unsupported as a product; some developer tools are local while live SP-API calls require credentials. No Amazon-hosted MCP service is inferred.",
        "source": "amazon_local_mcp", "supporting": [],
        "claim": "The inspected first-party README supports the local-example classification and its stated scope.",
        "observation": "Direct README sections cover support status, installation, tool lists and credential prerequisites.",
        "reason": "Replace the incomplete first-pass MCP search note with the directly inspected first-party example and its limitations.",
        "error_type": "source_scope_detail_added",
    },
    (9, "mcp.search_scope"): {
        "value": "Opened Copper's official Developer API landing page, authentication/OAuth material and webhook overview, and ran a targeted official-domain MCP search. The opened pages establish REST, OAuth/API-key and webhook surfaces but do not establish MCP ownership or absence. Search was bounded; status remains UNKNOWN.",
        "source": "copper_api", "supporting": ["copper_webhooks", "copper_oauth"],
        "claim": "The bounded official-source review does not establish Copper MCP availability or absence.",
        "observation": "The inspected developer pages cover REST, credentials and webhooks; the targeted MCP search did not surface a first-party MCP source.",
        "reason": "Record the actual bounded source scope while preserving UNKNOWN rather than treating an empty search as NOT_FOUND.",
        "error_type": "bounded_search_limitation_documented",
    },
    (91, "mcp.search_scope"): {
        "value": "Opened Google Cloud NotebookLM Enterprise API, setup and licensing documentation and ran a targeted first-party Google Cloud search for NotebookLM MCP/Model Context Protocol. Search results included generic Google Cloud MCP references but no NotebookLM Enterprise-specific endpoint/setup; generic services are not attributed to NotebookLM. Status remains UNKNOWN, not NO.",
        "source": "notebooklm_api", "supporting": ["notebooklm_setup", "notebooklm_licensing"],
        "claim": "The bounded official-source inspection did not establish a NotebookLM Enterprise-specific MCP endpoint or entitlement.",
        "observation": "NotebookLM API/setup/licensing pages were inspected; the targeted search returned generic Google Cloud MCP services rather than a product-specific NotebookLM MCP setup.",
        "reason": "Update the search-scope note with the fresh targeted official-source search and explicitly keep generic Google Cloud MCP references separate.",
        "error_type": "bounded_search_limitation_documented",
    },
}


def read_json(rel: str) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_json(rel: str, value: Any) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def get_path(record: dict, dotted_path: str) -> Any:
    current: Any = record
    for part in dotted_path.split("."):
        current = current[part]
    return current


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme.lower()}://{(parsed.hostname or '').lower()}{parsed.path.rstrip('/') or '/'}"


SOURCE_BY_NORMALIZED_URL = {normalize_url(s["source_url"]): key for key, s in SOURCES.items()}


def source_ref(key: str, observation: str | None = None) -> dict:
    spec = SOURCES[key]
    return {
        "source_url": spec["source_url"],
        "source_title": spec["source_title"],
        "source_type": spec["source_type"],
        "observation": observation or spec["observation"],
        "source_capture_key": key,
        "retrieved_on": DATE,
        "retrieval_timestamp_precision": "DATE_ONLY; fetch_page does not expose a per-request timestamp",
    }


def evidence_item(key: str, field: str, claim: str, observation: str | None = None, support: str = "supports") -> dict:
    spec = SOURCES[key]
    return {
        "claim": claim,
        "field": field,
        "source_url": spec["source_url"],
        "source_title": spec["source_title"],
        "source_type": spec["source_type"],
        "accessed_at": DATE,
        "support": support,
        "excerpt_or_observation": observation or spec["observation"],
    }


def raw_field_source(record: dict, evidence_field: str) -> dict:
    candidates = [e for e in record.get("evidence", []) if e.get("field") == evidence_field and e.get("support") == "supports"]
    if not candidates:
        candidates = [e for e in record.get("evidence", []) if e.get("field") == evidence_field and e.get("support") in {"context", "contradicts"}]
    if not candidates:
        raise ValueError(f"app {record.get('app_id')} has no claim evidence for {evidence_field}")
    item = candidates[0]
    normalized = normalize_url(item.get("source_url", ""))
    current_key = SOURCE_BY_NORMALIZED_URL.get(normalized)
    if current_key:
        return source_ref(current_key)
    return {
        "source_url": item["source_url"],
        "source_title": item.get("source_title", ""),
        "source_type": item.get("source_type", "unclassified"),
        "observation": item.get("excerpt_or_observation") or item.get("claim", ""),
        "source_capture_key": None,
        "retrieved_on": item.get("accessed_at"),
        "retrieval_timestamp_precision": "DATE_ONLY; inherited from the preserved first-pass evidence",
    }


def level_for(app: dict, primary: dict, supporting: list[dict]) -> str:
    if not primary.get("source_url"):
        return "UNRESOLVED_IDENTITY_OR_SOURCE_LIMIT"
    first_urls = {normalize_url(e.get("source_url", "")) for e in app.get("evidence", []) if e.get("source_url")}
    refs = [primary, *supporting]
    distinct_support = any(s.get("source_url") and s.get("source_url") != primary.get("source_url") for s in supporting)
    if supporting and distinct_support:
        return "MULTI_SOURCE"
    if normalize_url(primary["source_url"]) in first_urls:
        return "FRESH_REINSPECTION"
    if any(normalize_url(s.get("source_url", "")) not in first_urls for s in refs if s.get("source_url")):
        return "ALTERNATIVE_SOURCE"
    return "FRESH_REINSPECTION"


def add_row(
    app: dict,
    field_path: str,
    *,
    metric_group: str | None = None,
    verified_value: Any | None = None,
    adjudicable: bool = True,
    source_key: str | None = None,
    supporting_keys: list[str] | None = None,
    reason: str = "",
    correction: str = "",
    error_type: str = "",
    evidence_patch: list[dict] | None = None,
    apply_correction: bool = True,
) -> dict:
    initial = copy.deepcopy(get_path(app, field_path))
    if verified_value is None:
        verified_value = copy.deepcopy(initial)
    if source_key:
        primary = source_ref(source_key)
    elif metric_group and app["app_id"] == 84:
        primary = {}
    else:
        field = dict(CORE_FIELDS).get(field_path)
        if field_path.startswith("api."):
            field = "api"
        elif field_path.startswith("mcp."):
            field = "mcp"
        elif field_path.startswith("buildability."):
            field = "buildability"
        primary = raw_field_source(app, field or "other")
    supporting = [source_ref(k) for k in (supporting_keys or [])]
    row = {
        "app_id": app["app_id"],
        "app": app["app"],
        "field_path": field_path,
        "metric_group": metric_group,
        "initial_value": initial,
        "verified_value": copy.deepcopy(verified_value),
        "adjudicable": adjudicable,
        "verifier_type": "automated_independent",
        "method": "Fresh first-party source inspection with Arena.ai native web tools on 2026-09-25; no product account, credential, authenticated API call or MCP session was used. See source capture for URL, extraction status, scope and timestamp precision.",
        "source": primary,
        "supporting_sources": supporting,
        "independence_level": level_for(app, primary, supporting),
        "reason": reason or ("The directly inspected official source supports the first-pass value." if adjudicable else "The bounded first-party evidence did not establish a determinate value; keep UNKNOWN distinct from NO."),
        "correction": correction,
        "error_type": error_type,
        "apply_correction": apply_correction,
        "evidence_patch": copy.deepcopy(evidence_patch or []),
        "verified_at": DATE,
        "verified_at_precision": "DATE_ONLY; exact fetch timestamp unavailable",
    }
    if not adjudicable:
        row["apply_correction"] = False
        row["verified_value"] = copy.deepcopy(initial)
    return row


def search_events() -> list[dict]:
    return [
        {
            "query": '"Paygent Connect" "NMI-powered" app official Paygent Connect',
            "tool": "web_search", "status": "SUCCESS", "retrieved_on": DATE,
            "timestamp_precision": "DATE_ONLY", "used_as_evidence": False,
            "purpose": "Resolve app ID 84 identity only; snippets used as discovery leads, not final evidence.",
            "follow_up": "Opened Paygent Japan and NMI first-party pages; neither links the manifest identity. The unrelated paygent.tech candidate failed direct page inspection with Site Not Found.",
        },
        {
            "query": "site:developer.copper.com \"MCP\" OR \"Model Context Protocol\" Copper",
            "tool": "web_search", "status": "SUCCESS", "retrieved_on": DATE,
            "timestamp_precision": "DATE_ONLY", "used_as_evidence": False,
            "purpose": "Bounded official-domain Copper MCP discovery; not evidence of absence.",
            "follow_up": "Opened Copper's Developer API landing page, OAuth quickstart and webhook overview; no official MCP source was verified. Status remains UNKNOWN.",
        },
        {
            "query": 'site:cloud.google.com OR site:docs.cloud.google.com "NotebookLM Enterprise" MCP "Model Context Protocol"',
            "tool": "web_search", "status": "SUCCESS", "retrieved_on": DATE,
            "timestamp_precision": "DATE_ONLY", "used_as_evidence": False,
            "purpose": "Bounded first-party NotebookLM Enterprise MCP discovery; generic Google Cloud MCP pages are not attributed to NotebookLM.",
            "follow_up": "Opened NotebookLM API, setup and licensing docs. Search results included generic Google Cloud MCP services but did not establish a product-specific NotebookLM server; status remains UNKNOWN.",
        },
    ]


def make_source_capture(rows: list[dict], sample: list[dict], attempts_obj: dict, post_checks: list[dict], post_search_events: list[dict] | None = None) -> dict:
    trace_by_id = {t.get("app_id"): t for t in attempts_obj.get("traces", [])}
    sample_ids = [r["app_id"] for r in sample]
    packets: dict[str, dict] = {}

    def register(ref: dict, app_id: int | None = None, field_path: str | None = None, role: str = "verification") -> None:
        url = ref.get("source_url", "")
        if not url:
            return
        packet_key = url
        packet = packets.get(packet_key)
        capture_key = ref.get("source_capture_key") or SOURCE_BY_NORMALIZED_URL.get(normalize_url(url))
        spec = SOURCES.get(capture_key) if capture_key else None
        if packet is None:
            packet = {
                "source_id": "SRC-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:12],
                "source_url": url,
                "source_title": ref.get("source_title", ""),
                "source_type": ref.get("source_type", "unclassified"),
                "capture_key": capture_key,
                "retrieved_on": spec.get("retrieved_on") if spec else ref.get("retrieved_on"),
                "retrieval_timestamp_precision": "DATE_ONLY; exact fetch time not exposed" if spec else ref.get("retrieval_timestamp_precision", "NOT_CAPTURED_IN_FIRST_PASS_TRACE"),
                "fields_inspected": [],
                "observations": [],
                "capture_roles": [],
                "first_pass_apps": [],
                "first_pass_source_modes": {},
                "verification_apps": [],
                "post_recheck_apps": [],
                "candidate_identity_context_apps": [],
                "first_pass_fetch_recorded": role.startswith("first_pass"),
                "verification_fetch_recorded": role == "verification",
                "post_recheck_fetch_recorded": role == "post_recheck",
                "extraction_attempts": [],
                "extraction_warnings": list(spec.get("warnings", [])) if spec else [],
                "has_more": spec.get("has_more", False) if spec else False,
            }
            if spec:
                packet["observations"].append(spec["observation"])
                packet["extraction_attempts"].extend(
                    {
                        "attempt": index + 1,
                        "tool": "fetch_page",
                        "chunk_index": chunk,
                        "status": spec["status"] if not spec.get("has_more") else "SUCCESS_PARTIAL_CHUNK_HAS_MORE",
                        "retrieved_on": spec["retrieved_on"],
                        "timestamp_precision": spec["timestamp_precision"],
                        "error": None,
                    }
                    for index, chunk in enumerate(spec.get("chunks", [0]))
                )
            packets[packet_key] = packet
        elif capture_key and not packet.get("capture_key"):
            packet["capture_key"] = capture_key
            packet["retrieved_on"] = spec.get("retrieved_on") if spec else packet.get("retrieved_on")
            if spec:
                packet["source_title"] = spec["source_title"]
                packet["source_type"] = spec["source_type"]
                packet["observations"].append(spec["observation"])
                packet["extraction_warnings"].extend(spec.get("warnings", []))
                packet["has_more"] = spec.get("has_more", False)
                packet["extraction_attempts"].extend(
                    {
                        "attempt": index + 1,
                        "tool": "fetch_page",
                        "chunk_index": chunk,
                        "status": spec["status"] if not spec.get("has_more") else "SUCCESS_PARTIAL_CHUNK_HAS_MORE",
                        "retrieved_on": spec["retrieved_on"],
                        "timestamp_precision": spec["timestamp_precision"],
                        "error": None,
                    }
                    for index, chunk in enumerate(spec.get("chunks", [0]))
                )
        if role == "post_recheck" and spec and not packet.get("post_recheck_fetch_recorded"):
            packet["post_recheck_fetch_recorded"] = True
            packet["extraction_attempts"].extend(
                {
                    "attempt": len(packet["extraction_attempts"]) + index + 1,
                    "tool": "fetch_page",
                    "chunk_index": chunk,
                    "status": "SUCCESS_POST_CORRECTION_REINSPECTION" if not spec.get("has_more") else "SUCCESS_POST_CORRECTION_CHUNK_HAS_MORE",
                    "retrieved_on": spec["retrieved_on"],
                    "timestamp_precision": spec["timestamp_precision"],
                    "after_corrected_dataset_generated": True,
                    "error": None,
                }
                for index, chunk in enumerate(spec.get("chunks", [0]))
            )
        if app_id is not None:
            if role.startswith("first_pass"): 
                if app_id not in packet["first_pass_apps"]:
                    packet["first_pass_apps"].append(app_id)
                mode = role.removeprefix("first_pass_")
                packet["first_pass_source_modes"][str(app_id)] = mode
            elif role == "verification":
                if app_id not in packet["verification_apps"]:
                    packet["verification_apps"].append(app_id)
            elif role == "post_recheck":
                if app_id not in packet["post_recheck_apps"]:
                    packet["post_recheck_apps"].append(app_id)
            elif role == "candidate_identity_context_only":
                if app_id not in packet["candidate_identity_context_apps"]:
                    packet["candidate_identity_context_apps"].append(app_id)
        if field_path and field_path not in packet["fields_inspected"]:
            packet["fields_inspected"].append(field_path)
        if role not in packet["capture_roles"]:
            packet["capture_roles"].append(role)
        observation = ref.get("observation")
        if observation and observation not in packet["observations"]:
            packet["observations"].append(observation)

    # Retain every first-pass source packet and its provenance; candidate pages
    # for ID84 are tagged context-only, never field support.
    raw_by_id = {r["app_id"]: r for r in sample}
    for app in sample:
        raw_role = "first_pass_live_agent" if app.get("source_mode") == "LIVE_AGENT" else "first_pass_prior_capture"
        for item in app.get("evidence", []):
            ref = {
                "source_url": item.get("source_url", ""),
                "source_title": item.get("source_title", ""),
                "source_type": item.get("source_type", "unclassified"),
                "observation": item.get("excerpt_or_observation") or item.get("claim", ""),
                "retrieved_on": item.get("accessed_at"),
                "retrieval_timestamp_precision": "DATE_ONLY; inherited from claim-linked first-pass evidence",
            }
            register(ref, app["app_id"], item.get("field"), raw_role)
            if app["app_id"] == 84:
                register(ref, app["app_id"], item.get("field"), "candidate_identity_context_only")

    for row in rows:
        register(row.get("source") or {}, row["app_id"], row["field_path"], "verification")
        for item in row.get("supporting_sources", []):
            register(item, row["app_id"], row["field_path"], "verification")
        for item in row.get("evidence_patch", []):
            register({
                "source_url": item["source_url"], "source_title": item["source_title"],
                "source_type": item["source_type"], "observation": item.get("excerpt_or_observation"),
                "retrieved_on": item.get("accessed_at"),
                "retrieval_timestamp_precision": "DATE_ONLY; verification evidence date",
            }, row["app_id"], row["field_path"], "verification")
    for post in post_checks:
        register(post.get("source") or {}, post["app_id"], post["field_path"], "post_recheck")
        for item in post.get("supporting_sources", []):
            register(item, post["app_id"], post["field_path"], "post_recheck")

    for packet in packets.values():
        if not packet["extraction_attempts"]:
            packet["extraction_attempts"].append({
                "attempt": None,
                "tool": "preserved_first_pass_trace",
                "chunk_index": None,
                "status": "SOURCE_RETAINED_FROM_MIXED_PROVENANCE_FIRST_PASS",
                "retrieved_on": packet.get("retrieved_on"),
                "timestamp_precision": packet.get("retrieval_timestamp_precision"),
                "error": None,
            })
        packet["first_pass_apps"].sort()
        packet["verification_apps"].sort()
        packet["post_recheck_apps"].sort()
        packet["candidate_identity_context_apps"].sort()
        packet["fields_inspected"].sort()
        packet["capture_roles"].sort()

    selected_modes = Counter(app.get("source_mode", "MISSING") for app in sample)
    sample_traces = [copy.deepcopy(trace_by_id[i]) for i in sample_ids if i in trace_by_id]
    failures = [
        {
            "url": "https://core.telegram.org/bots/api", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "HTTP_403", "error": "Telegram core Bot API documentation was inaccessible; search snippets were not used as claim evidence.",
        },
        {
            "url": "https://core.telegram.org/api/obtaining_api_id?setln=en", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "HTTP_403", "error": "Official API ID page was inaccessible; TDLib README only establishes the self-hosted server requirement.",
        },
        {
            "url": "https://www.zoho.com/cliq/help/restapi/v3/oauth/", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "SUCCESS_PARTIAL_NO_RESULTS_SHELL", "error": "The page exposed navigation but rendered 'No Results Found'; no detailed OAuth claims were taken from it.",
        },
        {
            "url": "https://docs.snowflake.com/en/user-guide/snowflake-trial", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "HTTP_404", "error": "An incorrect docs-site trial URL failed; the Snowflake product-site trial page was opened successfully instead.",
            "superseded_by": "https://www.snowflake.com/en/snowflake-trial/",
        },
        {
            "url": "https://developers.grain.com/mcp", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "REDIRECTS_TO_GENERAL_API_OVERVIEW", "error": "The route did not provide an MCP setup guide; the first-party MCP release note and pricing page were used only for availability/endpoint and plan labels.",
        },
        {
            "url": "https://developers.grain.com/mcp.html", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "ACCESS_DENIED", "error": "The detailed MCP route was not accessible; exact MCP authentication/tool entitlements remain unverified.",
        },
        {
            "url": "https://support.freshdesk.com/support/solutions/articles/50000011012-workflow-automator-webhook", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "REDIRECTED_TO_SUPPORT_LOGIN", "error": "The URL redirected to Freshdesk support login and exposed no article body; it is not used as claim evidence. The separate directly opened 132589 automation article is the source used for the Freshdesk distinction.",
        },
        {
            "url": "https://paygent.tech/", "tool": "fetch_page", "retrieved_on": DATE,
            "status": "SITE_NOT_FOUND", "error": "A search-result candidate domain returned a Site Not Found page and was not attributed to app ID 84.",
        },
    ]
    return {
        "capture_id": "final-sample-source-captures-20260925",
        "created_on": DATE,
        "created_at_precision": "DATE_ONLY",
        "raw_research_source_mode_counts_full_population": {"LIVE_AGENT": 76, "PRIOR_CAPTURE": 24},
        "raw_research_source_mode_counts_sample": dict(sorted(selected_modes.items())),
        "verification_capture_mode": "LIVE_AGENT_WEB_REINSPECTION",
        "mode_note": "The sample contains mixed LIVE_AGENT and PRIOR_CAPTURE first-pass rows. Their original labels are preserved. Fresh native web_search/fetch_page inspections are verification-only and do not relabel first-pass data.",
        "manifest_file": MANIFEST_PATH,
        "raw_dataset_file": RAW_PATH,
        "raw_dataset_sha256": sha256_file(RAW_PATH),
        "raw_attempt_log_file": ATTEMPTS_PATH,
        "candidate_selection_file": SELECTION_PATH,
        "verification_ledger_file": LEDGER_PATH,
        "post_recheck_file": POST_PATH,
        "final_dataset_file": "data/verified/final_dataset.json",
        "sample_ids": sample_ids,
        "sample_first_pass_research_traces": sample_traces,
        "source_packets": list(packets.values()),
        "search_events": [*search_events(), *(post_search_events or [])],
        "post_recheck_search_events": copy.deepcopy(post_search_events or []),
        "fetch_failures_and_extraction_limits": failures,
        "retry_accounting": {
            "provider_retries": "Not applicable to the source-assisted verification capture; no provider-backed full-population run was executed in this builder.",
            "verification_tool_retries": 0,
            "note": "Chunk-index fetches are page-extraction steps, not retries. The incorrect Snowflake documentation URL followed by the correct product-site URL is a corrected URL discovery, not a retry of the same request. First-pass retry accounting remains in the original attempt log or is explicitly unmeasurable.",
        },
        "source_packet_count": len(packets),
        "first_pass_evidence_packet_count": sum(len(app.get("evidence", [])) for app in sample),
        "timestamp_note": "Web tools exposed date-only source-inspection precision. Exact per-request times are not fabricated; historical evidence dates remain unchanged.",
    }


def build_checks(sample: list[dict]) -> list[dict]:
    checks: list[dict] = []
    for app in sample:
        app_id = app["app_id"]
        for field_path, _evidence_field in CORE_FIELDS:
            key = (app_id, field_path)
            unresolved = key in UNRESOLVED
            source_key = CORE_SOURCE_KEYS[key]
            support_keys = SUPPORTING_SOURCE_KEYS.get(key, [])
            initial = get_path(app, field_path)
            verified = copy.deepcopy(VERIFIED_OVERRIDES.get(key, initial))
            reason, error_type, correction = CRITICAL_REASONS.get(key, ("", "", ""))
            if unresolved:
                reason = UNRESOLVED_REASONS[app_id]
                error_type = "bounded_identity_or_source_limit"
                correction = "No correction applied; retain the first-pass value and unresolved status until first-party identity/source evidence becomes available."
            patch = []
            if key == (4, "auth_methods"):
                patch = [evidence_item("attio_auth", "auth", "Attio documents OAuth 2.0, API-key tokens, Bearer authorization and HTTP Basic.", "The directly inspected authentication guide documents each method and the HTTP Basic token placement.")]
            elif key == (4, "self_serve_status"):
                patch = [
                    evidence_item("attio_pricing", "self_serve", "Attio lists a no-credit-card Free plan with API/webhook and MCP access.", "The official pricing matrix lists a Free tier and API/MCP features."),
                    evidence_item("attio_mcp", "self_serve", "Attio's first-party hosted MCP uses user OAuth and does not require an API key.", "The MCP guide documents OAuth-based user connection."),
                    evidence_item("attio_admin_key", "self_serve", "Attio workspace API keys remain admin-created and scoped.", "The help article says only workspace admins can create/manage API keys."),
                ]
            elif key == (49, "mcp.status"):
                patch = [evidence_item("amazon_local_mcp", "mcp", "Amazon's official repository documents a first-party local MCP example for SP-API; it is not a supported hosted product.", "The README directly states the educational/unsupported status and describes the local MCP server.")]
            elif app_id == 84:
                patch = []
            src = add_row(
                app, field_path, metric_group=METRIC_GROUP[field_path], verified_value=verified,
                adjudicable=not unresolved, source_key=source_key, supporting_keys=support_keys,
                reason=reason or ("Direct first-party source inspection supports the recorded value; product-specific account entitlement was not tested." if not unresolved else ""),
                correction=correction, error_type=error_type, evidence_patch=patch,
                apply_correction=not unresolved,
            )
            checks.append(src)

    # Supplemental API interface taxonomy changes.
    for app_id, spec in API_TYPE_ADDITIONS.items():
        app = next(x for x in sample if x["app_id"] == app_id)
        initial_types = copy.deepcopy(app["api"]["types"])
        if spec["type"] not in initial_types:
            updated_types = [*initial_types, spec["type"]]
            patch = [evidence_item(spec["source"], "api", spec["claim"], spec["observation"])]
            checks.append(add_row(
                app, "api.types", verified_value=updated_types, source_key=spec["source"],
                supporting_keys=spec["supporting"],
                reason=f"The first-pass api.types list omitted the directly documented {spec['type']} interface. {spec['observation']}",
                correction=f"Add {spec['type']} while preserving all first-pass API types.",
                error_type="api_interface_omission", evidence_patch=patch,
            ))
        checks.append(add_row(
            app, "api.details", verified_value=spec["details"], source_key=spec["source"],
            supporting_keys=spec["supporting"],
            reason=f"Clarify the distinct documented interface and its limits: {spec['observation']}",
            correction="Update API detail to explain the added interface; the raw first-pass detail remains unchanged.",
            error_type="api_scope_detail_added",
            evidence_patch=[evidence_item(spec["source"], "api", spec["claim"], spec["observation"])],
        ))

    for (app_id, field_path), spec in DETAIL_UPDATES.items():
        app = next(x for x in sample if x["app_id"] == app_id)
        patch = [evidence_item(spec["source"], "mcp" if field_path.startswith("mcp.") else "api", spec["claim"], spec["observation"])]
        for support_key in spec.get("supporting", []):
            patch.append(evidence_item(support_key, "mcp" if field_path.startswith("mcp.") else "api", spec["claim"], SOURCES[support_key]["observation"], "context"))
        checks.append(add_row(
            app, field_path, verified_value=spec["value"], source_key=spec["source"],
            supporting_keys=spec.get("supporting", []), reason=spec["reason"],
            correction="Update the corrected narrative/scope; raw first-pass text remains unchanged.",
            error_type=spec["error_type"], evidence_patch=patch,
        ))
    return checks


def validate_inputs(selection: dict, raw: list[dict], attempts: dict, manifest: list[dict]) -> tuple[list[dict], dict[int, dict]]:
    raw_by_id = {r["app_id"]: r for r in raw}
    manifest_ids = {r["app_id"] for r in manifest}
    if len(raw) != 100 or len(raw_by_id) != len(raw) or set(raw_by_id) != manifest_ids:
        raise ValueError("verification builder requires exactly one first-pass record for every manifest ID")
    if len(attempts.get("traces", [])) != 100 or {t.get("app_id") for t in attempts["traces"]} != manifest_ids:
        raise ValueError("verification builder requires one preserved attempt trace for every manifest ID")
    modes = Counter(r.get("source_mode") for r in raw)
    statuses = Counter(r.get("research_status") for r in raw)
    if modes != Counter({"LIVE_AGENT": 76, "PRIOR_CAPTURE": 24}):
        raise ValueError(f"unexpected full-population provenance distribution: {dict(modes)}")
    if sum(statuses.get(s, 0) for s in ("COMPLETE", "PARTIAL")) != 100:
        raise ValueError(f"full-population research gate is incomplete: {dict(statuses)}")
    if selection.get("status") != "REPRODUCIBLE_COVERAGE_SAMPLE_FROM_FULLY_RESEARCHED_POPULATION":
        raise ValueError("sample selection does not show the full-population research gate")
    ids = selection.get("selected_ids", [])
    if len(ids) != 20 or len(set(ids)) != 20 or any(i not in raw_by_id for i in ids):
        raise ValueError("selection must contain 20 unique IDs present in the full research dataset")
    if ids != [22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9]:
        raise ValueError("sample IDs differ from the user-approved full-population coverage sample")
    sample = [raw_by_id[i] for i in ids]
    selected_modes = Counter(r.get("source_mode") for r in sample)
    if selected_modes != Counter({"LIVE_AGENT": 14, "PRIOR_CAPTURE": 6}):
        raise ValueError(f"unexpected mixed-provenance sample distribution: {dict(selected_modes)}")
    if any(r.get("source_mode") not in {"LIVE_AGENT", "PRIOR_CAPTURE"} for r in sample):
        raise ValueError("selected record has missing/NOT_RUN provenance")
    return sample, raw_by_id


def build_post_obj(post_recheck_input: str | None) -> dict:
    if post_recheck_input:
        payload = read_json(post_recheck_input)
        checks = payload.get("checks", [])
        if not checks:
            raise ValueError("post-recheck input was supplied but contains no explicit observations")
        return {
            "audit_id": payload.get("audit_id", "final-post-correction-audit-20260925"),
            "created_on": payload.get("created_on", DATE),
            "created_at_precision": payload.get("created_at_precision", "DATE_ONLY"),
            "verification_capture_mode": "LIVE_AGENT_WEB_REINSPECTION_AFTER_CORRECTION",
            "capture_source_file": CAPTURE_PATH,
            "checks": checks,
            "search_events": payload.get("search_events", []),
            "status": "SEPARATE_POST_CORRECTION_RECHECK_CAPTURED",
            "notes": payload.get("notes", []),
        }
    return {
        "audit_id": "final-post-correction-audit-20260925",
        "created_on": DATE,
        "created_at_precision": "DATE_ONLY",
        "verification_capture_mode": "LIVE_AGENT_WEB_REINSPECTION_AFTER_CORRECTION",
        "capture_source_file": CAPTURE_PATH,
        "checks": [],
        "status": "PENDING_SEPARATE_POST_CORRECTION_RECHECK",
        "notes": [
            "No post-correction checks are populated at primary-verification time.",
            "A separate direct source inspection must occur after corrected values are produced; the runner must not copy verified_value into this file.",
            "Only changed rows will receive a post-recheck entry. Unchanged rows will remain explicitly not rechecked.",
        ],
    }


def build_nomenclature_audit() -> dict:
    raw = read_json(RAW_PATH)
    raw_by_id = {r["app_id"]: r for r in raw}
    return {
        "created_on": DATE,
        "scope": "Targeted terminology check outside the 20-app accuracy sample; does not change sample denominators or correction metrics.",
        "findings": [
            {
                "app_id": 13,
                "app": raw_by_id[13]["app"],
                "api_types_in_raw_first_pass": raw_by_id[13]["api"]["types"],
                "verified_dataset_api_types_after_correction": ["REST"],
                "official_sources": [source_ref("freshdesk_webhook"), source_ref("freshdesk_webhook_examples"), source_ref("freshdesk_api")],
                "conclusion": "Freshdesk exposes a REST API and outbound webhook automation to external URLs. The inspected docs do not establish a dedicated standalone Webhooks API; do not add Webhooks to api.types on this basis.",
            },
            {
                "app_id": 19,
                "app": raw_by_id[19]["app"],
                "api_types_in_raw_first_pass": raw_by_id[19]["api"]["types"],
                "official_sources": [source_ref("gorgias_http"), source_ref("gorgias_sync")],
                "conclusion": "Gorgias first-party docs describe outbound HTTP integrations and webhook actions for ticket/message events. This is not a dedicated Webhooks API; the retained interface classification remains REST, with webhook capability described narratively.",
            },
            {
                "app_id": 9,
                "app": raw_by_id[9]["app"],
                "official_sources": [source_ref("copper_webhooks")],
                "conclusion": "Copper's docs explicitly define subscriptions and event callbacks for a webhook subsystem. The analysis records a Webhooks interface, but does not claim a general REST Webhooks API.",
            },
        ],
        "guardrail": "A webhook interface, dedicated webhook-management API, and outbound automation action are distinct. Freshdesk and Gorgias are not represented as dedicated Webhooks APIs.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build fresh source-backed verification inputs from the final full-population sample.")
    parser.add_argument("--post-recheck-input", default=None, help="Explicit second-pass JSON; supply only after separate post-correction page inspections.")
    args = parser.parse_args()

    selection = read_json(SELECTION_PATH)
    raw = read_json(RAW_PATH)
    attempts = read_json(ATTEMPTS_PATH)
    manifest = read_json(MANIFEST_PATH)
    sample, raw_by_id = validate_inputs(selection, raw, attempts, manifest)
    checks = build_checks(sample)

    # Exactly six critical rows per selected record; supplemental rows remain separate.
    core = [r for r in checks if r.get("metric_group")]
    if len(core) != 120 or len({(r["app_id"], r["field_path"]) for r in core}) != 120:
        raise ValueError("primary verification must contain exactly six unique critical checks per selected app")
    if any(get_path(raw_by_id[r["app_id"]], r["field_path"]) != r["initial_value"] for r in checks):
        raise ValueError("a verification initial_value does not match the preserved raw first pass")

    mode_counts = Counter(r.get("source_mode") for r in sample)
    ledger_obj = {
        "created_on": DATE,
        "created_at_precision": "DATE_ONLY",
        "capture_id": "final-sample-source-captures-20260925",
        "raw_dataset": RAW_PATH,
        "raw_dataset_sha256": sha256_file(RAW_PATH),
        "sample_selection": SELECTION_PATH,
        "sample_ids": [r["app_id"] for r in sample],
        "raw_source_mode_counts": dict(sorted(mode_counts.items())),
        "full_population_source_mode_counts": {"LIVE_AGENT": 76, "PRIOR_CAPTURE": 24},
        "verification_capture_mode": "LIVE_AGENT_WEB_REINSPECTION",
        "verifier_type": "automated_independent; no human review or account access claimed",
        "checks": checks,
        "notes": [
            "The reproducible 20-app sample was selected after all 100 canonical apps had COMPLETE/PARTIAL research records. It is a weighted coverage audit sample, not a probability sample.",
            "The selected sample is mixed-provenance: 14 LIVE_AGENT and 6 PRIOR_CAPTURE records; first-pass labels are not altered or homogenized.",
            "Search snippets are discovery leads only. Claim adjudication refers to directly opened official/vendor-owned pages or an explicit unresolved scope/identity limit.",
            "ID84's product identity remains unresolved; all six product-specific critical fields remain UNKNOWN and are not adjudicated by candidate-product pages.",
            "ID27 cloud bot onboarding/authentication and MCP remain unresolved where official pages were blocked; the TDLib README does not settle those fields.",
            "ID23's REST/OAuth page extraction rendered 'No Results Found'; its API auth_methods remains unresolved rather than inferred from the page navigation.",
            "ID9 Copper and ID91 NotebookLM MCP values remain UNKNOWN where first-party product-specific availability/absence was not established.",
            "Raw first-pass values/evidence in data/raw/final_full_research.json remain unchanged. Primary verification does not include a post-correction recheck.",
        ],
    }
    post_obj = build_post_obj(args.post_recheck_input)
    capture_obj = make_source_capture(checks, sample, attempts, post_obj["checks"], post_obj.get("search_events", []))
    write_json(LEDGER_PATH, ledger_obj)
    write_json(POST_PATH, post_obj)
    write_json(CAPTURE_PATH, capture_obj)
    write_json("data/evidence/api_webhook_nomenclature_audit.json", build_nomenclature_audit())
    print(f"Wrote {len(checks)} primary ledger rows: {len(core)} critical across {len(sample)} apps, {len(checks)-len(core)} supplemental; post-recheck rows={len(post_obj['checks'])}; source packets={capture_obj['source_packet_count']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

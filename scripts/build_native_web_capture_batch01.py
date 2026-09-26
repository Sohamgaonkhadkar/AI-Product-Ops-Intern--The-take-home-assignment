#!/usr/bin/env python3
"""Assemble the first manually researched native-web evidence batch.

This writes an evidence/capture artifact only. It deliberately does not replace
final_full_research.json: the remaining manifest apps still require research.
Search-result snippets are never copied into claim evidence; every cited claim
below points to an opened official page (or an official vendor GitHub repository).
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.quality import validate_record_quality
from src.utils.validation import validate_record

DATE = "2026-09-24"
RUN_ID = "arena-native-web-batch01-20260924"
TOOL = "Arena.ai Agent Mode native web_search + fetch_page; official-source-led manual research"


def source(url: str, title: str, source_type: str, observation: str, chunks=(0,)) -> dict:
    return {
        "url": url,
        "title": title,
        "source_type": source_type,
        "capture_method": "fetch_page",
        "capture_status": "OPENED",
        "retrieved_at": DATE,
        "retrieval_precision": "DATE_ONLY; fetch_page does not expose a per-page clock time",
        "retrieved_chunk_indexes": list(chunks),
        "excerpt_or_observation": observation,
    }


SOURCES = {
    # Slack (app_id 21)
    "slack_web": source(
        "https://docs.slack.dev/apis/web-api/", "Slack Web API | Slack Developer Docs", "official_api_docs",
        "The page describes the Web API as querying information from and enacting changes in a Slack workspace. It calls the methods HTTP RPC-style methods, explicitly says it is not a REST API, and documents bearer-token authorization for JSON requests.", (0,)
    ),
    "slack_mcp": source(
        "https://docs.slack.dev/ai/slack-mcp-server/", "Overview | Slack Developer Docs", "official_docs",
        "Official Slack MCP endpoint is https://mcp.slack.com/mcp over Streamable HTTP. The page lists search/read/write tools across messages, channels, files, users, canvases and lists. Chunk 1 documents confidential OAuth, client ID/secret, consent/scopes, app registration, and says only directory-published or internal apps may use MCP; workspace admins can manage/approve apps.", (0, 1)
    ),
    "slack_pricing": source(
        "https://slack.com/pricing", "Slack Pricing Plans: Find the Right Fit for Your Team | Slack", "official_pricing",
        "The official pricing page lists a Free plan at $0 with self-serve Get Started and up to 10 apps, plus paid self-serve Pro and Business+ plans. It does not state that every API method or MCP feature is enabled on every plan.", (0,)
    ),

    # Zoho Cliq (app_id 23)
    "zoho_api": source(
        "https://www.zoho.com/cliq/help/restapi/v3/introduction/", "Introduction | Zoho Cliq | API Documentation", "official_api_docs",
        "Official REST API V3 documentation with navigation for chats, messages, channels, users, bots, extensions, functions, databases, and related resources; docs expose an OAuth 2.0 section and API reference.", (0,)
    ),
    "zoho_oauth": source(
        "https://www.zoho.com/cliq/help/restapi/v3/oauth/", "Introduction to OAuth 2.0 | Zoho Cliq | API Documentation", "official_auth_docs",
        "The opened OAuth documentation says developers register an app in Zoho API Console to receive a Client ID and Client Secret; access is granted only after the user consents, tokens are scoped, and API requests use the Zoho-oauthtoken bearer scheme. The scopes table includes channels, chats, messages, users, bots and other resources.", (0, 4)
    ),
    "zoho_mcp_setup": source(
        "https://www.zoho.com/cliq/help/platform/configure-zoho-cliq-mcp.html", "Configuring Your Zoho MCP Server", "official_docs",
        "Zoho’s setup guide requires valid authenticated credentials for selected services, directs users to the Zoho MCP console, lets them choose Zoho Cliq tools, and says a unique secure MCP URL is generated for each server. This supports the setup path, not proof of a specific account’s access.", (0,)
    ),
    "zoho_mcp": source(
        "https://www.zoho.com/cliq/help/platform/zoho-cliq-mcp.html", "Guide to Zoho Cliq's MCP Server", "official_docs",
        "Zoho identifies an official Cliq MCP Server and describes actions including sending/scheduling messages, reminders, channel organization, threads and participants. The guide links to free signup and plan comparison.", (0, 1)
    ),
    "zoho_pricing": source(
        "https://www.zoho.com/cliq/pricing.html", "Cliq - Chat Pricing | Free Chat plans for all Teams size", "official_pricing",
        "The official pricing page lists a Free plan at US$0 with Try Now/Get Started, plus paid Standard, Professional and Enterprise plans. The page does not map each API scope to a particular paid tier.", (0,)
    ),

    # Lark (app_id 24)
    "lark_repo": source(
        "https://github.com/larksuite/lark-openapi-mcp", "GitHub - larksuite/lark-openapi-mcp: Feishu/Lark official OpenAPI MCP", "official_github",
        "The larksuite repository labels this the official Feishu/Lark OpenAPI MCP, says it wraps Open Platform API interfaces as MCP tools, and marks the project Beta. Its preparation steps require creating an app, obtaining App ID/App Secret, and adding permissions.", (0,)
    ),
    "lark_readme": source(
        "https://github.com/larksuite/lark-openapi-mcp/blob/main/README.md", "lark-openapi-mcp/README.md at main · larksuite/lark-openapi-mcp · GitHub", "official_github",
        "The opened README documents local MCP configuration with App ID/App Secret, optional OAuth/user_access_token mode, and domain selection for international Lark. It lists API tool presets and explicitly notes that file upload/download and direct document editing are not supported in the inspected version.", (1,)
    ),
    "lark_rate": source(
        "https://open.larksuite.com/document/server-docs/getting-started/frequency-control", "Rate limits - Server API - Documentation - Lark Developer", "official_api_docs",
        "Lark Open Platform documents per-API/app/tenant rate limits and different levels by app package. This is evidence of an official API platform and package/tenant-specific restrictions, not a universal plan price.", (0,)
    ),
    "lark_endpoint": source(
        "https://open.larksuite.com/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/search", "Search records - Server API - Documentation - Lark Developer", "official_api_docs",
        "The official endpoint is POST https://open.larksuite.com/open-apis/bitable/v1/.../records/search, requires JSON and Bearer tenant_access_token or user_access_token, and lists required scopes. Its docs show several create/read/update/delete APIs in the adjacent Base resource navigation.", (0,)
    ),

    # Pumble (app_id 25)
    "pumble_api": source(
        "https://pumble.com/help/integrations/automation-workflow-integrations/api-keys-integration/", "Pumble API Overview - Pumble Help", "official_support",
        "Pumble says its API add-on is available on all plans to Owners, Admins and Members. Users install the add-on in a workspace and generate API keys there; listed actions include send/reply/delete messages, reactions, channel creation and listing. Rate limit is stated as up to 1,000 requests/minute/user.", (0,)
    ),
    "pumble_openapi": source(
        "https://pumble-api-keys.addons.marketplace.cake.com/api-docs/", "Scalar API Reference", "official_api_docs",
        "The Pumble API add-on's linked OpenAPI 3.0 reference labels authentication as ApiKeyAuth and shows JSON API operations for users, scheduled messages, messages and channels, including send/search/edit/delete/list actions.", (0,)
    ),
    "pumble_mcp": source(
        "https://pumble.com/help/integrations/automation-workflow-integrations/how-to-use-the-pumble-mcp-server/", "How to use the Pumble MCP server - Pumble Help", "official_support",
        "Pumble documents a hosted MCP endpoint https://mcp.pumble.com/mcp. Setup requires creating/installing a workspace app and copying App key plus user/bot token; the tool set depends on selected scopes and includes search/read/write messages, channels, users and scheduled messages.", (0, 1)
    ),
    "pumble_ai": source(
        "https://pumble.com/learn/pumble/ai-automation-guide/", "How to Use AI & Automation in Pumble (API, MCP, AI Assistant)", "official_docs",
        "Pumble’s own Aug. 19, 2026 article describes the API add-on as simple HTTP endpoints for messaging actions, explicitly says it lacks an Events API, and separately describes a Pumble MCP server for search/read/actions. The help center remains the primary source for entitlements and setup.", (0,)
    ),

    # Discord (app_id 26)
    "discord_api": source(
        "https://docs.discord.com/developers/reference", "API Reference - Documentation - Discord", "official_api_docs",
        "Discord describes its API as a REST API with base URL https://discord.com/api and documents bot-token, OAuth2 bearer-token and token-endpoint Basic authentication.", (0,)
    ),
    "discord_oauth": source(
        "https://docs.discord.com/developers/topics/oauth2", "OAuth2 - Documentation - Discord", "official_auth_docs",
        "Discord says developers register an application in the Developer Portal and supports authorization code, implicit, client credentials and bot/webhook-specific flows; some OAuth scopes require Discord approval or partner access.", (0,)
    ),
    "discord_app": source(
        "https://docs.discord.com/developers/resources/application", "Application Resource - Documentation - Discord", "official_docs",
        "Discord application docs define server and user installation contexts, OAuth install settings, event webhooks, and app authorization/install counts; this source supports app setup and installation constraints.", (0,)
    ),

    # Telegram (app_id 27); core.telegram.org fetches were blocked, so GitHub captures are narrow.
    "telegram_repo": source(
        "https://github.com/tdlib/telegram-bot-api", "GitHub - tdlib/telegram-bot-api: Telegram Bot API server", "official_github",
        "The TDLib repository identifies itself as the Telegram Bot API server and says it provides an HTTP API for creating Telegram bots; the repository was updated in Aug. 2026 when inspected.", (0,)
    ),
    "telegram_readme": source(
        "https://github.com/tdlib/telegram-bot-api/blob/master/README.md", "telegram-bot-api/README.md at master · tdlib/telegram-bot-api · GitHub", "official_github",
        "The official repository README says the Bot API is an HTTP API. For a self-hosted local Bot API server, the mandatory options include api_id and api_hash obtained through the linked Telegram developer flow. This does not establish the cloud Bot API bot-token acquisition path, which remained unverified because core.telegram.org pages returned HTTP 403.", (0,)
    ),

    # WhatsApp Business (app_id 28)
    "whatsapp_get_started": source(
        "https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started", "WhatsApp Cloud API Get Started | Developer Documentation", "official_docs",
        "Meta’s June 2026 guide describes developer registration, creating a Meta app, connecting/creating a Messaging account, a temporary test token and test phone number, and then a system-user token with business_management, whatsapp_business_messaging and whatsapp_business_management permissions. It also documents webhooks and a production business-number path.", (0, 1)
    ),
    "whatsapp_messages": source(
        "https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-phone-number/message-api", "WhatsApp Cloud API - Message API | Developer Documentation", "official_api_docs",
        "The official reference documents POST /{Version}/{Phone-Number-ID}/messages at graph.facebook.com with Authorization: Bearer token; supported payloads include text, media, templates, interactive messages, reactions and more.", (0,)
    ),
    "whatsapp_pricing": source(
        "https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing", "Pricing on the WhatsApp Business Platform | Developer Documentation", "official_pricing",
        "Meta’s pricing page was updated Sep. 10, 2026. It states Cloud API charges are per delivered template message, varying by category and recipient country; non-template messages are free in an open customer-service window, with further dated pricing updates noted for 2026.", (0,)
    ),

    # Aircall (app_id 29)
    "aircall_auth": source(
        "https://developer.aircall.io/docs/authentication", "Overview", "official_auth_docs",
        "Aircall documents Basic Auth (API ID/token generated in dashboard) for internal/private integrations and OAuth for apps serving multiple Aircall customers; OAuth is for approved tech partners/public integrations.", (0,)
    ),
    "aircall_api": source(
        "https://developers.aircall.io/api-references/", "API References | Aircall", "official_api_docs",
        "Aircall labels the product REST API and documents Basic Auth for customers plus OAuth for technology partners. The reference navigation includes users, teams, calls, dialer/outbound campaigns, numbers and other resources.", (0,)
    ),
    "aircall_outbound": source(
        "https://developer.aircall.io/docs/outbound-calls", "Start an outbound call", "official_docs",
        "Aircall’s guide documents POST /v1/users/:id/calls, customer or qualifying tech-partner account setup, authentication choice, and requirement that the user be assigned to the Aircall number. This is a specific API workflow, not evidence of a dedicated Webhooks API.", (0,)
    ),

    # Vonage (app_id 30)
    "vonage_api": source(
        "https://developer.vonage.com/en/api", "API", "official_api_docs",
        "Vonage’s official API index lists messaging, SMS, voice, numbers, verification, applications, account, pricing, reports and related API families; multiple entries are documented as REST endpoints and the index distinguishes beta/developer-preview APIs.", (0,)
    ),
    "vonage_auth": source(
        "https://developer.vonage.com/en/verify/concepts/authentication", "Authentication API Guide | Vonage API Documentation", "official_auth_docs",
        "The guide documents Basic Auth using dashboard API key/API secret and JWT Bearer auth signed with an Application ID/private key; some operations/webhooks require an application and JWT.", (0,)
    ),
    "vonage_tooling_mcp": source(
        "https://developer.vonage.com/en/blog/access-the-vonage-tooling-mcp-server-on-google-antigravity", "Access the Vonage Tooling MCP Server on Google Antigravity", "official_blog",
        "Vonage’s July 15, 2026 developer guide demonstrates configuring @vonage/vonage-mcp-server-api-bindings with API key/secret and calling an SMS tool. It says an account can start with free credit and the example purchases a virtual number. The linked implementation repository is under Vonage-Community, so vendor documentation is confirmed but repository ownership/maintenance is not independently assumed.", (0,)
    ),
    "vonage_mcp_announcement": source(
        "https://developer.vonage.com/en/blog/introducing-mcp-ai-meets-programmable-communications-with-vonage", "Introducing MCP: AI Meets Programmable Communications With Vonage", "official_blog",
        "Vonage announced a live Documentation MCP server and described the tooling server roadmap in Oct. 2025; later official July 2026 guidance demonstrates the Tooling MCP package. The newer documentation is treated as current evidence for the operational/tooling server.", (0,)
    ),

    # Google Ads (app_id 31)
    "google_quickstart": source(
        "https://developers.google.com/google-ads/api/docs/get-started/make-first-call", "Quick start | Google Ads API | Google for Developers", "official_api_docs",
        "Google’s quick start documents calls to the Google Ads API, Google Cloud project, Google Ads manager/client account, developer token, OAuth 2.0 and service-account credentials; API access level controls production access and quotas.", (0,)
    ),
    "google_access": source(
        "https://developers.google.com/google-ads/api/docs/api-policy/access-levels", "Access levels and permissible use | Google Ads API | Google for Developers", "official_docs",
        "Google says access begins at Test for test accounts and higher production access levels require additional application steps; access level and permissible use control production availability, quota and features.", (0,)
    ),
    "google_mcp": source(
        "https://developers.google.com/google-ads/api/docs/developer-toolkit/mcp-server", "Google Ads MCP server: Developer integration guide | Google Ads API | Google for Developers", "official_docs",
        "Google documents an official MCP server, currently read-only, using OAuth 2.0 or service accounts and a Google Cloud project with Ads API access. It exposes customer discovery, GAQL search and resource metadata; configuration uses the googleads/google-ads-mcp repository.", (0, 1)
    ),
    "google_pricing": source(
        "https://developers.google.com/google-ads/api/docs/productionize/access-levels", "Access levels and RMF | Google Ads API | Google for Developers", "official_docs",
        "Google states the Google Ads API is free at Explorer, Basic and Standard access levels, while Standard access is subject to Required Minimum Functionality review and non-compliance fees may apply.", (0,)
    ),
}

# The first ten lead searches occurred in an earlier tool turn. The session log
# preserves which apps were searched but not the exact query text; that loss is
# explicitly represented, never replaced with invented wording.
PRIOR_LEAD_QUERY = {
    "query": None,
    "query_details_status": "NOT_PRESERVED_IN_PRIOR_TURN_SUMMARY",
    "depth": "1",
    "lead_only": True,
    "note": "The prior session log confirms one initial native web_search for this app; exact query text is unavailable. Search snippet was not used as evidence.",
}

QUERIES = {
    21: [
        "site:api.slack.com OR site:docs.slack.dev Slack official MCP server OAuth remote MCP endpoint",
        "site:slack.com/pricing Slack API app pricing free plan API access official",
    ],
    23: [
        "site:zoho.com/cliq OR site:zoho.com MCP server Zoho Cliq official MCP",
        "site:www.zoho.com/cliq/help/restapi/v3/oauth/ Cliq OAuth scopes client register official token authentication",
    ],
    24: [
        "site:open.larksuite.com/document OR site:github.com/larksuite/lark-openapi-mcp Lark API auth pricing plans MCP official",
        "site:open.larksuite.com/document Lark OpenAPI authentication API rate limits pricing official",
        "site:open.larksuite.com/document authentication access token create app secret OAuth Lark OpenAPI official",
    ],
    25: [
        "site:pumble.com OR site:docs.pumble.com Pumble API addon MCP server pricing API keys",
        "site:pumble.com/pricing Pumble pricing API addon all plans API keys",
        "site:pumble.com/help/integrations/automation-workflow-integrations/how-to-use-the-pumble-mcp-server Pumble MCP setup official",
    ],
    26: [
        "site:docs.discord.com/developers Discord MCP server official API OAuth authentication docs",
        "site:discord.com/developers/docs MCP server Discord official developers",
    ],
    27: [
        "site:core.telegram.org Telegram Bot API authentication developer account official MCP server",
        "site:core.telegram.org MCP Telegram official Model Context Protocol server",
        "site:core.telegram.org/bots/api Bot API token BotFather HTTP API official Telegram",
        "site:telegram.org/faq botfather create bot token official Telegram API HTTP Bot API",
        "site:github.com/tdlib/telegram-bot-api official Telegram Bot API server API documentation authentication",
        "site:telegram.org Bot API developers botfather token official create bot",
    ],
    28: [
        "site:developers.facebook.com/docs/whatsapp WhatsApp Business Platform Cloud API authentication pricing MCP server official",
        "site:developers.facebook.com/docs/whatsapp/cloud-api/get-started Cloud API authentication access token test number setup official",
        "site:developers.facebook.com/docs/whatsapp pricing Cloud API per message free business platform official 2026",
    ],
    29: [
        "site:developer.aircall.io Aircall API authentication Basic OAuth pricing official MCP",
        "site:developer.aircall.io MCP server Aircall official API key OAuth pricing official",
        "site:developer.aircall.io/api-references Aircall REST API endpoints authentication Basic OAuth official",
        "site:developer.aircall.io/pricing Aircall API public API available Professional plan tech partner MCP official",
    ],
    30: [
        "site:developer.vonage.com API authentication official MCP documentation server pricing",
        "site:developer.vonage.com/en/api API authentication official developer pricing",
        "site:developer.vonage.com authentication API key secret JWT official docs Vonage",
        "site:developer.vonage.com/en/blog Vonage MCP API bindings tooling official November 2025",
    ],
    31: [
        "site:developers.google.com/google-ads Google Ads MCP server official docs API authentication developer token pricing",
        "site:developers.google.com/google-ads/api MCP server official Google Ads MCP docs read-only OAuth developer token",
        "site:developers.google.com/google-ads/api/docs/api-policy/access-levels developer token access levels application approval official Google Ads",
        "site:developers.google.com/google-ads/api pricing free API no charges developer token access official",
    ],
}

# Fetch calls not represented as evidence sources because the requested page did
# not open or returned no usable captured text. They remain in the attempt log.
FAILED_FETCHES = {
    21: [
        {"url": "https://api.slack.com/web", "chunk_index": 0, "status": "HTTP_403", "note": "Retried with the current docs.slack.dev Web API documentation, which opened successfully."},
    ],
    24: [
        {"url": "https://open.larksuite.com/document/uAjLw4CM/ukTMukTMukTM/mcp_integration/advanced-configuration", "chunk_index": 0, "status": "OPENED_NO_USABLE_BODY", "note": "Returned only page chrome; not treated as evidence."},
    ],
    27: [
        {"url": "https://core.telegram.org/bots/api", "chunk_index": 0, "status": "HTTP_403", "note": "Official core docs page could not be inspected; search result was not used as evidence."},
        {"url": "https://core.telegram.org/bots/api?setln=en", "chunk_index": 0, "status": "HTTP_403", "note": "Retry with language parameter also failed."},
        {"url": "https://core.telegram.org/bots/features#botfather", "chunk_index": 0, "status": "HTTP_403", "note": "Official BotFather page could not be inspected; search result was not used as evidence."},
        {"url": "https://core.telegram.org/api/obtaining_api_id?setln=en", "chunk_index": 0, "status": "HTTP_403", "note": "Official API ID page could not be inspected; search result was not used as evidence."},
        {"url": "https://core.telegram.org/bots", "chunk_index": 0, "status": "HTTP_403", "note": "Official bot overview could not be inspected; search result was not used as evidence."},
        {"url": "https://core.telegram.org/bots/features", "chunk_index": 0, "status": "HTTP_403", "note": "Official feature page could not be inspected; search result was not used as evidence."},
        {"url": "https://telegram.org/faq", "chunk_index": 0, "status": "HTTP_403", "note": "FAQ page could not be inspected; search result was not used as evidence."},
    ],
}

# Fetch-page call count per successful source. Repeated chunk calls are explicit.
FETCH_COUNTS = {
    21: {"slack_web": [0], "slack_mcp": [0, 1], "slack_pricing": [0]},
    23: {"zoho_api": [0], "zoho_oauth": [0, 4], "zoho_mcp_setup": [0], "zoho_mcp": [0, 1], "zoho_pricing": [0]},
    24: {"lark_repo": [0], "lark_readme": [1], "lark_rate": [0], "lark_endpoint": [0]},
    25: {"pumble_api": [0], "pumble_openapi": [0], "pumble_mcp": [0, 1], "pumble_ai": [0]},
    26: {"discord_api": [0], "discord_oauth": [0], "discord_app": [0]},
    27: {"telegram_repo": [0], "telegram_readme": [0]},
    28: {"whatsapp_get_started": [0, 1], "whatsapp_messages": [0], "whatsapp_pricing": [0]},
    29: {"aircall_auth": [0], "aircall_api": [0], "aircall_outbound": [0]},
    30: {"vonage_api": [0], "vonage_auth": [0], "vonage_tooling_mcp": [0], "vonage_mcp_announcement": [0]},
    31: {"google_quickstart": [0], "google_access": [0], "google_mcp": [0, 1], "google_pricing": [0]},
}


def ev(field: str, claim: str, source_key: str, observation: str | None = None, support="supports") -> dict:
    s = SOURCES[source_key]
    item = {
        "claim": claim,
        "field": field,
        "source_url": s["url"],
        "source_title": s["title"],
        "source_type": s["source_type"],
        "accessed_at": DATE,
        "support": support,
        "excerpt_or_observation": observation or s["excerpt_or_observation"],
    }
    return item


RECORDS = {
    21: {
        "description": "Workplace messaging and collaboration app; its Web API queries information from and enacts changes in a Slack workspace.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "The official pricing page lists a Free $0 workspace and self-serve signup. This does not establish that every Web API method or MCP feature is available on every plan; OAuth scopes and workspace/admin policies apply.",
        "credential_access": {"status": "RESTRICTED", "path": "Register or reuse a Slack app, then complete OAuth consent for user scopes; for MCP, configure the app/client and authorize it in the workspace.", "plan_or_gate": "MCP is limited to directory-published or internal apps, with workspace-admin approval/management and scopes; Web API method limits/entitlements are method/workspace-specific and not exhaustively plan-audited here."},
        "api": {"available": "YES", "types": ["RPC"], "breadth": "BROAD", "details": "Slack explicitly describes the Web API as HTTP RPC-style methods (not REST). The official MCP docs enumerate broad message, channel, file, user, canvas, and list actions; rate limits remain method-specific."},
        "mcp": {"status": "AVAILABLE", "details": "Official remote Slack MCP server at https://mcp.slack.com/mcp over Streamable HTTP. Supports search/read/write actions across messages, channels, files, users, canvases, and lists; confidential OAuth and an eligible internal or directory-published Slack app are required.", "search_scope": "Opened Slack's official MCP overview and authentication sections (including endpoint, OAuth, scopes, app publishing constraints) and official Web API documentation."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Slack workspace, registered app, user OAuth/scopes, and applicable admin approval; MCP app eligibility is restricted to internal or directory-published apps.", "rationale": "Documented Web API methods and a first-party hosted MCP endpoint make technical integration feasible. OAuth consent, scopes, app-eligibility rules, workspace governance, and method-level limits prevent calling the path universally frictionless."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["No Slack tenant was authenticated or tested; pricing page was used only to establish a self-serve free workspace path, not universal API entitlement."],
        "evidence": [
            ev("description", "Slack describes its Web API as querying information from and enacting changes in a Slack workspace.", "slack_web"),
            ev("auth", "Slack API requests use bearer tokens under OAuth 2.0; MCP clients additionally use app client credentials and user consent.", "slack_web"),
            ev("self_serve", "Slack offers a self-serve Free plan at $0, but API/MCP entitlements remain subject to method scopes and workspace rules.", "slack_pricing"),
            ev("credential_access", "MCP credentials are obtained through a registered Slack app and user OAuth; only internal or directory-published apps may use the official server and admins manage approval.", "slack_mcp"),
            ev("api", "The Slack Web API is a collection of HTTP RPC-style methods and is explicitly not described as REST.", "slack_web"),
            ev("mcp", "Slack documents the official hosted MCP endpoint and its Streamable HTTP transport, tool families, OAuth, and app restrictions.", "slack_mcp"),
            ev("buildability", "The official Slack MCP server and documented OAuth/app flow support a build path, subject to scope, publication and workspace-admin constraints.", "slack_mcp"),
        ],
    },
    23: {
        "description": "Team messaging and workplace collaboration product with an official REST API for chats, channels, messages, users, bots, and related resources.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Cliq pricing lists a Free $0 plan with Try Now/Get Started. The API path involves developer-console app registration, scoped OAuth and user consent; inspected material does not map every API scope to a particular plan.",
        "credential_access": {"status": "SELF_SERVE", "path": "Register an application in Zoho API Console to obtain client ID/secret, request scopes, obtain user consent, and use scoped OAuth access/refresh tokens. Zoho MCP setup separately creates a server and generated secure MCP URL.", "plan_or_gate": "Free plan is listed. Access to a user's Cliq data is consent- and scope-controlled; selected Zoho MCP tools require valid authenticated service credentials. No specific paid API gate was established in the inspected pages."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Official Cliq REST API V3 documentation includes broad communication and platform resources (chats, messages, channels, users, bots, extensions, functions, and data stores) with OAuth scope controls."},
        "mcp": {"status": "AVAILABLE", "details": "Zoho documents an official Cliq MCP Server. Its tool surface supports chat/message/channel organization, reminders, threads and related actions; Zoho MCP setup creates a server-specific secure URL and requires authenticated service credentials.", "search_scope": "Opened Zoho's official Cliq REST API/OAuth docs, MCP overview/configuration pages, and pricing page. MCP presence is directly documented by Zoho."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Zoho account, app registration or MCP-server setup, OAuth consent/scopes, and the appropriate Cliq data access; account/plan-specific entitlement was not tested.", "rationale": "Official REST API, OAuth workflow, free signup path, and first-party Cliq MCP documentation support technical feasibility. User consent, scoped permissions, and account-specific access are required."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["No live Zoho tenant, OAuth grant, or MCP endpoint was created; exact scope-to-plan entitlements were not exhaustively audited."],
        "evidence": [
            ev("description", "Zoho's official Cliq docs describe a REST API with chat, channel, message, user, bot and related product resources.", "zoho_api"),
            ev("auth", "Zoho Cliq REST access uses OAuth 2.0 scoped access tokens and the Zoho-oauthtoken bearer scheme.", "zoho_oauth"),
            ev("self_serve", "Zoho Cliq offers a Free $0 plan with Try Now/Get Started; API scope entitlements are not fully mapped by this pricing page.", "zoho_pricing"),
            ev("credential_access", "Zoho documents developer app registration, client credentials and user-consented OAuth; its MCP console generates a server-specific secure URL after tool selection.", "zoho_mcp_setup"),
            ev("api", "The official API is REST V3 and its docs enumerate broad chat, message, channel, user, bot and platform-resource scopes.", "zoho_api"),
            ev("mcp", "Zoho identifies an official Cliq MCP Server with chat, message, channel, reminder and thread actions.", "zoho_mcp"),
            ev("buildability", "The documented REST/OAuth path and official MCP setup make integration feasible, subject to user consent and authenticated Cliq/MCP access.", "zoho_oauth"),
        ],
    },
    24: {
        "description": "Lark workplace-collaboration platform with Open Platform APIs spanning messaging, Base records, documents, calendar, and related resources.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Custom"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Lark's developer materials describe creating a custom app in the Open Platform and configuring scopes. API limits vary by API, app, tenant, and associated organization package; the inspected pages do not establish one universal plan gate.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a Lark app and obtain App ID/App Secret; configure required API permissions. App identity uses access tokens, while user-identity use requires OAuth authorization and user_access_token.", "plan_or_gate": "Application permissions, tenant/user data access and API frequency controls apply; custom-app limits may vary by the organization's package. The official MCP is labeled Beta."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "The Lark Open Platform documents HTTP JSON OpenAPI endpoints using POST/GET resource paths and Bearer tenant/user access tokens. Official API navigation spans messaging, docs/Base, calendar, tasks, contacts and other platform areas."},
        "mcp": {"status": "AVAILABLE", "details": "Lark's larksuite OpenAPI MCP repository calls the server official and Beta; it wraps Open Platform API tools. App ID/secret and scopes are required; OAuth/user-token mode is available. The inspected README notes file upload/download and direct document editing are unsupported in that version.", "search_scope": "Opened larksuite's official OpenAPI MCP repository/README and Lark Open Platform endpoint/rate-limit docs. Status refers to the vendor-published MCP project, not a hosted remote endpoint."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires app creation, app secret, scopes and tenant/user authorization; MCP is Beta and quotas/capabilities vary by API and package.", "rationale": "A documented Lark REST/OpenAPI surface and first-party-published MCP implementation support integration. App permissions, region-specific Lark/Feishu domains, tenant quotas, and Beta capability gaps are material constraints."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["The official MCP repository is labeled Beta and was not executed; no Lark tenant/account permissions were tested. Lark and Feishu domain differences are noted in the source."],
        "evidence": [
            ev("description", "Lark's official developer portal groups API resources across Messaging, Docs/Base and other workplace features.", "lark_endpoint"),
            ev("auth", "Lark APIs accept Bearer tenant_access_token or user_access_token; app ID/secret and optional OAuth are documented in the official OpenAPI MCP materials.", "lark_endpoint"),
            ev("self_serve", "Lark documents app creation and required permissions; rate limits can depend on the app's associated organization package.", "lark_rate"),
            ev("credential_access", "Lark's official MCP setup requires App ID/App Secret and app scopes; user identity requires OAuth authorization and a user access token.", "lark_readme"),
            ev("api", "An official Lark OpenAPI endpoint uses HTTP POST with JSON and Bearer access tokens; adjacent platform docs expose create/update/delete operations.", "lark_endpoint"),
            ev("mcp", "The larksuite repository identifies its Beta Feishu/Lark OpenAPI MCP and documents the supported API-tool configuration.", "lark_repo"),
            ev("buildability", "An official REST/OpenAPI path and first-party-published MCP implementation are available, with Beta, permission and quota constraints.", "lark_readme"),
        ],
    },
    25: {
        "description": "Pumble is a team-chat and collaboration product with a workspace API add-on and a hosted MCP server for messaging and workspace operations.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "Bearer/token", "Custom"],
        "self_serve_status": "SELF_SERVE",
        "self_serve_details": "Pumble says its API add-on is available on all plans to Owners, Admins and Members; users install it in the workspace and generate keys. MCP setup separately requires creating/installing a scoped workspace app; MCP plan entitlement is not separately specified in the inspected guide.",
        "credential_access": {"status": "SELF_SERVE", "path": "For the API add-on, install the workspace add-on and generate an API key in Pumble. For MCP, create/install a workspace app and copy its App key plus user or bot token; select scopes to expose tools.", "plan_or_gate": "The API add-on is documented as available on all Pumble plans. API calls use an API key; MCP tools depend on app scopes. The MCP guide does not separately state plan eligibility."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "Pumble documents an HTTP/OpenAPI API add-on with API-key authentication for users, scheduled messages, messages and channels. The help article lists message/channel actions and states the API add-on has no Events API; MCP provides additional scoped tools."},
        "mcp": {"status": "AVAILABLE", "details": "Pumble documents a hosted MCP endpoint at https://mcp.pumble.com/mcp. Workspace app key and user/bot token are sent as headers; the available search/read/write tools depend on chosen app scopes.", "search_scope": "Opened Pumble's official MCP setup guide, API add-on help page, linked OpenAPI reference and Pumble developer article. Vendor documentation directly confirms endpoint, auth and tools."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Pumble workspace, installed API add-on or custom app, generated credentials and selected scopes; MCP plan entitlement was not separately stated or account-tested.", "rationale": "Pumble documents API-key generation on all plans and a hosted MCP endpoint with configurable tools. Workspace installation, credential security and scope configuration remain prerequisites; no live tenant was tested."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["No workspace was authenticated. The API add-on's all-plans availability is explicit; the MCP guide does not separately resolve MCP plan eligibility."],
        "evidence": [
            ev("description", "Pumble describes the API add-on and MCP server as engineering interfaces for workspace messaging, search, reading and actions.", "pumble_ai"),
            ev("auth", "Pumble API add-on uses ApiKeyAuth.", "pumble_openapi"),
            ev("auth", "Pumble MCP setup uses an App key and user/bot token headers.", "pumble_mcp"),
            ev("self_serve", "Pumble's API add-on is available on all plans and workspace users can install it and generate keys.", "pumble_api"),
            ev("credential_access", "Pumble documents self-service add-on/key generation and app installation that returns an App key plus user/bot tokens for MCP.", "pumble_mcp"),
            ev("api", "The linked Pumble API reference is OpenAPI 3.0 and lists authenticated HTTP operations for users, scheduled messages, messages and channels.", "pumble_openapi"),
            ev("mcp", "Pumble's official help guide documents a hosted MCP server, endpoint, required app/token headers and scope-dependent tools.", "pumble_mcp"),
            ev("buildability", "Pumble documents an API add-on available on all plans with a self-service key-generation workflow, supporting an implementable API integration path.", "pumble_api"),
        ],
    },
    26: {
        "description": "Discord is a communication/community platform whose developer platform exposes a REST API for Discord data, apps and bot integrations.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token", "Custom"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Developers register applications in Discord's Developer Portal; server and user installation contexts are documented. Some OAuth scopes require Discord approval or partner access, and server installation requires a member with MANAGE_GUILD permission.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a Developer Portal application and use its bot token or configure OAuth2 to obtain a user bearer token; install the app in the permitted server/user context.", "plan_or_gate": "Some OAuth scopes are partner/Discord-approved; server installs require MANAGE_GUILD. The inspected docs do not establish a general paid API plan gate."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Discord documents a broad REST API at https://discord.com/api, with bot-token and OAuth2 flows; application resources also expose event-webhook configuration."},
        "mcp": {"status": "UNKNOWN", "details": "No first-party Discord MCP server or native MCP integration was verified in the inspected official materials; this is UNKNOWN, not a claim that none exists. Community-built tools may exist outside this research scope.", "search_scope": "Reviewed Discord official REST reference, OAuth2 docs, application resource docs, and a targeted docs.discord.com/developers MCP query. No direct first-party MCP source was opened."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires developer app registration, bot/OAuth credentials, permitted installation context and necessary permissions; some scopes need Discord approval.", "rationale": "Discord documents a REST API and standard app/bot OAuth setup. Approval-only scopes and server/user installation constraints can block particular use cases; no account or permission check was performed."},
        "confidence": "MEDIUM", "research_status": "COMPLETE",
        "limitations": ["Official MCP availability remains UNKNOWN after a scoped search; no account, guild or OAuth grant was tested. API pricing/plan details were not evaluated."],
        "evidence": [
            ev("description", "Discord's official developer documentation presents application, bot and REST API interfaces for the Discord platform.", "discord_api"),
            ev("auth", "Discord supports bot-token authorization and OAuth2 bearer tokens, with Basic authentication used for OAuth token endpoints.", "discord_api"),
            ev("self_serve", "A Discord developer app can be registered, but some OAuth scopes require approval and server installs require MANAGE_GUILD permission.", "discord_oauth"),
            ev("credential_access", "Discord credentials come from a registered Developer Portal app and bot/OAuth flow; installation context and approved scopes limit access.", "discord_oauth"),
            ev("api", "Discord documents a REST API base URL and application event-webhook resources.", "discord_api"),
            ev("buildability", "Documented REST/OAuth/bot flows make integration feasible; partner-approved scopes and server install permissions are constraints.", "discord_oauth"),
        ],
    },
    27: {
        "description": "Telegram's Bot API is an HTTP interface for creating Telegram bots; this capture does not establish the full user/MTProto API surface.",
        "auth_status": "PARTIAL", "auth_methods": ["Other"],
        "self_serve_status": "UNKNOWN",
        "self_serve_details": "Unknown. Official core.telegram.org Bot API, BotFather and API-ID pages returned HTTP 403 when opened. The accessible official TDLib repository documents the HTTP Bot API and says its self-hosted local server requires api_id/api_hash, but this does not settle the cloud bot-token or plan/onboarding path.",
        "credential_access": {"status": "UNKNOWN", "path": "Not fully established. The official TDLib README confirms api_id/api_hash are required for a self-hosted local Bot API server and links to Telegram's API-ID flow; cloud Bot API bot-token setup could not be verified from opened official pages.", "plan_or_gate": "Unknown; do not infer pricing or production access from blocked pages or search snippets."},
        "api": {"available": "YES", "types": ["Other"], "breadth": "UNKNOWN", "details": "The official TDLib repository describes the Bot API as an HTTP API for Telegram bots. Strict REST conformance and API breadth were not established from the captured pages; user/MTProto details remain unresolved."},
        "mcp": {"status": "UNKNOWN", "details": "No first-party Telegram MCP capability was verified from opened sources. Core documentation pages were blocked, and no negative MCP claim is made.", "search_scope": "Targeted Telegram/core.telegram.org and official TDLib queries were run. Core.telegram.org pages returned HTTP 403; official TDLib GitHub README/repository opened. MCP status remains UNKNOWN."},
        "buildability": {"verdict": "UNKNOWN", "blocker": "Core Telegram developer documentation was inaccessible during this capture; cloud bot-token onboarding, scopes and plan/production gates remain unverified.", "rationale": "An official repository confirms an HTTP Bot API and a self-hosted server option, but the authentication and production credential path for a normal cloud integration were not established."},
        "confidence": "LOW", "research_status": "PARTIAL",
        "limitations": ["Multiple official core.telegram.org pages returned HTTP 403. Search snippets were treated only as leads and were not used as claim evidence. Re-research from accessible official docs is required before full-population completion."],
        "evidence": [
            ev("description", "The Telegram Bot API server repository describes the Bot API as an HTTP API for creating Telegram bots.", "telegram_repo"),
            ev("auth", "The official README documents api_id/api_hash as mandatory options for the self-hosted local Bot API server only; the cloud Bot API bot-token route remains unverified.", "telegram_readme"),
            ev("api", "The official TDLib repository identifies Telegram Bot API as an HTTP API; no strict REST type or breadth conclusion is made.", "telegram_readme"),
        ],
    },
    28: {
        "description": "WhatsApp Business Platform's Cloud API lets business apps send and receive WhatsApp messages and receive status webhooks, with separate test and production onboarding paths.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Meta documents developer registration, Meta app creation, a test Messaging account/phone and temporary test token. Production use requires a real business phone/Messaging account and a system-user token with business permissions; usage pricing varies by delivered template category and recipient country.",
        "credential_access": {"status": "RESTRICTED", "path": "Register as a Meta developer, create/connect a Meta app and Messaging account, generate a temporary test access token, then configure a system user, assign app/WhatsApp assets and create a token with business_management and WhatsApp permissions for production.", "plan_or_gate": "Test assets and test messages are available for development; production requires business assets, a real number, permissions and production token setup. Delivered template messages are billed per Meta's pricing rules."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "The Cloud API is an HTTP Graph API endpoint using POST and Bearer tokens; message API supports text, media, templates, interactive content, reactions and status tracking, with webhooks and other documented business features."},
        "mcp": {"status": "UNKNOWN", "details": "No first-party Meta/WhatsApp MCP server was verified in the inspected official materials; status remains UNKNOWN rather than NOT_FOUND.", "search_scope": "Reviewed Meta WhatsApp Cloud API onboarding, message reference and pricing docs, plus a targeted Meta developer-domain MCP query. No first-party MCP page was opened."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Production requires a business portfolio/Messaging account, real phone number, long-lived system-user token, permissions, webhook setup and message-template pricing; test setup is narrower.", "rationale": "Meta documents an end-to-end self-serve test path and a production Cloud API. Business asset onboarding, token permissions, phone registration, policy requirements and variable delivered-template costs are material constraints."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["No Meta app or business account was created; account-specific verification/eligibility was not tested. Pricing is market/category-dependent and Meta documents further 2026 changes."],
        "evidence": [
            ev("description", "Meta describes the Cloud API as send/receive messaging with webhooks for message-status notifications.", "whatsapp_get_started"),
            ev("auth", "WhatsApp Cloud API requests use Bearer access tokens; Meta documents temporary test tokens and system-user tokens with business permissions.", "whatsapp_messages"),
            ev("self_serve", "Meta documents a test app/account/number/token setup and a separate real-business-number path for production.", "whatsapp_get_started"),
            ev("credential_access", "Production token creation requires a system user, assigned app/WhatsApp assets and specified business permissions.", "whatsapp_get_started"),
            ev("api", "The official Message API documents HTTP POST at graph.facebook.com using Bearer auth and a range of message payloads.", "whatsapp_messages"),
            ev("buildability", "Meta documents a complete test flow and production setup, while pricing is per delivered template message and business assets are required.", "whatsapp_pricing"),
        ],
    },
    29: {
        "description": "Aircall's REST API exposes business phone-system resources such as users, teams, calls, numbers and campaigns for integrations.",
        "auth_status": "CONFIRMED", "auth_methods": ["Basic", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Aircall customers can create dashboard API ID/token credentials for private integrations. Public multi-customer OAuth integrations use the Technology Partner route and require approved partner status; subscription-specific API feature eligibility was not exhaustively audited.",
        "credential_access": {"status": "RESTRICTED", "path": "Private/customer integrations use API ID and token generated in the Aircall Dashboard with Basic Auth. Public integrations use OAuth client credentials provided through Aircall's technology-partner process.", "plan_or_gate": "An Aircall account is required. OAuth for multi-customer public apps is restricted to approved tech partners; some API features can depend on the customer's subscription/number configuration."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Aircall explicitly labels its Public API as REST and provides endpoints across users, teams, calls, numbers, dialer/outbound campaigns, and other operational resources."},
        "mcp": {"status": "UNKNOWN", "details": "No first-party Aircall MCP server was verified in the inspected official developer materials; this remains UNKNOWN, not NOT_FOUND.", "search_scope": "Reviewed official Aircall authentication, REST API references and outbound-call guide; issued targeted developer-domain queries for MCP. No official MCP page was opened."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Private integrations require an Aircall customer account and dashboard credentials; public OAuth apps require approved tech-partner status; specific API features may need eligible plans/numbers.", "rationale": "Aircall documents a broad REST API and two concrete authentication routes. Customer account and number configuration, plan limits and partner approval constrain external/public builds."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["No Aircall account or number was tested. Public OAuth approval and plan-level access were not requested or verified; outbound call docs do not imply a dedicated Webhooks API."],
        "evidence": [
            ev("description", "Aircall's official REST API navigation includes user, team, call, number and campaign resources.", "aircall_api"),
            ev("auth", "Aircall supports Basic Auth for private customer tools and OAuth for public multi-customer applications.", "aircall_auth"),
            ev("self_serve", "Customers can generate Basic Auth credentials, while public OAuth requires approved technology-partner status.", "aircall_auth"),
            ev("credential_access", "Basic credentials are generated in the customer dashboard; OAuth client credentials are supplied to approved technology partners.", "aircall_auth"),
            ev("api", "Aircall labels the API REST and documents endpoints across users, teams, calls and campaigns.", "aircall_api"),
            ev("buildability", "Aircall documents an outbound-call workflow after customer/partner setup, authentication and number assignment.", "aircall_outbound"),
        ],
    },
    30: {
        "description": "Vonage provides programmable communications APIs across messaging, voice, number management, verification and related services.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "Basic", "Bearer/token", "Custom"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Vonage's developer guide offers account signup with free credit and exposes API key/secret in the dashboard. Some voice/messaging tasks require creating an application, downloading a private key, buying a virtual number, and paying for service usage; prices/availability vary by service and destination.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create a Vonage API account and retrieve API key/secret from API Settings. For application-based APIs, create an application and private key; generate JWTs where required. Purchase a virtual number when the selected service/use case requires one.", "plan_or_gate": "Dashboard API key/secret are self-service; account credit, number purchase, application setup and jurisdiction/service-specific requirements can be needed for production calls/messages."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "The official API index spans SMS/messaging, voice, number management, verification, account/application management, pricing and reports; individual API pages note beta/developer-preview status where relevant."},
        "mcp": {"status": "AVAILABLE", "details": "Vonage's first-party developer guides document a Tooling MCP server package (@vonage/vonage-mcp-server-api-bindings) that calls Vonage APIs, plus a separate Documentation MCP server. The shown local tooling setup uses API key/secret and sometimes an Application ID/private key. The implementation repository is under Vonage-Community, so vendor documentation is confirmed but independent repository ownership/maintenance is not assumed.", "search_scope": "Opened Vonage's official API index, authentication guide, MCP announcement and July 2026 Tooling MCP guide. The July 2026 first-party guide demonstrates API-tool invocation."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires Vonage account credentials; app ID/private key and/or purchased virtual numbers are needed for some APIs, and messaging/voice usage may incur service charges.", "rationale": "A broad REST API, self-service dashboard credentials and a vendor-documented tooling MCP package support implementation. Service-specific auth, phone-number purchase, account credit and regulatory constraints remain."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["No Vonage account or MCP package was executed. The tooling package is linked by Vonage's developer guide but lives in the Vonage-Community GitHub organization; ownership/maintenance is not inferred from the blog alone."],
        "evidence": [
            ev("description", "Vonage's API index lists messaging, voice, number, Verify, application, account and pricing API families.", "vonage_api"),
            ev("auth", "Vonage documents dashboard API key/secret Basic Auth and JWT Bearer auth signed with an Application ID/private key.", "vonage_auth"),
            ev("self_serve", "Vonage offers self-service account signup/free credit and dashboard credentials; some use cases require a purchased virtual number.", "vonage_tooling_mcp"),
            ev("credential_access", "API key/secret are exposed in API Settings; the documented Tooling MCP setup uses those credentials, with application ID/private key for some tools.", "vonage_tooling_mcp"),
            ev("api", "Vonage documents API families spanning messaging, voice, numbers, Verify, account and applications.", "vonage_api"),
            ev("mcp", "Vonage's official 2026 developer guide configures @vonage/vonage-mcp-server-api-bindings and invokes an SMS tool; the documentation MCP is a separate server.", "vonage_tooling_mcp"),
            ev("buildability", "Vonage documents a broad API surface with concrete REST services that can be integrated using the documented authentication schemes.", "vonage_api"),
        ],
    },
    31: {
        "description": "Google Ads API lets applications retrieve and manage Google Ads account data through REST/gRPC, with production access and quotas controlled by project/developer-token level.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Service account"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Google documents starting with Test access when enabling the API. Production access and daily operation limits are tied to access levels and applications; API usage is free, but projects need developer tokens and account permissions, and Standard access entails RMF review.",
        "credential_access": {"status": "RESTRICTED", "path": "Set up a Google Cloud project and OAuth client or service account; obtain a Google Ads developer token through an Ads manager account/API Center and authorize access to the target customer account.", "plan_or_gate": "Test access supports test accounts. Production account access/quota requires the appropriate access level and may require application review; Google Ads API use is free, with possible non-compliance fees under Standard-access RMF."},
        "api": {"available": "YES", "types": ["REST", "RPC"], "breadth": "BROAD", "details": "Google Ads API supports REST and gRPC and exposes extensive account, campaign and reporting resources; daily access, quotas and permitted use vary by developer-token/project access level."},
        "mcp": {"status": "AVAILABLE", "details": "Google officially documents a Google Ads MCP server. Current release is read-only, uses OAuth 2.0 or service-account credentials, and exposes accessible-customer discovery, GAQL search and resource metadata.", "search_scope": "Opened official Google Ads MCP integration guide, API quick start, access-level policy and pricing/RMF documentation. Google documentation directly links the googleads/google-ads-mcp repository."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Cloud project, developer token, Ads manager/customer account access and OAuth/service-account credentials; production access levels require application steps. Official MCP is read-only.", "rationale": "Google documents a free API, REST/gRPC API, a test path and an official read-only MCP server. Production access levels, quota and read-only MCP scope constrain feasible use cases."},
        "confidence": "HIGH", "research_status": "COMPLETE",
        "limitations": ["No Google Ads manager account, developer token, OAuth grant or MCP server was configured. Access-level application outcomes depend on Google's review and target account permissions."],
        "evidence": [
            ev("description", "Google's quick start describes Google Ads API access to client-account data and production access levels.", "google_quickstart"),
            ev("auth", "The official quick start documents OAuth 2.0/service-account credentials and a developer token for API calls.", "google_quickstart"),
            ev("self_serve", "Test access is available for test accounts; production access levels use additional application steps, while API use itself is free.", "google_access"),
            ev("credential_access", "API access requires a developer token, Cloud project OAuth/service-account credentials and target customer access; higher levels require review.", "google_access"),
            ev("api", "Google Ads supports both REST and gRPC, with broad account/campaign/query resources and access-level quotas.", "google_quickstart"),
            ev("mcp", "Google officially documents a read-only MCP server and its OAuth/service-account configuration and core tool capabilities.", "google_mcp"),
            ev("buildability", "Google's MCP is read-only and requires project/API access levels; its API is free but Standard access may impose RMF review.", "google_pricing"),
        ],
    },
}

# Exact queries executed in the current continuation, grouped above. The prior
# query is retained as a clearly-labeled unknown-text event, not reconstructed.

def build_batch() -> dict:
    manifest = json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8"))
    placeholders = json.loads((ROOT / "data/raw/final_full_research.json").read_text(encoding="utf-8"))
    base_by_id = {r["app_id"]: r for r in placeholders}
    manifest_by_id = {r["app_id"]: r for r in manifest}
    ids = sorted(RECORDS)
    records_out = []
    traces_out = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for app_id in ids:
        if app_id not in base_by_id or app_id not in manifest_by_id:
            raise ValueError(f"app_id={app_id} missing from current manifest/baseline")
        data = copy.deepcopy(RECORDS[app_id])
        rec = copy.deepcopy(base_by_id[app_id])
        rec.update({k: copy.deepcopy(v) for k, v in data.items() if k != "evidence"})
        rec["evidence"] = copy.deepcopy(data["evidence"])
        rec["source_mode"] = "LIVE_AGENT"
        rec["research_tool"] = TOOL
        rec["research_timestamp"] = now
        rec["research_status"] = data["research_status"]
        rec["verification_status"] = "NOT_CHECKED"
        rec["research_run_id"] = RUN_ID
        rec["failure_reason"] = None
        rec["quality_gate"] = {}

        query_rows = [copy.deepcopy(PRIOR_LEAD_QUERY)] + [
            {"query": q, "depth": "1", "search_status": "SUCCESS", "lead_only": True,
             "note": "Search results were used only to find candidate URLs; snippets were not used as final claim evidence."}
            for q in QUERIES[app_id]
        ]
        app_sources = [copy.deepcopy(SOURCES[k]) for k in FETCH_COUNTS[app_id]]
        fetch_attempts = []
        for key, chunk_indexes in FETCH_COUNTS[app_id].items():
            s = SOURCES[key]
            for chunk_index in chunk_indexes:
                fetch_attempts.append({
                    "tool": "fetch_page", "url": s["url"], "chunk_index": chunk_index,
                    "status": "SUCCESS", "note": "Official page opened; saved excerpt/observation in source packet."
                })
        for fail in FAILED_FETCHES.get(app_id, []):
            fetch_attempts.append({"tool": "fetch_page", **copy.deepcopy(fail)})

        query_attempts = [
            {"tool": "web_search", "query": q.get("query"), "status": "SUCCESS_RESULT_RECORDED",
             "query_details_status": q.get("query_details_status", "PRESERVED"),
             "note": q.get("note", "Search results used as URL-discovery leads only; not claim evidence.")}
            for q in query_rows
        ]
        attempts = query_attempts + fetch_attempts
        rec["query_count"] = len(query_rows)
        rec["source_count"] = len(app_sources)
        rec["attempt_count"] = len(attempts)
        rec["trace_limitations"] = [
            "The initial ten lead searches were confirmed by the prior-session action log, but exact query text was not retained in that summary; each is represented as a null-text, explicitly unpreserved query event. Their snippets were not used as evidence.",
            "Attempt trace enumerates preserved search events and known fetch_page chunk opens/errors for this batch. Captured claim evidence is limited to pages opened and excerpted in the source packets.",
        ]

        source_urls = {s["url"] for s in app_sources}
        gate = validate_record_quality(rec, source_urls=source_urls)
        rec["quality_gate"] = gate
        records_out.append(rec)
        traces_out.append({
            "app_id": app_id,
            "app": rec["app"],
            "source_mode": "LIVE_AGENT",
            "status": rec["research_status"],
            "research_run_id": RUN_ID,
            "research_tool": TOOL,
            "queries": query_rows,
            "sources": app_sources,
            "attempts": attempts,
            "trace_limitations": copy.deepcopy(rec["trace_limitations"]),
        })

    return {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "run_started_at": now,
        "run_completed_at": now,
        "source_mode": "LIVE_AGENT",
        "tool": TOOL,
        "provider_credentials": {"TAVILY_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL", "OPENAI_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL"},
        "scope": "Apps 21 and 23-31 only; app 22 Twilio remains a preserved PRIOR_CAPTURE. This is an incremental capture artifact, not the completed 100-app dataset.",
        "search_result_policy": "Search-result snippets were leads only and are excluded from claim evidence. Claim evidence cites opened official pages or official vendor repositories.",
        "records": records_out,
        "traces": traces_out,
    }


def main() -> int:
    payload = build_batch()
    errors = []
    for record in payload["records"]:
        errs = validate_record(record)
        if errs:
            errors.append((record["app_id"], errs))
        if record["quality_gate"]["status"] == "FAIL":
            errors.append((record["app_id"], record["quality_gate"]["errors"]))
        trace = next(t for t in payload["traces"] if t["app_id"] == record["app_id"])
        if record["query_count"] != len(trace["queries"]):
            errors.append((record["app_id"], ["query count mismatch"]))
        if record["source_count"] != len(trace["sources"]):
            errors.append((record["app_id"], ["source count mismatch"]))
        if record["attempt_count"] != len(trace["attempts"]):
            errors.append((record["app_id"], ["attempt count mismatch"]))
    if errors:
        print(json.dumps(errors, indent=2, ensure_ascii=False))
        return 1
    out = ROOT / "data/evidence/native_web_capture_batch01_2026-09-24.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} with {len(payload['records'])} rows and {len(payload['traces'])} traces")
    print("record quality:", {s: sum(r['quality_gate']['status'] == s for r in payload['records']) for s in ['PASS','WARN','FAIL']})
    for r in payload["records"]:
        print(r["app_id"], r["app"], r["research_status"], r["quality_gate"]["status"], r["query_count"], r["source_count"], r["attempt_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
Exit(main())

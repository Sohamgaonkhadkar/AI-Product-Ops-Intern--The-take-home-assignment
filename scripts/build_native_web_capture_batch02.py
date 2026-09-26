#!/usr/bin/env python3
"""Assemble the second manually researched native-web evidence batch.

This writes a standalone auditable capture for manifest apps 32-41 only. It
never edits the raw dataset. Search-result snippets are discovery leads, not
claim evidence; evidence below cites opened official vendor/developer pages.
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
RUN_ID = "arena-native-web-batch02-20260924"
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
    # 32 Meta Ads
    "meta_api": source(
        "https://developers.facebook.com/documentation/ads-commerce/marketing-api",
        "Marketing API | Meta | Developer Documentation", "official_api_docs",
        "Meta describes the Marketing API as a collection of Graph API endpoints and related features for advertising across Meta technologies. The opened overview links to campaign creation/management, ad optimization/insights, Conversions API, Catalog API, Business Management API, and Commerce API. It does not describe the interface as GraphQL; the record classifies the Graph API surface as Other.", (0,)
    ),
    "meta_faq": source(
        "https://developers.facebook.com/documentation/ads-commerce/marketing-api/using-the-api/faq",
        "Frequently Asked Questions | Developer Documentation", "official_api_docs",
        "Meta's FAQ says production use of the Marketing API requires app review and approval, access tokens can be generated in the developer portal, campaigns are created via POST /act_<AD_ACCOUNT_ID>/campaigns, and the Insights API reads reporting data.", (0,)
    ),
    "meta_auth": source(
        "https://developers.facebook.com/documentation/ads-commerce/marketing-api/get-started/authorization",
        "Authorization | Developer Documentation", "official_auth_docs",
        "The current authorization guide (updated May 5, 2026) says adding the Marketing API product grants default Limited/development access; Full access follows App Review and qualification (including 500 successful calls in 15 days and <15% error rate in the last 500 calls). It documents ads_read/ads_management scopes, user OAuth consent, app roles, access levels, and possible business verification.", (0, 1)
    ),
    "meta_rate": source(
        "https://developers.facebook.com/documentation/ads-commerce/marketing-api/overview/rate-limiting",
        "Marketing API Rate Limiting | Developer Documentation", "official_api_docs",
        "Meta distinguishes default Limited/development access from Full access, with different account/app rate quotas. The opened 2026 page describes API-level, ad-account-level, mutation-QPS and concurrent-request limits; access-tier labels were updated in 2026.", (0,)
    ),

    # 33 LinkedIn Ads
    "linkedin_access": source(
        "https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access",
        "Getting Access to LinkedIn APIs - LinkedIn | Microsoft Learn", "official_auth_docs",
        "LinkedIn documents OAuth 2.0 for API authorization/authentication and says Marketing/Advertising API permissions require approval through the Developer Portal. Advertising API is requested on the app's Products tab; open self-service permissions are limited to unrelated consumer scopes.", (0,)
    ),
    "linkedin_tiers": source(
        "https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access?view=li-lms-2026-06",
        "Increasing Access - LinkedIn | Microsoft Learn", "official_auth_docs",
        "Current 2026 docs state all apps start in Development tier and Standard access must be requested separately. Advertising Development tier permits unlimited reads and edits on up to five administered ad accounts; Standard permits broader campaign management and requires a support-ticket request. Marketing permissions are member-consented 3-legged OAuth; role/scope requirements are enumerated.", (0, 1, 2)
    ),
    "linkedin_ads": source(
        "https://learn.microsoft.com/en-us/linkedin/marketing/integrations/ads/getting-started?view=li-lms-2026-09&viewFallbackFrom=li-lms-2025-08",
        "Campaign Management Getting Started - LinkedIn | Microsoft Learn", "official_api_docs",
        "The opened campaign guide requires rw_ads for Marketing API operations, shows REST-style endpoints such as POST https://api.linkedin.com/rest/adAccounts, and explains mapping ad accounts to apps in Development tier. It includes campaign account/group workflows.", (0,)
    ),

    # 34 GoHighLevel / LeadConnector
    "ghl_api": source(
        "https://marketplace.gohighlevel.com/docs/",
        "HighLevel API Documentation - Developer Portal | HighLevel API", "official_api_docs",
        "The official portal documents a comprehensive REST API for CRM/contacts, conversations and messaging, calendars, opportunities, payments, webhooks, and other HighLevel platform features. Quick start offers Marketplace app or Private integration with OAuth 2.0 or Private Integration Token.", (0,)
    ),
    "ghl_auth": source(
        "https://marketplace.gohighlevel.com/docs/Authorization/authorization_doc/",
        "Authorization | HighLevel API", "official_auth_docs",
        "HighLevel documents Private Integration Tokens for internal/single-sub-account use and OAuth 2.0 for public/Marketplace integrations, multi-location access, webhooks, custom modules, or user-approved access.", (0,)
    ),
    "ghl_support": source(
        "https://help.gohighlevel.com/support/solutions/articles/48001060529-highlevel-api",
        "HighLevel API Documentation : HighLevel Support Portal", "official_support",
        "Official support documentation says API v1 reached end of support on 2025-12-31; Basic API access is included in Starter and Unlimited, while Agency Pro has Advanced API access including OAuth/agency-level tokens. It separately describes REST endpoints, V2 rate limits, and current API documentation location.", (0, 1)
    ),
    "ghl_mcp": source(
        "https://marketplace.gohighlevel.com/docs/other/mcp/",
        "LeadConnector MCP Server | HighLevel API", "official_docs",
        "Official hosted LeadConnector MCP endpoints are documented for Claude and OpenAI-compatible clients. The server uses OAuth consent/scopes, exposes a compact tool set over 550+ operations in 38 domains, and enforces selected sub-account boundaries and safety checks. Agency-wide multi-account connections are described as rolling out.", (0,)
    ),
    "ghl_pricing": source(
        "https://www.gohighlevel.com/pricing",
        "HighLevel Pricing", "official_pricing",
        "The opened pricing page exposes a self-serve 14-day trial signup. Its dynamically rendered capture did not include the plan-feature comparison, so API entitlement is taken from HighLevel's API support article, not inferred from this page.", (0,)
    ),

    # 35 Mailchimp
    "mailchimp_api": source(
        "https://mailchimp.com/developer/marketing/api/",
        "Mailchimp Marketing API Reference | Mailchimp Developer", "official_api_docs",
        "The official Marketing API reference is v3.0.91 and lists resource groups and HTTP verbs for audiences/contacts, authorized apps, automation flows, batches, webhooks, campaigns, and other marketing data. It is a broad HTTP API surface; Transactional/Mandrill is documented separately.", (0,)
    ),
    "mailchimp_quickstart": source(
        "https://mailchimp.com/developer/marketing/guides/quick-start/",
        "Marketing API Quick Start Guide | Mailchimp Developer", "official_api_docs",
        "Mailchimp's quick start says an account is required, API keys are self-generated, a key grants full account access, requests use the v3.0 regional API root and Basic authentication with the key as password, and OAuth 2 is preferred for integrations acting on behalf of other Mailchimp users.", (0,)
    ),
    "mailchimp_key_help": source(
        "https://mailchimp.com/help/about-api-keys/",
        "About API Keys | Mailchimp", "official_support",
        "Manager users can generate their own Marketing API keys; Admins can see other users' keys. Keys grant full account access subject to user role/endpoint permissions. New keys created on or after 2026-06-22 expire after one year; keys can be revoked in account settings.", (0,)
    ),
    "mailchimp_integrations": source(
        "https://mailchimp.com/developer/marketing/docs/integrations/",
        "Integrations Documentation | Mailchimp Developer", "official_docs",
        "Marketing integrations use the Marketing API and should use OAuth 2.0. Marketplace listing requires joining the Integration Partner Program; its requirements include a review/test, OAuth, 25+ active users in 90 days, three core Mailchimp features, support, a test account, and partner terms. The guide links to audience, automation, e-commerce, contacts and reports endpoints.", (0, 1)
    ),
    "mailchimp_mcp": source(
        "https://mailchimp.com/developer/transactional/guides/how-to-use-mailchimps-transactional-messaging-mcp/",
        "How to Use Mailchimp's Transactional Messaging MCP Guide | Mailchimp Developer", "official_docs",
        "Mailchimp documents an official hosted MCP endpoint at https://mandrillapp.com/mcp for Transactional Messaging (Mandrill), with API-key Bearer auth and tools for account status, templates, API calls/descriptions, send troubleshooting and onboarding. Restricted API keys require the 'AI Agents' permission group. This is not evidence of a Marketing API MCP.", (0,)
    ),

    # 36 Klaviyo
    "klaviyo_api": source(
        "https://developers.klaviyo.com/en/reference/api_overview",
        "API overview | Klaviyo Developers", "official_api_docs",
        "Klaviyo's API overview describes private-key, OAuth and public-key access; scoped REST/JSON API surfaces; OpenAPI/Postman specs; rate limits; and JSON:API resources. It links to a broad set of endpoint families and developer guides.", (0,)
    ),
    "klaviyo_auth": source(
        "https://developers.klaviyo.com/en/docs/authenticate_",
        "Authenticate API requests | Klaviyo Developers", "official_auth_docs",
        "Private API keys authenticate server-side /api requests; OAuth is recommended for tech partners and App Marketplace integrations; public company IDs authenticate /client endpoints. Key creation requires Owner, Admin, or Manager role; keys have configurable endpoint scopes and use the Klaviyo-API-Key header.", (0,)
    ),
    "klaviyo_key_help": source(
        "https://help.klaviyo.com/hc/en-us/articles/7423954176283",
        "How to create or clone a private API key | Klaviyo Help Center", "official_support",
        "The help page says only an Owner or Admin may create/clone/delete private API keys; keys can be read-only, full, or custom scoped, and the value/scopes cannot be viewed or edited after creation.", (0,)
    ),
    "klaviyo_mcp_current": source(
        "https://developers.klaviyo.com/en/docs/klaviyo_mcp_server",
        "Klaviyo MCP server | Klaviyo Developers", "official_docs",
        "Current Klaviyo developer docs introduce the vendor's MCP server and link to both a recommended remote-hosted server and a local server. The page was marked updated nine days before the 2026-09-24 capture.", (0,)
    ),
    "klaviyo_mcp_connect": source(
        "https://developers.klaviyo.com/en/docs/connect_to_the_klaviyo_mcp_server",
        "Connect to the MCP server | Klaviyo Developers", "official_docs",
        "The current guide recommends the remote server https://mcp.klaviyo.com/mcp with OAuth. Connection is limited to Klaviyo Owner/Admin/Manager users. Claude and ChatGPT setup flows are documented; optional read-only, user-generated-content, core-tools-only and other query parameters control exposure.", (0,)
    ),
    "klaviyo_mcp_tools": source(
        "https://developers.klaviyo.com/en/docs/klaviyo_mcp_server_available_tools",
        "Available tools | Klaviyo Developers", "official_docs",
        "The current tools catalog lists 260+ MCP tools across accounts, campaigns, catalogs, events, flows, groups, profiles, reporting, templates and other areas. It marks read/write behavior, user-generated-content exposure and which tools are available on the remote server.", (0,)
    ),
    "klaviyo_mcp_beta": source(
        "https://developers.klaviyo.com/en/v2025-04-15/docs/klaviyo_mcp_server",
        "(Beta) Klaviyo MCP server | Deprecated 2025-04-15 documentation", "official_docs",
        "An older versioned 2025 documentation page is now labeled deprecated and describes a local beta server using a private API key. It is retained as a superseded research trace; the current unversioned documentation describes the remote-hosted OAuth server.", (0,)
    ),

    # 37 systeme.io
    "systeme_api": source(
        "https://developer.systeme.io/reference/api",
        "Public API | Systeme.io Developer", "official_api_docs",
        "The public API is described as RESTful. It authenticates with an X-API-Key header, documents contacts/tags and other resource endpoints, pagination, PATCH merge behavior, and shared rate limits.", (0,)
    ),
    "systeme_key_help": source(
        "https://help.systeme.io/article/2323-how-to-create-a-public-api-key-on-systeme-io",
        "How to use the systeme.io public API (Application Programming Interface) | Help Center", "official_support",
        "The official help article explains account-setting key creation, optional expiration (leave blank for no expiry), a maximum of three Public API keys, and API coverage including contacts, tags, custom fields, newsletters/campaigns, funnels, courses, products, automations, bookings and webhooks. It also contains some API/MCP-specific limitations for selected features; last updated 2026-09-15.", (0, 1)
    ),
    "systeme_mcp_dev": source(
        "https://developer.systeme.io/docs/mcp-server",
        "MCP Server | Systeme.io Developer", "official_docs",
        "The official technical MCP page calls this an initial release, requires an MCP key, supports X-MCP-Key header or mcpKey query parameter, shares Public API rate limits, and lists contacts, tags, contact fields, and newsletters as the currently supported MCP operations. It says those are the only capabilities exposed in that documentation version.", (0,)
    ),
    "systeme_mcp_help": source(
        "https://help.systeme.io/article/9489-how-to-use-systeme-ios-mcp",
        "How to use the systeme.io MCP server (Model Context Protocol) | Help Center", "official_support",
        "The help article (last updated 2026-09-15) describes MCP key creation, maximum two keys with 90-day lifetime, and lists contacts/tags/newsletters plus campaigns, funnels, price plans, automation, products, bookings, courses and SMS templates. It says OAuth is planned. Its catalog is broader than the official technical MCP page; this conflict is preserved, not silently resolved.", (0, 1)
    ),
    "systeme_mcp_chatgpt": source(
        "https://developer.systeme.io/docs/mcp-integration-with-chatgpt",
        "Integration with ChatGPT | Systeme.io Developer", "official_docs",
        "The official integration guide uses https://mcp.systeme.io/mcp?mcpKey=YOUR_KEY, says ChatGPT access is in Beta and requires Developer Mode, and warns that some write actions may be restricted or require extra confirmation. The endpoint key is placed in the URL.", (0,)
    ),
    "systeme_chatgpt_help": source(
        "https://help.systeme.io/article/11229-how-to-connect-your-systemeio-account-with-chatgpt-using-mcp-keys",
        "How to connect your systeme.io account to ChatGPT using MCP keys | Help Center", "official_support",
        "The official help page (last updated 2026-08-25) gives the MCP endpoint/query-key setup, requires a Systeme.io account and MCP key, and notes ChatGPT/workspace plan settings can restrict or require confirmation for write actions.", (0,)
    ),
    "systeme_pricing": source(
        "https://systeme.io/pricing",
        "Systeme.io Pricing — Free, Startup, Webinar, Unlimited Plans", "official_pricing",
        "The official pricing comparison lists a $0 Free plan and API requests/minute limits by tier (Free 30, Startup 60, Webinar 120, Unlimited unlimited). It is not treated as proof that every API/MCP operation has identical plan entitlements.", (0,)
    ),

    # 38 Pinterest
    "pinterest_api": source(
        "https://developers.pinterest.com/docs/api/v5/introduction/",
        "Pinterest Developers | Pinterest REST API 5.31.0", "official_api_docs",
        "The API reference identifies Pinterest REST API v5 and documents conversion tracking, Pins/boards, ads/campaigns, media planning, targeting/audiences, catalogs/shopping, analytics and reporting.", (0,)
    ),
    "pinterest_auth": source(
        "https://developers.pinterest.com/docs/getting-started/set-up-authentication-and-authorization/",
        "Pinterest Developers | Set up authentication and authorization", "official_auth_docs",
        "Pinterest requires an app ID/client secret, registered redirect URI and scopes. It documents OAuth Authorization Code and Client Credentials grants, Basic client authentication at the token endpoint, and Bearer access tokens; current continuous refresh tokens are refreshable indefinitely after the 60-day access-token lifetime.", (0, 1)
    ),
    "pinterest_app": source(
        "https://developers.pinterest.com/docs/getting-started/connect-app/",
        "Pinterest Developers | Connect app", "official_docs",
        "App registration requires a Pinterest business account, verified email and acceptance of Developer Terms. Developers submit an application for Trial API access; Pinterest reviews it and only approved apps receive app ID/secret and Trial access.", (0,)
    ),
    "pinterest_tiers": source(
        "https://developers.pinterest.com/docs/key-concepts/access-tiers/",
        "Pinterest Developers | Access tiers", "official_docs",
        "Trial access has daily limits and created Pins/Boards are sandbox-visible only to their creator. Standard access requires a separate upgrade request and a demo video showing OAuth/live Pinterest integration; approval is reviewed by Pinterest. Some read/ads operations are available in Trial.", (0,)
    ),
    "pinterest_mcp": source(
        "https://developers.pinterest.com/about-pinterest-mcp/",
        "Pinterest Developers | MCP Server", "official_docs",
        "The official page announces a Pinterest MCP server and shows a Bearer-token endpoint example, but repeatedly says 'Be the first to know when it launches' and asks developers to sign up for launch updates. It does not establish public availability as of the capture date.", (0,)
    ),

    # 39 Threads (Meta)
    "threads_get_started": source(
        "https://developers.facebook.com/documentation/threads/get-started",
        "Get started with the Threads API | Developer Documentation", "official_auth_docs",
        "Meta requires a developer app with the Threads use case and Threads-specific app credentials. OAuth 2.0 user access tokens are used; scopes include threads_basic and feature-specific scopes. Testers can grant permissions, while external app users require App Review and publication; short-lived tokens last 1 hour and long-lived tokens 60 days.", (0, 1)
    ),
    "threads_overview": source(
        "https://developers.facebook.com/documentation/threads/overview",
        "Threads API overview | Developer Documentation", "official_api_docs",
        "The Threads API supports publishing and displaying content for the author, with graph.threads.com/.net endpoints, profile-specific publishing and reply quotas, post/media operations, discovery and other documented resources.", (0,)
    ),
    "threads_profiles": source(
        "https://developers.facebook.com/documentation/threads/threads-profiles",
        "Threads Profiles | Developer Documentation", "official_api_docs",
        "Meta documents the Threads Profile API and Profile Discovery API, their Threads user-token permission scopes, profile endpoints/fields, and discovery limitations such as public-profile requirements and standard-access restrictions.", (0,)
    ),

    # 40 SendGrid
    "sendgrid_product": source(
        "https://www.twilio.com/en-us/sendgrid",
        "SendGrid Email API and Email Marketing Campaigns | Twilio", "official_product",
        "Twilio's SendGrid product page describes Email API/SMTP and separate marketing-campaign offerings, linking to developer documentation and Email API pricing.", (0,)
    ),
    "sendgrid_auth": source(
        "https://www.twilio.com/docs/sendgrid/for-developers/sending-email/authentication",
        "Authentication | SendGrid Docs | Twilio", "official_auth_docs",
        "SendGrid API keys are created in account Settings and sent as Bearer tokens; keys can be permission-scoped. Basic auth with an account password is not supported; some services accept Basic auth with username 'apikey' and the API key as password. Twilio requires 2FA for all users.", (0,)
    ),
    "sendgrid_quickstart": source(
        "https://www.twilio.com/docs/sendgrid/for-developers/sending-email/api-getting-started",
        "Getting started with the SendGrid API | SendGrid Docs | Twilio", "official_api_docs",
        "The official quick start uses the v3 API root https://api.sendgrid.com/v3, creates an API key in the console, sends JSON HTTP requests, and identifies sender authentication/domain setup as a prerequisite for deliverability. SDKs are available in seven languages.", (0, 1)
    ),
    "sendgrid_api": source(
        "https://www.twilio.com/docs/sendgrid/api-reference/how-to-use-the-sendgrid-v3-api",
        "How to use the SendGrid V3 API | SendGrid Docs | Twilio", "official_api_docs",
        "The official reference calls the SendGrid v3 surface a Web REST API and lists seven supported language SDKs.", (0,)
    ),
    "sendgrid_pricing": source(
        "https://www.twilio.com/en-us/products/email-api/pricing",
        "Email API Pricing | Twilio", "official_pricing",
        "Current Twilio pricing page lists a self-serve, no-credit-card 60-day free trial capped at 100 emails/day, paid Essentials from $19.95/month, Pro from $89.95/month, and custom Premier pricing. The pricing page describes SMTP and RESTful HTTP/JSON APIs.", (0,)
    ),
    "twilio_mcp": source(
        "https://www.twilio.com/docs/ai/mcp",
        "Twilio MCP server | Twilio", "official_docs",
        "Twilio's public-beta hosted MCP at https://mcp.twilio.com/docs is unauthenticated and read-only: it searches/retrieves public API specs and docs, does not execute calls, and indexes Twilio SendGrid documentation/support articles. This is a documentation MCP for SendGrid, not a SendGrid account/action connector.", (0, 1)
    ),

    # 41 Shopify
    "shopify_graphql": source(
        "https://shopify.dev/docs/api/admin-graphql/latest",
        "GraphQL Admin API reference | Shopify Dev", "official_api_docs",
        "Shopify's GraphQL Admin API is a broad store-admin API with versioned schema/reference, authenticated access tokens, queries/mutations, rate limits and client libraries.", (0,)
    ),
    "shopify_rest": source(
        "https://shopify.dev/docs/api/admin-rest",
        "REST Admin API reference | Shopify Dev", "official_api_docs",
        "Shopify labels REST Admin API legacy as of 2024-10-01 and says new public apps must use GraphQL Admin API as of 2025-04-01. Existing REST calls still use OAuth-generated access tokens and requested scopes.", (0,)
    ),
    "shopify_auth": source(
        "https://shopify.dev/docs/apps/build/authentication-authorization",
        "About app authentication | Shopify Dev", "official_auth_docs",
        "Shopify apps obtain store access tokens through token exchange, authorization-code grant, or client-credentials grant depending on app/store context; calls use X-Shopify-Access-Token and merchant-approved scopes. Shopify CLI/templates handle most flows.", (0,)
    ),
    "shopify_scopes": source(
        "https://shopify.dev/docs/api/usage/access-scopes",
        "Shopify API access scopes | Shopify Dev", "official_auth_docs",
        "Apps declare authenticated, unauthenticated and customer scopes; merchants approve scopes at installation, and Shopify requires approval for selected protected scopes/data. Access varies by API/scope and store feature availability.", (0,)
    ),
    "shopify_distribution": source(
        "https://shopify.dev/docs/apps/launch/distribution",
        "About app distribution | Shopify Dev", "official_docs",
        "Public apps can serve multiple stores but require Shopify approval. Custom distribution does not require that approval but is limited to a single store, selected Plus organizations or eligible development stores; old admin-created custom apps are no longer available to create.", (0,)
    ),
    "shopify_storefront_mcp": source(
        "https://shopify.dev/docs/apps/build/storefront-mcp/servers/storefront",
        "Storefront MCP server | Shopify Dev", "official_docs",
        "Each store exposes Storefront MCP at /api/mcp and catalog/UCP MCP at /api/ucp/mcp. Shopify says these endpoints do not require authentication; tools support catalog search/lookup, product detail, cart operations and policy/FAQ search, though some stores may restrict access.", (0,)
    ),
    "shopify_dev_mcp": source(
        "https://shopify.dev/docs/apps/build/ai-toolkit",
        "Shopify AI Toolkit | Shopify Dev", "official_docs",
        "The official developer AI Toolkit includes Shopify Dev MCP, which runs locally without authentication and searches documentation/API schemas and validates code. The page also describes store-management tasks through an authenticated Shopify CLI store context with the developer choosing whether to execute them. The legacy /apps/build/devmcp URL resolved to this current AI Toolkit page.", (0,)
    ),
}

QUERIES = {
    32: [
        "site:developers.facebook.com/docs/marketing-apis Meta Marketing API authentication ads_management app review official MCP",
        "site:developers.facebook.com/docs/marketing-apis Marketing API getting started developer app ads_management access levels standard access official",
        "Meta Marketing API Graph API endpoints create ads campaigns access token ads_management OAuth official developer documentation",
        "site:developers.facebook.com/docs/marketing-api/overview Meta Marketing API official Graph API endpoint developers app ads permissions",
        "site:developers.facebook.com/documentation/ads-commerce/marketing-api authentication access token OAuth app review production Ads Management permission",
    ],
    33: [
        "site:learn.microsoft.com/linkedin/marketing LinkedIn Marketing API OAuth access request official MCP",
        "site:learn.microsoft.com/en-us/linkedin/marketing/authentication OAuth 2.0 Marketing API request access developer portal advertising API",
        "LinkedIn Marketing APIs getting access products Ads API OAuth r_ads r_ads_reporting official developer program site:learn.microsoft.com/linkedin/marketing OR site:learn.microsoft.com/en-us/linkedin",
        "site:learn.microsoft.com/en-us/linkedin/marketing REST API Advertising API OAuth 2.0 Campaign Management authentication access tier",
        "site:learn.microsoft.com/en-us/linkedin/marketing MCP server LinkedIn Ads MCP official developer model context protocol",
    ],
    34: [
        "site:marketplace.gohighlevel.com/docs OR site:highlevel.stoplight.io GoHighLevel API OAuth app review MCP official developer",
        "site:marketplace.gohighlevel.com/docs/other/mcp LeadConnector MCP auth OAuth private integration token HighLevel pricing API official",
        "HighLevel LeadConnector API OAuth private integration token developer docs apps marketplace pricing plan official",
        "site:marketplace.gohighlevel.com/docs API v2 OAuth private integration token REST API HighLevel endpoints",
        "site:gohighlevel.com pricing HighLevel API access Starter Unlimited Agency Pro official trial self serve",
    ],
    35: [
        "site:mailchimp.com/developer Mailchimp Marketing API authentication API key OAuth MCP official",
        "site:mailchimp.com/developer MCP Mailchimp official Model Context Protocol API partner access pricing",
        "Mailchimp Transactional MCP server official connection endpoint authentication AI Agents permission API key docs",
        "site:mailchimp.com/help create API key Account extras API keys Mailchimp API access official free plan pricing",
        "Mailchimp Marketing API REST v3 OAuth API key self-service credentials official documentation",
    ],
    36: [
        "site:developers.klaviyo.com API authentication private API key OAuth scopes MCP official",
        "site:developers.klaviyo.com/en/docs authentication private API keys OAuth apps developer MCP server official",
        "Klaviyo MCP server beta tools read only write operations official docs scopes API private key API pricing plan",
        "site:developers.klaviyo.com MCP server https mcp.klaviyo.com remote MCP connector hosted official",
        "site:developers.klaviyo.com \"mcp.klaviyo.com\" remote MCP connector hosted official 2026",
    ],
    37: [
        "site:systeme.io API documentation API key MCP official integrations developer",
        "site:systeme.io/pricing public API MCP keys plan all plans official site:developer.systeme.io/docs/mcp-server",
        "Systeme.io official MCP docs endpoint tools contact tags OAuth API keys available plans developer.systeme.io MCP server",
        "site:developer.systeme.io/docs/mcp-server MCP server systeme.io official tools endpoint key authentication",
        "site:developer.systeme.io/docs/mcp-server \"MCP\" \"systeme.io\" official server endpoint tools authentication",
    ],
    38: [
        "site:developers.pinterest.com API OAuth developer access MCP official",
        "Pinterest API OAuth developer official MCP access",
        "Pinterest API MCP Server official documentation endpoints ads analytics OAuth permissions rate limits API access developers.pinterest.com",
        "site:developers.pinterest.com/docs/api/v5 Pinterest API v5 scopes approved access trial standard authentication official",
        "site:developers.pinterest.com/docs/getting-started/connect-app Pinterest app review Trial access Standard access API official developer",
    ],
    39: [
        "site:developers.facebook.com/docs/threads Threads API OAuth permissions app review MCP official",
        "site:developers.facebook.com/documentation/threads Threads API access OAuth permissions getting started official MCP server",
        "Threads API getting started app setup OAuth scopes access token official developer docs Threads Graph API MCP",
        "site:developers.facebook.com/documentation/threads/get-started Threads API getting started create app access token scopes official",
        "site:developers.facebook.com/documentation/threads/get-started Threads API OAuth permissions app review Threads Tester official",
    ],
    40: [
        "site:twilio.com/docs/sendgrid API key authentication developer MCP official",
        "site:twilio.com/docs/sendgrid pricing free plan API MCP server official",
        "site:twilio.com/docs/sendgrid \"MCP\" SendGrid official Model Context Protocol server",
        "site:twilio.com/docs/sendgrid/pricing Twilio SendGrid pricing free plan official API",
        "site:twilio.com/docs/ai/mcp SendGrid API Twilio MCP supported products official",
    ],
    41: [
        "site:shopify.dev/docs/api MCP Storefront MCP developer docs GraphQL API authentication app scopes official",
        "site:shopify.dev/docs/apps/build/mcp-server Shopify MCP Storefront API developer server official",
        "Shopify MCP server Shopify Dev MCP Server official Shopify Storefront API MCP tools docs site:shopify.dev",
        "site:shopify.dev/docs/apps/build/authentication-authorization OAuth authentication custom apps Shopify Admin GraphQL API official",
        "site:shopify.dev/docs/api/admin-rest legacy Shopify REST API new public apps GraphQL 2025",
    ],
}

# Successful opened pages, with chunk indexes inspected. The count is for
# distinct retained page/chunk captures used in this evidence packet; repeated
# exploratory fetches are not duplicated as separate source records.
FETCH_COUNTS = {
    32: {"meta_api": [0], "meta_faq": [0], "meta_auth": [0, 1], "meta_rate": [0]},
    33: {"linkedin_access": [0], "linkedin_tiers": [0, 1, 2], "linkedin_ads": [0]},
    34: {"ghl_api": [0], "ghl_auth": [0], "ghl_support": [0, 1], "ghl_mcp": [0], "ghl_pricing": [0]},
    35: {"mailchimp_api": [0], "mailchimp_quickstart": [0], "mailchimp_key_help": [0], "mailchimp_integrations": [0, 1], "mailchimp_mcp": [0]},
    36: {"klaviyo_api": [0], "klaviyo_auth": [0], "klaviyo_key_help": [0], "klaviyo_mcp_current": [0], "klaviyo_mcp_connect": [0], "klaviyo_mcp_tools": [0], "klaviyo_mcp_beta": [0]},
    37: {"systeme_api": [0], "systeme_key_help": [0, 1], "systeme_mcp_dev": [0], "systeme_mcp_help": [0, 1], "systeme_mcp_chatgpt": [0], "systeme_chatgpt_help": [0], "systeme_pricing": [0]},
    38: {"pinterest_api": [0], "pinterest_auth": [0, 1], "pinterest_app": [0], "pinterest_tiers": [0], "pinterest_mcp": [0]},
    39: {"threads_get_started": [0, 1], "threads_overview": [0], "threads_profiles": [0]},
    40: {"sendgrid_product": [0], "sendgrid_auth": [0], "sendgrid_quickstart": [0, 1], "sendgrid_api": [0], "sendgrid_pricing": [0], "twilio_mcp": [0, 1]},
    41: {"shopify_graphql": [0], "shopify_rest": [0], "shopify_auth": [0], "shopify_scopes": [0], "shopify_distribution": [0], "shopify_storefront_mcp": [0], "shopify_dev_mcp": [0]},
}

# Unusable redirects / exploratory fetches are retained as failed or non-evidence
# events rather than being presented as successful claim sources.
FAILED_FETCHES = {
    35: [
        {"url": "https://mailchimp.com/developer/marketing/guides/marketing-api-conventions/", "chunk_index": 0, "status": "REDIRECTED_TO_GENERIC_DEVELOPER_HOME", "note": "Returned the generic Mailchimp Developer landing page, not the requested Marketing API conventions; excluded from claim evidence and replaced with opened official quick-start/integrations docs."},
    ],
    40: [
        {"url": "https://sendgrid.com/pricing/", "chunk_index": 0, "status": "REDIRECTED_TO_PRODUCT_OVERVIEW", "note": "Resolved to a generic Twilio SendGrid landing page without plan details; later opened the current Twilio Email API pricing page directly."},
    ],
    41: [
        {"url": "https://shopify.dev/docs/apps/build/devmcp", "chunk_index": 0, "status": "REDIRECTED_TO_CURRENT_AI_TOOLKIT_DOCS", "note": "The current first-party AI Toolkit page was opened and retained as the canonical Shopify Dev MCP source."},
    ],
}


def ev(field: str, claim: str, source_key: str, observation: str | None = None, support="supports") -> dict:
    s = SOURCES[source_key]
    return {
        "claim": claim,
        "field": field,
        "source_url": s["url"],
        "source_title": s["title"],
        "source_type": s["source_type"],
        "accessed_at": DATE,
        "support": support,
        "excerpt_or_observation": observation or s["excerpt_or_observation"],
    }


RECORDS = {
    32: {
        "description": "Meta Marketing API is a Graph API-based surface for creating, managing, and analyzing advertising campaigns across Meta technologies.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Developers can create an app and add the Marketing API for default Limited/development access. Live advertiser production use, broader permissions and Full access are subject to App Review, advertiser consent, app access levels and account eligibility.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a Meta developer app, add Marketing API, generate access tokens, request ads_read/ads_management as needed, and obtain ad-account authorization from the advertiser; system-user tokens are also documented for server-side use.", "plan_or_gate": "Default Limited access is development-only and heavily rate-limited. Full access and advanced permissions require App Review/qualification; some sensitive access may require business verification. Ad spend is separate from API access."},
        "api": {"available": "YES", "types": ["Other"], "breadth": "BROAD", "details": "Meta describes the Marketing API as Graph API endpoints (not GraphQL), covering campaigns, ad sets, creatives, audience/optimization, insights, catalogs and related business resources."},
        "mcp": {"status": "UNKNOWN", "details": "No opened first-party Meta Ads MCP setup or availability page was identified in the targeted official searches. This is UNKNOWN, not a claim that no Meta Ads MCP exists.", "search_scope": "Targeted official Meta Developer searches for Marketing API MCP/Meta Ads MCP and inspected the official Marketing API overview, FAQ, authorization and rate-limit pages; no dedicated first-party MCP connection guide was captured."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Production use for external advertisers depends on Meta app review/permissions, Full access qualification, business/ad-account roles and any required business verification.", "rationale": "The official Graph API endpoints and SDK paths make an integration technically feasible, with development access for exploration. Production access and operational limits are material app-review and advertiser-account constraints."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No Meta developer app, ad account, token, or live API call was created or tested. MCP availability remains UNKNOWN."],
        "evidence": [
            ev("description", "Meta describes the Marketing API as advertising functionality across its technologies through Graph API endpoints.", "meta_api"),
            ev("auth", "Meta's Marketing API authorization uses developer-generated access tokens and OAuth permission consent such as ads_read or ads_management.", "meta_auth"),
            ev("self_serve", "Adding the Marketing API product grants default Limited/development access; full/production access is subject to App Review and qualification.", "meta_auth"),
            ev("credential_access", "Developers create a Meta app, generate tokens and request scopes; external ad-account use requires the appropriate app access and advertiser permissions.", "meta_auth"),
            ev("api", "The official overview defines this as a collection of Graph API endpoints and links campaign, insights, catalog, and business resources.", "meta_api"),
            ev("buildability", "Meta's official FAQ says production use requires app review and documents campaign/insights endpoints for API integration.", "meta_faq"),
        ],
    },
    33: {
        "description": "LinkedIn's Advertising API supports programmatic ad-account, campaign-management and reporting workflows.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "ADMIN_APPROVAL_REQUIRED",
        "self_serve_details": "A developer app can be created in the Developer Portal, but Advertising API product access requires LinkedIn approval. All apps start in Development tier; Standard access is a separate request and has broader multi-account capabilities.",
        "credential_access": {"status": "GATED", "path": "Create a LinkedIn developer app, request the Advertising API product, receive approval, then obtain a 3-legged OAuth member token with rw_ads/r_ads scopes and map eligible ad accounts in Development tier.", "plan_or_gate": "LinkedIn approves Advertising API access. Development tier edits up to five administered ad accounts; Standard tier requires a separate support-ticket request and member/ad-account roles."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Versioned REST endpoints cover ad accounts, campaign groups, campaigns, creatives and reporting; Marketing API writes require rw_ads and tier/role-specific access."},
        "mcp": {"status": "UNKNOWN", "details": "No first-party LinkedIn Ads MCP connection page was identified in the targeted official Microsoft Learn/LinkedIn developer searches. Status remains UNKNOWN, not NO.", "search_scope": "Searched LinkedIn Marketing API, OAuth/access tiers, and LinkedIn Ads MCP across official learn.microsoft.com/linkedin and LinkedIn developer documentation; claim evidence uses opened OAuth and API pages only."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Advertising API approval and member-consented OAuth scopes are required; broad production campaign management requires Standard-tier approval and eligible ad-account roles.", "rationale": "LinkedIn provides a Development tier for approved developers to build/test and REST campaign endpoints. Production multi-account capabilities and approval remain a material external gate."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No LinkedIn app, member authorization, or ad-account access was tested. MCP availability remains UNKNOWN."],
        "evidence": [
            ev("description", "LinkedIn's campaign guide shows Advertising API account and campaign workflows.", "linkedin_ads"),
            ev("auth", "LinkedIn Marketing permissions are member-granted 3-legged OAuth scopes, including rw_ads and r_ads.", "linkedin_tiers"),
            ev("self_serve", "The Developer Portal app flow does not automatically enable Advertising API access; LinkedIn approval is required.", "linkedin_access"),
            ev("credential_access", "After API product approval, member OAuth and account-role/scope consent are needed; Standard tier access is a separate support request.", "linkedin_tiers"),
            ev("api", "The current campaign guide uses LinkedIn REST endpoints such as POST /rest/adAccounts and campaign resources.", "linkedin_ads"),
            ev("buildability", "The Development tier permits end-to-end testing with limited edit access; broader Standard access must be requested separately.", "linkedin_tiers"),
        ],
    },
    34: {
        "description": "HighLevel is a CRM and marketing platform with REST endpoints for contacts, conversations, calendars, workflows, payments and related services.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "HighLevel offers a self-serve 14-day account trial. Its API support article says Basic API access is included on Starter and Unlimited, while Agency Pro includes Advanced API access/OAuth and agency-level tokens; exact endpoint availability can vary by plan.",
        "credential_access": {"status": "RESTRICTED", "path": "Use a Private Integration Token for an internal/single-sub-account integration, or request an OAuth 2.0 Marketplace app for user-authorized public or multi-location access.", "plan_or_gate": "Basic and Advanced API access differ by HighLevel plan; the support article places OAuth/agency-level tokens in Agency Pro. API v1 is end-of-support; new work should use V2."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "The official portal exposes REST resources for CRM/contacts, conversations, calendars, opportunities, workflows, payments, webhooks and more; API V1 is deprecated/end-of-support."},
        "mcp": {"status": "AVAILABLE", "details": "Official hosted LeadConnector MCP endpoints use OAuth and expose a compact tool interface over 550+ active operations across 38 domains. Available clients/endpoints are documented for Claude and ChatGPT/OpenAI-compatible clients; access is scope- and sub-account-bounded, and multi-account agency rollout is ongoing.", "search_scope": "Opened the official HighLevel API portal, authorization docs, plan/access support article and LeadConnector MCP connection/catalog documentation."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "A qualifying HighLevel plan, app/account authorization and least-privilege scopes are required; public OAuth/multi-location use is plan-gated and internal PITs are narrower.", "rationale": "HighLevel documents both a broad REST API and a hosted OAuth MCP path. V2 is current, but API entitlement, OAuth availability, location boundaries and account-level roles materially constrain deployment."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No HighLevel tenant, plan, location or credential was checked. The opened pricing page rendered the trial signup but not its feature matrix; plan/API details are attributed to the dedicated API support article."],
        "evidence": [
            ev("description", "The API portal describes CRM, conversation, calendar, opportunity and payment resources for the HighLevel platform.", "ghl_api"),
            ev("auth", "HighLevel supports PIT bearer tokens for internal integrations and OAuth 2.0 for public/Marketplace integrations.", "ghl_auth"),
            ev("self_serve", "HighLevel documents a self-serve 14-day trial and plan-specific Basic versus Advanced API access.", "ghl_support"),
            ev("credential_access", "HighLevel directs single-location/internal users to PITs and public/multi-location integrations to OAuth; its support article notes plan-dependent access.", "ghl_auth"),
            ev("api", "The portal exposes broad REST API categories including contacts, messaging, calendars, payments and webhooks.", "ghl_api"),
            ev("mcp", "LeadConnector documents hosted client endpoints, OAuth scopes and 550+ operations across 38 domains.", "ghl_mcp"),
            ev("buildability", "Plan-specific API access and the MCP's authorization/sub-account model are documented constraints for deployment.", "ghl_support"),
        ],
    },
    35: {
        "description": "Mailchimp's Marketing API exposes email-marketing resources for audiences/contacts, campaigns, automation flows, e-commerce and reporting.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["API key", "Basic", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Mailchimp Manager users can generate a Marketing API key in account settings; Admins can view account users' keys. New keys created since 2026-06-22 expire after one year. Marketplace listing and multi-user partner distribution require program review and eligibility; plan-specific endpoint entitlements were not exhaustively mapped.",
        "credential_access": {"status": "RESTRICTED", "path": "Use a self-generated account API key for a single account, or OAuth 2.0 for delegated access to other Mailchimp users; create keys from the account's API Keys settings.", "plan_or_gate": "API keys grant full account access subject to user/endpoint permissions, are not suitable for client-side exposure, and expire after one year if newly created. Marketplace listing requires partner approval, OAuth and 25+ active users in 90 days."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Marketing API v3.0 is a broad HTTP resource API for audiences/contacts, campaigns, automation, e-commerce, reports, batches and webhooks. Transactional Messaging is a separate API/product surface."},
        "mcp": {"status": "AVAILABLE", "details": "Mailchimp's official hosted MCP at https://mandrillapp.com/mcp is scoped to Transactional Messaging (Mandrill), not the Marketing API. It offers transactional account/API/template/onboarding tools with Bearer API-key auth; restricted keys need the AI Agents permission group. No official Marketing API MCP was established by the inspected pages.", "search_scope": "Inspected official Mailchimp Marketing API, API-key, integrations/partner-program and Transactional Messaging MCP docs; MCP availability is scoped to the official Transactional product only."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Account keys are high-privilege and user-role-bound; multi-tenant OAuth Marketplace distribution is subject to partner review and eligibility; transactional MCP does not cover Marketing API.", "rationale": "Mailchimp documents a full Marketing REST API, self-generated API keys and OAuth. A single-account connector is technically feasible, while safe multi-tenant distribution and Marketplace listing require OAuth, partner qualification and review."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No Mailchimp account, plan, API key, OAuth app or partner application was tested. The official MCP finding applies only to Transactional Messaging."],
        "evidence": [
            ev("description", "Mailchimp's Marketing API reference enumerates audiences/contacts, campaigns, automation, batch/webhook and other marketing resources.", "mailchimp_api"),
            ev("auth", "Mailchimp's Marketing API uses account API keys via Basic auth and OAuth 2 for delegated access to other users.", "mailchimp_quickstart"),
            ev("self_serve", "Manager users can generate API keys themselves; new keys expire after one year, while Marketplace listing has a separate approval/partner process.", "mailchimp_key_help"),
            ev("credential_access", "Mailchimp documents self-generated API keys and OAuth for third-party integrations; key access depends on user role and is full-account sensitive.", "mailchimp_quickstart"),
            ev("api", "The official v3.0.91 reference lists broad REST resources across marketing workflows.", "mailchimp_api"),
            ev("mcp", "The official hosted Mailchimp MCP docs specify Transactional Messaging tools and Bearer API-key authorization, not a Marketing API connector.", "mailchimp_mcp"),
            ev("buildability", "Mailchimp recommends OAuth for integrations acting for other users; Marketplace participation requires partner review and active-user/features criteria.", "mailchimp_integrations"),
        ],
    },
    36: {
        "description": "Klaviyo is a marketing automation/customer-engagement platform with APIs and MCP tools for profiles, campaigns, flows, events, catalogs, lists and reporting.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["API key", "OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Private API keys are self-generated from account settings but key management is limited to Owner, Admin or Manager roles and keys must be scoped. Tech-partner OAuth/App Marketplace access is a separate integration path; no universal plan entitlement was inferred.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a scoped private API key in account settings for server-side API calls, use OAuth for delegated tech-partner integrations, or authorize the remote Klaviyo MCP with an Owner/Admin/Manager account.", "plan_or_gate": "Key management and remote MCP connection require Owner, Admin or Manager roles. Private keys are sensitive and scopes cannot be edited after creation; delete/recreate to change them. App Marketplace/OAuth partner flow is distinct from a single-account key."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Klaviyo documents versioned JSON:API/REST surfaces for accounts, campaigns, catalogs, events, flows, profiles, lists/segments, reporting and more, with private-key or OAuth server auth and public-key client endpoints."},
        "mcp": {"status": "AVAILABLE", "details": "Klaviyo's current official remote-hosted MCP is at https://mcp.klaviyo.com/mcp with OAuth; a local private-key server is also documented. The current catalog lists 260+ tools, including read/write campaign, catalog, profile, event, flow and reporting operations, with read-only/user-content filters. Owner/Admin/Manager access is required.", "search_scope": "Opened the current Klaviyo Developer MCP overview, remote connection guide and tools catalog, plus official API authentication and private-key role/scope docs. An older versioned 2025 local-beta page was marked deprecated and not used for current status."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Klaviyo account with an Owner/Admin/Manager role and OAuth consent or a scoped private key; customer-profile data and write-capable tools require careful access controls.", "rationale": "The platform exposes broad REST APIs and a first-party hosted OAuth MCP. Account role, API scopes, user-generated-content handling, and write/read-only configuration are material operating constraints."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No Klaviyo tenant, account role, plan, credentials or MCP session was tested; tool counts and availability reflect the opened official docs."],
        "evidence": [
            ev("description", "Klaviyo's API/MCP documentation covers campaign, flow, profile, event, catalog and reporting data.", "klaviyo_api"),
            ev("auth", "Klaviyo uses private API keys or OAuth for server-side APIs and public company IDs for client-side APIs.", "klaviyo_auth"),
            ev("self_serve", "Klaviyo lets authorized Owner/Admin/Manager users create scoped private API keys from account settings.", "klaviyo_key_help"),
            ev("credential_access", "The remote hosted MCP connection requires an Owner/Admin/Manager account, and direct API keys are scoped and role-controlled.", "klaviyo_mcp_connect"),
            ev("api", "The official API overview lists private-key/OAuth auth, OpenAPI resources and broad versioned JSON:API endpoint families.", "klaviyo_api"),
            ev("mcp", "The current official remote MCP guide and tool catalog document 260+ tools, OAuth access, read/write distinctions and role requirements.", "klaviyo_mcp_tools"),
            ev("buildability", "Klaviyo's remote OAuth connector and local scoped-key path provide implementation routes, with roles, consent and data/write controls.", "klaviyo_mcp_connect"),
        ],
    },
    37: {
        "description": "systeme.io is an all-in-one online business platform spanning funnels, contacts/CRM, email marketing, courses, products and automations.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["API key"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "The official pricing page lists a $0 Free plan and API request limits of 30/minute (higher paid-tier limits are shown). Public API and MCP keys are created in dashboard settings; the MCP is described as Beta/initial-release and ChatGPT custom use requires Developer Mode and a compatible plan/workspace.",
        "credential_access": {"status": "SELF_SERVE", "path": "Generate a Public API key or MCP key under Profile Settings → MCP & API keys. The Public API key is sent in X-API-Key; MCP uses X-MCP-Key or an mcpKey URL parameter.", "plan_or_gate": "Public API keys can be configured with no expiry and are capped at three per account; MCP keys are capped at two and last at most 90 days. OAuth is planned, not documented as available. ChatGPT's custom MCP path is in Beta and may be restricted by ChatGPT plan/workspace settings."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "The Public API covers contacts, tags, newsletters/campaigns, funnels, courses, products, automation rules, subscriptions, bookings and webhooks, using X-API-Key auth and shared rate limits. Some operations are restricted or unsupported through MCP specifically."},
        "mcp": {"status": "AVAILABLE", "details": "Official hosted MCP at https://mcp.systeme.io/mcp is available in Beta with key-based access and shared API rate limits. Developer docs list contacts, tags, contact fields and newsletters; a newer Help Center MCP guide (2026-09-15) additionally lists campaigns, funnels, automations, products, price plans, bookings, courses and SMS templates. Catalog scope conflicts across first-party docs, so the wider tool list is not treated as independently reconciled.", "search_scope": "Opened current official developer MCP docs, ChatGPT integration guide, 2026-09-15 Help Center MCP guide, Public API docs/key help and pricing. The technical and Help Center MCP tool catalogs differ; this is preserved as a source conflict."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Uses self-managed API/MCP keys; MCP keys expire within 90 days, OAuth is not yet available, API quotas vary by plan, and MCP is Beta with a conflicting official tool catalog.", "rationale": "The Public REST API is documented and a first-party remote MCP is available, including a free plan path. Key rotation, shared rate limits, client Developer Mode and the unresolved tool-catalog mismatch constrain production use."},
        "confidence": "MEDIUM",
        "research_status": "PARTIAL",
        "source_conflicts": [
            {"field": "mcp", "summary": "The official developer MCP reference says only contacts, tags, contact fields and newsletters are supported; the official Help Center MCP article last updated 2026-09-15 lists many additional domains, including campaigns, funnels, automation, products, bookings, courses and SMS templates.", "resolution": "Both opened first-party sources are retained. The MCP server's existence and key auth are confirmed, but the current full tool catalog is unresolved; broader Help Center capabilities are reported as vendor-documented, not reconciled as a single authoritative catalog."}
        ],
        "limitations": ["No systeme.io account or MCP connection was tested. Free-plan API limits are recorded from the official pricing comparison; no claim is made that every MCP/API operation is identically enabled on all plans."],
        "evidence": [
            ev("description", "Systeme.io pricing and developer materials describe funnels, contacts, email marketing and other online-business features.", "systeme_pricing"),
            ev("auth", "The Public API's only documented auth option is an X-API-Key request header.", "systeme_api"),
            ev("self_serve", "Systeme.io lists a free plan with 30 API requests/minute; account keys are generated in settings, while ChatGPT MCP is a Beta custom connector.", "systeme_pricing"),
            ev("credential_access", "The official help docs give account-setting steps for Public API/MCP key creation and key-count/expiry rules.", "systeme_key_help"),
            ev("api", "The Public API is RESTful and its help/reference documents contacts, newsletters, funnels, courses, automations, products and webhooks.", "systeme_key_help"),
            ev("mcp", "Official Systeme.io documents a hosted MCP endpoint and key-based auth; its current Help Center lists expanded MCP capabilities, while the technical tool catalog is narrower.", "systeme_mcp_help"),
            ev("mcp", "The official technical MCP reference documents the endpoint auth headers and the core contacts/tags/fields/newsletters tool set.", "systeme_mcp_dev"),
            ev("buildability", "Systeme.io documents a direct hosted MCP URL and key-based setup, but labels ChatGPT integration Beta and warns about write restrictions.", "systeme_mcp_chatgpt"),
        ],
    },
    38: {
        "description": "Pinterest's REST API supports content management, ads, analytics, targeting, conversion tracking, shopping catalogs and media planning.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Basic", "Bearer/token"],
        "self_serve_status": "ADMIN_APPROVAL_REQUIRED",
        "self_serve_details": "Developers must use a Pinterest business account, verify email and request Trial API access; Pinterest reviews the app before providing app ID/secret. Standard access requires a separate upgrade request with a demo video and review.",
        "credential_access": {"status": "GATED", "path": "Register an app through Pinterest Developers, receive app credentials after Trial approval, then use OAuth scopes and a registered redirect URI to obtain Bearer access tokens.", "plan_or_gate": "Trial access itself is reviewed; Standard access is a further approval gate, with higher rate limits and user-visible Pins/Boards. Trial-created Pins/Boards are sandbox-visible only to their creator."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Pinterest REST API v5 spans content/Pins/boards, ads/campaigns, analytics, conversion tracking, audiences/targeting, media planning and shopping catalogs."},
        "mcp": {"status": "UNKNOWN", "details": "Pinterest Developers announces an MCP server but its page says to sign up for updates 'when it launches'; a sample endpoint appears, but public launch/connection availability is not confirmed. Status remains UNKNOWN, not NO.", "search_scope": "Opened the official Pinterest MCP announcement and searched official developer docs for its public connection/setup. The announcement indicates a pending launch rather than a verified available service."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Pinterest reviews Trial access requests and separately approves Standard access; OAuth, verified business-account administration, scopes, demo and rate-limit tiers apply.", "rationale": "The REST API is broad and has a documented OAuth flow, but API credentials require approved app access and full production functionality requires Standard-tier review."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No Pinterest developer account, app request, business account or token was created. MCP launch status is not confirmed."],
        "evidence": [
            ev("description", "Pinterest's official v5 reference lists content, ads, analytics, conversions, targeting and catalog use cases.", "pinterest_api"),
            ev("auth", "Pinterest documents Authorization Code/Client Credentials OAuth, app credentials, Basic token endpoint auth and Bearer API requests.", "pinterest_auth"),
            ev("self_serve", "Trial access requires an app request reviewed by Pinterest; Standard access requires a separate reviewed upgrade with a demo video.", "pinterest_app"),
            ev("credential_access", "A business account, verified email, Developer Terms acceptance and approved Trial app are prerequisites for app ID/secret and OAuth.", "pinterest_app"),
            ev("api", "The Pinterest API is REST v5 with broad content, advertising, analytics, targeting, conversion and shopping endpoints.", "pinterest_api"),
            ev("mcp", "The official Pinterest MCP page is a launch announcement with a waitlist and does not confirm the server is publicly launched.", "pinterest_mcp", support="context"),
            ev("buildability", "Pinterest differentiates Trial from Standard access and requires an OAuth/live-integration demo for Standard review.", "pinterest_tiers"),
        ],
    },
    39: {
        "description": "The Threads API enables authorized apps to retrieve profile/media data, publish content, manage replies and access selected insights for Threads users.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Developers can create a Meta app with the Threads use case and test with Threads Testers. Users without an app role can authorize only after the relevant permissions pass App Review and the app is published.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a Threads-use-case Meta app, use its Threads-specific app ID/secret, complete the OAuth authorization window, and receive an app-scoped Threads user access token with requested scopes.", "plan_or_gate": "App testers can grant permissions for development; public user access requires App Review and app publication. Short-lived tokens last 1 hour, long-lived tokens 60 days; media for publishing must be publicly accessible."},
        "api": {"available": "YES", "types": ["Other"], "breadth": "MODERATE", "details": "Threads exposes versioned Graph API-style HTTP endpoints for profile discovery, media retrieval/publishing, replies and insights. This is a Threads-specific Graph API surface, not GraphQL."},
        "mcp": {"status": "UNKNOWN", "details": "No first-party Meta Threads MCP connection or action server was identified in the inspected official Threads developer docs. Status remains UNKNOWN, not a definitive NO; community MCP projects are outside the evidence scope.", "search_scope": "Searched official Meta Threads developer documentation for MCP and inspected Get Started, API overview and Profiles pages. Search results for third-party MCPs were not used as evidence."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "External-user access requires app review/publication, user OAuth/scopes, token refresh handling, and a publicly reachable media URL for publishing.", "rationale": "Meta documents a usable Threads API and tester workflow, but public rollout is permission-reviewed and tokens/media hosting impose operational requirements."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No Meta app, Threads tester, user token or API call was created or tested. MCP availability remains UNKNOWN."],
        "evidence": [
            ev("description", "Meta's Threads overview supports publishing/displaying content for the author and describes profile/content API functions.", "threads_overview"),
            ev("auth", "Threads API uses app-scoped user access tokens conforming to OAuth 2.0, sent with the required permissions.", "threads_get_started"),
            ev("self_serve", "App users with a tester role can authorize during development; users without app roles require reviewed permissions and a published app.", "threads_get_started"),
            ev("credential_access", "Threads credentials are app-use-case-specific and OAuth user tokens require scope consent; App Review gates access for non-testers.", "threads_get_started"),
            ev("api", "Meta documents Graph API-style Threads profile and discovery endpoints plus publishing and rate-limited content operations.", "threads_profiles"),
            ev("buildability", "The Threads overview documents publishing and operational quotas that a production integration must handle.", "threads_overview"),
        ],
    },
    40: {
        "description": "SendGrid provides a transactional email API/SMTP service and separate marketing-campaign products.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["API key", "Bearer/token", "Basic"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "SendGrid offers a self-serve, no-credit-card 60-day free trial capped at 100 emails/day; Essentials/Pro are paid and Premier is sales-led. API-key creation is self-service, while 2FA, key scopes, sender/domain authentication and volume limits apply.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create a permission-scoped API key in SendGrid account Settings and send it as a Bearer token; some services accept Basic auth with username 'apikey' and the key as password.", "plan_or_gate": "Twilio requires 2FA for all SendGrid users. Production email requires sender/domain authentication for deliverability; trial/paid plans impose volume and feature limits."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "SendGrid Web API v3 is an HTTP/JSON REST API with SDKs for seven languages and email sending, templates, account/deliverability, event webhooks and related resource families."},
        "mcp": {"status": "AVAILABLE", "details": "Twilio's official hosted MCP (Public Beta) indexes SendGrid documentation/support and public API information. It is unauthenticated and read-only search/retrieval; it does not connect to a SendGrid account or execute email/API actions. No SendGrid-specific action MCP is asserted.", "search_scope": "Opened SendGrid API/auth/pricing docs and Twilio's official MCP documentation, which explicitly lists SendGrid docs/support as indexed content and states the MCP is read-only/public-spec retrieval."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "A scoped API key, enforced 2FA, sender/domain authentication, free-trial message caps and paid-plan volume limits apply; Twilio MCP is documentation-only.", "rationale": "The v3 REST API and SDKs are documented with a self-serve account/key path. A production email connector still needs sending-domain setup, secure key handling, quota management and appropriate plan capacity."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No SendGrid account, sender domain, API key, email send or MCP session was created/tested. MCP status refers only to documentation retrieval, not SendGrid account actions."],
        "evidence": [
            ev("description", "Twilio describes SendGrid Email API/SMTP and a separate marketing-campaign product.", "sendgrid_product"),
            ev("auth", "SendGrid API keys are used as Bearer tokens; Basic auth is only supported with the API key as password for some services.", "sendgrid_auth"),
            ev("self_serve", "Twilio lists a no-credit-card self-serve free trial (100 emails/day for 60 days) and paid monthly plans.", "sendgrid_pricing"),
            ev("credential_access", "The official docs show self-service API-key creation in account Settings and permission-scoped keys.", "sendgrid_auth"),
            ev("api", "SendGrid identifies its v3 surface as a Web REST API with official libraries in seven languages.", "sendgrid_api"),
            ev("mcp", "Twilio's official MCP is a read-only hosted documentation/spec search that includes SendGrid docs/support.", "twilio_mcp"),
            ev("buildability", "The API quick start requires an account/key and documents sender authentication as an email-delivery prerequisite.", "sendgrid_quickstart"),
        ],
    },
    41: {
        "description": "Shopify is an ecommerce platform with merchant-facing Admin and Storefront APIs for products, orders, customers and store operations.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Developers can build public or custom apps and merchants approve requested scopes during installation. Public distribution requires Shopify review; custom distribution avoids public-app approval but is limited to eligible stores. Protected scopes/data may require additional Shopify approval.",
        "credential_access": {"status": "RESTRICTED", "path": "Create an app in the Shopify developer workflow, request only needed scopes, obtain a store access token through token exchange/OAuth/client credentials as appropriate, and send X-Shopify-Access-Token.", "plan_or_gate": "Merchant approval is required for requested scopes; some scopes require Shopify approval. Public apps require review; custom distribution has store/organization limits. Legacy Admin-created custom apps can no longer be created."},
        "api": {"available": "YES", "types": ["GraphQL", "REST"], "breadth": "BROAD", "details": "GraphQL Admin API is the required surface for new public apps; REST Admin API remains documented but is legacy as of 2024-10-01. Shopify exposes broad Admin, Storefront, Customer Account and related API families with access scopes."},
        "mcp": {"status": "AVAILABLE", "details": "Shopify documents two first-party MCP surfaces: a no-auth local Dev MCP/AI Toolkit for docs, API schemas and code validation; and per-store Storefront MCP endpoints for catalog, cart and policy actions, with no authentication requirement but possible store-specific restrictions. This does not imply a general Admin API action MCP.", "search_scope": "Opened Shopify Dev MCP/AI Toolkit docs, Storefront MCP server docs, API auth/scopes, GraphQL/REST references and app distribution requirements."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Merchant-approved scopes, protected-data approvals, app distribution review and store/organization limits apply; new public apps must use GraphQL Admin API rather than legacy REST.", "rationale": "Shopify provides broad versioned API surfaces and official SDK/CLI support, plus first-party developer/storefront MCP servers. App review, scope approvals, merchant authorization and store-context limits shape the implementation."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "limitations": ["No Shopify developer account, store, app, merchant installation, protected-data request or API/MCP call was tested. Storefront MCP availability can vary by shop."],
        "evidence": [
            ev("description", "Shopify's Admin API reference describes building apps/integrations that extend the merchant admin; the API family includes Storefront surfaces.", "shopify_graphql"),
            ev("auth", "Shopify apps use app-specific grants and store access tokens sent in the X-Shopify-Access-Token header.", "shopify_auth"),
            ev("self_serve", "Shopify documents public and custom app distribution; public apps require approval while custom distribution does not but is store-limited.", "shopify_distribution"),
            ev("credential_access", "Access scopes are declared by apps, approved by merchants at install, and selected protected scopes require Shopify approval.", "shopify_scopes"),
            ev("api", "Shopify directs new public apps to GraphQL Admin API and labels REST Admin API legacy as of 2024-10-01.", "shopify_rest"),
            ev("mcp", "Shopify's official Storefront MCP has per-shop catalog/cart/policy tools; the Dev MCP is a separate local documentation/schema tool.", "shopify_storefront_mcp"),
            ev("mcp", "Shopify's AI Toolkit documents the unauthenticated local Dev MCP for developer documentation, schemas and validation.", "shopify_dev_mcp"),
            ev("buildability", "Shopify's distribution documentation distinguishes approved public apps from no-review but restricted custom-distribution apps.", "shopify_distribution"),
        ],
    },
}


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
        rec["verification_status"] = "NOT_CHECKED"
        rec["research_run_id"] = RUN_ID
        rec["failure_reason"] = None
        rec["quality_gate"] = {}

        query_rows = [
            {"query": q, "depth": "1", "search_status": "SUCCESS", "lead_only": True,
             "note": "Search results were used only to find candidate URLs; snippets were not used as claim evidence."}
            for q in QUERIES[app_id]
        ]
        app_sources = [copy.deepcopy(SOURCES[k]) for k in FETCH_COUNTS[app_id]]
        fetch_attempts = []
        for key, chunk_indexes in FETCH_COUNTS[app_id].items():
            s = SOURCES[key]
            for chunk_index in chunk_indexes:
                fetch_attempts.append({
                    "tool": "fetch_page", "url": s["url"], "chunk_index": chunk_index,
                    "status": "SUCCESS", "note": "Official page opened; claim-relevant observation is retained in the source packet."
                })
        for fail in FAILED_FETCHES.get(app_id, []):
            fetch_attempts.append({"tool": "fetch_page", **copy.deepcopy(fail)})

        query_attempts = [
            {"tool": "web_search", "query": q["query"], "status": "SUCCESS",
             "note": "Search invocation succeeded; results were discovery leads only and not claim evidence."}
            for q in query_rows
        ]
        attempts = query_attempts + fetch_attempts
        rec["query_count"] = len(query_rows)
        rec["source_count"] = len(app_sources)
        rec["attempt_count"] = len(attempts)
        rec["trace_limitations"] = [
            "Search counts preserve the five exact native web_search invocations issued for this app in this batch; snippets were not promoted to evidence.",
            "Source/attempt counts describe distinct retained page/chunk captures used in this evidence packet. Exploratory duplicate fetches are not separately duplicated; known unusable redirects are listed explicitly. The source packet stores date precision because fetch_page does not expose a page-level clock time.",
            "This is an incremental 10-app capture artifact only. It is not a merged or verified 100-app dataset.",
        ]

        source_urls = {s["url"] for s in app_sources}
        rec["quality_gate"] = validate_record_quality(rec, source_urls=source_urls)
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
        "scope": "Apps 32-41 only. App records in this standalone capture are not merged into data/raw/final_full_research.json; this is not the completed 100-app dataset.",
        "search_result_policy": "Search-result snippets are discovery leads only and are excluded from claim evidence. Evidence cites opened official vendor/developer pages.",
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
        identity = next(x for x in json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8")) if x["app_id"] == record["app_id"])
        if record["app"] != identity["app"] or record["category"] != identity["category"]:
            errors.append((record["app_id"], ["manifest identity/category mismatch"]))
    if errors:
        print(json.dumps(errors, indent=2, ensure_ascii=False))
        return 1

    out = ROOT / "data/evidence/native_web_capture_batch02_2026-09-24.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} with {len(payload['records'])} rows and {len(payload['traces'])} traces")
    print("record quality:", {s: sum(r['quality_gate']['status'] == s for r in payload['records']) for s in ['PASS', 'WARN', 'FAIL']})
    for r in payload["records"]:
        print(r["app_id"], r["app"], r["research_status"], r["quality_gate"]["status"], r["query_count"], r["source_count"], r["attempt_count"])
        for warning in r["quality_gate"]["warnings"]:
            print("  WARN:", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

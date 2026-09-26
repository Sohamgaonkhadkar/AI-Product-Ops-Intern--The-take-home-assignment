#!/usr/bin/env python3
"""Assemble the sixth standalone native-web evidence batch.

Scope: manifest IDs 71-79. This builder never edits the authoritative raw
research JSON/CSV. Native search results are discovery leads only; claims cite
opened first-party pages. Records remain standalone until the dataset-wide gates
and independent validation are complete.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.quality import validate_record_quality
from src.utils.validation import validate_record

DATE = "2026-09-24"
RUN_ID = "arena-native-web-batch06-20260924"
IDS = list(range(71, 80))
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
    # 71 Notion
    "notion_mcp_overview": source(
        "https://developers.notion.com/guides/mcp/overview",
        "Notion MCP overview - Notion Docs",
        "official_docs",
        "Notion documents a hosted, vendor-operated MCP server and explains its role as an agent interface to Notion workspace content. The connection uses Notion authorization and inherits the connected user's access; the official remote service is distinct from the older self-hosted open-source server.",
        (0,),
    ),
    "notion_mcp_setup": source(
        "https://developers.notion.com/guides/mcp/get-started-with-mcp",
        "Connect to Notion MCP - Notion Docs",
        "official_docs",
        "The guide configures the hosted Streamable HTTP endpoint https://mcp.notion.com/mcp and completes an OAuth flow. The page also distinguishes the hosted service from the no-longer-maintained open-source server.",
        (0, 1),
    ),
    "notion_mcp_tools": source(
        "https://developers.notion.com/guides/mcp/mcp-supported-tools",
        "Supported tools - Notion Docs",
        "official_docs",
        "The official tool reference covers searching, reading, creating and updating Notion content. Some advanced data-source querying requires Business/Enterprise with Notion AI; view mode is generally available and other plans receive metered single-data-source access.",
        (0, 1),
    ),
    "notion_api": source(
        "https://developers.notion.com/reference/intro",
        "Introduction - Notion API",
        "official_api_docs",
        "Notion's public API is a versioned REST API for workspace content and objects, including pages, blocks, databases/data sources, users, comments and related resources. Requests use bearer authorization; internal integrations and OAuth-based public connections are documented.",
        (0,),
    ),
    "notion_api_limits": source(
        "https://developers.notion.com/reference/request-limits",
        "Request limits - Notion API",
        "official_api_docs",
        "Notion publishes API request-limit guidance and instructs integrations to handle rate-limit responses; this provides a concrete operational constraint for automated API use.",
        (0,),
    ),
    "notion_pricing": source(
        "https://www.notion.com/pricing",
        "Notion Pricing Plans: Free, Plus, Business, & Enterprise",
        "official_pricing",
        "The official pricing page lists Free at $0, Plus at $10/member/month, Business at $20/member/month, and Enterprise at custom pricing. The exact availability of advanced MCP tools is separately plan-dependent.",
        (0,),
    ),
    "notion_mcp_security": source(
        "https://developers.notion.com/guides/mcp/mcp-security-best-practices",
        "Security best practices - Notion Docs",
        "official_auth_docs",
        "Notion's security guide confirms official remote MCP endpoints, warns clients can access content available to the connected user, recommends action confirmation, and documents workspace-owner connection controls and organization-level connection management.",
        (0,),
    ),

    # 72 Airtable
    "airtable_mcp": source(
        "https://support.airtable.com/articles/9897799762-using-the-airtable-mcp-server",
        "Using the Airtable MCP server",
        "official_support",
        "Airtable documents its hosted MCP endpoint https://mcp.airtable.com/mcp, OAuth and PAT connection paths, availability on all Airtable plans with no additional Airtable MCP fee, and permission inheritance from the user's Airtable role. Third-party integration controls may require an owner/admin allow-list; MCP usage counts against existing API rate limits and base limits.",
        (0, 1),
    ),
    "airtable_api": source(
        "https://airtable.com/developers/web",
        "Airtable Web API documentation",
        "official_api_docs",
        "Airtable publishes a Web API for programmatic access to bases, records, schemas and related workspace data, with resource-specific reference documentation.",
        (0,),
    ),
    "airtable_auth": source(
        "https://airtable.com/developers/web/api/authentication",
        "Authentication and OAuth - Airtable Web API",
        "official_auth_docs",
        "Airtable's API authentication documentation covers personal access tokens and OAuth authorization, including permission scopes and bearer-token use. Token/integration permissions remain constrained by the user's Airtable access.",
        (0,),
    ),
    "airtable_api_help": source(
        "https://support.airtable.com/articles/6292134965-getting-started-with-airtable-s-web-api",
        "Getting started with Airtable's Web API",
        "official_support",
        "Official help material says Web API access is available on all plan types with varying call limitations, documents a base-level rate limit and plan-specific monthly call caps, and notes that certain organization/base operations need elevated roles.",
        (0,),
    ),
    "airtable_pricing": source(
        "https://airtable.com/pricing",
        "Airtable Pricing",
        "official_pricing",
        "Airtable lists Free at $0, Team at $20/seat/month billed annually, Business at $45/seat/month billed annually, and Enterprise Scale at custom pricing. Plan limits and role controls still apply to API/MCP usage.",
        (0,),
    ),

    # 73 Linear
    "linear_mcp": source(
        "https://linear.app/docs/mcp",
        "MCP server - Linear Docs",
        "official_docs",
        "Linear documents the hosted Streamable HTTP endpoint https://mcp.linear.app/mcp, with OAuth 2.1/dynamic client registration for interactive setup and bearer API-key/OAuth-token alternatives. Default tools are read/write; the /readonly endpoint or read scope restricts tools to read-only. The page documents issues/projects workflow tools and does not clearly map MCP entitlements to each Linear plan.",
        (0, 1),
    ),
    "linear_graphql": source(
        "https://linear.app/developers/graphql",
        "GraphQL API - Linear Developers",
        "official_api_docs",
        "Linear exposes a GraphQL API at https://api.linear.app/graphql for reading and mutating workspace objects. The API reference and developer material cover issues, teams, projects, cycles, users, comments and related product data.",
        (0,),
    ),
    "linear_oauth": source(
        "https://linear.app/developers/oauth-2-0-authentication",
        "OAuth 2.0 authentication - Linear Developers",
        "official_auth_docs",
        "Linear documents OAuth app registration/authorization and personal API-key creation for programmatic access; scopes and the authenticated user/workspace determine accessible actions.",
        (0,),
    ),
    "linear_pricing": source(
        "https://linear.app/pricing",
        "Linear Pricing",
        "official_pricing",
        "The page lists a Free tier at $0, Basic at $10/user/month and Business at $16/user/month when billed annually, plus custom Enterprise. Although MCP appears among product features, the captured feature matrix does not clearly assign MCP availability to a specific plan column.",
        (0,),
    ),
    "linear_rate_limits": source(
        "https://linear.app/developers/rate-limiting",
        "Rate limiting - Linear Developers",
        "official_api_docs",
        "Linear documents request and complexity limits for GraphQL API clients (including hourly user/app quotas) and advises filtering and avoiding polling. API quotas therefore constrain high-volume integration designs.",
        (0,),
    ),

    # 74 Jira / Atlassian
    "jira_rovo_overview": source(
        "https://developer.atlassian.com/cloud/rovo-mcp/",
        "Atlassian Rovo MCP Overview",
        "official_docs",
        "Atlassian's cloud-hosted Rovo MCP server connects MCP clients to Jira and other Atlassian Cloud apps at https://mcp.atlassian.com/v2/mcp. OAuth 2.1 is primary; API-token authentication is an alternative only when enabled by an organization admin. Actions honor existing Atlassian user permissions.",
        (0,),
    ),
    "jira_rovo_getting_started": source(
        "https://developer.atlassian.com/cloud/rovo-mcp/guides/getting-started/",
        "Getting started with the Atlassian Rovo MCP Server",
        "official_docs",
        "The setup guide covers OAuth 2.1 interactive authorization and, where an organization administrator has enabled it, non-interactive API-token authentication for the hosted Rovo MCP endpoint.",
        (0,),
    ),
    "jira_rovo_tools": source(
        "https://developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/",
        "Supported tools - Atlassian Rovo MCP",
        "official_docs",
        "The official dynamic tool catalog includes Jira read/write tools, required scopes/workspace linking and additional permission controls. Some Rovo search/Teamwork Graph calls may consume credits; availability varies by tool and authentication method.",
        (0,),
    ),
    "jira_rovo_oauth": source(
        "https://developer.atlassian.com/cloud/rovo-mcp/guides/configuring-oauth-2-1/",
        "Configuring OAuth 2.1 - Atlassian Rovo MCP",
        "official_auth_docs",
        "Atlassian documents OAuth 2.1 configuration and requested scopes for Rovo MCP; workspace/org policies and the user's existing product permissions continue to apply.",
        (0,),
    ),
    "jira_rovo_api_token": source(
        "https://developer.atlassian.com/cloud/rovo-mcp/guides/configuring-authentication-via-api-token/",
        "Configuring authentication via API token - Atlassian Rovo MCP",
        "official_auth_docs",
        "The API-token guide supports personal-token Basic authentication or service-account-key Bearer authentication, but says organization-admin enablement is required. OAuth 2.1 remains recommended for interactive scenarios.",
        (0,),
    ),
    "jira_rest_software": source(
        "https://developer.atlassian.com/cloud/jira/software/rest/intro/",
        "Jira Software Cloud REST API introduction",
        "official_api_docs",
        "Jira Software Cloud provides a REST API for programmatically accessing Jira software project and issue functionality.",
        (0,),
    ),
    "jira_rest_platform": source(
        "https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/",
        "Jira Cloud platform REST API v3 introduction",
        "official_api_docs",
        "The Jira Cloud platform REST API v3 documents resource groups and operations for issues, projects and wider Jira Cloud administration through HTTP REST endpoints.",
        (0,),
    ),
    "jira_oauth_3lo": source(
        "https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/",
        "OAuth 2.0 (3LO) apps - Jira Cloud platform",
        "official_auth_docs",
        "Atlassian describes OAuth 2.0 three-legged authorization for apps acting on behalf of Jira Cloud users, including app registration and user consent.",
        (0,),
    ),
    "jira_security": source(
        "https://developer.atlassian.com/cloud/jira/platform/security-overview/",
        "Security overview - Jira Cloud platform",
        "official_auth_docs",
        "Atlassian's security guidance describes product permissions and administrative controls that constrain API/app access; API-token-based MCP authentication can be disabled by an organization administrator.",
        (0,),
    ),
    "jira_pricing": source(
        "https://www.atlassian.com/software/jira/pricing",
        "Jira Software Pricing",
        "official_pricing",
        "The public Jira pricing page lists Free at $0 for up to 10 users, Standard at $7.91/user/month, Premium at $14.54/user/month, and custom Enterprise pricing. Rovo-credit/tool availability is a separate, account/plan-specific consideration.",
        (0,),
    ),

    # 75 Asana
    "asana_mcp_tools": source(
        "https://developers.asana.com/docs/mcp-tools-reference",
        "MCP Tools Reference - Asana Developers",
        "official_docs",
        "Asana's V2 MCP tool reference documents read/write task and project actions, interactive confirmation tools in some clients, workspace-scoped MCP tokens, no MCP-specific scopes, and separation between MCP tokens and REST API credentials. Some advanced search tools are plan-limited.",
        (0, 1),
    ),
    "asana_mcp_using": source(
        "https://developers.asana.com/docs/using-asanas-mcp-server",
        "Using Asana's MCP Server",
        "official_docs",
        "Asana publishes the V2 Streamable HTTP endpoint https://mcp.asana.com/v2/mcp and requires user authorization. A client must not be blocked by workspace app management; the page describes Enterprise+ admin allow/block controls and per-client configuration.",
        (0,),
    ),
    "asana_mcp_connect": source(
        "https://developers.asana.com/docs/connecting-mcp-clients-to-asanas-v2-server",
        "Connecting MCP clients to Asana's V2 server",
        "official_docs",
        "The official V2 client guide configures the remote endpoint and OAuth client details for supported coding clients; client setup and redirect configuration are required for some clients.",
        (0,),
    ),
    "asana_mcp_integrate": source(
        "https://developers.asana.com/docs/integrating-with-asanas-mcp-server",
        "Integrating with Asana's MCP Server",
        "official_auth_docs",
        "Asana's V2 MCP is generally available and requires a pre-registered MCP app in the developer console. OAuth 2.0 authorization uses a registered client ID/secret and PKCE; dynamic client registration is not supported. MCP tokens work only with MCP, not REST API calls; app distribution can be restricted to selected workspaces.",
        (0,),
    ),
    "asana_oauth": source(
        "https://developers.asana.com/docs/oauth",
        "OAuth - Asana Developers",
        "official_auth_docs",
        "Asana documents OAuth authorization-code/token exchange and user consent for standard API apps; PATs are also documented for development/testing separately from V2 MCP tokens.",
        (0,),
    ),
    "asana_api": source(
        "https://developers.asana.com/docs/overview",
        "Asana API overview",
        "official_api_docs",
        "Asana's primary developer surface is its REST API for the Work Graph, covering tasks, projects and related workspace resources, with API-reference operations and client tooling.",
        (0,),
    ),
    "asana_pricing": source(
        "https://asana.com/pricing",
        "Asana Pricing - Plans and features",
        "official_pricing",
        "Asana lists Personal at $0 (up to 2 users), Starter at $10.99/user/month and Advanced at $24.99/user/month when billed annually, with custom Enterprise plans. Plan-limited MCP features are distinct from core server availability.",
        (0,),
    ),

    # 76 monday.com
    "monday_mcp_integration": source(
        "https://developer.monday.com/api-reference/docs/integrate-with-monday-mcp",
        "Integrate with the monday MCP server",
        "official_docs",
        "The hosted Platform MCP endpoint is https://mcp.monday.com/mcp over Streamable HTTP. The guide supports OAuth or a bearer personal API token for personal/private use and requires dynamic-client-registration setup for a public integration; calls run with the authenticated user's permissions.",
        (0,),
    ),
    "monday_mcp_ai": source(
        "https://developer.monday.com/api-reference/docs/build-on-monday-with-ai",
        "Build on monday.com with AI",
        "official_docs",
        "The developer guide documents monday.com's hosted Platform MCP (read/write boards, items, workspaces, docs and GraphQL tools), a separate local Apps MCP, and the GraphQL API/typed SDK. Platform MCP calls operate as the user and consume the plan's API quota.",
        (0,),
    ),
    "monday_mcp_tools": source(
        "https://developer.monday.com/api-reference/docs/platform-mcp-tools",
        "Platform MCP tools",
        "official_docs",
        "The official catalog lists more than 60 platform tools for boards/items, workspaces/folders, docs, dashboards/views, users/teams and GraphQL execution. Some newer tools use a preview API schema and may change.",
        (0,),
    ),
    "monday_graphql": source(
        "https://developer.monday.com/api-reference/docs/getting-started",
        "Making your first request - monday.com API",
        "official_api_docs",
        "monday.com's public API is GraphQL at https://api.monday.com/v2, with one endpoint for queries and mutations, API-version headers and examples across several client languages.",
        (0,),
    ),
    "monday_auth": source(
        "https://developer.monday.com/api-reference/docs/authentication",
        "Authentication - monday.com API",
        "official_auth_docs",
        "Personal V2 API tokens are available to users with API access in the Developer Center and sent in the Authorization header; app integrations can use OAuth scopes. Personal tokens inherit the user's monday.com permissions.",
        (0,),
    ),
    "monday_oauth": source(
        "https://developer.monday.com/apps/docs/oauth",
        "OAuth and Permissions - monday.com Apps",
        "official_auth_docs",
        "The OAuth guide documents authorization, permission scopes and app registration. It labels the legacy flow and links to the newer OAuth 2.1 flow, which adds PKCE, expiring access tokens, refresh tokens and revocation.",
        (0,),
    ),
    "monday_oauth_v21": source(
        "https://developer.monday.com/apps/docs/migrating-to-the-new-oauth-flow",
        "Migrating to the new OAuth 2.1 flow - monday.com Apps",
        "official_auth_docs",
        "The current migration guide describes OAuth 2.1 with PKCE, expiring access tokens, refresh-token rotation and revocation. The flow is enabled per app version, so older and newer OAuth implementations coexist.",
        (0,),
    ),
    "monday_rate_limits": source(
        "https://developer.monday.com/api-reference/docs/rate-limits",
        "Rate limits - monday.com API",
        "official_api_docs",
        "The rate-limit guide states hosted Platform MCP tool calls count against the account's daily API limit. Documented daily quotas are 1,000 for Free/Standard/Basic, 10,000 Pro and 25,000 Enterprise; complexity, per-minute and concurrency limits also apply.",
        (0,),
    ),
    "monday_pricing": source(
        "https://monday.com/pricing",
        "monday.com pricing and plans",
        "official_pricing",
        "The pricing page lists Free at $0, Basic at $9/seat/month, Standard at $12, Pro at $19 when billed annually, and custom Enterprise. Seat counts, AI features, usage and API limits vary by plan.",
        (0,),
    ),

    # 77 ClickUp
    "clickup_mcp_overview": source(
        "https://developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server",
        "ClickUp's MCP Server",
        "official_docs",
        "ClickUp documents a public-beta hosted MCP server at https://mcp.clickup.com/mcp and says it is available on all plans. The server supports natural-language task/list/folder/doc workflows and OAuth only; it has no deletion tools as a safety measure. Its page currently lists 50 calls/24h for Free Forever and 300 calls/24h for Unlimited and above without the Everything AI add-on.",
        (0,),
    ),
    "clickup_mcp_help": source(
        "https://help.clickup.com/hc/en-us/articles/33335772678423-What-is-ClickUp-MCP",
        "What is ClickUp MCP? - ClickUp Help",
        "official_support",
        "ClickUp Help confirms all-plan MCP availability and OAuth-only authentication, but its daily call table differs from the developer page: without Everything AI it lists Free 100, Unlimited 300, Business 1,000, Business Plus 2,500 and Enterprise 5,000 per rolling 24 hours. It separately describes API-per-token limits when Everything AI is enabled.",
        (0,),
    ),
    "clickup_mcp_setup": source(
        "https://developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server-1",
        "MCP Server Setup Instructions",
        "official_docs",
        "The setup guide connects MCP clients to https://mcp.clickup.com/mcp with an OAuth authorization flow; Team/Enterprise workspace owners/admins can control configuration in some client environments.",
        (0,),
    ),
    "clickup_mcp_tools": source(
        "https://developer.clickup.com/docs/mcp-tools",
        "Supported Tools - ClickUp MCP",
        "official_docs",
        "The official tool catalog documents workspace/task search, create/update/bulk task operations, comments, tags, dependencies, time tracking and workspace hierarchy. Tools are limited by the user's ClickUp permissions.",
        (0,),
    ),
    "clickup_api_auth": source(
        "https://developer.clickup.com/docs/authentication",
        "Authentication - ClickUp API",
        "official_auth_docs",
        "ClickUp's REST API supports personal API tokens for individual use and OAuth 2.0 authorization-code apps for integrations. Tokens are sent in Authorization; personal token generation requires signing in under Settings > Apps, while only Workspace owners/admins may create OAuth apps.",
        (0,),
    ),
    "clickup_api_start": source(
        "https://developer.clickup.com/docs/Getting%20Started",
        "Get Started with the ClickUp API",
        "official_api_docs",
        "ClickUp provides a public API with v2 and selected v3 endpoints, says endpoint availability varies by plan, and directs users to an OpenAPI reference and per-token rate-limit documentation.",
        (0,),
    ),
    "clickup_api_spec": source(
        "https://developer.clickup.com/docs/open-api-spec",
        "OpenAPI Specification - ClickUp API",
        "official_api_docs",
        "ClickUp publishes OpenAPI specifications for public API v2 and v3, suitable for API tooling/code generation and direct REST integration.",
        (0,),
    ),
    "clickup_api_limits": source(
        "https://developer.clickup.com/docs/rate-limits",
        "Rate Limits - ClickUp API",
        "official_api_docs",
        "API requests are limited per token and vary by Workspace plan; the current table lists 100 requests/minute for Free/Unlimited/Business, 1,000 for Business Plus and 10,000 for Enterprise/Enterprise Plus.",
        (0,),
    ),
    "clickup_pricing": source(
        "https://clickup.com/pricing",
        "ClickUp Pricing and Plans",
        "official_pricing",
        "ClickUp lists Free Forever, Unlimited at $7/user/month billed yearly ($10 monthly), Business at $12 yearly ($19 monthly), and custom Enterprise. Some API features and MCP rates vary by plan/add-on.",
        (0,),
    ),

    # 78 Coda / Superhuman Docs
    "coda_api": source(
        "https://docs.superhuman.com/developers/apis/v1",
        "Superhuman Docs API (v1) Reference Documentation",
        "official_api_docs",
        "The current API reference identifies Superhuman Docs as formerly Coda and documents a REST API at https://coda.io/apis/v1 for docs, folders, pages, tables, rows, formulas, controls, permissions and analytics. API access is free in free and paid workspaces but respects the associated user's role. The reference also documents endpoint/rate-limit behavior.",
        (0, 1, 2),
    ),
    "coda_account": source(
        "https://help.superhuman.com/hc/en-us/articles/46210093335949-Manage-your-Superhuman-Docs-account-settings",
        "Manage your Superhuman Docs account settings",
        "official_support",
        "Superhuman Docs account settings expose API settings where a signed-in user can generate, name and manage personal API tokens. The support page identifies the account as formerly Coda and notes some Enterprise settings may be organization-admin managed.",
        (0,),
    ),
    "coda_mcp_connect": source(
        "https://help.superhuman.com/hc/en-us/articles/46210076980365-Connect-to-the-Superhuman-Docs-MCP",
        "Connect to the Superhuman Docs MCP",
        "official_support",
        "The current official MCP endpoint is https://docs.superhuman.com/apis/mcp. Supported clients use OAuth 2 for some clients or Personal Access Tokens for others. OAuth can be limited to chosen workspaces/folders; the older Coda MCP remains supported for now but is planned for deprecation.",
        (0,),
    ),
    "coda_mcp_security": source(
        "https://help.superhuman.com/hc/en-us/articles/46210118248205-Security-recommendations-for-the-Docs-MCP",
        "Security recommendations for the Docs MCP",
        "official_auth_docs",
        "The security guide describes OAuth 2 with PKCE and MCP-restricted PATs with read, write or read/write scopes. OAuth grants read/write tool access but can be narrowed by workspace/folder; Enterprise administrators can disable PAT access. It identifies the official endpoint and legacy Coda MCP status.",
        (0,),
    ),
    "coda_mcp_guide": source(
        "https://coda.io/resources/guides/getting_started_with_coda_mcp",
        "Getting started with Superhuman Docs MCP",
        "official_product",
        "The official product guide describes an MCP server built into Superhuman Docs for reading data, creating docs/tables and updating content in response to natural-language prompts.",
        (0,),
    ),
    "coda_pricing": source(
        "https://superhuman.com/plans/docs?source=coda.io",
        "Superhuman Docs | Pricing & Plans",
        "official_pricing",
        "Current plans list Free at $0 with a limited MCP trial, Pro at $12 per Doc Maker/month billed annually ($15 monthly), Business at $33 annually ($40 monthly), and custom Enterprise. Paid Pro advertises creating with Claude and other clients via MCP.",
        (0,),
    ),

    # 79 Smartsheet
    "smartsheet_mcp_intro": source(
        "https://developers.smartsheet.com/ai-mcp/smartsheet/mcp-server",
        "Smartsheet MCP server introduction",
        "official_docs",
        "Smartsheet publishes a hosted MCP server for reading, analyzing and managing sheet data; US, EU and AU endpoints are documented. The official introduction and tools reference require Business, Enterprise or Advanced Work Management; portfolio/scenario capabilities have additional plan/role constraints.",
        (0,),
    ),
    "smartsheet_mcp_install": source(
        "https://developers.smartsheet.com/ai-mcp/smartsheet/install-the-smartsheet-mcp-server",
        "Install the Smartsheet MCP server",
        "official_docs",
        "The installation guide requires Business, Enterprise or Advanced Work Management and documents regional hosted endpoints. Clients may use an API token or supported OAuth integrations such as ChatGPT, Claude, Gemini Enterprise Plus and Microsoft 365 Copilot.",
        (0,),
    ),
    "smartsheet_mcp_quickstart": source(
        "https://developers.smartsheet.com/ai-mcp/smartsheet/mcp-quickstart",
        "Quickstart with the MCP server",
        "official_docs",
        "The quickstart configures the hosted HTTP MCP endpoint with a Smartsheet API token and provides a connection test using the server's tool list.",
        (0,),
    ),
    "smartsheet_mcp_tools": source(
        "https://developers.smartsheet.com/ai-mcp/smartsheet/mcp-server-tools",
        "Smartsheet MCP server tools",
        "official_docs",
        "The official tool reference uses the public API under MCP and lists discovery/navigation, sheet/row/column, workflow, user-plan, portfolio and scenario-planning tools. Required plans and OAuth access scopes vary by tool.",
        (0,),
    ),
    "smartsheet_api_intro": source(
        "https://developers.smartsheet.com/api/smartsheet/introduction",
        "Smartsheet API introduction",
        "official_api_docs",
        "The Smartsheet API is REST at https://api.smartsheet.com/2.0, with resource endpoints and client SDKs for JavaScript, Python, Java and C#. Current developer docs say Business, Enterprise or Advanced Work Management is required.",
        (0,),
    ),
    "smartsheet_api_start": source(
        "https://developers.smartsheet.com/api/smartsheet/guides/getting-started",
        "Get Started - Smartsheet API",
        "official_api_docs",
        "The getting-started guide explains in-product token generation, Bearer API requests and a Business/Enterprise/Advanced Work Management plan gate for access tokens.",
        (0,),
    ),
    "smartsheet_api_auth": source(
        "https://developers.smartsheet.com/api/smartsheet/guides/basics/authentication",
        "Authentication - Smartsheet API",
        "official_auth_docs",
        "Smartsheet REST calls accept access tokens/API keys as Bearer credentials; OAuth 2.0 is recommended for user-consent integrations, while raw tokens suit machine-to-machine cases. Regional/Gov environments use separate tokens.",
        (0,),
    ),
    "smartsheet_oauth": source(
        "https://developers.smartsheet.com/api/smartsheet/guides/advanced-topics/oauth",
        "OAuth - Smartsheet API",
        "official_auth_docs",
        "The OAuth guide documents app registration through Smartsheet Developer Tools, user consent, OAuth 2.0 scopes and SDK support. App registration may require activation of Developer Tools for the user account.",
        (0,),
    ),
    "smartsheet_token_help": source(
        "https://help.smartsheet.com/articles/2482389-generate-API-key",
        "Generate an API access token - Smartsheet Learning Center",
        "official_support",
        "The Help Center token-generation article documents in-product token creation/revocation but lists Business and Enterprise under eligible plans, omitting Advanced Work Management from the current developer guides' list.",
        (0,),
    ),
    "smartsheet_free_help": source(
        "https://help.smartsheet.com/articles/2482687-free-plan",
        "Free plan details - Smartsheet Learning Center",
        "official_support",
        "The specific Free-plan help article says Free was discontinued for new Smartsheet signups as of August 28, 2024; existing Free accounts may continue and new users are offered a 30-day trial and paid plans.",
        (0,),
    ),
    "smartsheet_trial_faq": source(
        "https://help.smartsheet.com/articles/529590-smartsheet-free-trial-faqs",
        "FAQ: Smartsheet free trial",
        "official_support",
        "The official trial FAQ describes a 30-day Business-plan trial without billing information and explicitly says trial users cannot generate API access tokens; paid upgrade is required for token/API use.",
        (0,),
    ),
    "smartsheet_pricing": source(
        "https://www.smartsheet.com/pricing",
        "Smartsheet Pricing",
        "official_pricing",
        "The current pricing page lists Pro, Business, Enterprise and Advanced Work Management plans; Business can be started online, while Enterprise/AWM are contact-sales. Business advertises connection to external AI tools through MCP-enabled integrations.",
        (0, 1),
    ),
    "smartsheet_marketing_faq": source(
        "https://www.smartsheet.com/content/smartsheet-faqs",
        "Smartsheet FAQs",
        "official_product",
        "The Smartsheet marketing FAQ, dated April 20, 2026, says Smartsheet offers both a free trial and a free plan, which conflicts with the specific Help Center article stating the Free plan is no longer available to new signups.",
        (0,),
    ),
}

QUERIES = {
    71: [("site:developers.notion.com/guides/mcp Notion MCP official endpoint OAuth API token pricing", "2")],
    72: [("site:support.airtable.com Airtable MCP server OAuth PAT API authentication official pricing", "2")],
    73: [("site:linear.app/docs/mcp Linear MCP endpoint OAuth API keys pricing official", "2")],
    74: [("site:developer.atlassian.com/cloud/rovo-mcp Jira Rovo MCP OAuth API token pricing official", "2")],
    75: [("site:developers.asana.com/docs Asana MCP v2 endpoint OAuth PAT pricing official API", "2")],
    76: [("site:developer.monday.com/api-reference/docs monday MCP server GraphQL OAuth API tokens pricing official", "2")],
    77: [("site:developer.clickup.com/docs ClickUp MCP server OAuth only all plans rate limits API auth pricing", "2")],
    78: [("site:docs.superhuman.com Coda Superhuman Docs MCP server authentication API token pricing free paid", "2")],
    79: [("site:developers.smartsheet.com MCP server required plan API access token free plan FAQ Smartsheet", "2")],
}

FETCH_COUNTS = {
    71: {"notion_mcp_overview": [0], "notion_mcp_setup": [0, 1], "notion_mcp_tools": [0, 1], "notion_api": [0], "notion_api_limits": [0], "notion_pricing": [0], "notion_mcp_security": [0]},
    72: {"airtable_mcp": [0, 1], "airtable_api": [0], "airtable_auth": [0], "airtable_api_help": [0], "airtable_pricing": [0]},
    73: {"linear_mcp": [0, 1], "linear_graphql": [0], "linear_oauth": [0], "linear_pricing": [0], "linear_rate_limits": [0]},
    74: {"jira_rovo_overview": [0], "jira_rovo_getting_started": [0], "jira_rovo_tools": [0], "jira_rovo_oauth": [0], "jira_rovo_api_token": [0], "jira_rest_software": [0], "jira_rest_platform": [0], "jira_oauth_3lo": [0], "jira_security": [0], "jira_pricing": [0]},
    75: {"asana_mcp_tools": [0, 1], "asana_mcp_using": [0], "asana_mcp_connect": [0], "asana_mcp_integrate": [0], "asana_oauth": [0], "asana_api": [0], "asana_pricing": [0]},
    76: {"monday_mcp_integration": [0], "monday_mcp_ai": [0], "monday_mcp_tools": [0], "monday_graphql": [0], "monday_auth": [0], "monday_oauth": [0], "monday_oauth_v21": [0], "monday_rate_limits": [0], "monday_pricing": [0]},
    77: {"clickup_mcp_overview": [0], "clickup_mcp_help": [0], "clickup_mcp_setup": [0], "clickup_mcp_tools": [0], "clickup_api_auth": [0], "clickup_api_start": [0], "clickup_api_spec": [0], "clickup_api_limits": [0], "clickup_pricing": [0]},
    78: {"coda_api": [0, 1, 2], "coda_account": [0], "coda_mcp_connect": [0], "coda_mcp_security": [0], "coda_mcp_guide": [0], "coda_pricing": [0]},
    79: {"smartsheet_mcp_intro": [0], "smartsheet_mcp_install": [0], "smartsheet_mcp_quickstart": [0], "smartsheet_mcp_tools": [0], "smartsheet_api_intro": [0], "smartsheet_api_start": [0], "smartsheet_api_auth": [0], "smartsheet_oauth": [0], "smartsheet_token_help": [0], "smartsheet_free_help": [0], "smartsheet_trial_faq": [0], "smartsheet_pricing": [0, 1], "smartsheet_marketing_faq": [0]},
}

# Material failed/redirected/irrelevant paths are retained as non-evidence rows.
# Search-result snippets are never added to SOURCES or claim evidence.
NON_EVIDENCE_FETCHES = {
    76: [
        {"url": "https://developer.monday.com/api-reference/docs/graphql", "chunk_index": 0, "status": "HTTP_404", "note": "The guessed GraphQL documentation path returned 404; the official Getting Started page and API reference were opened directly and used instead."},
    ],
    77: [
        {"url": "https://clickup.com/api", "chunk_index": 0, "status": "REDIRECTED_NOT_RELEVANT", "note": "The assignment-hint URL redirected to the current ClickUp developer documentation; the canonical API and MCP pages were opened directly."},
        {"url": "https://developer.clickup.com/reference", "chunk_index": 0, "status": "SUCCESS_NOT_USED", "note": "The reference root resolved to a stale/expired request-example page; the official Getting Started guide and OpenAPI specifications were opened for API claims."},
    ],
    78: [
        {"url": "https://coda.io/developers/apis/v1/authentication", "chunk_index": 0, "status": "HTTP_404", "note": "The guessed legacy authentication path returned a not-found page; the current Superhuman Docs API reference and account-settings help page were opened for API token claims."},
        {"url": "https://coda.io/developers/apis/v1", "chunk_index": 0, "status": "REDIRECTED_NOT_RELEVANT", "note": "The legacy Coda API URL redirects to current Superhuman Docs API documentation; the canonical docs URL is captured as a separate opened source."},
    ],
}

RECORDS = {
    71: {
        "description": "Notion is a collaborative workspace for documents, wikis, projects and structured databases, with REST API and MCP surfaces for reading and managing workspace content.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Notion offers Free ($0), Plus ($10/member/month), Business ($20/member/month) and custom Enterprise plans. The hosted MCP is documented, but advanced data-source querying/features vary by plan; Business/Enterprise with Notion AI is required for some advanced tools.",
        "credential_access": {"status": "RESTRICTED", "path": "Create an internal integration/token in Notion's developer/integration settings or authorize the hosted MCP through OAuth. Workspace owners manage MCP client connections in Settings > Connections; organization owners can administer/revoke connections.", "plan_or_gate": "The authenticated user and integration permissions constrain data access. Workspace/organization administrators can restrict clients; some advanced MCP tools require Business/Enterprise with Notion AI."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Notion's versioned REST API covers pages, blocks, databases/data sources, users, comments and other workspace objects. Bearer authentication, request limits and permission-scoped integrations apply."},
        "mcp": {"status": "AVAILABLE", "details": "Notion operates the hosted Streamable HTTP MCP endpoint https://mcp.notion.com/mcp with OAuth. Tools search/read/create/update Notion content; available functions and advanced data-source queries vary by plan and Notion AI entitlement. User/workspace access remains in force.", "search_scope": "Opened Notion's official MCP overview, setup, tool reference, security guidance, REST API introduction/request limits and pricing. Search snippets were discovery-only; no workspace was connected and no MCP/API tool was executed."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Hosted MCP uses user OAuth and workspace/organization controls; some advanced tools are plan/Notion-AI gated, and API request limits apply.", "rationale": "The official REST API and hosted MCP document broad read/write workspace workflows. Use the least-privileged integration and trusted MCP client, confirm plan-specific tools and admin policy, and require review for write actions; no tenant-specific entitlement was checked."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Notion workspace, account plan, integration token, OAuth grant, API request, MCP session or human review was performed; plan-specific feature entitlements were not tested."],
        "researcher_notes": "Notion's hosted OAuth MCP is distinct from the older open-source server, which the official guide says is no longer actively maintained. Search-result snippets were not used as evidence.",
        "evidence": [
            ("description", "Notion's API and MCP documentation cover a collaborative workspace of pages, blocks, databases/data sources and other structured content.", "notion_api"),
            ("auth", "Notion REST API requests use bearer authorization; internal integrations and public OAuth connections are documented.", "notion_api"),
            ("auth", "The hosted Notion MCP setup guide connects to mcp.notion.com/mcp through OAuth.", "notion_mcp_setup"),
            ("self_serve", "The official pricing page lists Free, Plus, Business and Enterprise tiers with the captured monthly prices.", "notion_pricing"),
            ("self_serve", "Notion's MCP tool reference identifies Business/Enterprise with Notion AI as a requirement for some advanced data-source querying.", "notion_mcp_tools"),
            ("credential_access", "Notion provides internal integration/API credentials and an OAuth flow for the hosted MCP connection.", "notion_mcp_setup"),
            ("credential_access", "Workspace owners can manage connections and organization owners can administer/revoke MCP client connections.", "notion_mcp_security"),
            ("api", "The official reference catalogs REST resources for pages, blocks, databases/data sources and other Notion workspace objects.", "notion_api"),
            ("api", "Notion documents API request limits and rate-limit handling for integrations.", "notion_api_limits"),
            ("mcp", "Notion publishes the hosted remote MCP endpoint and tool guide for searching, reading and changing workspace content.", "notion_mcp_overview"),
            ("mcp", "Advanced data-source querying is plan/Notion-AI dependent, while view access is generally available.", "notion_mcp_tools"),
            ("buildability", "Notion warns that connected clients can act on content available to the user and recommends trusted clients, action confirmation and workspace-level controls.", "notion_mcp_security"),
            ("buildability", "Some MCP capabilities require Business/Enterprise plus Notion AI, so feature selection must be matched to the target workspace.", "notion_mcp_tools"),
        ],
    },
    72: {
        "description": "Airtable is a collaborative, database-style work platform built around bases, tables, records, views and connected workflows, with a Web API and official hosted MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Airtable has a Free plan ($0), Team ($20/seat/month annually), Business ($45/seat/month annually) and custom Enterprise Scale. Web API/MCP access is available across plans, but monthly request/base limits, roles and organization integration controls vary.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a personal access token in Airtable account settings or register an OAuth integration; the hosted MCP supports OAuth and PAT authorization. Owner/Creator/Editor roles can manage MCP setup, while an organization admin may need to allow-list third-party integrations.", "plan_or_gate": "User role, base/workspace permissions and organization third-party-integration policy govern access. API calls and MCP actions count against plan/base limits; no additional Airtable MCP fee is documented."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "Airtable's Web API provides REST operations for bases, records, schemas and related resources. The docs list a 5-requests/second/base limit and plan-specific monthly call caps (including 1,000 Free and 100,000 Team); Enterprise limits and certain admin functions differ."},
        "mcp": {"status": "AVAILABLE", "details": "Airtable operates https://mcp.airtable.com/mcp with OAuth and PAT connection paths. MCP is listed for all Airtable plans at no extra Airtable charge; it mirrors the user's role and permissions and counts against API/base limits. Workspace admins can restrict third-party integrations.", "search_scope": "Opened Airtable's official MCP support guide (including setup/FAQ sections), Web API reference/authentication, API getting-started help and current pricing. No base/account was connected and no API/MCP operation was run."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a user-authorized OAuth/PAT connection, role access to the target base and any required admin allow-listing; API call and base limits apply.", "rationale": "The hosted MCP and REST Web API provide documented record/schema workflows across plan types. Use narrowly scoped credentials, confirm organization policy and base permissions, and account for Free/Team rate quotas; no tenant-specific settings were inspected."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Airtable workspace/base, role, plan, token, OAuth grant, API request, MCP session or human review was performed; actual organization policy and usage remain unverified."],
        "researcher_notes": "MCP availability across plans does not imply equal API quotas or identical data access. The official support page says MCP permissions mirror the user's Airtable role and API limits still apply.",
        "evidence": [
            ("description", "Airtable's official Web API documentation organizes programmatic access around bases, records, schema and related workspace resources.", "airtable_api"),
            ("auth", "Airtable documents OAuth and personal access tokens for Web API authentication; MCP supports OAuth or a bearer PAT.", "airtable_auth"),
            ("self_serve", "The Airtable pricing page lists Free, Team, Business and custom Enterprise Scale plans.", "airtable_pricing"),
            ("self_serve", "Airtable's official MCP guide says the hosted MCP server is available on all plans with no additional Airtable charge.", "airtable_mcp"),
            ("credential_access", "Users can create scoped PATs or configure OAuth, but Airtable organization settings may require an admin to allow-list third-party MCP integrations.", "airtable_mcp"),
            ("credential_access", "Airtable's API authentication guide documents token scopes and OAuth registration for developer connections.", "airtable_auth"),
            ("api", "Airtable publishes a REST Web API for bases, records and schema, with API reference documentation.", "airtable_api"),
            ("api", "Official help documents a 5-request/second/base limit and monthly call limits that vary by plan.", "airtable_api_help"),
            ("mcp", "Airtable hosts an official MCP endpoint with OAuth and PAT setup; access mirrors Airtable roles and existing API/base limits.", "airtable_mcp"),
            ("buildability", "Web API limits and elevated-role requirements apply to some API functions, so target-plan and base access must be checked.", "airtable_api_help"),
        ],
    },
    73: {
        "description": "Linear is a product-development and issue-tracking workspace for teams, projects, cycles and work planning, exposed through a GraphQL API and hosted MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Linear lists Free ($0), Basic ($10/user/month annually), Business ($16/user/month annually) and custom Enterprise. The current pricing capture includes an MCP feature but does not clearly assign it to a plan column; API/MCP plan entitlement is therefore not inferred from the page.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create a personal API key in Linear's Security & Access settings or register an OAuth application; the hosted MCP also supports interactive OAuth/dynamic client registration and direct bearer-token/API-key configuration.", "plan_or_gate": "API keys and OAuth credentials operate with the authenticated user's/workspace permissions and chosen scopes. Public API use is rate-limited; confirm any plan-specific feature entitlement with the target workspace."},
        "api": {"available": "YES", "types": ["GraphQL"], "breadth": "BROAD", "details": "Linear's GraphQL API at https://api.linear.app/graphql supports queries and mutations across issues, teams, projects, cycles, users and related workflow objects. API-key and OAuth rate limits and query-complexity limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "Linear's hosted Streamable HTTP MCP is https://mcp.linear.app/mcp; interactive auth uses OAuth 2.1/DCR. Direct bearer API keys or OAuth tokens are supported. Default MCP access is read/write; /readonly or a read-only scope limits the session to reads. The captured pricing matrix does not resolve plan-by-plan entitlement.", "search_scope": "Opened Linear's official MCP setup/FAQ, GraphQL and OAuth developer docs, rate-limit reference and pricing page. The service and auth options are documented; plan-specific MCP availability was not legible in the captured pricing matrix and is left unresolved."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an authorized Linear user/workspace and properly scoped OAuth/API key; query complexity and hourly request limits apply, while MCP plan entitlement is not explicit in the captured pricing matrix.", "rationale": "The GraphQL API and hosted MCP document direct issue/project workflows. Use read-only access when possible, limit query breadth, confirm target-plan access and require review for write actions; no workspace or account entitlement was tested."},
        "confidence": "MEDIUM",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Linear workspace, account plan, API key, OAuth grant, GraphQL query, MCP call or human review was performed. The pricing page's rendered MCP feature row did not expose a clear plan-column mapping."],
        "researcher_notes": "Do not treat a public GraphQL reference or hosted MCP endpoint as proof that a particular plan includes every feature. Direct documentation confirms the endpoint/auth choices but not the captured plan matrix mapping.",
        "evidence": [
            ("description", "Linear's official developer and MCP docs describe issue/project/cycle workflows for product teams.", "linear_graphql"),
            ("auth", "Linear documents personal API keys and OAuth for API clients; the hosted MCP uses OAuth and accepts API-key/bearer-token headers.", "linear_oauth"),
            ("self_serve", "Linear's pricing page lists Free, Basic, Business and custom Enterprise plans; its rendered MCP feature row does not show a reliable plan mapping.", "linear_pricing"),
            ("credential_access", "Users can create personal API keys and OAuth apps through Linear's documented developer/security settings.", "linear_oauth"),
            ("api", "Linear publishes a GraphQL API endpoint and documents queries/mutations for issues, teams, projects and related objects.", "linear_graphql"),
            ("api", "Linear describes hourly request and query-complexity limits for API-key and OAuth clients.", "linear_rate_limits"),
            ("mcp", "Linear hosts a Streamable HTTP MCP server with interactive OAuth/DCR and direct bearer API-key/OAuth-token options.", "linear_mcp"),
            ("mcp", "The official MCP guide documents default read/write access and read-only endpoint/scope options.", "linear_mcp"),
            ("buildability", "Linear recommends query filtering/avoiding polling and documents user/app API and query-complexity quotas.", "linear_rate_limits"),
        ],
    },
    74: {
        "description": "Jira is Atlassian's project and issue-tracking platform for planning and managing software and business work, with Cloud REST APIs and the Atlassian Rovo MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "API key", "Bearer/token", "Basic"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Jira Cloud offers Free for up to 10 users, Standard ($7.91/user/month), Premium ($14.54/user/month) and custom Enterprise. Rovo MCP tool sets, admin settings and possible Rovo-credit consumption vary; no tenant plan/credit entitlement was checked.",
        "credential_access": {"status": "RESTRICTED", "path": "Use OAuth 2.1 for the hosted Atlassian Rovo MCP; a personal Atlassian API token or service-account API key is an alternative only when the organization administrator enables token authentication. Jira REST apps can use OAuth 2.0 (3LO); user API tokens are managed through Atlassian account settings.", "plan_or_gate": "Cloud account and Jira project/user permissions are required. API-token MCP authentication and sensitive tool groups/scopes can be admin-disabled or require explicit admin setup; API access is not equivalent to Rovo credit entitlement."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Jira Cloud REST APIs include Jira Software and platform v3 resources for issues, projects and related configuration/administration. OAuth 2.0 and API-token authentication are documented; resource access follows Jira permissions."},
        "mcp": {"status": "AVAILABLE", "details": "Atlassian hosts Rovo MCP at https://mcp.atlassian.com/v2/mcp, including Jira read/write tools. OAuth 2.1 is primary; admin-enabled API-token auth is available for some scenarios. Tool availability/scopes are dynamic, user permissions remain in force, some Rovo tools may consume credits, and certain elevated groups are disabled by default.", "search_scope": "Opened Atlassian's Rovo overview, setup, supported-tools, OAuth/token-auth guides, Jira Software and REST v3 API intros, OAuth 3LO/security docs and Jira pricing. This confirms a first-party cloud MCP/API; no Atlassian tenant, Rovo credit balance or Jira project was accessed."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an authorized Jira Cloud user, required OAuth/API token setup and permissions; API-token MCP auth and elevated tools can require admin enablement, and some Rovo tools consume credits.", "rationale": "The Jira REST APIs and hosted Rovo MCP document issue/project read-write workflows. Use least-privilege scopes, confirm workspace linking/admin policy and credit availability, and review mutations; Data Center/on-prem applicability is not asserted."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Jira/Atlassian Cloud account, admin policy, API token, OAuth consent, Rovo credit balance, API request, MCP session or human review was performed. Pricing and Rovo-tool entitlement may vary by tenant/region."],
        "researcher_notes": "Rovo MCP covers Atlassian Cloud; this record does not imply support for Jira Server/Data Center. API-token authentication is conditional on administrator settings and is not conflated with the OAuth flow.",
        "evidence": [
            ("description", "Jira Cloud REST references expose project and issue-tracking operations for Jira Software and the Jira platform.", "jira_rest_software"),
            ("auth", "Atlassian documents OAuth 2.1 for Rovo MCP and admin-enabled personal-token Basic or service-account Bearer alternatives; Jira REST also documents OAuth 2.0 3LO.", "jira_rovo_api_token"),
            ("self_serve", "The Jira pricing page lists a free tier for up to 10 users and paid Standard/Premium plans plus custom Enterprise.", "jira_pricing"),
            ("credential_access", "Rovo MCP API-token authentication must be enabled by an organization admin; OAuth 2.1 is the recommended interactive path.", "jira_rovo_api_token"),
            ("credential_access", "Jira Cloud supports user-consented OAuth 2.0 3LO apps and user API-token authentication for REST use.", "jira_oauth_3lo"),
            ("api", "The official Jira Cloud REST v3 reference catalogs broad project, issue and platform resource operations.", "jira_rest_platform"),
            ("api", "Jira Software Cloud publishes REST operations for project/issue tracking workflows.", "jira_rest_software"),
            ("mcp", "Atlassian publishes a cloud-hosted Rovo MCP endpoint that connects Jira and other Atlassian Cloud apps.", "jira_rovo_overview"),
            ("mcp", "The supported-tools page identifies Jira read/write tools, required scopes, workspace linking and possible Rovo-credit consumption.", "jira_rovo_tools"),
            ("buildability", "The Rovo MCP guide documents admin-controlled token auth, disabled-by-default elevated tool groups and permission-scoped actions.", "jira_rovo_api_token"),
            ("buildability", "Some Rovo tools may consume credits and user permissions/tool availability remain dynamic.", "jira_rovo_tools"),
        ],
    },
    75: {
        "description": "Asana is a work-management platform built around the Asana Work Graph for tasks, projects, portfolios and team coordination, with a REST API and hosted V2 MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Asana offers Personal at $0 (up to 2 users), Starter at $10.99/user/month and Advanced at $24.99/user/month billed annually, plus custom Enterprise. Core V2 MCP is available through OAuth, while some advanced search/tool capabilities depend on plan and workspace app policy.",
        "credential_access": {"status": "RESTRICTED", "path": "Register an MCP app in the Asana developer console, configure redirect/distribution and client credentials, then authorize with OAuth 2.0/PKCE. REST API testing can use a separate PAT/OAuth app; MCP tokens are workspace-scoped and cannot be reused for REST calls.", "plan_or_gate": "Asana V2 MCP does not support dynamic client registration; the MCP app must be pre-registered. Workspace app management may block the client or require an administrator to approve/unblock it; app distribution can be limited to selected workspaces."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Asana's REST API exposes Work Graph resources and workflows including tasks, projects and workspace objects. OAuth and PATs are documented for REST API use; API access remains scoped to the user's role and workspace."},
        "mcp": {"status": "AVAILABLE", "details": "Asana's hosted V2 Streamable HTTP server is https://mcp.asana.com/v2/mcp and uses OAuth with a pre-registered client. Tools search/read/create/update tasks and projects; MCP tokens are workspace-scoped, do not use scopes, and are separate from REST tokens. Some advanced search tools are plan-limited; workspace app management can block clients.", "search_scope": "Opened Asana's V2 tools reference, user/setup guide, coding-client setup, developer integration/OAuth and REST API overview, and current pricing. No Asana workspace, OAuth client, API or MCP session was exercised."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a pre-registered MCP OAuth client, user authorization and an app distribution/workspace policy that allows the client; plan-limited tools and workspace-scoped tokens constrain feature coverage.", "rationale": "The official REST API and generally available V2 MCP expose documented task/project workflows. Register the MCP app, scope it to needed workspaces, verify admin approval and plan-specific tools, and review destructive writes; no tenant or human QA was performed."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Asana account/workspace, plan, developer app, OAuth grant, PAT, API request, MCP session or human review was performed. Tool schemas and plan entitlements can change."],
        "researcher_notes": "Asana V2 MCP tokens are not REST API tokens. Dynamic client registration is not supported; registering a client and the workspace/app-management check are substantive setup gates.",
        "evidence": [
            ("description", "Asana describes its Work Graph and REST API as the primary platform for task/project and workspace work.", "asana_api"),
            ("auth", "Asana standard API supports OAuth and PAT-based testing; its V2 MCP server uses registered-client OAuth and Bearer access tokens.", "asana_mcp_integrate"),
            ("self_serve", "The Asana pricing page lists Personal, Starter, Advanced and Enterprise plans with the captured prices and user limits.", "asana_pricing"),
            ("credential_access", "Asana V2 MCP requires a pre-registered MCP app/client; dynamic client registration is not supported and the token is MCP-specific.", "asana_mcp_integrate"),
            ("credential_access", "Workspace app management can block the MCP client or prompt the user to request administrator unblocking.", "asana_mcp_using"),
            ("api", "Asana publishes a REST API for its Work Graph, including tasks, projects and related workspace resources.", "asana_api"),
            ("mcp", "Asana's official V2 server is hosted at mcp.asana.com/v2/mcp and supports OAuth-authenticated task/project workflows.", "asana_mcp_using"),
            ("mcp", "Asana MCP tokens are workspace-scoped, do not use MCP-specific scopes, and are separate from REST API tokens; some advanced search tools are plan-limited.", "asana_mcp_tools"),
            ("buildability", "Asana's V2 server requires a registered OAuth app and workspace distribution configuration; admin app controls can block access.", "asana_mcp_integrate"),
            ("buildability", "Some tool capabilities depend on plan, and tokens are scoped to one workspace per authorization session.", "asana_mcp_tools"),
        ],
    },
    76: {
        "description": "monday.com is a customizable work platform for project management, CRM, development and service workflows, organized around workspaces, boards, groups, items and typed columns.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "monday.com lists Free ($0, up to 2 seats), Basic ($9/seat/month), Standard ($12), Pro ($19) billed annually, and custom Enterprise. Hosted MCP tool calls count against plan-specific API daily limits (1,000 Free/Basic/Standard; 10,000 Pro; 25,000 Enterprise).",
        "credential_access": {"status": "SELF_SERVE", "path": "Users with API access can reveal/regenerate a personal V2 API token in the Developer Center; apps may register OAuth scopes. The hosted MCP supports OAuth or a bearer personal token for personal/private use.", "plan_or_gate": "User tokens inherit monday.com UI permissions. Public MCP integrations must register through dynamic client registration; private/internal use can use a personal token or app OAuth without public registration. Plan-based API quota applies to MCP calls."},
        "api": {"available": "YES", "types": ["GraphQL", "SDK"], "breadth": "BROAD", "details": "The GraphQL API at https://api.monday.com/v2 supports queries/mutations across workspaces, boards, items, columns, users, docs and other platform objects. An official typed JavaScript/TypeScript SDK is documented; daily, complexity, per-minute and concurrency limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "The hosted Platform MCP at https://mcp.monday.com/mcp exposes 60+ read/write tools across boards/items, columns, workspaces, docs, dashboards, users and GraphQL. It uses OAuth or a bearer personal token, executes as the authenticated user and consumes that account's API quota. Public third-party distribution requires DCR registration. A separate local Apps MCP handles app-development tasks.", "search_scope": "Opened monday.com's official MCP integration/AI/tool docs, GraphQL quickstart, authentication and current OAuth migration guides, rate limits and pricing. No monday account, token, OAuth client, API request, MCP session or tenant entitlement was tested."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a permitted monday.com user/token or OAuth grant, plan quota management and public DCR registration for a distributed integration; some newer MCP tools rely on preview API schema.", "rationale": "The documented GraphQL API, SDK and hosted MCP cover broad board/item/workspace workflows. Use narrow OAuth scopes, respect account permissions and daily limits, and confirm preview-tool stability before production; no account was connected."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No monday.com account, API token, OAuth flow, app registration, GraphQL request, MCP call, usage quota or human review was checked. Some tool schemas use preview APIs and may change."],
        "researcher_notes": "Hosted Platform MCP is distinct from the local Apps MCP. Personal/private testing and public distribution have different registration requirements; the current OAuth docs describe a newer versioned OAuth 2.1 flow alongside a legacy flow.",
        "evidence": [
            ("description", "monday.com describes a customizable AI work platform for project, CRM, development and service use, organized around boards/items/columns.", "monday_mcp_ai"),
            ("auth", "monday.com personal V2 API tokens are bearer credentials; OAuth apps request permission scopes for user access.", "monday_auth"),
            ("self_serve", "The monday.com pricing page lists Free, Basic, Standard, Pro and custom Enterprise plans with current seat prices.", "monday_pricing"),
            ("self_serve", "Plan-specific daily API call quotas apply to platform access; Free/Basic/Standard, Pro and Enterprise have different limits.", "monday_rate_limits"),
            ("credential_access", "Users with API access can self-serve personal API tokens in the Developer Center; publicly distributed MCP clients must use DCR registration.", "monday_auth"),
            ("api", "monday.com exposes a GraphQL API endpoint for queries/mutations and documents an official typed JavaScript/TypeScript SDK.", "monday_graphql"),
            ("mcp", "The hosted Platform MCP provides more than 60 tools for reading/writing boards, items, docs, users, workspaces and GraphQL operations.", "monday_mcp_tools"),
            ("mcp", "MCP calls execute as the authenticated user and consume the monday.com plan's daily API quota.", "monday_rate_limits"),
            ("buildability", "Publicly distributed hosted-MCP integrations require dynamic client registration; all actions remain subject to the user's permissions.", "monday_mcp_integration"),
            ("buildability", "The Platform MCP guide warns that some newer tools use preview API schemas and can change.", "monday_mcp_ai"),
        ],
    },
    77: {
        "description": "ClickUp is a work-management platform for tasks, docs, projects, lists, spaces, comments and time tracking, with a public REST API and official hosted MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "ClickUp lists Free Forever, Unlimited ($7/user/month annually; $10 monthly), Business ($12 annually; $19 monthly) and custom Enterprise. Official docs say MCP is available on all plans, but daily MCP limits vary by plan/add-on and API endpoint availability/rates also vary.",
        "credential_access": {"status": "SELF_SERVE", "path": "Generate a personal API token after signing in under Settings > Apps; use OAuth 2.0 for third-party API apps. ClickUp MCP itself accepts OAuth only (OAuth 2.1/PKCE for compatible custom clients), not a personal API token.", "plan_or_gate": "Personal API token generation requires a ClickUp account; creating OAuth apps requires a Workspace owner/admin. MCP may be configured only by owners/admins in some Team/Enterprise client/workspace contexts; API endpoint access depends on plan."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "ClickUp publishes a public REST API v2 plus selected v3 endpoints and OpenAPI specs. API coverage includes tasks, spaces, folders, lists, users, comments, time tracking and related workspace resources; endpoint access and per-token rate limits vary by plan."},
        "mcp": {"status": "AVAILABLE", "details": "ClickUp's public-beta hosted MCP endpoint is https://mcp.clickup.com/mcp and is documented for all plans. MCP requires OAuth only and provides workspace/task search, read/write task, comment, time-tracking and hierarchy tools; deletion tools are omitted for safety. Daily call-limit tables conflict between two official pages, so no single numeric cap is asserted.", "search_scope": "Opened ClickUp's developer MCP overview/setup/tool reference, Help Center MCP article, API authentication/Getting Started/OpenAPI/rate-limit docs and current pricing. Both official MCP rate-limit tables were opened; their daily figures conflict. No ClickUp workspace, OAuth grant, API call, MCP operation or human review was performed."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "MCP requires OAuth 2.1/PKCE and has plan/add-on-dependent daily caps with conflicting official figures; API endpoint access and per-token limits vary by plan, and MCP intentionally lacks delete tools.", "rationale": "ClickUp's public REST API and hosted OAuth MCP provide extensive task/workspace workflows. Confirm the live plan-specific MCP cap and workspace policy before sizing an agent, respect user permissions, and use the absence of delete tools as a real surface constraint."},
        "confidence": "MEDIUM",
        "research_status": "COMPLETE",
        "source_conflicts": [
            {"field": "mcp", "summary": "The current official developer MCP page lists 50 calls per rolling 24 hours on Free Forever and 300 on Unlimited and above without Everything AI; the official Help Center article lists 100 on Free, 300 Unlimited, 1,000 Business, 2,500 Business Plus and 5,000 Enterprise under its no-add-on table. Both describe plan-dependent rolling daily limits, but Free and higher-tier figures differ.", "source_urls": ["https://developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server", "https://help.clickup.com/hc/en-us/articles/33335772678423-What-is-ClickUp-MCP"], "resolution": "Preserve the discrepancy rather than selecting a number. Treat MCP calls as plan/add-on constrained and confirm the current workspace cap in product/vendor documentation before implementation. The separately documented API per-token rate table does not resolve the conflicting MCP daily table."}
        ],
        "limitations": ["No ClickUp workspace, plan, Everything AI add-on, token, OAuth authorization, API request, MCP call or human review was checked. Official developer and Help Center pages disagree on daily MCP call quotas."],
        "researcher_notes": "Do not confuse ClickUp REST API personal-token auth with MCP auth: the official MCP FAQ supports OAuth only. MCP and API rate limits are separate; no deletion tools are currently exposed through MCP.",
        "evidence": [
            ("description", "ClickUp's official tool catalog covers tasks, docs, comments, time tracking and workspace hierarchies.", "clickup_mcp_tools"),
            ("auth", "ClickUp API uses personal API tokens or OAuth 2.0, while the official MCP setup uses OAuth.", "clickup_api_auth"),
            ("self_serve", "ClickUp's pricing page lists Free Forever, Unlimited, Business and Enterprise tiers with current annual/monthly prices.", "clickup_pricing"),
            ("self_serve", "The official Help Center says ClickUp MCP is available on all plans; daily call caps vary by Workspace plan/add-on.", "clickup_mcp_help"),
            ("credential_access", "Users can generate a personal API token in Settings > Apps; only Workspace owners/admins may create OAuth apps.", "clickup_api_auth"),
            ("credential_access", "The ClickUp MCP setup guide configures the hosted endpoint through OAuth authorization.", "clickup_mcp_setup"),
            ("api", "ClickUp publishes public API v2/v3 OpenAPI specifications and states endpoint access varies by plan.", "clickup_api_spec"),
            ("api", "The official API rate table documents per-token request limits that differ by Workspace plan.", "clickup_api_limits"),
            ("mcp", "ClickUp's hosted public-beta MCP is available on all plans and exposes search/task/workspace workflows using OAuth.", "clickup_mcp_overview"),
            ("mcp", "The MCP tools reference documents task, comment, time-tracking and workspace-hierarchy operations and says permissions follow the user.", "clickup_mcp_tools"),
            ("buildability", "ClickUp omits delete tools as a safety measure and supports plan/add-on-dependent MCP limits.", "clickup_mcp_overview"),
            ("buildability", "MCP call quotas vary by plan/add-on and the two official daily-limit tables conflict.", "clickup_mcp_help"),
        ],
    },
    78: {
        "description": "Coda, now branded Superhuman Docs, is a collaborative document and workflow workspace combining docs, pages, tables, formulas and automations, with a REST API and native MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Superhuman Docs lists Free ($0) with a limited MCP trial, Pro ($12 per Doc Maker/month annually; $15 monthly), Business ($33 annually; $40 monthly) and custom Enterprise. The REST API is free in free and paid workspaces, subject to workspace role; paid plans expand MCP/product features.",
        "credential_access": {"status": "SELF_SERVE", "path": "Generate an API token in account settings. For MCP, create an MCP-restricted PAT with read, write or read/write access, or use OAuth 2 with PKCE; OAuth can be restricted to selected workspaces/folders.", "plan_or_gate": "API and token creation are self-service but data access follows the user's workspace role. Enterprise administrators can disable PAT use; Free MCP is a limited trial and OAuth read/write access must be narrowed by workspace/folder where needed."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "The REST API at https://coda.io/apis/v1 manages folders, docs, pages, permissions, tables, rows, formulas, controls, analytics and related resources. API use is free across free/paid workspaces but role-gated; read/write rate limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "The current official Superhuman Docs MCP endpoint is https://docs.superhuman.com/apis/mcp and supports reading/searching docs, creating documents/tables and modifying rows/content. OAuth 2 with PKCE is recommended; MCP-restricted PATs can be read-only, write-only or read/write. The legacy Coda endpoint https://coda.io/apis/mcp remains supported for now but is planned for deprecation. Free includes a limited MCP trial.", "search_scope": "Opened current Superhuman Docs MCP connection/security guides, account token-settings help, API reference (including authentication, free/paid workspaces and rate limits), product guide and current pricing. These first-party pages confirm a native MCP server; no workspace or connector was used."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a user API token or OAuth connection and access to the target workspace/docs; Free MCP is trial-limited, API operations follow Doc Maker/editor roles, and OAuth defaults to read/write unless narrowed.", "rationale": "The REST API and first-party MCP cover document/table creation, reading and updates. Use MCP-specific least-privilege tokens or limited OAuth folders/workspaces, verify plan/role limits and review destructive writes; no account-specific entitlement was checked."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Superhuman Docs/Coda account, plan, token, OAuth flow, API request, MCP session or human review was performed. The existing Coda MCP endpoint is officially supported for now but slated for eventual deprecation."],
        "researcher_notes": "Current first-party materials confirm a native Superhuman Docs MCP server, resolving the search-only/community lead that suggested Coda lacked one. Preserve the product label Coda from the manifest and note the current Superhuman Docs branding; legacy Coda MCP is being phased out, not absent today." ,
        "evidence": [
            ("description", "The current API reference identifies Superhuman Docs as formerly Coda and lists docs, pages, tables, rows, formulas and controls as product resources.", "coda_api"),
            ("auth", "The REST API uses bearer API tokens, while the official MCP guide supports OAuth 2 with PKCE and MCP-restricted PATs.", "coda_mcp_security"),
            ("self_serve", "The current pricing page lists Free, Pro, Business and Enterprise plans and marks Free MCP as a limited trial.", "coda_pricing"),
            ("self_serve", "The API is available without charge in both free and paid workspaces, subject to user role.", "coda_api"),
            ("credential_access", "Users can create and manage API tokens from signed-in account settings.", "coda_account"),
            ("credential_access", "MCP PATs can be restricted to MCP and scoped read, write or read/write; OAuth access can be limited to selected workspaces/folders.", "coda_mcp_security"),
            ("api", "Superhuman Docs publishes a REST API covering folders, docs, pages, tables, rows, formulas, controls and permissions.", "coda_api"),
            ("mcp", "Superhuman Docs documents its own hosted MCP endpoint and task flows for reading docs, creating tables and updating content.", "coda_mcp_connect"),
            ("mcp", "The product guide describes native MCP-driven document/table creation and data updates; the legacy Coda endpoint remains supported temporarily.", "coda_mcp_guide"),
            ("buildability", "Superhuman Docs recommends least privilege, limited OAuth workspace/folder access and scoped PATs; OAuth is read/write unless constrained by content access.", "coda_mcp_security"),
            ("buildability", "The current pricing page marks MCP on Free as a limited trial and advertises broader MCP use on paid plans.", "coda_pricing"),
        ],
    },
    79: {
        "description": "Smartsheet is a work-management platform for planning and tracking projects, portfolios and processes with collaborative sheets, reports, dashboards and automations, exposed through a REST API and hosted MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Smartsheet offers a no-card 30-day Business trial and paid Pro/Business plans; Enterprise and Advanced Work Management are sales-led. The specific Help Center article says Free is discontinued for new signups, while an April 2026 marketing FAQ says new users can choose a free plan; this official-source conflict is preserved rather than treating a new-user free plan as confirmed.",
        "credential_access": {"status": "GATED", "path": "Generate an API access token in Personal Settings > API Access, or register a Developer Tools OAuth app for user-consented access; configure the regional MCP endpoint and required OAuth scopes/token.", "plan_or_gate": "Current API/MCP developer docs require Business, Enterprise or Advanced Work Management. Trial users cannot generate API tokens. An older Help Center token article lists Business and Enterprise only, omitting Advanced Work Management; verify the target tenant/plan before implementation."},
        "api": {"available": "YES", "types": ["REST", "SDK"], "breadth": "BROAD", "details": "Smartsheet REST API v2 and official SDKs cover sheets, rows, columns, folders, users, reports and other work resources. Current developer docs require Business, Enterprise or Advanced Work Management and accept Bearer tokens or OAuth 2.0; rate and resource limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "Smartsheet operates regional hosted MCP endpoints (US https://mcp.smartsheet.com, EU https://mcp.smartsheet.eu, AU https://mcp.smartsheet.au). The server exposes 30+ tools for discovery, sheets/rows, workflows and plan/portfolio tasks; Business/Enterprise/Advanced Work Management is required, and some tool groups have higher plan/role gates. Clients use OAuth where supported or API-token Bearer auth.", "search_scope": "Opened Smartsheet's official MCP introduction/install/quickstart/tools, REST API intro/getting-started/auth/OAuth, token help, current pricing, free-plan and free-trial help, and 2026 marketing FAQ. Direct official sources conflict on free-plan availability and on whether Advanced Work Management is included in the token/API plan list; both discrepancies are retained."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "API/MCP access is gated to Business/Enterprise/Advanced Work Management in current developer docs; trial users cannot generate API tokens, and the Free-plan and AWM token-eligibility sources conflict.", "rationale": "The documented REST API/SDK and hosted regional MCP support broad sheet/project operations. A Business plan is self-serve, but plan eligibility, admin roles, region, OAuth scopes and tool-specific gates must be verified before build; no account, token, API/MCP operation or human review was performed."},
        "confidence": "MEDIUM",
        "research_status": "COMPLETE",
        "source_conflicts": [
            {"field": "self_serve", "summary": "The specific Help Center Free-plan article says the Free plan was discontinued to new signups on August 28, 2024 and new users receive a trial/paid plans, while Smartsheet's April 20, 2026 marketing FAQ says a free plan is available to new users.", "source_urls": ["https://help.smartsheet.com/articles/2482687-free-plan", "https://www.smartsheet.com/content/smartsheet-faqs", "https://help.smartsheet.com/articles/529590-smartsheet-free-trial-faqs"], "resolution": "Keep the discrepancy visible. The specific Help Center plan article explicitly dates the signup cutoff, and the separate trial FAQ confirms a 30-day no-card trial with paid upgrade; do not tell a new user that an ongoing Free plan is available without current account/vendor confirmation."},
            {"field": "credential_access", "summary": "Current Smartsheet developer API/MCP pages list Business, Enterprise and Advanced Work Management as required, while the Help Center token-generation article lists Business and Enterprise only.", "source_urls": ["https://developers.smartsheet.com/api/smartsheet/introduction", "https://developers.smartsheet.com/api/smartsheet/guides/getting-started", "https://developers.smartsheet.com/ai-mcp/smartsheet/mcp-server", "https://help.smartsheet.com/articles/2482389-generate-API-key"], "resolution": "Preserve both official plan lists. Use the current developer docs' Business/Enterprise/Advanced Work Management requirement for provisional planning, but confirm AWM token generation with the target tenant or Smartsheet before relying on it."}
        ],
        "limitations": ["No Smartsheet account/tenant, plan, trial, token, OAuth app, API call, MCP session, admin policy or human review was checked. Official sources disagree on new-signup Free availability and on Advanced Work Management token/API eligibility."],
        "researcher_notes": "The 2026 marketing FAQ's Free-plan wording conflicts with the specific Help Center notice that new Free signups ended in 2024. Current developer documentation includes AWM in the API/MCP gate, whereas the token Help article does not. Neither discrepancy has been silently normalized.",
        "evidence": [
            ("description", "Smartsheet describes a work-management platform for projects, portfolios and processes using sheets, reports, dashboards and automations.", "smartsheet_marketing_faq"),
            ("auth", "Smartsheet REST requests use Bearer API access tokens; OAuth 2.0 is documented for user-consented integrations and supported MCP clients.", "smartsheet_api_auth"),
            ("self_serve", "The official trial FAQ documents a 30-day Business trial without billing information and says trial users cannot create API tokens.", "smartsheet_trial_faq"),
            ("self_serve", "The 2026 marketing FAQ says Smartsheet offers both a free trial and a free plan to new users.", "smartsheet_marketing_faq"),
            ("self_serve", "The specific Help Center Free-plan article says new signups have not been eligible for the ongoing Free plan since August 28, 2024.", "smartsheet_free_help", "contradicts"),
            ("credential_access", "Current API and MCP developer docs require Business, Enterprise or Advanced Work Management; the trial FAQ prohibits token generation during trial.", "smartsheet_api_intro"),
            ("credential_access", "The older Help Center token-generation article lists Business and Enterprise, a narrower plan list than current developer guides.", "smartsheet_token_help", "context"),
            ("api", "Smartsheet publishes a REST API v2 and official SDKs, with resource endpoints for sheets and other organizational work objects.", "smartsheet_api_intro"),
            ("api", "Current API getting-started material requires a paid Business/Enterprise/Advanced Work Management plan for access tokens.", "smartsheet_api_start"),
            ("mcp", "Smartsheet documents a hosted regional MCP server with 30+ tools and a Business/Enterprise/Advanced Work Management gate.", "smartsheet_mcp_intro"),
            ("mcp", "The install guide supports regional endpoints and OAuth for supported clients or API-token Bearer authentication.", "smartsheet_mcp_install"),
            ("buildability", "Trial accounts cannot generate API tokens, while current developer docs require a Business, Enterprise or Advanced Work Management plan.", "smartsheet_api_start"),
            ("buildability", "MCP tools have per-tool plan and permission requirements, including higher gates for some portfolio/scenario actions.", "smartsheet_mcp_tools"),
        ],
    },
}


def ev(field: str, claim: str, key: str, support: str = "supports") -> dict:
    src = SOURCES[key]
    return {
        "claim": claim,
        "field": field,
        "source_url": src["url"],
        "source_title": src["title"],
        "source_type": src["source_type"],
        "accessed_at": DATE,
        "support": support,
    }


for _record in RECORDS.values():
    _record["evidence"] = [ev(*row) for row in _record["evidence"]]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_batch() -> dict:
    manifest = json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8"))
    raw_path = ROOT / "data/raw/final_full_research.json"
    csv_path = ROOT / "data/raw/final_full_research.csv"
    raw_records = json.loads(raw_path.read_text(encoding="utf-8"))
    base_by_id = {row["app_id"]: row for row in raw_records}
    manifest_by_id = {row["app_id"]: row for row in manifest}
    raw_hashes_before = {"json": file_hash(raw_path), "csv": file_hash(csv_path)}
    output_records: list[dict] = []
    output_traces: list[dict] = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for app_id in IDS:
        if app_id not in base_by_id or app_id not in manifest_by_id:
            raise ValueError(f"app_id={app_id} missing from manifest/raw baseline")
        baseline = base_by_id[app_id]
        if baseline.get("source_mode") != "NOT_RUN" or baseline.get("research_status") != "FAILED":
            raise ValueError(f"app_id={app_id} baseline is no longer the expected NOT_RUN/FAILED row")
        data = copy.deepcopy(RECORDS[app_id])
        record = copy.deepcopy(baseline)
        record.update({key: copy.deepcopy(value) for key, value in data.items() if key != "evidence"})
        record["evidence"] = copy.deepcopy(data["evidence"])
        record.update({
            "source_mode": "LIVE_AGENT",
            "research_tool": TOOL,
            "research_timestamp": now,
            "verification_status": "NOT_CHECKED",
            "research_run_id": RUN_ID,
            "failure_reason": None,
            "quality_gate": {},
        })

        query_rows = [
            {"query": query, "depth": depth, "search_status": "SUCCESS", "lead_only": True,
             "note": "Native search response used for discovery only; search snippets were not claim evidence."}
            for query, depth in QUERIES[app_id]
        ]
        app_sources = [copy.deepcopy(SOURCES[key]) for key in FETCH_COUNTS[app_id]]
        fetch_attempts = []
        for key, chunk_indexes in FETCH_COUNTS[app_id].items():
            src = SOURCES[key]
            for chunk in chunk_indexes:
                fetch_attempts.append({
                    "tool": "fetch_page", "url": src["url"], "chunk_index": chunk,
                    "status": "SUCCESS",
                    "note": "Official page opened directly; the source packet retains the claim-relevant observation.",
                })
        for row in NON_EVIDENCE_FETCHES.get(app_id, []):
            fetch_attempts.append({"tool": "fetch_page", **copy.deepcopy(row)})
        query_attempts = [
            {"tool": "web_search", "query": row["query"], "depth": row["depth"],
             "status": "SUCCESS", "note": "Discovery lead only; not claim evidence."}
            for row in query_rows
        ]
        attempts = query_attempts + fetch_attempts
        record["query_count"] = len(query_rows)
        record["source_count"] = len(app_sources)
        record["attempt_count"] = len(attempts)
        record["trace_limitations"] = [
            "The preliminary Batch06 discovery phase included 26 successful native searches, but the exact earlier query strings/results were not retained in the saved workspace/session summary and are not reconstructed. This artifact records nine exact additional searches executed on 2026-09-24; search snippets are not evidence.",
            "Direct official-page captures for IDs 71-75 were opened earlier on 2026-09-24 and the remaining sources were opened during the current capture. fetch_page exposes date-only retrieval precision, not per-page clock time; redundant navigation captures are not reconstructed.",
            "LIVE_AGENT denotes native web research only. No provider credentials, Composio call, vendor account/tenant check, API request, MCP connection/action, deployment or human review is claimed.",
            "This standalone capture covers IDs 71-79 only and is not merged into the authoritative 100-row raw dataset. Full-population research, sampling, independent verification, human QA, corrected-dataset analysis, HTML regeneration, tests and deployment gates remain unfinished.",
        ]
        urls = {src["url"] for src in app_sources}
        record["quality_gate"] = validate_record_quality(record, source_urls=urls)
        output_records.append(record)
        output_traces.append({
            "app_id": app_id, "app": record["app"], "source_mode": "LIVE_AGENT",
            "status": record["research_status"], "research_run_id": RUN_ID,
            "research_tool": TOOL, "queries": query_rows, "sources": app_sources,
            "attempts": attempts, "trace_limitations": copy.deepcopy(record["trace_limitations"]),
        })

    raw_hashes_after = {"json": file_hash(raw_path), "csv": file_hash(csv_path)}
    if raw_hashes_after != raw_hashes_before:
        raise RuntimeError("authoritative raw JSON/CSV changed while assembling Batch06")
    return {
        "schema_version": "1.0", "run_id": RUN_ID,
        "run_started_at": now, "run_completed_at": now,
        "source_mode": "LIVE_AGENT", "tool": TOOL,
        "provider_credentials": {"TAVILY_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL", "OPENAI_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL"},
        "raw_dataset_hashes_before_and_after": raw_hashes_before,
        "scope": "Apps 71-79 only. Standalone native-web capture; not merged into data/raw/final_full_research.json or CSV and not the completed 100-app dataset.",
        "search_result_policy": "Search snippets are discovery leads only and excluded from claim evidence; evidence cites directly opened first-party pages.",
        "records": output_records, "traces": output_traces,
    }


def main() -> int:
    payload = build_batch()
    manifest = json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8"))
    manifest_by_id = {row["app_id"]: row for row in manifest}
    issues = []
    if [row["app_id"] for row in payload["records"]] != IDS:
        issues.append(("batch", "record IDs/order differ from scope"))
    if len(payload["traces"]) != len(IDS):
        issues.append(("batch", "trace count differs from scope"))
    for record in payload["records"]:
        errors = validate_record(record)
        if errors:
            issues.append((record["app_id"], errors))
        if record["quality_gate"]["status"] != "PASS":
            issues.append((record["app_id"], record["quality_gate"]))
        trace = next((row for row in payload["traces"] if row["app_id"] == record["app_id"]), None)
        if not trace or record["query_count"] != len(trace["queries"]) or record["source_count"] != len(trace["sources"]) or record["attempt_count"] != len(trace["attempts"]):
            issues.append((record["app_id"], "trace count reconciliation failed"))
        identity = manifest_by_id.get(record["app_id"])
        if not identity or (record["app"], record["category"], record["website_hint"]) != (identity["app"], identity["category"], identity["website_hint"]):
            issues.append((record["app_id"], "manifest identity/category/website mismatch"))
    if issues:
        print(json.dumps(issues, indent=2, ensure_ascii=False))
        return 1
    out = ROOT / "data/evidence/native_web_capture_batch06_2026-09-24.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} with {len(payload['records'])} rows and {len(payload['traces'])} traces")
    print("record quality:", {status: sum(r["quality_gate"]["status"] == status for r in payload["records"]) for status in ("PASS", "WARN", "FAIL")})
    for record in payload["records"]:
        print(record["app_id"], record["app"], record["research_status"], record["quality_gate"]["status"], record["query_count"], record["source_count"], record["attempt_count"])
        for warning in record["quality_gate"]["warnings"]:
            print("  WARN:", warning)
    print("raw JSON/CSV hashes unchanged:", payload["raw_dataset_hashes_before_and_after"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

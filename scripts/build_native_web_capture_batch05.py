#!/usr/bin/env python3
"""Assemble the fifth standalone native-web evidence batch.

Scope: manifest IDs 62-70. This builder never edits the authoritative raw
research JSON/CSV. Search results are discovery leads only; claims cite opened
first-party sources. The records are not merged into the 100-app dataset.
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
RUN_ID = "arena-native-web-batch05-20260924"
IDS = list(range(62, 71))
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
    # 62 Vercel
    "vercel_mcp": source(
        "https://vercel.com/docs/agent-resources/vercel-mcp",
        "Use Vercel's MCP server",
        "official_docs",
        "Vercel documents an official remote MCP endpoint at https://mcp.vercel.com with OAuth, public and authenticated tools, account/project access, and Beta availability on all Vercel plans. The opened setup/security sections state only reviewed/approved clients are supported, user consent is required, and an MCP client receives the connected Vercel user's access.",
        (0, 1, 2),
    ),
    "vercel_api": source(
        "https://vercel.com/docs/rest-api",
        "Vercel REST API Reference",
        "official_api_docs",
        "The official REST reference says the API supports HTTP requests/SDKs, Bearer access tokens, team scoping, and endpoints for projects, deployments, domains, environment variables/secrets, logs, analytics and other platform resources.",
        (0,),
    ),
    "vercel_tokens": source(
        "https://vercel.com/docs/rest-api/authentication/create-an-auth-token",
        "Create an Auth Token | Vercel REST API",
        "official_auth_docs",
        "The token endpoint creates a bearer token for an authenticated Vercel user; token creation can scope to a project/team, and the token value is returned only once. Vercel account settings also provide access-token management.",
        (0,),
    ),
    "vercel_pricing": source(
        "https://vercel.com/pricing",
        "Vercel Pricing: Hobby, Pro, and Enterprise plans",
        "official_pricing",
        "The pricing page lists Hobby at $0/month for personal projects, Pro at $20/month, and custom Enterprise plans with additional controls/support. API/MCP research does not infer broader production eligibility from the Hobby label.",
        (0,),
    ),

    # 63 Netlify
    "netlify_mcp_setup": source(
        "https://docs.netlify.com/build/build-with-ai/agent-setup-guides/set-up-claude-code-for-netlify/",
        "Set up Claude Code for Netlify | Netlify Docs",
        "official_docs",
        "Netlify recommends the hosted remote MCP endpoint https://netlify-mcp.netlify.app/mcp. The setup guide says an initial setup can begin without a Netlify account/team, then prompts for login when needed; it also documents local installation and Netlify CLI authentication. The page covers draft, production and temporary anonymous deploy workflows.",
        (0, 1),
    ),
    "netlify_mcp_repo": source(
        "https://github.com/netlify/netlify-mcp",
        "Netlify's Official MCP server",
        "official_github",
        "The first-party netlify/netlify-mcp repository identifies the official server, documents local installation through @netlify/mcp, remote setup via Netlify docs, and personal-access-token fallback for local authentication. It warns not to commit PATs.",
        (0, 8),
    ),
    "netlify_api": source(
        "https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/",
        "Get started with the Netlify API | Netlify Docs",
        "official_api_docs",
        "Netlify documents a versioned REST API at api.netlify.com/api/v1 for site/deploy management, forms, DNS and other resources, with JavaScript and Go clients. Manual use supports bearer PATs; public integrations must use OAuth2. Typical limit is 500 requests/minute, with stricter deploy limits.",
        (0,),
    ),
    "netlify_cli_auth": source(
        "https://docs.netlify.com/api-and-cli-guides/cli-guides/get-started-with-cli/",
        "Get started with Netlify CLI | Netlify Docs",
        "official_auth_docs",
        "Netlify CLI obtains OAuth authorization through browser login or a user-generated PAT in account settings; a PAT can be scoped to SAML team access and assigned an expiration. The CLI supports local build/deploy workflows.",
        (0,),
    ),
    "netlify_pricing": source(
        "https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/",
        "Credit-based pricing plans | Netlify Docs",
        "official_pricing",
        "Current self-serve credit plans are Free ($0, 300 monthly credits with a hard limit), Personal ($9/month, 1,000 credits) and Pro (from $20/month, 3,000+ credits); Enterprise is sales-contact. Features and add-ons vary by plan.",
        (0,),
    ),

    # 64 Cloudflare
    "cloudflare_mcp": source(
        "https://developers.cloudflare.com/agents/model-context-protocol/cloudflare/servers-for-cloudflare/",
        "Cloudflare's own MCP servers · Cloudflare Agents docs",
        "official_docs",
        "Cloudflare documents a catalog of hosted remote MCP servers, including the API server at https://mcp.cloudflare.com/mcp. The API server exposes search/execute Code Mode over 2,500+ Cloudflare API endpoints; interactive access uses OAuth with permission selection, and automation can use scoped bearer API tokens. Product-specific MCP servers cover docs, Workers, builds, observability and other tools.",
        (0,),
    ),
    "cloudflare_api": source(
        "https://developers.cloudflare.com/api/",
        "API Reference | Cloudflare API",
        "official_api_docs",
        "Cloudflare's official API reference catalogs REST endpoints across accounts, zones, DNS, Workers and other platform resources and offers TypeScript, Python and Go clients plus Terraform support.",
        (0,),
    ),
    "cloudflare_tokens": source(
        "https://developers.cloudflare.com/fundamentals/api/get-started/create-token/",
        "Create API token · Cloudflare Fundamentals docs",
        "official_auth_docs",
        "Cloudflare users can create user or account API tokens in the dashboard, select permission groups and resources, optionally set IP/TTL restrictions, and use the secret as a Bearer token. Token templates/custom permissions are available.",
        (0,),
    ),
    "cloudflare_pricing": source(
        "https://www.cloudflare.com/plans/",
        "Pricing | Cloudflare",
        "official_pricing",
        "The plans page lists Free at $0/month, Pro at $20/month billed annually (or $25 monthly), Business at $200/month billed annually (or $250 monthly), and custom Contract plans. Product-specific usage/limits differ; the page also lists free and paid Workers/resource quotas.",
        (0,),
    ),

    # 65 Supabase
    "supabase_mcp": source(
        "https://supabase.com/docs/guides/ai-tools/mcp",
        "Supabase MCP Server | Supabase Docs",
        "official_docs",
        "Supabase operates a hosted MCP server at https://mcp.supabase.com/mcp with browser OAuth/dynamic client registration and optional PAT headers for CI. The server can be project-scoped, read-only, and limited to feature groups; tools include SQL/migrations, logs/advisors, Edge Functions, account management and docs. Branching tools require a paid plan; the docs warn about prompt-injection and write-access risks.",
        (0, 1, 2),
    ),
    "supabase_api": source(
        "https://supabase.com/docs/guides/api",
        "Data REST API | Supabase Docs",
        "official_api_docs",
        "Supabase auto-generates a PostgREST REST API from each Postgres schema for CRUD, relationships, views, functions and RLS-governed access, with a project-specific REST base URL.",
        (0,),
    ),
    "supabase_keys": source(
        "https://supabase.com/docs/guides/getting-started/api-keys",
        "API keys | Supabase Docs",
        "official_auth_docs",
        "Project keys are available in Dashboard/CLI: publishable keys are for public components and rely on RLS, while secret keys are elevated and bypass RLS. Supabase states legacy anon/service_role keys are being deprecated by end of 2026; secrets must remain server-side.",
        (0,),
    ),
    "supabase_pricing": source(
        "https://supabase.com/pricing",
        "Pricing & Fees | Supabase",
        "official_pricing",
        "Current plans list Free at $0/month with unlimited API requests, 500 MB database per project, 5 GB egress and 1 GB storage; free projects pause after one week inactive and are limited to two active projects. Pro starts at $25/month; Team at $599/month; Enterprise is custom.",
        (0,),
    ),

    # 66 Neo4j
    "neo4j_aura_mcp": source(
        "https://neo4j.com/docs/mcp/current/mcp-for-aura/",
        "MCP for Aura - Neo4j MCP",
        "official_docs",
        "Neo4j documents MCP for Aura as a hosted HTTP server with one URL per Aura instance, constructed from or copied using the instance ID. It is available for Free, Professional and Business Critical instances; VDC support was not yet available in the opened doc.",
        (0,),
    ),
    "neo4j_mcp_config": source(
        "https://neo4j.com/docs/mcp/current/client-configuration/",
        "Client configuration - Neo4j MCP",
        "official_docs",
        "The first-party client guide configures Aura MCP over HTTP and local MCP over stdio. Local examples use a database URI, username/password, database name, and optional NEO4J_READ_ONLY setting.",
        (0,),
    ),
    "neo4j_mcp_tools": source(
        "https://neo4j.com/docs/mcp/current/tools/",
        "Tools - Neo4j MCP",
        "official_docs",
        "The Neo4j MCP tool reference lists schema inspection, read-only Cypher, write-Cypher and GDS procedure listing. Read-only mode hides write tools; write tools can alter data, so the docs advise care in production.",
        (0,),
    ),
    "neo4j_security": source(
        "https://neo4j.com/docs/mcp/current/security/",
        "Security - Neo4j MCP",
        "official_docs",
        "Neo4j recommends a restricted database user and reviewing LLM-generated Cypher before execution, especially against production databases.",
        (0,),
    ),
    "neo4j_api": source(
        "https://neo4j.com/docs/query-api/current/",
        "Introduction - Query API",
        "official_api_docs",
        "Neo4j Query API is an HTTP API for executing Cypher statements; it is enabled by default for current Neo4j and Aura versions and supersedes the deprecated HTTP API. Aura uses HTTPS; official drivers are recommended where available.",
        (0,),
    ),
    "neo4j_auth": source(
        "https://neo4j.com/docs/query-api/current/authentication-authorization/",
        "Authorize requests - Query API",
        "official_auth_docs",
        "Query API requests require a valid user's login credentials unless server authentication is disabled. It supports Basic username/password and Bearer tokens generated through a configured SSO provider.",
        (0,),
    ),
    "neo4j_pricing": source(
        "https://neo4j.com/pricing/",
        "Cloud & self-hosted graph database platform pricing | Neo4j",
        "official_pricing",
        "AuraDB Free is $0 with no payment method required; Professional starts at $65/GB/month and Business Critical at $146/GB/month. The page lists the Aura API to provision/manage instances and Query API on Free, with features varying by tier.",
        (0,),
    ),

    # 67 Snowflake
    "snowflake_mcp": source(
        "https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp",
        "Snowflake-managed MCP server | Snowflake Documentation",
        "official_docs",
        "Snowflake's managed MCP server is configured as a database/schema object and can expose Cortex Agents, Analyst, Search, SQL execution and generic tools. Snowflake OAuth is default, External OAuth is optional, and roles/permissions are managed separately for the server and each tool.",
        (0,),
    ),
    "snowflake_sql": source(
        "https://docs.snowflake.com/en/developer-guide/sql-api/intro",
        "Introduction to the SQL API | Snowflake Documentation",
        "official_api_docs",
        "Snowflake SQL API is a REST API to submit SQL, check/cancel statement execution, fetch results and manage database/deployment resources. It supports standard queries and most DDL/DML, subject to documented limitations and account network policies.",
        (0,),
    ),
    "snowflake_auth": source(
        "https://docs.snowflake.com/en/developer-guide/sql-api/authenticating",
        "Authenticating to the server | Snowflake Documentation",
        "official_auth_docs",
        "Snowflake SQL API supports OAuth, key-pair JWT, and workload identity federation; requests use Bearer authorization. Public keys must be assigned to Snowflake users for key-pair auth. MCP defaults to Snowflake OAuth and can use External OAuth.",
        (0,),
    ),
    "snowflake_ai_pricing": source(
        "https://docs.snowflake.com/en/user-guide/snowflake-cortex/pricing",
        "Snowflake AI pricing | Snowflake Documentation",
        "official_pricing",
        "Snowflake distinguishes Platform Credits from AI Credits; AI feature usage is consumption-based, with Cortex Agents, Cortex REST API and Search among metered services. Query/warehouse compute and AI service usage can add separate costs.",
        (0,),
    ),
    "snowflake_trial": source(
        "https://www.snowflake.com/en/snowflake-trial/",
        "Snowflake Trial: Build AI & Apps in Minutes",
        "official_pricing",
        "Snowflake advertises a 30-day AI Data Cloud trial with $400 in credits; a separate Cortex Code CLI trial is advertised. This capture does not infer payment-card requirements.",
        (0,),
    ),

    # 68 MongoDB Atlas
    "mongodb_mcp_overview": source(
        "https://www.mongodb.com/docs/mcp-server/overview/",
        "MongoDB MCP Server Overview - MongoDB MCP Server - MongoDB Docs",
        "official_docs",
        "MongoDB calls its MCP server an official implementation with local and Atlas-managed deployment types. Atlas Managed MCP is hosted by MongoDB, supports Atlas only, and offers user-delegated OAuth via Atlas App Connections plus admin controls, roles, IP restrictions and read-only enforcement for programmatic setups.",
        (0,),
    ),
    "mongodb_mcp_setup": source(
        "https://www.mongodb.com/docs/mcp-server/get-started/?ai-client=claude-code",
        "Get Started with the MongoDB MCP Server - MongoDB MCP Server - MongoDB Docs",
        "official_docs",
        "The setup guide says an organization owner must enable AI Clients for plugin access, then users authorize with Atlas OAuth. Programmatic setup uses Atlas CLI/API to create organization/project MCP configuration, assign roles/IP allowlists and generate one-time client secrets.",
        (0,),
    ),
    "mongodb_admin_api": source(
        "https://www.mongodb.com/docs/atlas/configure-api-access/?interface=atlas-ui&programmatic-access=service-account",
        "Get Started with the Atlas Administration API - Atlas - MongoDB Docs",
        "official_api_docs",
        "Atlas Administration API is REST for management, not cluster data reads/writes. It supports OAuth service-account tokens and API keys using HTTP Digest; organization owners create service accounts/keys, project owners grant project access, and organization-created API keys may require IP access-list entries. Database reads/writes use separate database-user credentials.",
        (0,),
    ),
    "mongodb_pricing": source(
        "https://www.mongodb.com/pricing",
        "Pricing | MongoDB",
        "official_pricing",
        "MongoDB Atlas lists a free-forever $0/hour tier with 512 MB storage, plus Flex and Dedicated usage-priced tiers. Free-tier capabilities/resources are limited; the pricing page does not establish that every MCP tool or feature is available on M0.",
        (0,),
    ),

    # 69 Datadog
    "datadog_mcp": source(
        "https://docs.datadoghq.com/mcp_server/setup.md",
        "Set Up the Datadog MCP Server",
        "official_docs",
        "Datadog documents a hosted, site-specific MCP server with OAuth for ChatGPT, Claude, Claude Code and other clients, selectable product toolsets, and local binary setup. US-FED/US2-FED sites are marked unsupported in the opened guide.",
        (0,),
    ),
    "datadog_llmobs_mcp": source(
        "https://docs.datadoghq.com/llm_observability/build_with_ai/mcp_server.md?tab=remoteauthentication",
        "Agent Observability MCP and Skills",
        "official_docs",
        "The Agent Observability toolset covers LLM traces, spans and experiment results. Its docs use OAuth 2.0 by default with API-key plus application-key headers as a fallback, require permission to the relevant data, and state site-specific endpoint selection; US-FED/US2-FED are unsupported.",
        (0,),
    ),
    "datadog_api": source(
        "https://docs.datadoghq.com/api/latest.md",
        "API Reference",
        "official_api_docs",
        "Datadog exposes an HTTP REST API with JSON/resource-oriented URLs and client libraries. The reference uses DD-API-KEY and, for some endpoints, DD-APPLICATION-KEY; endpoint catalogs span telemetry, configuration and account resources.",
        (0,),
    ),
    "datadog_using_api": source(
        "https://docs.datadoghq.com/api/latest/using-the-api.md",
        "Using the API",
        "official_api_docs",
        "The API guide documents sending/reading metrics, events, logs, traces, synthetic results and integrations; creating dashboards, monitors, SLOs and security signals; and managing users, roles, organizations, keys and usage.",
        (0,),
    ),
    "datadog_credentials": source(
        "https://docs.datadoghq.com/getting_started/access_for_enterprises/credential_management.md",
        "Credential Management",
        "official_auth_docs",
        "Datadog distinguishes org-wide ingestion API keys, user-scoped PATs, service-account SATs, legacy application keys, and RUM tokens. PATs/SATs are preferred for API access; credentials inherit user/service-account permissions and should be scoped/short-lived.",
        (0,),
    ),
    "datadog_keys": source(
        "https://docs.datadoghq.com/account_management/api-app-keys.md",
        "API and Application Keys",
        "official_auth_docs",
        "API keys are organization-specific; application keys plus an API key authorize programmatic API access and inherit the creating user's permissions. Organization/user/service-account permissions govern key creation and scopes; secrets can be one-time-read for new organizations.",
        (0,),
    ),
    "datadog_pricing": source(
        "https://www.datadoghq.com/pricing/",
        "Pricing | Datadog",
        "official_pricing",
        "The opened pricing section includes product-specific free-trial calls and usage/seat/host/credit-based prices (for example AI Credits are a separate metered product). Datadog pricing varies by product and site; this is not a single universal API/MCP price.",
        (3,),
    ),

    # 70 Sentry
    "sentry_mcp": source(
        "https://mcp.sentry.dev/",
        "Sentry MCP",
        "official_product",
        "Sentry's hosted MCP site advertises https://mcp.sentry.dev/mcp and connects the Sentry API to coding agents for issue, trace and debugging context; setup examples initiate an OAuth flow to the Sentry account.",
        (0,),
    ),
    "sentry_api": source(
        "https://docs.sentry.io/api/",
        "API Reference | Sentry Docs",
        "official_api_docs",
        "Sentry's web API is version v0 and supports programmatic management of organization/team resources and data access/export. Public endpoints are generally stable; region-specific API domains may be used.",
        (0,),
    ),
    "sentry_auth": source(
        "https://docs.sentry.io/api/auth/",
        "API Authentication | Sentry Docs",
        "official_auth_docs",
        "Sentry API tokens use Bearer authorization; users can create scoped personal tokens, internal integrations can issue tokens, and third-party apps can use OAuth2 authorization-code/PKCE with org scoping.",
        (0,),
    ),
    "sentry_pricing": source(
        "https://sentry.io/pricing/",
        "Pricing: Free Developer Plan, Pay as You Grow | Sentry",
        "official_pricing",
        "The Developer plan is $0, limited to one user, and includes MCP access. Team is listed at $26/month annually and includes API/third-party integrations; data quotas and paid features vary by plan.",
        (0,),
    ),
}

QUERIES = {
    62: [("Vercel official MCP remote server docs API authentication pricing plan deploy search docs site:vercel.com/docs OR site:vercel.com/pricing", "2")],
    63: [("Netlify official MCP server docs hosted MCP API auth pricing free plan site:docs.netlify.com OR site:netlify.com/pricing", "2")],
    64: [("Cloudflare official MCP server remote docs API token free tier pricing site:developers.cloudflare.com OR site:cloudflare.com/plans", "2")],
    65: [("Supabase official MCP server docs hosted remote API auth free plan pricing site:supabase.com/docs OR site:supabase.com/pricing", "2")],
    66: [
        ("Neo4j official MCP server Aura MCP docs remote API authentication free plan pricing site:neo4j.com/docs OR site:neo4j.com/pricing", "2"),
        ("site:neo4j.com/docs/mcp/current \"HTTP Authentication\" MCP for Aura authentication login OAuth access token", "2"),
        ("site:neo4j.com/docs/query-api/current authentication basic credentials Aura API authentication Neo4j", "2"),
    ],
    67: [
        ("Snowflake official MCP server docs OAuth API auth pricing credits Cortex Analyst MCP site:docs.snowflake.com", "2"),
        ("Snowflake official free trial account 30 days credits no credit card sign up usage consumption pricing site:snowflake.com OR site:docs.snowflake.com", "2"),
        ("site:docs.snowflake.com/en/developer-guide/sql-api authentication OAuth JWT key pair API SQL API auth credentials", "2"),
    ],
    68: [("MongoDB Atlas official MCP server docs remote API authentication free tier pricing site:mongodb.com/docs OR site:mongodb.com/pricing", "2")],
    69: [
        ("Datadog official MCP server docs remote OAuth API key application key plans pricing site:docs.datadoghq.com OR site:datadoghq.com/pricing", "2"),
        ("Datadog official pricing free trial 14 days self serve account API app keys pricing plans site:datadoghq.com OR site:docs.datadoghq.com", "2"),
    ],
    70: [("Sentry official remote MCP docs OAuth API token plans pricing site:docs.sentry.io OR site:sentry.io/pricing", "2")],
}

FETCH_COUNTS = {
    62: {"vercel_mcp": [0, 1, 2], "vercel_api": [0], "vercel_tokens": [0], "vercel_pricing": [0]},
    63: {"netlify_mcp_setup": [0, 1], "netlify_mcp_repo": [0, 8], "netlify_api": [0], "netlify_cli_auth": [0], "netlify_pricing": [0]},
    64: {"cloudflare_mcp": [0], "cloudflare_api": [0], "cloudflare_tokens": [0], "cloudflare_pricing": [0]},
    65: {"supabase_mcp": [0, 1, 2], "supabase_api": [0], "supabase_keys": [0], "supabase_pricing": [0]},
    66: {"neo4j_aura_mcp": [0], "neo4j_mcp_config": [0], "neo4j_mcp_tools": [0], "neo4j_security": [0], "neo4j_api": [0], "neo4j_auth": [0], "neo4j_pricing": [0]},
    67: {"snowflake_mcp": [0], "snowflake_sql": [0], "snowflake_auth": [0], "snowflake_ai_pricing": [0], "snowflake_trial": [0]},
    68: {"mongodb_mcp_overview": [0], "mongodb_mcp_setup": [0], "mongodb_admin_api": [0], "mongodb_pricing": [0]},
    69: {"datadog_mcp": [0], "datadog_llmobs_mcp": [0], "datadog_api": [0], "datadog_using_api": [0], "datadog_credentials": [0], "datadog_keys": [0], "datadog_pricing": [3]},
    70: {"sentry_mcp": [0], "sentry_api": [0], "sentry_auth": [0], "sentry_pricing": [0]},
}

# Relevant incorrect-path/redirect attempts are retained as non-evidence trace rows.
# Navigation-only/redundant HTML captures are not reconstructed as claim sources.
NON_EVIDENCE_FETCHES = {
    62: [
        {"url": "https://vercel.com/docs/rest-api/authentication", "chunk_index": 0, "status": "REDIRECTED_NOT_RELEVANT", "note": "The guessed group URL opened the SSO Token Exchange endpoint rather than the authentication overview; the REST API reference and Create an Auth Token page were opened for the relevant claims."},
    ],
    66: [
        {"url": "https://neo4j.com/docs/mcp/current/http-authentication/", "chunk_index": 0, "status": "HTTP_404", "note": "The guessed HTTP Authentication route returned a 404; the current MCP client/security docs and Query API authentication page were opened instead."},
    ],
    69: [
        {"url": "https://www.datadoghq.com/pricing.md", "chunk_index": 0, "status": "HTTP_404", "note": "The pricing Markdown guess returned a 404; the HTML pricing page was opened and its product section captured directly."},
        {"url": "https://www.datadoghq.com/free-trial/", "chunk_index": 0, "status": "HTTP_404", "note": "The guessed free-trial route returned a 404; the official pricing page's Start Free Trial calls and product pricing were inspected instead."},
        {"url": "https://docs.datadoghq.com/llm_observability/pricing.md", "chunk_index": 0, "status": "HTTP_404", "note": "No such LLM Observability pricing Markdown page was found; no plan price is inferred from this failed path."},
    ],
    70: [
        {"url": "https://docs.sentry.io/product/sentry-mcp.md", "chunk_index": 0, "status": "HTTP_404", "note": "The guessed Markdown route returned a page-not-found response. The official docs page redirected to the Sentry MCP product site, which was opened directly."},
    ],
}

RECORDS = {
    62: {
        "description": "Vercel is a cloud platform for deploying and operating web applications, with projects, deployments, domains, environment variables, logs and analytics managed through its dashboard, CLI, APIs and MCP.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["Bearer/token", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Hobby is listed at $0/month for personal projects; Pro is $20/month and Enterprise is custom. Vercel MCP is in Beta on all plans, but production eligibility, resource limits and team permissions remain plan/account dependent.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create/manage an access token in Vercel account settings; REST requests send Authorization: Bearer <TOKEN>. MCP uses an OAuth consent flow. Tokens can be scoped to a project/team and the bearer value is returned only once when created.", "plan_or_gate": "Requires a Vercel user/account with access to the target personal account or team. MCP clients must be on Vercel's reviewed/approved list; OAuth grants the connected user's account permissions."},
        "api": {"available": "YES", "types": ["REST", "SDK"], "breadth": "BROAD", "details": "Vercel's REST API/SDK covers deployments, projects, domains, environment variables/secrets, logs, analytics, teams, integrations and related platform services. Bearer tokens and team identifiers scope access; endpoint rate limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "Official remote MCP at https://mcp.vercel.com uses OAuth and exposes documentation search, project/deployment management, logs and Web Analytics tools; public and authenticated tools are distinguished. It is a public Beta on all Vercel plans.", "search_scope": "Opened Vercel's official MCP overview/setup/security sections, REST API reference, token endpoint and current plan page. The capture confirms a first-party remote server; no Vercel account was connected or tools executed."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an authorized Vercel user/team and a supported MCP client or a scoped API token; MCP is Beta and an agent can exercise the connected user's project permissions.", "rationale": "The documented REST/SDK and hosted OAuth MCP surfaces are technically usable for project/deployment automation. Use least privilege, approved clients and human confirmation for production changes; Hobby is described for personal projects, and no account-specific entitlement was checked."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Vercel account/team was accessed; token creation, OAuth consent, API requests, deployments, MCP calls, plan checks and human review were not performed. Beta features and user permissions may change."],
        "researcher_notes": "The erroneous REST authentication group URL opened a Vercel SSO-token-exchange page, not the REST access-token guide; the official REST API and Create an Auth Token sources were opened and used instead. No live deployment was attempted.",
        "evidence": [
            ("description", "Vercel's REST API manages web applications through projects, deployments, domains, environment variables/secrets and logs, supporting the cloud deployment-platform classification.", "vercel_api"),
            ("auth", "REST calls use Authorization: Bearer access tokens; the hosted MCP connection uses OAuth.", "vercel_api"),
            ("self_serve", "Hobby is $0/month for personal projects, Pro is $20/month and Enterprise is custom; official MCP Beta is available on all plans.", "vercel_pricing"),
            ("self_serve", "Vercel documents hosted MCP Beta availability on all plans, separately from plan-specific project eligibility.", "vercel_mcp"),
            ("credential_access", "Users create/manage access tokens in account settings; the create-token endpoint can scope the token to a project/team and returns the bearer secret once.", "vercel_tokens"),
            ("api", "The official REST reference lists resource groups including deployments, projects, domains, environment, logs, teams, analytics and integrations; SDK or direct HTTP use is supported.", "vercel_api"),
            ("mcp", "Vercel documents a hosted OAuth endpoint, public/authenticated tools and project, deployment, log, documentation and analytics interactions.", "vercel_mcp"),
            ("buildability", "Vercel restricts its MCP to reviewed clients and warns that the agent receives the user's Vercel access; explicit consent and human confirmation are recommended.", "vercel_mcp"),
        ],
    },
    63: {
        "description": "Netlify is a cloud platform for building, deploying and operating websites/apps, with site, deploy, forms, DNS and related resources available through a REST API, CLI and MCP.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "The current credit plans list Free at $0/month with 300 hard-limited credits, Personal at $9/month and Pro from $20/month; Enterprise is sales-contact. Metered features, team seats and add-ons depend on plan. The hosted MCP prompts for Netlify login when account-backed actions are needed.",
        "credential_access": {"status": "SELF_SERVE", "path": "Authorize Netlify CLI/MCP in a browser or create a PAT under user Applications settings. API requests use Authorization: Bearer <PAT>; public third-party integrations must register/use OAuth2 rather than collecting user PATs.", "plan_or_gate": "Requires a Netlify user/account for account-backed calls; team SSO can require explicit token authorization. PATs can have an expiration and must be kept out of repositories."},
        "api": {"available": "YES", "types": ["REST", "SDK", "CLI"], "breadth": "BROAD", "details": "Netlify REST API v1 manages sites, atomic deploys, forms, DNS and more; official Go/JavaScript clients and the Netlify CLI are also documented. Typical REST limits are 500 requests/minute, while deploy calls have stricter per-minute/day caps."},
        "mcp": {"status": "AVAILABLE", "details": "Netlify operates a remote MCP server at https://netlify-mcp.netlify.app/mcp and publishes an official local @netlify/mcp package. Setup uses Netlify authorization; a PAT is documented as a local troubleshooting fallback. The official repository describes site building, deployment and management workflows.", "search_scope": "Opened Netlify's official remote-MCP setup guide, first-party MCP repository/README, REST API authentication reference, CLI auth instructions and current credit-plan docs. This confirms the official remote and local surfaces; no account was connected or deploy action run."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Netlify account/token/OAuth grant for account-backed actions, respects team SSO and plan credit limits, and API deploy operations are more tightly rate-limited than ordinary requests.", "rationale": "The documented REST/CLI/MCP paths cover site and deployment automation. Use a scoped/expiring credential, keep PATs outside source control, and use draft or temporary anonymous deployment for safe testing; production deployment and account permissions were not checked."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Netlify account/team, SSO policy, API token, deployment, MCP client or billable usage was tested; public MCP setup and API docs do not verify account-specific permissions."],
        "researcher_notes": "A public deployment capability is not equivalent to permission to deploy into a user's site. Anonymous deploys described by the docs are temporary and claimable, not used in this research.",
        "evidence": [
            ("description", "Netlify's REST guide covers site/app deploys, form submissions, DNS and other resources; its MCP/CLI setup describes building and deploying sites.", "netlify_api"),
            ("auth", "Netlify API uses OAuth2; manually created PATs are sent as Bearer tokens, while public integrations must implement OAuth2.", "netlify_api"),
            ("self_serve", "The official credit-plan docs list Free at $0/month with 300 monthly credits, Personal at $9/month and Pro from $20/month; Enterprise requires contacting Sales.", "netlify_pricing"),
            ("credential_access", "Netlify CLI login authorizes through a browser, and the user settings page allows creating an expiring PAT for scripts and CLI use.", "netlify_cli_auth"),
            ("api", "The API guide documents REST v1, site/deploy/forms/DNS use cases, official Go/JavaScript clients and API rate limits.", "netlify_api"),
            ("mcp", "Netlify's first-party docs publish a hosted remote MCP endpoint and the official repository documents @netlify/mcp plus a PAT fallback.", "netlify_mcp_setup"),
            ("mcp", "The first-party repository identifies the package as Netlify's official MCP server and warns against committing PATs.", "netlify_mcp_repo"),
            ("buildability", "The official setup guide separates draft, production and short-lived anonymous deploys and requires login when account-backed actions are needed.", "netlify_mcp_setup"),
        ],
    },
    64: {
        "description": "Cloudflare is a cloud connectivity, security and developer platform spanning DNS, CDN, Workers, storage, Zero Trust, analytics and related services.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["API key", "Bearer/token", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Cloudflare lists a $0 Free plan and self-serve Pro/Business subscriptions; a custom Contract tier is also available. Product-specific quotas, account/zone eligibility and paid add-ons differ, so a Free account does not imply access to every API endpoint or MCP tool.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create a user or account API token from the Cloudflare dashboard, choose a permission template or custom scopes/resources, then send it as an Authorization: Bearer token. Interactive remote MCP uses Cloudflare OAuth and lets the user select permissions.", "plan_or_gate": "Token creation is dashboard/account-bound and grants only selected account/zone resources. Some API services and product MCP servers have separate plan or usage quotas."},
        "api": {"available": "YES", "types": ["REST", "SDK"], "breadth": "BROAD", "details": "Cloudflare exposes a large REST API across accounts, zones, DNS, Workers, R2, security and other products; the API reference provides TypeScript, Python and Go clients and Terraform support. Endpoint permissions and product entitlements vary."},
        "mcp": {"status": "AVAILABLE", "details": "Cloudflare runs a hosted remote MCP catalog. The API MCP endpoint uses two Code Mode tools (search/execute) across 2,500+ API endpoints; additional product MCP servers cover docs, Workers bindings/builds, observability and more. OAuth is interactive; scoped bearer API tokens are documented for automation.", "search_scope": "Opened Cloudflare's first-party managed MCP catalog, REST API reference, API-token guide and plan page. The official docs distinguish managed remotes and scoped token access; no account, token or MCP server was exercised."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "A Cloudflare account/token or OAuth grant is needed for account operations; wide API access is permission-scoped and some services are separately metered or unavailable on Free.", "rationale": "The REST API, official SDKs and hosted MCP provide broad integration paths. Limit tokens to the required account/zone, validate which endpoints are enabled on the target plan, and require review before agents apply security, DNS or deployment changes."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Cloudflare account, zone, token, API request, MCP authorization or billable service was checked. The API catalog count and available tools are vendor-documented, not independently enumerated or run."],
        "researcher_notes": "The documentation's API catalog is broad, but specific endpoint access and service pricing remain account/plan/permission dependent.",
        "evidence": [
            ("description", "Cloudflare's API/MCP catalog spans DNS, Workers, R2, Zero Trust and other platform products, supporting a broad developer/security platform description.", "cloudflare_mcp"),
            ("auth", "Cloudflare's remote API MCP uses OAuth, while API tokens are passed in a Bearer Authorization header.", "cloudflare_mcp"),
            ("self_serve", "Cloudflare's official plans page lists Free at $0, Pro and Business self-serve subscriptions, and a custom Contract plan.", "cloudflare_pricing"),
            ("credential_access", "The dashboard token flow lets an account user create user/account tokens, select permissions/resources, set optional IP/TTL restrictions and copy the generated secret.", "cloudflare_tokens"),
            ("api", "The first-party API reference catalogs REST operations and official TypeScript, Python and Go clients plus Terraform support.", "cloudflare_api"),
            ("mcp", "Cloudflare documents a managed remote MCP catalog and OAuth flow, with product-specific endpoints for docs, Workers, builds and observability.", "cloudflare_mcp"),
            ("buildability", "Cloudflare token templates/custom scopes can limit resource permissions, while the plan page lists product-specific free and paid quotas.", "cloudflare_tokens"),
        ],
    },
    65: {
        "description": "Supabase is a managed Postgres application platform with an auto-generated REST Data API and services for authentication, storage, edge functions, realtime and database operations.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["API key", "Bearer/token", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Supabase offers a $0 Free plan with unlimited API requests, 500 MB database per project, 5 GB egress and 1 GB storage; Free is limited to two active projects and pauses projects after one inactive week. Pro starts at $25/month and Team at $599/month; project quotas and add-ons vary by plan.",
        "credential_access": {"status": "SELF_SERVE", "path": "Retrieve a project's publishable or secret API key in Dashboard/CLI; public components use publishable keys under RLS, while secret keys are server-only and bypass RLS. Hosted MCP uses browser OAuth/dynamic registration; CI can use a scoped PAT header.", "plan_or_gate": "Requires a Supabase user/project. Account tools operate with developer permissions; scope MCP to a project, enable read-only mode and restrict tool groups. Branching MCP features require a paid plan."},
        "api": {"available": "YES", "types": ["REST", "SDK"], "breadth": "BROAD", "details": "Supabase auto-generates a PostgREST REST Data API from Postgres schemas for CRUD, relationships, views and functions, secured through API keys and RLS. Projects also expose service APIs; the available schema and enabled products depend on the project."},
        "mcp": {"status": "AVAILABLE", "details": "Supabase hosts https://mcp.supabase.com/mcp with OAuth/dynamic client registration and project-scoping, read-only and feature-group options. Tools span database/SQL/migrations, logs/advisors, Edge Functions, account management and docs; branching is experimental/paid and storage is disabled by default.", "search_scope": "Opened the current Supabase hosted MCP guide including setup, tools, authentication and security sections, the Data REST API, key guide and pricing page. The remote server is first-party; no user account or project was connected and no query/tool was executed."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "MCP may execute SQL/migrations and other account actions under the connected developer's permissions; production use needs explicit project scope, read-only/tool restrictions, RLS/role review and plan/usage checks.", "rationale": "The hosted MCP and schema-generated REST API are directly documented and can support application/database integrations. Supabase explicitly warns about prompt injection and recommends project scoping, read-only mode, limited feature groups and manual approval for interactive work."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No organization, project, database schema, API key, OAuth grant or billing account was inspected. No SQL/API/MCP operation or human security review was performed; exact RLS and project entitlements remain unknown."],
        "researcher_notes": "Publishable keys are not user identity and do not replace RLS; secret keys bypass RLS and must remain server-side. MCP authentication and Data API key authentication are distinct surfaces.",
        "evidence": [
            ("description", "Supabase's docs describe a Postgres-backed platform with a schema-generated Data REST API; the MCP guide lists database, Auth-related account, storage and Edge Function tool groups.", "supabase_api"),
            ("auth", "Data API calls use project API keys; hosted MCP uses OAuth and can use a Bearer PAT for CI.", "supabase_mcp"),
            ("auth", "Supabase distinguishes publishable project keys from elevated secret keys and legacy anon/service_role keys.", "supabase_keys"),
            ("self_serve", "The pricing page lists the free quota/limits and paid Pro/Team plans; project quotas and add-ons vary by plan.", "supabase_pricing"),
            ("credential_access", "Project keys are retrieved from the dashboard/CLI; publishable keys rely on RLS and secret keys bypass RLS and must remain server-side.", "supabase_keys"),
            ("api", "The Data API is auto-generated REST over Postgres and supports CRUD, nested relationships, views, functions, grants and RLS.", "supabase_api"),
            ("mcp", "Supabase documents a hosted endpoint, browser OAuth/dynamic registration, project scope/read-only controls and first-party database/account tool groups.", "supabase_mcp"),
            ("buildability", "Supabase recommends project-scoping, read-only mode and restricted feature groups to mitigate prompt-injection and production-data risks.", "supabase_mcp"),
        ],
    },
    66: {
        "description": "Neo4j is a graph database platform with managed Aura cloud instances and self-managed deployments, queried with Cypher through drivers and an HTTP Query API.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["Basic", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "AuraDB Free is $0 and requires no payment method; Professional starts at $65/GB/month and Business Critical at $146/GB/month. Aura MCP is documented for Free, Professional and Business Critical instances; VDC was not supported in the opened MCP page.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create an Aura instance/user in Neo4j Console and use valid database login credentials for Query API/local MCP. Query API supports Basic user/password and Bearer tokens generated through configured SSO; hosted Aura MCP uses a per-instance endpoint.", "plan_or_gate": "A running Aura/self-managed instance and a user with appropriate database permissions are required. Aura Free is suitable for limited learning/prototyping; account-specific roles, plan limits and hosted MCP authentication details were not tested."},
        "api": {"available": "YES", "types": ["REST", "SDK"], "breadth": "MODERATE", "details": "The HTTP Query API executes Cypher against databases and is enabled by default on current Neo4j/Aura. Official drivers are recommended when available; the older HTTP API is deprecated. Aura API/instance-management capabilities and Query API entitlements vary by tier."},
        "mcp": {"status": "AVAILABLE", "details": "Neo4j offers hosted MCP for Aura at a unique HTTP URL per Aura instance and a local stdio MCP server. Tools include schema inspection, read-only Cypher, optional write-Cypher and GDS procedure listing; read-only mode hides write tools. Hosted Aura MCP authentication flow was not resolved in this capture.", "search_scope": "Opened Neo4j Aura MCP, client configuration, tool and security docs, Query API/auth docs and pricing. A guessed HTTP-authentication page returned 404; no credentials were inferred from the separate API docs, no instance was connected, and MCP auth remains unverified here."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an Aura or self-managed database, user credentials/permissions and careful query controls; write-Cypher can change or delete production data, and hosted MCP auth details were not confirmed.", "rationale": "The REST Query API, official drivers and hosted/local MCP are documented. Use a restricted user, enable read-only mode and review generated Cypher before production execution; Free/paid tier limits and VDC support differ."},
        "confidence": "MEDIUM",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Aura instance, database user, Query API request or MCP connection was used. The guessed HTTP-authentication route returned 404; authentication claims describe the Query API/local database path and do not establish hosted Aura MCP's auth flow."],
        "researcher_notes": "Do not conflate Aura's MCP URL with its connection or Query API URL. The documented API login mechanisms are not assumed to be the hosted MCP authorization scheme.",
        "evidence": [
            ("description", "Neo4j's Query API executes Cypher against graph databases, while Aura is Neo4j's managed cloud service.", "neo4j_api"),
            ("auth", "Query API requests require valid user credentials and support Basic authentication or Bearer tokens when SSO is configured.", "neo4j_auth"),
            ("self_serve", "AuraDB pricing lists a no-payment-method Free tier, paid Professional/Business Critical tiers and the feature matrix for Query API/Aura tools.", "neo4j_pricing"),
            ("credential_access", "Local MCP examples require a Neo4j URI, database username/password and database name; API access uses a valid database user's credentials.", "neo4j_mcp_config"),
            ("api", "Neo4j documents an HTTP Query API for Cypher, enabled by default in current versions/Aura and distinct from the deprecated HTTP API.", "neo4j_api"),
            ("mcp", "Neo4j documents an HTTP hosted MCP endpoint per Aura instance and availability on Free, Professional and Business Critical tiers.", "neo4j_aura_mcp"),
            ("mcp", "The official MCP tool reference lists schema/read/write Cypher and GDS tools; read-only mode removes write tools.", "neo4j_mcp_tools"),
            ("buildability", "Neo4j advises using a restricted user and reviewing LLM-generated Cypher; local MCP supports a read-only mode.", "neo4j_security"),
        ],
    },
    67: {
        "description": "Snowflake is a managed cloud data and AI platform with SQL access, data storage/compute, Cortex AI services and governed database roles.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "Bearer/token", "Custom"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Snowflake advertises a 30-day trial with $400 in Snowflake credits; AI and platform services are consumption-metered and may incur separate costs. This capture does not infer card requirements or a universally free production plan.",
        "credential_access": {"status": "RESTRICTED", "path": "Create/connect a Snowflake account, user and role; SQL API accepts OAuth Bearer tokens or key-pair JWTs. For the managed MCP server, create the database/schema MCP object and grant least-privilege role/tool permissions; Snowflake OAuth is default, External OAuth is optional.", "plan_or_gate": "Requires a Snowflake account plus database/schema and role privileges. Cortex AI/warehouse use consumes credits; tool access must be granted separately and account/network policies apply."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "The Snowflake SQL REST API submits SQL, polls/cancels statements, fetches results and supports most DDL/DML and deployment management. Cortex REST/API services add AI operations; supported statement types, network policies and usage charges apply."},
        "mcp": {"status": "AVAILABLE", "details": "Snowflake-managed MCP is a server object inside a database/schema and exposes Cortex Agents, Analyst, Search, SQL execution and generic tools. It uses Snowflake OAuth by default or External OAuth, with RBAC and separate per-tool grants; it removes the need to deploy separate MCP infrastructure.", "search_scope": "Opened Snowflake managed-MCP, SQL REST API, SQL API authentication, Cortex AI pricing and official trial pages. The capture confirms first-party managed server and token/auth options; no Snowflake account, SQL, role grant or MCP client was used."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an account, schema-level MCP object, least-privilege grants and available platform/AI credits; a broad SQL tool can execute data-changing statements if the role permits them.", "rationale": "The REST SQL API and Snowflake-managed MCP/Cortex tools provide buildable integration paths. Restrict allowed roles/tools, review SQL, account for AI and warehouse consumption, and verify regional/network controls before production."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Snowflake trial/account, role, OAuth client, SQL API request or MCP server object was created or tested. No account-specific Cortex/warehouse entitlement, region or credit balance was checked."],
        "researcher_notes": "The Snowflake MCP server is a database/schema object; it is not a globally shared vendor endpoint. Distinguish AI Credits from ordinary Platform Credits and compute charges.",
        "evidence": [
            ("description", "The SQL API supports queries and deployment/resource management, while Snowflake's Cortex pricing docs list AI services and data-platform compute.", "snowflake_sql"),
            ("auth", "SQL API requests accept OAuth Bearer tokens or key-pair JWTs; managed MCP defaults to Snowflake OAuth with optional External OAuth.", "snowflake_auth"),
            ("self_serve", "Snowflake's official trial page advertises 30 days and $400 in Snowflake credits; usage pricing is consumption-based.", "snowflake_trial"),
            ("credential_access", "Snowflake requires account users/roles; MCP tools need separate grants, and least-privilege OAuth/roles are recommended.", "snowflake_mcp"),
            ("api", "The SQL API is a REST interface for statements, execution status, cancellation and results, with most DDL/DML supported.", "snowflake_sql"),
            ("mcp", "The managed MCP guide documents an in-account server object, supported Cortex/SQL tool types, OAuth and role/tool governance.", "snowflake_mcp"),
            ("buildability", "Snowflake pricing separates AI Credits from Platform Credits and states that warehouse/data services continue to consume platform usage.", "snowflake_ai_pricing"),
            ("buildability", "The MCP guide recommends least privilege, separate tool grants, OAuth and safeguards against recursive or unbounded agent loops.", "snowflake_mcp"),
        ],
    },
    68: {
        "description": "MongoDB Atlas is MongoDB's managed cloud document-database service, with separate administration APIs and database-level access for cluster data.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["OAuth 2.0", "API key"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Atlas lists a free-forever $0/hour tier with 512 MB storage plus Flex and Dedicated usage-priced tiers. MCP/API access depends on Atlas organization/project settings, role and database tier; the free price listing does not prove every managed MCP tool is available on M0.",
        "credential_access": {"status": "RESTRICTED", "path": "Atlas Administration API supports OAuth service-account access tokens or API keys (HTTP Digest); create service accounts/organization keys as an Organization Owner and grant project access with the appropriate owner role. Atlas Managed MCP plugin uses delegated OAuth/App Connections; programmatic MCP setup creates a config client ID/secret.", "plan_or_gate": "An Atlas organization/project is required. Organization owner enables AI Clients for plugin use; API keys/service accounts require owner privileges and may require an IP access-list entry. Database reads/writes use separate database-user credentials."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "The Atlas Administration REST API manages Atlas organizations/projects/clusters and credentials, but does not read/write data stored in clusters. Database data-plane access requires separate database-user credentials; do not treat the admin API as a general document-query API."},
        "mcp": {"status": "AVAILABLE", "details": "MongoDB provides an official Atlas Managed MCP server hosted by MongoDB and a self-managed local MCP implementation. Atlas plugin access uses user-delegated OAuth/App Connections; programmatic configurations use service-account OAuth credentials, roles/IP access lists and optional read-only enforcement. Tools cover cluster/database operations and performance context.", "search_scope": "Opened MongoDB MCP overview and setup docs, Atlas Administration API access guide and current pricing. This verifies first-party managed/local MCP paths and the control-plane/data-plane distinction; no Atlas account, cluster, IP list or MCP session was checked."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Atlas organization/project permissions and AI-client opt-in are required; admin REST credentials do not access cluster data, and managed MCP role/IP/read-only settings must be reviewed.", "rationale": "The official managed MCP and REST administration API can support Atlas automation; database reads/writes require separate database credentials. Use least privilege, read-only mode where possible and verify tier/tool support before touching production data."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [],
        "limitations": ["No Atlas org/project, AI-client opt-in, service account, IP access list, database user, cluster or MCP client was accessed. No specific Atlas tier's complete MCP tool compatibility was verified."],
        "researcher_notes": "Atlas Administration API is a control-plane REST API, not a database query API. OAuth delegated App Connections and programmatic service-account credentials are different MCP setup modes.",
        "evidence": [
            ("description", "MongoDB documents Atlas as a managed database deployment and distinguishes it from local/self-managed MongoDB deployments.", "mongodb_mcp_overview"),
            ("auth", "Atlas Administration API uses OAuth service-account tokens or API keys with HTTP Digest; managed MCP plugin setup uses an OAuth flow.", "mongodb_admin_api"),
            ("self_serve", "MongoDB's official Atlas pricing page lists a free-forever $0/hour tier with 512 MB storage and paid Flex/Dedicated tiers.", "mongodb_pricing"),
            ("credential_access", "Only an Organization Owner can create organization service accounts/API keys; Project Owner grants project access and API use can be IP-list restricted.", "mongodb_admin_api"),
            ("credential_access", "An organization owner must enable AI Clients for the Atlas MCP plugin, and programmatic setup creates configuration credentials/roles/IP rules.", "mongodb_mcp_setup"),
            ("api", "The Atlas Administration API is REST for administrative resources and explicitly does not provide cluster data access; database users are separate.", "mongodb_admin_api"),
            ("mcp", "MongoDB documents an official Atlas-managed MCP server and local server, with Atlas App Connections/OAuth and programmatic configuration options.", "mongodb_mcp_overview"),
            ("buildability", "The managed MCP overview documents project-level access controls and read-only enforcement; setup requires organization opt-in and role/IP configuration.", "mongodb_mcp_setup"),
        ],
    },
    69: {
        "description": "Datadog is a cloud observability and security platform with telemetry collection, dashboards, monitors, logs, traces, synthetic tests, integrations and account-management APIs.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["API key", "Bearer/token", "OAuth 2.0", "Service account"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Datadog's pricing is product-specific and usage/seat/host/credit-metered; the opened pricing page includes trial CTAs and separate product prices. Datadog MCP additionally depends on account permissions, selected regional site and product/toolset availability; no single universal API/MCP fee was inferred.",
        "credential_access": {"status": "RESTRICTED", "path": "Create organization API keys for telemetry intake, and user/service-account PATs or SATs for API access; legacy application keys plus API keys are still documented for some endpoints/MCP fallback. Credentials inherit creator permissions and can be scoped.", "plan_or_gate": "Requires a Datadog organization/user or service account with relevant product permissions. MCP endpoints are site-specific; some toolsets/sites are unsupported. Prefer short-lived scoped PAT/SAT and least-privilege service accounts."},
        "api": {"available": "YES", "types": ["REST", "SDK"], "breadth": "BROAD", "details": "The HTTP REST API and official clients cover telemetry submission/query, integrations, dashboards, monitors, logs, events, traces, synthetic tests, users, roles, organization settings, keys and usage. Some operations require both an API key and application key or other scoped credentials."},
        "mcp": {"status": "AVAILABLE", "details": "Datadog runs a hosted, site-specific remote MCP server with OAuth and product toolsets; the Agent Observability toolset searches/analyzes LLM traces, spans and experiments. API key plus application key headers are a documented fallback for that toolset; US-FED and US2-FED are unsupported in the opened docs.", "search_scope": "Opened current Datadog MCP setup and Agent Observability pages, API reference/usage guide, credential-management and key docs, and product pricing. The capture is bounded to public docs; no site/org was selected, OAuth completed, account entitlement checked or MCP/API tool run."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Datadog org/site, endpoint-specific product permissions and appropriately scoped credentials; available MCP toolsets and commercial plans vary by site/product.", "rationale": "Datadog's REST API/client libraries and hosted OAuth MCP are documented for broad telemetry/account workflows. Use short-lived service access tokens and least privilege, confirm regional endpoint/toolset support, and avoid sending sensitive telemetry to unapproved agents."},
        "confidence": "MEDIUM",
        "research_status": "COMPLETE",
        "source_conflicts": [
            {"field": "auth", "summary": "The general API reference documents API-key and application-key headers for common API calls, while current credential guidance prefers short-lived PAT/SAT and calls application keys legacy; Agent Observability MCP uses OAuth by default with API/app-key fallback.", "source_urls": ["https://docs.datadoghq.com/api/latest.md", "https://docs.datadoghq.com/getting_started/access_for_enterprises/credential_management.md", "https://docs.datadoghq.com/llm_observability/build_with_ai/mcp_server.md?tab=remoteauthentication"], "resolution": "Treat credentials as endpoint/product specific, not mutually interchangeable. Follow each endpoint's current auth guide and use scoped PAT/SAT where supported; retain API keys for ingestion and avoid assuming a legacy application key is the preferred new pattern."}
        ],
        "limitations": ["No Datadog organization/site, pricing account, trial, key, user permission or product entitlement was checked. No API request, MCP login or human review was performed; legacy-versus-current credential guidance may vary by endpoint."],
        "researcher_notes": "Datadog API keys are for telemetry ingestion; read/configuration APIs use user/service-account credentials and sometimes legacy application keys. Do not generalize Agent Observability MCP availability to unsupported government sites or every product plan.",
        "evidence": [
            ("description", "Datadog's HTTP API guide covers telemetry, dashboards, monitors, logs, SLOs, integrations and account resources.", "datadog_using_api"),
            ("auth", "The API reference documents DD-API-KEY and, for some endpoints, DD-APPLICATION-KEY headers; newer guidance distinguishes PAT/SAT and legacy app keys.", "datadog_api"),
            ("auth", "Datadog recommends PATs for interactive API use and SATs for automation, with app keys treated as legacy; hosted MCP uses OAuth by default.", "datadog_credentials"),
            ("self_serve", "The official product-pricing page displays self-serve trial CTAs and metered, product-specific prices, including separate AI credits.", "datadog_pricing"),
            ("credential_access", "Datadog keys are organization/user/service-account scoped; application keys inherit creator permissions and require permissions to create/scope.", "datadog_keys"),
            ("api", "Datadog documents an HTTP REST API and official client libraries; API endpoints cover platform, telemetry and account administration.", "datadog_api"),
            ("api", "The API guide lists integrations, metrics, events, synthetic tests, traces, dashboards, monitors, logs, security signals, users, roles and usage endpoints.", "datadog_using_api"),
            ("mcp", "Datadog publishes a hosted site-specific MCP server using OAuth and selectable product toolsets, with unsupported sites clearly identified.", "datadog_mcp"),
            ("mcp", "The Agent Observability MCP guide documents LLM trace/span/experiment tools and an API-key/application-key fallback.", "datadog_llmobs_mcp"),
            ("buildability", "Current credential guidance recommends short-lived scoped tokens/service accounts, while MCP requires account permission and a supported Datadog site.", "datadog_credentials"),
        ],
    },
    70: {
        "description": "Sentry is a developer observability platform for application errors, performance traces, releases and debugging, with a web API and an agent-facing MCP server.",
        "auth_status": "CONFIRMED",
        "auth_methods": ["Bearer/token", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "The $0 Developer plan is limited to one user and includes MCP access; Team is listed at $26/month annually and adds API/third-party integrations. Data quotas, roles and paid product features vary, so API entitlement on Developer was not inferred from public documentation alone.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create scoped personal tokens in User Settings or an internal integration; third-party applications can use OAuth2 authorization-code/PKCE. The hosted Sentry MCP server prompts an OAuth flow and can be scoped to an organization or project endpoint.", "plan_or_gate": "Requires a Sentry user and access to the selected organization/project. The Developer plan has one user and quotas; pricing identifies API/third-party integrations as a Team feature, so confirm the target API plan entitlement."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "Sentry's web API v0 manages organization/team resources and reads/exports data, with regional domains and endpoint-specific scopes/permissions. Public endpoints are generally stable; beta endpoints can change."},
        "mcp": {"status": "AVAILABLE", "details": "Sentry hosts a remote MCP endpoint at https://mcp.sentry.dev/mcp with OAuth. The server provides issue, trace/performance, documentation and debugging context; optional organization/project-scoped endpoint paths are documented, and MCP access is included on the Developer plan.", "search_scope": "Opened Sentry's official MCP product site, API reference/authentication pages and pricing. The docs page redirected to the product site; no Sentry org, OAuth grant, API request, MCP call or account plan was inspected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an authorized Sentry organization/project and OAuth or scoped token; Developer plan limits users/quotas and the pricing page lists API/third-party integrations as a Team feature.", "rationale": "The public REST v0 API and hosted OAuth MCP are documented and suitable for issue/trace debugging workflows. Confirm API plan/endpoint access, use narrow scopes/project scoping, and protect telemetry/error data; no account-specific access was tested."},
        "confidence": "HIGH",
        "research_status": "COMPLETE",
        "source_conflicts": [
            {"field": "self_serve", "summary": "Sentry's public API reference documents a web API, while current pricing lists API and third-party integrations as a Team-plan feature; the separate hosted MCP is explicitly included on the one-user Developer plan.", "source_urls": ["https://docs.sentry.io/api/", "https://sentry.io/pricing/", "https://mcp.sentry.dev/"], "resolution": "Keep API plan entitlement distinct from MCP availability. Do not infer that every REST endpoint/integration is included on the free Developer plan; verify the specific organization and endpoint before implementation."}
        ],
        "limitations": ["No Sentry organization/project, API token, OAuth flow, MCP client, event quota or plan entitlement was checked. No error/trace data was read and no human review was performed."],
        "researcher_notes": "Public API documentation does not itself prove free-plan access. Pricing explicitly lists MCP access on Developer and API/third-party integrations on Team; keep those product surfaces separate.",
        "evidence": [
            ("description", "Sentry's API documentation exposes organization/team management and data export, while its MCP site centers on issue, trace and debugging context.", "sentry_api"),
            ("auth", "Sentry API requests use Bearer tokens; OAuth2 authorization-code/PKCE is available for third-party apps and the hosted MCP setup uses OAuth.", "sentry_auth"),
            ("self_serve", "Sentry's pricing page lists a $0 one-user Developer plan with MCP access and paid Team/Business plans with different feature quotas.", "sentry_pricing"),
            ("credential_access", "Users can create scoped tokens in User Settings and third-party apps can request scoped OAuth authorization; organization scoping is applied.", "sentry_auth"),
            ("api", "Sentry documents a versioned v0 web API for organization/team resources and data access/export, with regional API domains.", "sentry_api"),
            ("mcp", "Sentry's product site publishes a hosted remote MCP URL and OAuth setup for coding agents; pricing separately confirms MCP is on Developer.", "sentry_mcp"),
            ("mcp", "The current pricing page lists MCP access on the Free Developer plan, distinct from the Team API/integrations feature listing.", "sentry_pricing"),
            ("buildability", "Sentry pricing makes API/third-party integration a Team feature and the Developer tier has one user/quotas; target plan must be verified.", "sentry_pricing"),
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


# Convert compact evidence tuples to schema rows after the source map is defined.
for _record in RECORDS.values():
    _record["evidence"] = [ev(*row) for row in _record["evidence"]]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_batch() -> dict:
    manifest = json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8"))
    raw_path = ROOT / "data/raw/final_full_research.json"
    csv_path = ROOT / "data/raw/final_full_research.csv"
    raw_records = json.loads(raw_path.read_text(encoding="utf-8"))
    base_by_id = {r["app_id"]: r for r in raw_records}
    manifest_by_id = {r["app_id"]: r for r in manifest}
    raw_hashes_before = {"json": file_hash(raw_path), "csv": file_hash(csv_path)}
    output_records: list[dict] = []
    output_traces: list[dict] = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for app_id in IDS:
        if app_id not in base_by_id or app_id not in manifest_by_id:
            raise ValueError(f"app_id={app_id} missing from manifest/raw baseline")
        data = copy.deepcopy(RECORDS[app_id])
        record = copy.deepcopy(base_by_id[app_id])
        record.update({k: copy.deepcopy(v) for k, v in data.items() if k != "evidence"})
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
             "note": "Search results were discovery leads only; snippets were not used as claim evidence."}
            for query, depth in QUERIES[app_id]
        ]
        app_sources = [copy.deepcopy(SOURCES[k]) for k in FETCH_COUNTS[app_id]]
        fetch_attempts = []
        for key, chunk_indexes in FETCH_COUNTS[app_id].items():
            src = SOURCES[key]
            for chunk in chunk_indexes:
                fetch_attempts.append({
                    "tool": "fetch_page", "url": src["url"], "chunk_index": chunk,
                    "status": "SUCCESS",
                    "note": "First-party source opened; claim-relevant observation retained in the source packet.",
                })
        for row in NON_EVIDENCE_FETCHES.get(app_id, []):
            fetch_attempts.append({"tool": "fetch_page", **copy.deepcopy(row)})
        query_attempts = [
            {"tool": "web_search", "query": q["query"], "depth": q["depth"],
             "status": "SUCCESS", "note": "Discovery lead only; not claim evidence."}
            for q in query_rows
        ]
        attempts = query_attempts + fetch_attempts
        record["query_count"] = len(query_rows)
        record["source_count"] = len(app_sources)
        record["attempt_count"] = len(attempts)
        record["trace_limitations"] = [
            "This standalone trace enumerates the targeted searches and source captures retained for Batch05 IDs 62-70. Redundant navigation-only HTML captures are not reconstructed; material failed/redirected paths are retained as non-evidence attempts.",
            "Search results/snippets are discovery leads only. Claim evidence cites opened first-party sources; fetch_page capture time is date-only because the tool does not expose a per-page clock time.",
            "LIVE_AGENT denotes native web research only. No provider credentials, vendor account, tenant, API call, MCP execution, deployment, or human review is claimed.",
            "This partial capture covers IDs 62-70 only and is not merged into the authoritative 100-row dataset. Full-population research, verification, human QA, analysis, tests, HTML regeneration and deployment gates remain unfinished.",
        ]
        urls = {s["url"] for s in app_sources}
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
        raise RuntimeError("authoritative raw JSON/CSV changed while assembling Batch05")
    return {
        "schema_version": "1.0", "run_id": RUN_ID,
        "run_started_at": now, "run_completed_at": now,
        "source_mode": "LIVE_AGENT", "tool": TOOL,
        "provider_credentials": {"TAVILY_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL", "OPENAI_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL"},
        "raw_dataset_hashes_before_and_after": raw_hashes_before,
        "scope": "Apps 62-70 only. Standalone native-web capture; not merged into data/raw/final_full_research.json or CSV and not the completed 100-app dataset.",
        "search_result_policy": "Search snippets are discovery leads only and excluded from claim evidence; evidence cites opened official sources.",
        "records": output_records, "traces": output_traces,
    }


def main() -> int:
    payload = build_batch()
    manifest = json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8"))
    manifest_by_id = {r["app_id"]: r for r in manifest}
    issues = []
    if [r["app_id"] for r in payload["records"]] != IDS:
        issues.append(("batch", "record IDs/order differ from scope"))
    if len(payload["traces"]) != len(IDS):
        issues.append(("batch", "trace count differs from scope"))
    for record in payload["records"]:
        errors = validate_record(record)
        if errors:
            issues.append((record["app_id"], errors))
        if record["quality_gate"]["status"] != "PASS":
            issues.append((record["app_id"], record["quality_gate"]))
        trace = next((t for t in payload["traces"] if t["app_id"] == record["app_id"]), None)
        if not trace or record["query_count"] != len(trace["queries"]) or record["source_count"] != len(trace["sources"]) or record["attempt_count"] != len(trace["attempts"]):
            issues.append((record["app_id"], "trace count reconciliation failed"))
        identity = manifest_by_id.get(record["app_id"])
        if not identity or (record["app"], record["category"], record["website_hint"]) != (identity["app"], identity["category"], identity["website_hint"]):
            issues.append((record["app_id"], "manifest identity/category/website mismatch"))
    if issues:
        print(json.dumps(issues, indent=2, ensure_ascii=False))
        return 1
    out = ROOT / "data/evidence/native_web_capture_batch05_2026-09-24.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} with {len(payload['records'])} rows and {len(payload['traces'])} traces")
    print("record quality:", {s: sum(r["quality_gate"]["status"] == s for r in payload["records"]) for s in ("PASS", "WARN", "FAIL")})
    for r in payload["records"]:
        print(r["app_id"], r["app"], r["research_status"], r["quality_gate"]["status"], r["query_count"], r["source_count"], r["attempt_count"])
        for warning in r["quality_gate"]["warnings"]:
            print("  WARN:", warning)
    print("raw JSON/CSV hashes unchanged:", payload["raw_dataset_hashes_before_and_after"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

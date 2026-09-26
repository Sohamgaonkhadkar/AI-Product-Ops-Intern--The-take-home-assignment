#!/usr/bin/env python3
"""Build a standalone, source-linked native-web capture for manifest IDs 80-91, 93-100.

The builder never edits data/raw/final_full_research.json or its CSV. Search is
recorded as discovery only; claim evidence cites directly opened first-party
sources (or the official integration-provider documentation where appropriate).
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

DATE = "2026-09-25"
RUN_ID = "arena-native-web-batch07-20260925"
TOOL = "Arena.ai Agent Mode native web_search + fetch_page; official-source-led manual research"
IDS = list(range(80, 92)) + list(range(93, 101))
RAW_JSON = ROOT / "data/raw/final_full_research.json"
RAW_CSV = ROOT / "data/raw/final_full_research.csv"
OUT = ROOT / "data/evidence/native_web_capture_batch07_2026-09-25.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def src(key: str, url: str, title: str, source_type: str, observation: str, chunks=(0,)) -> dict:
    return {
        "key": key,
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


def ev(field: str, claim: str, source: dict, support: str = "supports", excerpt: str | None = None) -> dict:
    item = {
        "claim": claim,
        "field": field,
        "source_url": source["url"],
        "source_title": source["title"],
        "source_type": source["source_type"],
        "accessed_at": DATE,
        "support": support,
    }
    if excerpt:
        item["excerpt_or_observation"] = excerpt
    return item


# The primary native search query per app is retained verbatim; targeted follow-up queries are listed separately where performed.
SPECS: dict[int, dict] = {
    80: {
        "query": "Harvest official MCP REST API OAuth personal access token pricing",
        "description": "Harvest is a time-tracking, project and invoicing service with a REST API and a first-party hosted MCP connection for authorized account users.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Harvest offers a Free plan and paid plans; an active Harvest account is required for hosted MCP, and the connected user's role and permissions constrain access. No tenant-specific plan or role was checked.",
        "credential_access": {"status": "RESTRICTED", "path": "Connect the hosted MCP in a compatible client and authorize by signing in to Harvest; for REST API use, create a personal access token or OAuth app/token as documented.", "plan_or_gate": "An active Harvest account is required for hosted MCP. The user acts with their own Harvest role/permissions. No account or permission check was performed."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Harvest API v2 is a REST API covering time entries, projects, clients, tasks, expenses, invoices, estimates and users. API limits and account permissions apply; the page does not establish a general webhook API."},
        "mcp": {"status": "AVAILABLE", "details": "First-party hosted MCP at https://api.harvestapp.com/mcp. It supports time tracking, reports, budgets, projects, clients, tasks and invoices. It can create draft invoices only; sending/reviewing remains in Harvest, and payment-level notes/PDF links are not exposed through MCP.", "search_scope": "Opened Harvest's first-party MCP support article, API v2 reference/authentication pages, integrations help and pricing. Search results were discovery only; no Harvest account was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an active Harvest account and user authorization; actions inherit role permissions and invoice creation is draft-only.", "rationale": "The official REST API and hosted MCP document broad time/project/accounting workflows. Build with least-privilege access and human review of mutations; no tenant-specific entitlement or API/MCP operation was tested."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://support.getharvest.com/hc/en-us/articles/46293697226381-Harvest-MCP", "Harvest MCP – Harvest Help Center", "official_support", "The support article documents https://api.harvestapp.com/mcp, OAuth sign-in, active-account prerequisite, inherited Harvest role permissions, time/project/client/task/report workflows, draft-only invoices, and payment/PDF limitations.", (0, 1)),
            src("api", "https://help.getharvest.com/api-v2/", "Harvest API v2 Documentation", "official_api_docs", "The official API reference documents REST API v2 resources for time tracking, clients, projects, tasks, expenses, invoices, estimates and users, plus authentication and rate-limit guidance.", (0,)),
            src("auth", "https://help.getharvest.com/api-v2/authentication-api/authentication/authentication/", "Authentication - Harvest API v2", "official_auth_docs", "The API authentication guide documents OAuth 2 and personal access tokens for Harvest API v2 requests.", (0,)),
            src("pricing", "https://www.getharvest.com/pricing", "Harvest Pricing", "official_pricing", "The official pricing page lists a free tier and paid plans; plan features and seat/project limits differ.", (0,)),
        ],
        "evidence": [
            ("description", "Harvest describes a hosted MCP connection that lets an authorized user work with Harvest time-tracking and project data.", "mcp", "supports", "The MCP article lists timers, time entries, reports, budgets, projects and clients."),
            ("auth", "Harvest MCP requires the user to sign in and authorize the connection; REST API authentication supports OAuth 2 and personal access tokens.", "mcp", "supports", "The hosted setup signs in to Harvest; the API guide documents OAuth/PAT."),
            ("self_serve", "Harvest lists Free and paid plans; hosted MCP requires an active Harvest account.", "pricing", "supports", "The MCP article says an active Harvest account is required."),
            ("credential_access", "The MCP acts as the signed-in Harvest user and exposes only actions allowed by that user's role.", "mcp", "supports", "The support article says the assistant sees only what the user's Harvest role permits."),
            ("api", "Harvest publishes API v2 as a REST API with documented time, project, client, expense, invoice and user resources.", "api", "supports", "Official API v2 reference."),
            ("mcp", "Harvest operates the hosted MCP at https://api.harvestapp.com/mcp and limits invoice creation to drafts.", "mcp", "supports", "The article identifies the endpoint and draft-only invoices."),
            ("buildability", "Harvest documents both REST and hosted-MCP workflows, while user permissions and draft-only invoice behavior constrain automation.", "mcp", "supports", "The API reference and MCP support article provide setup and tool-scope details."),
        ],
        "notes": "Harvest MCP's current first-party feature list is broader than the legacy API-only view; REST API and hosted MCP are kept distinct.",
    },
    81: {
        "query": "Stripe official MCP server OAuth agent keys pricing API",
        "description": "Stripe is a payments and financial-services platform with a broad REST API and a first-party hosted MCP server in public preview.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Stripe offers self-serve account creation and test mode, with usage-based transaction pricing and account/region/business restrictions. Hosted MCP is in public preview. Stripe documents a future key-policy change effective October 31, 2026; it is not yet effective on this capture date.",
        "credential_access": {"status": "RESTRICTED", "path": "Authorize the hosted MCP with OAuth, or create an API/agent key in the Stripe Dashboard. Team administrators can enable/disable MCP access and manage team sessions.", "plan_or_gate": "Connected live/sandbox accounts and granted API permissions scope access. Organization settings or IT network policy can restrict MCP. Beginning 2026-10-31, MCP rejects full-access keys and restricted keys without the Agent tag."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Stripe's REST API spans payments, customers, products, subscriptions, invoicing, refunds, disputes and many adjacent financial resources. Access is determined by key scopes, account configuration and applicable regulatory/region requirements."},
        "mcp": {"status": "AVAILABLE", "details": "Stripe operates https://mcp.stripe.com (public preview) for Stripe API tools and documentation search. Hosted MCP supports OAuth or API keys; administrators can manage team access. Some higher-risk writes require confirmation. A future Agent-tagged restricted-key policy takes effect 2026-10-31.", "search_scope": "Opened Stripe's first-party MCP guide, key/agent-key documentation, REST API reference and pricing. The MCP docs identify the hosted endpoint, preview status, auth choices, team controls and future key-policy date; no Stripe account was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Public-preview MCP, Stripe account/key scoping, organization controls, risk-based action confirmation and future agent-key restrictions.", "rationale": "The REST API and hosted MCP support broad payment workflows, but production automation needs least-privilege keys, test/live separation and safety review. No Stripe account, key or transaction was tested."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://docs.stripe.com/mcp", "Model Context Protocol (MCP) | Stripe Documentation", "official_docs", "Stripe labels hosted MCP Public preview, lists endpoint https://mcp.stripe.com, API/documentation tools, OAuth/API-key auth, team access controls and API key policy details.", (0, 1)),
            src("keys", "https://docs.stripe.com/keys", "API keys | Stripe Documentation", "official_auth_docs", "The key guide covers standard, restricted and Agent API keys, permissions and the announced 2026-10-31 transition for MCP-compatible key use.", (0, 1, 2)),
            src("api", "https://docs.stripe.com/api", "Stripe API reference", "official_api_docs", "Stripe publishes a REST API reference for payments, billing, customers and related resources.", (0,)),
            src("pricing", "https://stripe.com/pricing", "Stripe pricing", "official_pricing", "Stripe's official pricing describes transaction-based charges and product-specific fees.", (0,)),
        ],
        "evidence": [
            ("description", "Stripe's MCP is an agent interface to Stripe API resources and its documentation knowledge base.", "mcp", "supports", "The MCP guide describes interacting with the Stripe API and searching Stripe documentation."),
            ("auth", "Hosted Stripe MCP supports OAuth and API-key authentication; API keys may be restricted and agent-tagged.", "mcp", "supports", "The MCP guide lists OAuth and API keys; the keys guide describes agent keys."),
            ("self_serve", "Stripe documents account creation, test mode and usage-based pricing; hosted MCP remains in public preview.", "mcp", "supports", "Official MCP and pricing pages."),
            ("credential_access", "Stripe access is scoped to authorized accounts/environments and can be managed by team administrators.", "mcp", "supports", "The MCP guide describes per-account/environment authorization and team settings."),
            ("api", "Stripe publishes a broad REST API for payments, billing and related financial resources.", "api", "supports", "Official API reference."),
            ("mcp", "Stripe operates https://mcp.stripe.com and labels its MCP service Public preview.", "mcp", "supports", "MCP setup and preview badge."),
            ("buildability", "Stripe documents broad REST/MCP functionality plus key scopes, team controls and risk-confirmation constraints.", "mcp", "supports", "MCP guide and API-key documentation."),
        ],
        "notes": "The Agent-tag requirement's effective date is 2026-10-31, after this capture date; do not present it as already active.",
    },
    82: {
        "query": "Plaid official Dashboard MCP Production approval mcp dashboard API",
        "description": "Plaid provides financial-data connectivity APIs and a remote Dashboard MCP for diagnostics and analytics about a team's Plaid integration.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Developers can use Plaid Sandbox, but production access is product/approval-dependent. Dashboard MCP works only with Production data and requires approval for at least one Plaid product; product plans and billing vary.",
        "credential_access": {"status": "GATED", "path": "For Dashboard MCP, use production Plaid client credentials to mint an OAuth token with scope mcp:dashboard, then send its bearer access token to the hosted MCP. The separate local AI coding toolkit is for development/Sandbox tools.", "plan_or_gate": "Plaid team must have Production approval for at least one product. Dashboard MCP does not provide consumer bank-account transaction access; it exposes diagnostics/analytics about the team's Plaid integration."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "Plaid's REST API offers multiple financial-data products (for example, Auth, Transactions, Identity and Assets). Available data/products, production access and billing depend on approval and account configuration."},
        "mcp": {"status": "AVAILABLE", "details": "Plaid offers a hosted Dashboard MCP at https://api.dashboard.plaid.com/mcp/ for Production diagnostics and analytics (Items, Link conversion, usage), plus a separate local AI coding toolkit MCP for mock data, docs, Sandbox tokens and webhook simulation. Dashboard MCP is not a consumer bank-transaction connector.", "search_scope": "Opened Plaid's first-party Dashboard MCP page and linked AI coding toolkit, REST API reference and billing docs. The docs explicitly distinguish remote Production diagnostics from local development tools; no Plaid tenant or API operation was used."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Dashboard MCP requires approved Production access and an mcp:dashboard OAuth token; the toolset is for integration diagnostics, not consumer transaction retrieval.", "rationale": "The REST API and MCP setup are documented, but the intended data surface must match the use case and products must be approved. No account approval, token, Link flow or tenant was checked."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://plaid.com/docs/resources/mcp/", "Resources - MCP Server | Plaid Docs", "official_docs", "The page distinguishes hosted Dashboard MCP (Production diagnostics/analytics) from a local developer toolkit, requires Production approval for at least one product, and documents URL https://api.dashboard.plaid.com/mcp/ plus OAuth scope mcp:dashboard.", (0, 1)),
            src("api", "https://plaid.com/docs/api/", "API - Plaid Docs", "official_api_docs", "Plaid publishes product-oriented REST APIs for financial data and platform workflows, with client ID/secret authentication and environment/product distinctions.", (0,)),
            src("billing", "https://plaid.com/docs/account/billing/", "Billing - Plaid Docs", "official_pricing", "Official billing documentation describes trial/production billing and product-dependent access; production products may require approval.", (0,)),
        ],
        "evidence": [
            ("description", "Plaid's Dashboard MCP serves integration diagnostics and analytics; a separate local toolkit serves development operations.", "mcp", "supports", "The MCP page explicitly distinguishes the two Plaid MCP products."),
            ("auth", "Plaid REST requests use client credentials; Dashboard MCP uses a production OAuth token with the mcp:dashboard scope and bearer authorization.", "mcp", "supports", "The MCP docs show client credentials, scope and bearer token flow."),
            ("self_serve", "Plaid documents Sandbox development and product/approval-dependent Production access; Dashboard MCP requires at least one approved Production product.", "mcp", "supports", "The page's requirements section states Production approval is required."),
            ("credential_access", "Dashboard MCP requires production approval and a token scoped mcp:dashboard.", "mcp", "supports", "OAuth token instructions and requirements."),
            ("api", "Plaid exposes REST APIs for multiple financial-data products; product access and billing vary.", "api", "supports", "Official API and billing docs."),
            ("mcp", "Plaid operates a remote Dashboard MCP endpoint and a separate local development MCP toolkit.", "mcp", "supports", "The MCP article names both servers and their distinct roles."),
            ("buildability", "Plaid's MCP/API are documented but Dashboard MCP is restricted to approved Production integration diagnostics.", "mcp", "supports", "Requirements and tool purpose are explicit."),
        ],
        "notes": "Do not describe Plaid Dashboard MCP as a consumer bank-transaction MCP; the local coding toolkit is a distinct product surface.",
    },
    83: {
        "query": "Binance official Agentic MCP dedicated sub-account no withdrawal",
        "description": "Binance offers a hosted Agentic MCP for market data and user-authorized trading inside a dedicated Agentic sub-account, alongside its trading APIs.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "API key"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "The hosted Agentic MCP requires a Binance.com account, desktop setup and an Agentic sub-account. The sub-account starts empty and the user must fund it manually; trade features remain subject to account authorization and jurisdiction/product eligibility.",
        "credential_access": {"status": "RESTRICTED", "path": "Add the official remote MCP endpoint in a supported client and authorize through the Binance OAuth consent flow. For direct exchange REST API integrations, create API credentials in Binance account settings.", "plan_or_gate": "Access is scoped to selected market/account/trade/transfer permissions and an Agentic sub-account. The agent cannot withdraw to an external address; the user funds the sub-account and can move assets back through Binance Sub-account Management. All non-read actions require confirmation."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Binance publishes Spot REST endpoints for market data and account/trading workflows. The direct REST API is separate from the hosted Agentic MCP; trading features depend on product, account and permissions. Other exchange transports were not assessed in this record."},
        "mcp": {"status": "AVAILABLE", "details": "First-party hosted endpoint https://agent.binance.com/mcp/agentic. The agent can read market data, view authorized balances and trade/transfer only within the dedicated Agentic sub-account. The agent cannot withdraw to an external address; the user funds the sub-account and confirms each non-read action.", "search_scope": "Opened Binance's first-party Agentic MCP setup/safeguards guide and Spot REST documentation. The official guide specifies OAuth authorization, least-privilege scopes, sub-account boundaries and confirmation; no Binance account was linked."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires eligible account/sub-account, user-selected scopes, manual sub-account funding and explicit confirmation for every non-read action.", "rationale": "Binance documents both REST and hosted MCP interfaces with concrete safeguards. Deploy only with strict scope boundaries and human confirmation; no account eligibility, sub-account or transaction was tested."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://developers.binance.com/en/docs/agent-native/mcp-server/agentic", "Binance MCP Server | Binance Developer Docs", "official_docs", "The official guide documents remote endpoint https://agent.binance.com/mcp/agentic, OAuth consent, selectable scopes, a dedicated Agentic sub-account, manual funding, no withdrawal scope and confirmation before every non-read action.", (0, 1)),
            src("api", "https://developers.binance.com/en/docs/products/spot/rest-api", "Spot REST API | Binance Developer Docs", "official_api_docs", "Binance's Spot REST reference documents market-data and trading/account endpoints, distinct from the Agentic MCP.", (0,)),
        ],
        "evidence": [
            ("description", "Binance's Agentic MCP provides agent access to market data and authorized account/trading functions in a dedicated sub-account.", "mcp", "supports", "The official MCP guide describes market data, balances, trading and transfers."),
            ("auth", "The hosted MCP uses Binance OAuth authorization; direct REST API integrations use API credentials.", "mcp", "supports", "The guide includes OAuth consent; the REST reference is a separate API surface."),
            ("self_serve", "The MCP requires a Binance account and an Agentic sub-account, which the user must manually fund.", "mcp", "supports", "Official prerequisites and funding instructions."),
            ("credential_access", "Binance scopes MCP permissions and permanently withholds withdrawal scope; non-read actions require confirmation.", "mcp", "supports", "The guide says no withdrawal scope and confirms before action."),
            ("api", "Binance publishes a Spot REST API for market data and exchange operations.", "api", "supports", "Official Spot REST reference."),
            ("mcp", "Binance hosts an Agentic MCP endpoint at https://agent.binance.com/mcp/agentic.", "mcp", "supports", "The official setup guide names this endpoint."),
            ("buildability", "Official Binance docs define explicit account, funding, scope and human-confirmation safeguards.", "mcp", "supports", "The setup and action workflow are documented."),
        ],
        "notes": "External withdrawals are unavailable to the agent; users can move funds back through Binance Sub-account Management. Market-data scope is public; trade/transfer scopes are separately granted.",
    },
    84: {
        "query": "Paygent Connect NMI-powered product official API identity Paygent NMI",
        "description": "Not established",
        "auth_status": "UNKNOWN", "auth_methods": [],
        "self_serve_status": "UNKNOWN",
        "self_serve_details": "UNKNOWN pending product identity. Public sources surfaced Paygent Japan and NMI candidate products, but no first-party source connected either candidate to the manifest label.",
        "credential_access": {"status": "UNKNOWN", "path": "UNKNOWN until the product behind manifest ID84 is identified.", "plan_or_gate": "UNKNOWN; evidence for Paygent Japan or NMI must not be attributed to Paygent Connect without an identity link."},
        "api": {"available": "UNKNOWN", "types": [], "breadth": "UNKNOWN", "details": "UNKNOWN. No product-specific API/auth facts are attributed to ID84 until a first-party source establishes the manifest product's identity."},
        "mcp": {"status": "UNKNOWN", "details": "UNKNOWN. Candidate-product evidence is not attributed to ID84.", "search_scope": "Searched for the exact manifest name and NMI-powered hint; opened Paygent Japan and NMI first-party pages and NMI gateway documentation. None identifies which product the manifest means; this is an identity-resolution failure, not evidence of no API or MCP."},
        "buildability": {"verdict": "UNKNOWN", "blocker": "The product identity is unresolved.", "rationale": "Do not design or test a connector until the user or an authoritative first-party source identifies the intended product. No candidate product's API/auth/MCP facts are transferred to ID84."},
        "confidence": "LOW",
        "sources": [
            src("paygent", "https://www.paygent.co.jp/", "PAYGENT", "official_product", "Opened the Paygent Japan product site; it describes a Japanese payment-services product but does not identify the assignment's 'Paygent Connect' or establish the 'NMI-powered' relationship.", (0,)),
            src("nmi", "https://secure.networkmerchants.com/gw/merchants/resources/integration/integration_portal.php", "NMI Integration Documentation", "official_api_docs", "Opened NMI's gateway integration material, which documents NMI transaction endpoints; it does not establish that the manifest's Paygent Connect is an NMI product or this NMI service.", (0,)),
        ],
        "evidence": [
            ("other", "Paygent Japan and NMI are candidate products surfaced by the manifest hint, but the opened first-party sources do not establish which product 'Paygent Connect' refers to.", "paygent", "context", "The Paygent site and NMI integration docs do not provide a linking identity statement."),
            ("other", "NMI's own gateway documentation is evidence about NMI only and is not attributed to ID84.", "nmi", "context", "Candidate evidence retained without inference."),
        ],
        "conflicts": [{"field": "identity", "summary": "The manifest calls ID84 'Paygent Connect' and hints 'NMI-powered'; first-party Paygent Japan and NMI sources do not establish the intended product identity.", "resolution": "Keep product-specific auth, access, API, MCP and buildability UNKNOWN. Do not attribute candidate Paygent/NMI facts until the user or a first-party source resolves identity."}],
        "notes": "User explicitly resolved ID84 as unresolved. This record preserves that decision and does not infer a product from the NMI-powered hint.",
    },
    85: {
        "query": "iPayX official MCP REST API developer pricing API key",
        "description": "iPayX is an FX-audit product that exposes a REST API and first-party hosted MCP for rate checks, transaction audits and forensic reports.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "iPayX documents public MCP tools with per-IP limits and a dashboard API key for full forensic reports. The developer page shows a Developer plan at $99/month and separate API tiers starting at $499/month; the retail pricing page instead lists a $99 one-time audit pack and $299/month Unlimited audits. The mapping among these offers is unclear and is not collapsed into one price ladder.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create an iPayX account and generate a production API key in the dashboard; send it as a Bearer token. Public MCP rate/risk tools can be used without a key, while full forensic reports require an API key.", "plan_or_gate": "Public MCP tools are limited per IP; full reports require a key. The developer page lists Developer at $99/month and separate API tiers from $499/month, while retail pricing lists a $99 one-time audit pack and $299/month Unlimited; exact product/entitlement mapping is unresolved."},
        "api": {"available": "YES", "types": ["REST", "Webhooks"], "breadth": "NARROW", "details": "The REST API audits FX transaction data and returns structured scores/spreads; first-party docs also describe audit-completed/alert webhooks. Documentation gives a Supabase function URL while saying a custom api.ipayx.ai domain is coming soon; treat endpoint branding and API tier mapping cautiously."},
        "mcp": {"status": "AVAILABLE", "details": "Official hosted MCP at https://mcp.ipayx.ai/mcp. Public tools check FX rates and audit transactions; the full forensic report tool requires a Bearer API key. The developer page lists public per-IP limits and exposes an OpenAPI/MCP manifest.", "search_scope": "Opened iPayX's first-party developer, MCP and pricing pages. The docs provide REST examples, webhook events, hosted MCP URL, tool/auth distinctions and pricing statements; no API key, account or tenant was tested."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Narrow FX-audit scope, API key required for full reports, per-IP limits on public MCP tools, and unclear tier/endpoint branding in first-party pricing/docs.", "rationale": "The first-party API and MCP setup is concrete enough for an FX-audit integration. Confirm commercial tier, rate limits and production endpoint with iPayX before a paid rollout; no live request was made."},
        "confidence": "MEDIUM",
        "sources": [
            src("dev", "https://www.ipayx.ai/developers", "FX Audit API & MCP — Developer Documentation — iPayX", "official_api_docs", "The developer page documents REST JSON, webhooks, account/API-key setup, Bearer auth, FX audit endpoint, current Supabase function URL, key-protected full reports, public MCP tools, and an API pricing table.", (0, 1)),
            src("mcp", "https://www.ipayx.ai/mcp", "iPayX MCP — Forensic FX audit for AI agents", "official_docs", "The MCP page lists https://mcp.ipayx.ai/mcp, Streamable HTTP configuration, unauthenticated public tools with per-IP limits, and full_forensic_report as key-authenticated.", (0,)),
            src("pricing", "https://www.ipayx.ai/pricing", "iPayX Pricing", "official_pricing", "The main pricing page lists retail FX audit products/credit packs separately from the developer API tier table; product mapping is not explicit.", (0,)),
        ],
        "evidence": [
            ("description", "iPayX describes an FX-audit engine with REST API and native MCP for FX checks, transaction audits and reports.", "dev", "supports", "The developer page labels REST API, MCP and FX audit engine."),
            ("auth", "iPayX uses Bearer API keys for REST and full forensic reports; its public MCP tools can be used without a key under IP limits.", "mcp", "supports", "The MCP page distinguishes public tools from full_forensic_report key auth."),
            ("self_serve", "iPayX documents public MCP tools and dashboard API-key generation; developer pricing lists a $99/month Developer plan plus separate API tiers, while the retail page lists different audit offers.", "dev", "supports", "The developer page shows the Developer plan and API tiers; the retail pricing page is retained separately."),
            ("credential_access", "An iPayX dashboard API key is self-generated; the full forensic MCP tool requires a Bearer key.", "dev", "supports", "The developer quickstart describes account/key generation and Bearer authentication."),
            ("api", "The iPayX developer documentation exposes a narrow REST FX-audit endpoint and audit webhooks.", "dev", "supports", "The developer page includes REST JSON and Webhooks & Events sections."),
            ("mcp", "iPayX publishes https://mcp.ipayx.ai/mcp with public rate/audit tools and a key-protected full report tool.", "mcp", "supports", "The official MCP page identifies endpoint and tool authentication."),
            ("buildability", "iPayX documents REST/MCP setup but endpoint branding and offer mapping need confirmation before paid production use.", "dev", "supports", "The developer page shows the Supabase function URL and says a custom domain is coming soon."),
        ],
        "conflicts": [{"field": "self_serve", "summary": "The developer page shows a $99/month Developer plan and separate API tiers starting at $499/month; the main retail page shows a $99 one-time pack and $299/month Unlimited audits. The relationship among these offers is not made explicit.", "resolution": "Preserve the exact page/offer labels and keep their entitlement mapping unresolved; do not present retail audit pricing as the developer API price."}, {"field": "api", "summary": "Developer documentation demonstrates a Supabase function URL while noting the api.ipayx.ai custom domain is coming soon.", "resolution": "Record the demonstrated URL and endpoint branding caveat; confirm production URL before integration."}],
        "notes": "MCP public-tool access is distinct from full-report key access. The developer page's Developer/API pricing and the retail audit offers are both retained; their product mapping was not reconciled.",
    },
    86: {
        "query": "Intuit QuickBooks Online official MCP OAuth API developer portal sandbox",
        "description": "QuickBooks Online is Intuit's cloud accounting product with a REST API and an Intuit-maintained local stdio MCP server.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "An Intuit Developer Portal app and OAuth client are required. The official MCP README supports a developer sandbox; production authorization requires a public HTTPS callback. Sandbox and production company/account access are distinct.",
        "credential_access": {"status": "RESTRICTED", "path": "Register a QBO app in Intuit Developer Portal, configure OAuth redirect URIs, obtain client credentials, then authorize a sandbox or production QuickBooks company through OAuth 2.0.", "plan_or_gate": "Sandbox is available for development; production requires a company authorization and public HTTPS callback. Intuit app setup is required; no QBO tenant or production approval was checked."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "QuickBooks Online Accounting API is REST and supports broad accounting resources; the official Intuit MCP project wraps QBO features with local tools. OAuth scopes and company permissions apply."},
        "mcp": {"status": "AVAILABLE", "details": "Intuit's official `intuit/quickbooks-online-mcp-server` is a local stdio server that authenticates to a QBO company via OAuth 2.0. Its README describes CRUD tools across accounting entities and reports; it is not a hosted Intuit MCP endpoint.", "search_scope": "Opened Intuit's official GitHub MCP README and QBO API authentication/sandbox docs. The README explicitly calls the server local/stdio and documents OAuth app setup; no QBO company was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires Intuit app registration, OAuth consent and a target QBO company; production redirect URI must be public HTTPS.", "rationale": "The official local MCP server and REST API are documented and sandbox testing is supported. Production use requires secure OAuth deployment and company authorization; no app, OAuth grant or API call was run."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://github.com/intuit/quickbooks-online-mcp-server/blob/main/README.md", "quickbooks-online-mcp-server/README.md · intuit/quickbooks-online-mcp-server · GitHub", "official_github", "Intuit's README identifies a local stdio MCP server, OAuth 2.0, Developer Portal app setup, sandbox/local redirect support and public HTTPS callback for production.", (1, 2)),
            src("oauth", "https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0", "OAuth 2.0 - QuickBooks Online API", "official_auth_docs", "Intuit documents OAuth 2.0 authorization for QuickBooks Online apps and company connections.", (0,)),
            src("sandbox", "https://developer.intuit.com/app/developer/qbo/docs/develop/sandboxes", "Sandboxes - QuickBooks Online API", "official_support", "Intuit documents developer sandbox companies for testing QBO integrations.", (0,)),
        ],
        "evidence": [
            ("description", "Intuit's QuickBooks Online MCP server exposes QBO accounting features to MCP clients through a local stdio process.", "mcp", "supports", "The official repository README calls it a local MCP server."),
            ("auth", "QBO API and the official local MCP use OAuth 2.0 authorization to connect to a company.", "mcp", "supports", "The README states OAuth 2.0; Intuit docs describe OAuth authorization."),
            ("self_serve", "The official MCP setup provides a developer sandbox path; production uses a QBO company and public HTTPS redirect.", "mcp", "supports", "README distinguishes sandbox and production redirect requirements."),
            ("credential_access", "A Developer Portal app and OAuth handshake are prerequisites for the official MCP server.", "mcp", "supports", "The README states app registration and one-time browser authorization are required."),
            ("api", "Intuit publishes the QuickBooks Online Accounting API as a REST resource API.", "oauth", "supports", "Official QBO developer documentation and reference."),
            ("mcp", "Intuit maintains a local, stdio QuickBooks Online MCP server.", "mcp", "supports", "The repository identifies owner and local transport."),
            ("buildability", "Sandbox and local MCP setup are documented, while production authorization requires OAuth and HTTPS callback deployment.", "mcp", "supports", "The README gives environment-specific constraints."),
        ],
        "notes": "The `MCP` classification refers to Intuit's official local server; community-hosted wrappers are not used as evidence.",
    },
    87: {
        "query": "Xero official MCP server OAuth API docs pricing limits",
        "description": "Xero is an accounting platform with public REST APIs and a XeroAPI-maintained local MCP server for accounting workflows.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "A Xero developer account and organization are required. The official MCP supports OAuth2 Custom Connections or bearer-token mode; connection availability and organization/region limits depend on Xero plan and account rules. An earlier Starter/Core connection-limit discrepancy remains unresolved.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a Xero developer app/custom connection or supply an authorized bearer token, then run the official `@xeroapi/xero-mcp-server` locally with scoped OAuth credentials.", "plan_or_gate": "Custom Connections and organization limits vary by plan/region; the prior official-plan evidence was internally inconsistent for a Starter/Core connection-limit detail. One connection should be treated as one organization unless official settings confirm otherwise."},
        "api": {"available": "YES", "types": ["REST", "SDK"], "breadth": "BROAD", "details": "Xero publishes broad REST APIs for accounting resources such as contacts, accounts, invoices and payments, with official SDKs. OAuth scopes, region-specific features and connection limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "XeroAPI's official `xero-mcp-server` is a local MCP implementation that bridges MCP tools to Xero APIs. The README documents OAuth2 Custom Connections and a bearer-token mode, Node.js runtime, and scope differences for connections created before/after April 29, 2026.", "search_scope": "Opened XeroAPI's first-party GitHub MCP README and official OAuth/API documentation. The README is under the XeroAPI organization and details local setup/auth/scopes; no Xero organization was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires a Xero developer app/credentials and organization authorization; plan/region connection limits and an earlier Starter/Core limit discrepancy need confirmation.", "rationale": "The official MCP server and REST API are buildable with local Node.js and OAuth credentials, but scopes and tenant connection rules must be matched to the target organization. No account or API operation was tested."},
        "confidence": "MEDIUM",
        "sources": [
            src("mcp", "https://github.com/XeroAPI/xero-mcp-server/blob/main/README.md", "xero-mcp-server/README.md · XeroAPI · GitHub", "official_github", "XeroAPI's README documents an MCP server for Xero, local Node.js setup, OAuth2 Custom Connections and bearer token mode, scopes and a developer/demo company path.", (1,)),
            src("api", "https://developer.xero.com/documentation/api/", "Xero API documentation", "official_api_docs", "Xero's official API docs publish accounting REST endpoints and SDK/reference material.", (0,)),
            src("oauth", "https://developer.xero.com/documentation/guides/oauth2/overview/", "OAuth 2.0 overview - Xero Developer", "official_auth_docs", "Xero documents OAuth 2.0 authorization and custom-connection setup; supported access and organization/region behavior depend on configuration.", (0,)),
        ],
        "evidence": [
            ("description", "XeroAPI publishes an MCP server that bridges MCP calls to Xero's accounting API.", "mcp", "supports", "The official README calls it an MCP server implementation for Xero."),
            ("auth", "The official Xero MCP supports OAuth2 Custom Connections and bearer-token authentication.", "mcp", "supports", "README documents both authentication modes."),
            ("self_serve", "Xero developers can configure API credentials, but connection limits and eligibility vary by plan/region; one published Starter/Core limit remains inconsistent in prior official evidence.", "oauth", "supports", "Official OAuth and pricing materials; see preserved conflict."),
            ("credential_access", "The local MCP requires Xero developer credentials and the scopes appropriate to the Custom Connection/API.", "mcp", "supports", "README lists client ID, client secret and scopes."),
            ("api", "Xero publishes REST accounting APIs and client SDKs.", "api", "supports", "Official API documentation."),
            ("mcp", "XeroAPI maintains an official local MCP server for Xero.", "mcp", "supports", "The repository is under XeroAPI and includes setup/auth instructions."),
            ("buildability", "Xero MCP/API use is technically documented but requires credentials, OAuth scopes and plan/region checks.", "mcp", "supports", "The setup README and OAuth docs identify those requirements."),
        ],
        "conflicts": [{"field": "self_serve", "summary": "The earlier official Xero plan materials showed inconsistent Starter/Core Custom Connection limits.", "resolution": "Retain the plan-limit detail as unresolved; state that plan/region limits apply and verify the current target plan before rollout."}],
        "notes": "Custom Connections created before/after 2026-04-29 use different granular OAuth scope sets per current README.",
    },
    88: {
        "query": "Brex official MCP API beta prerequisite Developer API agreement OAuth",
        "description": "Brex is a financial operations platform with developer APIs and a beta hosted MCP service for authorized account workflows.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token", "API key"],
        "self_serve_status": "ADMIN_APPROVAL_REQUIRED",
        "self_serve_details": "Brex MCP is beta-gated: an account/card admin must accept the Developer API agreement and enable the 'Brex in AI assistants' beta. Once enabled, users connect individually and tools inherit each user's Brex capabilities.",
        "credential_access": {"status": "GATED", "path": "An account/card admin accepts the Developer API agreement and enables the beta in Brex Dashboard. Users then authorize the hosted MCP by OAuth; admins can also provision scoped Bearer API tokens.", "plan_or_gate": "Admin agreement and beta enablement are required. API-token management is admin-controlled; MCP operations inherit user/tool-specific Brex permissions."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Brex's REST developer API covers users, expenses, cards, transactions, bills, vendors and related financial operations. API tokens are scoped and production API server is https://api.brex.com."},
        "mcp": {"status": "AVAILABLE", "details": "Brex hosts MCP at https://api.brex.com/mcp (beta). OAuth with Dynamic Client Registration is recommended; API Bearer tokens are also supported. Tools span users, expenses, cards, transactions and bills but remain limited by user capabilities; approval/card-management tools may be unavailable.", "search_scope": "Opened Brex's official MCP guide, developer authentication docs and API reference. The MCP guide explicitly states beta, admin agreement/enablement, OAuth/token options and role-specific tools; no Brex account was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Admin agreement and beta enablement are required; supported actions vary by user capability and the server remains beta.", "rationale": "Brex documents hosted OAuth MCP and a scoped REST API. A customer admin must first enable access, after which role-limited workflows can be integrated; no account or API token was tested."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://developer.brex.com/docs/mcp", "Brex MCP", "official_docs", "Brex documents a beta hosted server at https://api.brex.com/mcp, admin acceptance of Developer API terms, beta enablement, OAuth/DCR and Bearer token modes, and capability-gated tools.", (0, 1)),
            src("auth", "https://developer.brex.com/guides/authentication", "Authentication - Brex Developer Documentation", "official_auth_docs", "The authentication guide requires account/card admin credentials to create scoped Bearer tokens after Developer API terms are accepted.", (0,)),
            src("api", "https://developer.brex.com/docs", "Brex Developer Documentation", "official_api_docs", "Brex publishes REST API references for financial operations, resources and OAuth/token authentication.", (0,)),
        ],
        "evidence": [
            ("description", "Brex MCP allows assistants to interact with Brex expense, user, card, transaction and bill workflows.", "mcp", "supports", "Official MCP guide describes these tools."),
            ("auth", "Brex MCP supports OAuth/DCR and scoped Bearer API tokens; the REST API uses Bearer tokens.", "mcp", "supports", "MCP auth section and API auth guide."),
            ("self_serve", "Brex MCP requires an admin to accept the Developer API agreement and enable a beta feature.", "mcp", "supports", "Prerequisites section."),
            ("credential_access", "Admin agreement/beta enablement precede user OAuth; API tokens are admin-provisioned and scoped.", "mcp", "supports", "Official setup and authentication docs."),
            ("api", "Brex publishes REST APIs for financial operations and resource workflows.", "api", "supports", "Official API documentation."),
            ("mcp", "Brex operates the hosted MCP at https://api.brex.com/mcp as a beta service.", "mcp", "supports", "Official endpoint/setup documentation."),
            ("buildability", "Brex integration is possible after admin beta gating and remains capability-limited/beta.", "mcp", "supports", "Official prerequisites and tool-access column."),
        ],
        "notes": "MCP OAuth is user-authorized; it differs from the Brex Developer API's admin-provisioned service tokens.",
    },
    89: {
        "query": "Ramp official hosted MCP server demo production API OAuth role tools",
        "description": "Ramp is a finance-operations platform with developer APIs and a hosted MCP for spend, card, reimbursement and workflow operations.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Ramp MCP supports production and demo endpoints. Production requires an authenticated Ramp user/business; tools are role-limited, with most company-wide spend/bill tools requiring admin or business-owner access. Developer API credentials require a Ramp account and appropriate access.",
        "credential_access": {"status": "RESTRICTED", "path": "Add https://mcp.ramp.com/mcp and authenticate through Ramp OAuth; use the demo endpoint for sample data. For custom clients/gateways, request redirect-URI allowlisting. Developer API clients are created in Ramp settings by an authorized customer/admin.", "plan_or_gate": "User role governs accessible data/actions; admins can manage employee MCP access. Custom clients/gateways require redirect-URI review/allowlisting; partner integrations require a separate launch checklist."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "BROAD", "details": "Ramp's REST Developer API covers transactions, cards, reimbursements, bills, vendors, users, departments and other finance workflows. OAuth scopes, customer access and rate limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "Ramp's hosted MCP is at https://mcp.ramp.com/mcp; a demo server is at https://demo-mcp.ramp.com/mcp. It supports read/analyze, approvals, employee expenses, card workflows and more. Employee tools respect personal permissions; company-wide spend/vendor/GL functions usually require admin or business-owner access. Custom client redirect URIs need allowlisting.", "search_scope": "Opened Ramp's official MCP guide/LLM reference plus Developer API quickstart/authentication and support material. The guide lists production/demo endpoints, permission differences, beta status and allowlisting; no Ramp account/client was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Production tools require a Ramp business/user role; broad company data is admin-gated, and custom clients need redirect-URI allowlisting.", "rationale": "Ramp documents a working hosted MCP and a Developer API. The demo server supports sample exploration, while production integration must be designed around per-user access, admin controls and OAuth review; no tenant/API call was performed."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://docs.ramp.com/developer-api/v1/ramp-mcp", "Ramp MCP — Ramp API docs", "official_docs", "Ramp's guide documents hosted production/demo MCP endpoints, beta status, read/write tools, admin/employee permission differences, employee access controls and redirect URI allowlisting for custom clients.", (0, 1)),
            src("api", "https://docs.ramp.com/developer-api/v1/introduction", "Ramp Developer API introduction", "official_api_docs", "Ramp publishes a REST Developer API for financial operations and data resources.", (0,)),
            src("auth", "https://docs.ramp.com/developer-api/v1/authorization", "Authorization - Ramp API docs", "official_auth_docs", "Ramp documents OAuth 2.0, client-credentials and authorization-code flows, required client ID/secret, scopes, and Bearer access tokens.", (0,)),
        ],
        "evidence": [
            ("description", "Ramp MCP provides natural-language access to finance/spend analysis and workflow actions over Ramp data.", "mcp", "supports", "The official MCP guide describes data and action categories."),
            ("auth", "Ramp MCP uses an authenticated user connection; Developer API integrations use OAuth credentials.", "mcp", "supports", "Setup/auth instructions for hosted MCP and Developer API."),
            ("self_serve", "Ramp publishes production and demo MCP endpoints; production access depends on a Ramp business/user role.", "mcp", "supports", "Official MCP guide prerequisites and demo path."),
            ("credential_access", "Ramp MCP inherits user permissions, and custom client redirect URIs require allowlisting.", "mcp", "supports", "Official access and custom-client sections."),
            ("api", "Ramp publishes a REST Developer API for finance workflows.", "api", "supports", "Official Developer API docs."),
            ("mcp", "Ramp operates production and demo hosted MCP endpoints.", "mcp", "supports", "The MCP guide names both URLs."),
            ("buildability", "Ramp documents demo, hosted production and Developer API paths but applies role/admin/redirect controls.", "mcp", "supports", "Official permissions and allowlisting sections."),
        ],
        "notes": "Ramp's MCP is beta and may change; demo data is distinct from production business access.",
        "extra_attempts": [{"url": "https://docs.ramp.com/developer-api/v1/authentication", "status": "NOT_FOUND", "note": "The guessed authentication route returned Page Not Found; the directly opened /authorization guide is the source used."}],
    },
    90: {
        "query": "PitchBook official API access Premium MCP SSO license Claude Academy",
        "description": "PitchBook provides proprietary private-capital-market data through a contracted REST API and a Premium hosted MCP integration for eligible licensed users.",
        "auth_status": "CONFIRMED", "auth_methods": ["Bearer/token", "API key", "Custom"],
        "self_serve_status": "PARTNER_OR_CONTACT_SALES",
        "self_serve_details": "PitchBook's REST API is a separate offering requiring a standalone contract and Direct Data team access. Premium MCP requires SSO and a seat-based, unlimited or trial PitchBook license; users without MCP access are directed to their account representative.",
        "credential_access": {"status": "GATED", "path": "For API, request a connection through PitchBook Direct Data/API team and receive an API key or auth token. For Premium MCP, use SSO through the Claude connector URL with an eligible PitchBook license.", "plan_or_gate": "Standalone API contract; Premium MCP SSO and eligible seat-based/unlimited/trial license. No PitchBook tenant, contract or license entitlement was checked."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "PitchBook's REST API at https://api.pitchbook.com provides relational company, investor, fund, deal and financing data. API access is contract-based and packaged across several endpoints; available data depends on the agreement."},
        "mcp": {"status": "AVAILABLE", "details": "PitchBook Premium's hosted MCP endpoint is https://premium.mcp.pitchbook.com/mcp and is accessed via SSO. The official Claude integration guide describes private-market company, investor, fund and deal research; an eligible PitchBook license is required and access may require an account representative.", "search_scope": "Opened PitchBook's official API-access help page and Anthropic's official Claude Academy PitchBook integration guide. These directly describe the contracted REST API and SSO MCP integration; no PitchBook license was available to test."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "API requires a standalone contract; MCP requires SSO and an eligible PitchBook license/entitlement.", "rationale": "PitchBook documents both API and MCP surfaces, but access is commercially gated and no public self-serve credential path was established. Build only after a customer confirms contract, license and data terms; no account or SSO was tested."},
        "confidence": "HIGH",
        "sources": [
            src("api", "https://pitchbook.com/help/PitchBook-api", "PitchBook API - PitchBook", "official_support", "PitchBook says its REST API is a separate offering requiring a standalone contract; base URL https://api.pitchbook.com; access is requested through Direct Data or Plugins & Apps, with API key/auth token provisioned by the team.", (0,)),
            src("mcp", "https://academy.claude.com/tutorials/using-pitchbook-for-investment-research", "Using PitchBook for investment research · Claude Academy", "official_docs", "Anthropic's official guide documents PitchBook Premium remote MCP at https://premium.mcp.pitchbook.com/mcp, SSO setup, eligible seat-based/unlimited/trial PitchBook license and account-representative escalation if access is absent.", (0,)),
        ],
        "evidence": [
            ("description", "PitchBook's API/MCP surfaces provide company, investor, fund and deal data for private-market research.", "api", "supports", "PitchBook API and Claude Premium integration docs describe these data domains."),
            ("auth", "PitchBook API credentials are provisioned as an API key/auth token; Premium MCP uses SSO.", "api", "supports", "PitchBook help describes API credentials; Claude guide describes SSO. SSO is not relabeled as OAuth."),
            ("self_serve", "PitchBook API requires a standalone contract; Premium MCP requires eligible license and SSO.", "api", "supports", "PitchBook and Claude official integration pages."),
            ("credential_access", "PitchBook API access is requested through Direct Data; MCP access requires an eligible license and may require a representative.", "mcp", "supports", "Official API and integration guides."),
            ("api", "PitchBook publishes a REST API at https://api.pitchbook.com for relational private-market data.", "api", "supports", "PitchBook's API help page."),
            ("mcp", "PitchBook Premium offers a hosted MCP endpoint available through SSO.", "mcp", "supports", "Official Claude Academy setup guide."),
            ("buildability", "PitchBook integrations are technically documented but depend on contracts, license eligibility and SSO.", "mcp", "supports", "Both official sources specify material access requirements."),
        ],
        "notes": "The Claude Academy source is official Anthropic product documentation for the PitchBook connector; it is not represented as PitchBook-authored API documentation.",
    },
    91: {
        "query": "Google Cloud NotebookLM Enterprise API authentication license sources official docs",
        "extra_queries": [{"query": 'site:docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise "MCP" OR "Model Context Protocol"', "depth": "2", "search_status": "SUCCESS", "lead_only": True, "note": "Targeted first-party search for a NotebookLM Enterprise MCP; results did not establish a product-specific MCP."}],
        "description": "NotebookLM Enterprise is Google's enterprise notebook product; Google Cloud documents a separate REST API surface for enterprise notebooks and sources, distinct from consumer NotebookLM.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token"],
        "self_serve_status": "ENTERPRISE_ONLY",
        "self_serve_details": "The API applies to NotebookLM Enterprise through Google Cloud/Gemini Enterprise licensing and project/IAM setup; consumer NotebookLM access does not imply API entitlement. Some API features are preview/Pre-GA and have product/region prerequisites.",
        "credential_access": {"status": "GATED", "path": "Enable the documented Google Cloud APIs for an eligible project, assign required IAM roles and authenticate with the Google Cloud OAuth access token shown in the official API examples (for example, gcloud auth print-access-token).", "plan_or_gate": "Requires an eligible Gemini Enterprise/NotebookLM Enterprise licensing arrangement, Google Cloud project and administrative setup; API feature status and region access may be preview-gated. No project/license/IAM access was checked."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "Google Cloud documents REST endpoints for NotebookLM Enterprise notebooks and notebook sources, with enterprise authentication/IAM and project configuration. This is not a public consumer NotebookLM API; specific operations and status may be preview-dependent."},
        "mcp": {"status": "UNKNOWN", "details": "No product-specific NotebookLM Enterprise MCP endpoint or entitlement was established in the official pages opened. Do not infer one from generic Google Cloud MCP services or consumer NotebookLM integrations.", "search_scope": "Opened Google Cloud NotebookLM Enterprise notebook/source API, setup and licensing documentation and ran a targeted first-party Google Cloud search for NotebookLM MCP/Model Context Protocol. The returned official materials did not establish a product-specific MCP; status remains UNKNOWN, not NO."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "NotebookLM Enterprise API requires eligible enterprise licensing, Cloud project/IAM provisioning and preview/product access; consumer NotebookLM is not the same API product.", "rationale": "Google Cloud documents REST operations for enterprise notebooks and sources. Implementation is possible for an entitled organization but cannot be assumed self-serve; no project, license, token or API call was tested."},
        "confidence": "HIGH",
        "sources": [
            src("api", "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks", "NotebookLM Enterprise API - Google Cloud", "official_api_docs", "Google Cloud documents REST operations for NotebookLM Enterprise notebooks, project/IAM configuration and enterprise credentials.", (0,)),
            src("sources", "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources", "Add and manage notebook data sources (API) - Google Cloud", "official_api_docs", "The API reference documents notebook-source management as a distinct enterprise REST resource and uses Google Cloud OAuth access tokens in Bearer Authorization headers.", (0,)),
            src("setup", "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm", "Set up NotebookLM Enterprise - Google Cloud", "official_docs", "Setup documentation describes Cloud project, licensing, API enablement and IAM prerequisites.", (0,)),
            src("licensing", "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-licensing", "Get licenses for Gemini Notebook Enterprise - Google Cloud", "official_pricing", "Google requires a Notebook Enterprise subscription/license for users; the official page describes free trial and paid subscription tiers and license assignment.", (0,)),
        ],
        "evidence": [
            ("description", "Google distinguishes NotebookLM Enterprise API resources from the consumer NotebookLM product.", "setup", "supports", "Enterprise setup and API reference identify the Cloud/enterprise product."),
            ("auth", "NotebookLM Enterprise REST examples use a Google Cloud OAuth access token in a Bearer Authorization header; project IAM permissions also apply.", "api", "supports", "The API example uses gcloud auth print-access-token in the Bearer header."),
            ("self_serve", "NotebookLM Enterprise API setup is tied to enterprise licensing, Cloud project and API enablement rather than consumer NotebookLM signup.", "setup", "supports", "Setup and licensing docs."),
            ("credential_access", "Google Cloud project IAM and API enablement are prerequisites for the enterprise API.", "setup", "supports", "First-party setup guide."),
            ("api", "Google Cloud publishes REST APIs for NotebookLM Enterprise notebooks and sources.", "api", "supports", "API and source reference pages."),
            ("buildability", "Enterprise REST integration is documented but depends on licensing, IAM and preview/product eligibility.", "setup", "supports", "Setup and licensing pages identify those constraints."),
        ],
        "notes": "Manifest display name is NotebookLM; this record specifically assesses Google Cloud's Notebook Enterprise API product documented under Gemini Notebook Enterprise, not consumer NotebookLM. No first-party product-specific MCP was established.",
        "extra_attempts": [{"url": "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebook-sources", "status": "NOT_FOUND", "note": "A guessed singular-route URL returned 404; the correct first-party source is /api-notebooks-sources."}],
    },
    93: {
        "query": "Fathom official API MCP docs API key pricing webhooks",
        "description": "Fathom is an AI meeting recorder and conversation-intelligence product with user-scoped REST API, webhooks and a hosted MCP connector.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "OAuth 2.0", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Fathom lists Free and paid plans and a user-scoped API key path; plan-specific feature entitlements may differ. The public docs do not establish identical API/MCP availability for every tenant/tier, so verify the actual account entitlement.",
        "credential_access": {"status": "RESTRICTED", "path": "Create/use a Fathom user API key from the account settings for direct API access; connect the hosted MCP and authorize the user. Public integrations may use OAuth.", "plan_or_gate": "API keys are user-scoped and inherit user access; account plan may affect features and data. No Fathom account or plan was checked."},
        "api": {"available": "YES", "types": ["REST", "Webhooks"], "breadth": "MODERATE", "details": "Fathom documents a REST API for meeting recordings, transcripts, summaries and related data plus webhook events for meeting content. User-scoped access, pagination/limits and plan entitlements apply."},
        "mcp": {"status": "AVAILABLE", "details": "Fathom offers an official hosted MCP at https://api.fathom.ai/mcp for meeting data and AI assistants including ChatGPT and Claude. Setup requires authentication; tool access inherits the user/account permissions.", "search_scope": "Opened Fathom's first-party MCP guide, API overview, quickstart, webhooks and pricing pages. These document hosted endpoint, user-scoped API key/OAuth paths and meeting content; no Fathom account was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires user-authorized account credentials; plan entitlements and user-level data permissions may constrain meeting content.", "rationale": "Fathom documents a REST API, webhooks and hosted MCP for meeting workflows. Use user-scoped credentials and confirm tenant plan/consent; no API call, webhook registration or MCP session was performed."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://developers.fathom.ai/mcp-docs", "Overview - Fathom API", "official_docs", "The first-party MCP guide states Fathom offers an official MCP server and gives the endpoint https://api.fathom.ai/mcp for other compatible tools.", (0,)),
            src("api", "https://developers.fathom.ai/api-overview", "Fathom API overview", "official_api_docs", "Fathom documents REST API resources for meeting recordings and related content, with user-scoped API access.", (0,)),
            src("auth", "https://developers.fathom.ai/quickstart", "Fathom API quickstart", "official_auth_docs", "The quickstart documents API-key authorization and setup for API use.", (0,)),
            src("webhooks", "https://developers.fathom.ai/webhooks", "Fathom webhooks", "official_api_docs", "Fathom documents event/webhook delivery for meeting content workflows.", (0,)),
            src("pricing", "https://www.fathom.ai/pricing", "Fathom Pricing", "official_pricing", "The official pricing page lists free individual access and paid individual/team plans; tier features differ.", (0,)),
        ],
        "evidence": [
            ("description", "Fathom's developer materials cover meeting API data and an official hosted MCP connector.", "mcp", "supports", "Official MCP guide and API overview."),
            ("auth", "Fathom documents user-scoped API-key access and OAuth for public integrations/MCP clients.", "auth", "supports", "Quickstart and MCP docs."),
            ("self_serve", "Fathom offers Free and paid plans; account plan may affect available data/features.", "pricing", "supports", "Official pricing and developer plan caveat."),
            ("credential_access", "Fathom API access uses a user-scoped key; the hosted MCP requires user authorization.", "auth", "supports", "Official quickstart and MCP setup."),
            ("api", "Fathom documents REST meeting endpoints and webhook event delivery.", "api", "supports", "API overview and webhook guide."),
            ("mcp", "Fathom operates https://api.fathom.ai/mcp as its official MCP endpoint.", "mcp", "supports", "First-party MCP setup guide."),
            ("buildability", "Fathom documents API/MCP/webhooks but requires user consent and tenant plan/permission checks.", "mcp", "supports", "Official setup and API docs."),
        ],
        "notes": "Fathom here is the meeting-recording product indicated by fathom.video, not Fathom Analytics.",
    },
    94: {
        "query": "Consensus official MCP API plans API key documentation",
        "description": "Consensus is an academic research search product with a REST API and hosted MCP server for searching peer-reviewed literature.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "Bearer/token"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Consensus provides self-serve API keys on all plans and OAuth-based MCP; free and paid plans have different calls, papers-per-request and pagination limits. Enterprise custom call volumes/rates require contacting sales.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create an API key in Consensus' API & MCP Dashboard, or connect the hosted MCP and sign in to a Consensus account; Enterprise can use a Bearer API key.", "plan_or_gate": "API and MCP share the plan's monthly usage pool. Free plan is limited; paid plans add pagination/full-text features; Enterprise custom access is sales-gated."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "Consensus REST API supports literature search and paper retrieval, with plan-dependent page size, pagination, full-text excerpts and monthly call quotas. Search filters are available across plans; one call is charged per 100 papers returned, rounded up."},
        "mcp": {"status": "AVAILABLE", "details": "Hosted MCP at https://mcp.consensus.app/mcp. Normal plan access uses a connected Consensus account; the service is also usable without an account at reduced limits. Enterprise customers can use a Bearer API key. MCP and API share plan allowances.", "search_scope": "Opened Consensus' first-party API, MCP setup/feature, API-plan and MCP-plan documentation. These document hosted endpoint, auth, shared quota and plan differences; no Consensus account/API key was used."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Plan-dependent usage/pagination limits are shared between API and MCP; Enterprise-scale access requires sales.", "rationale": "Consensus documents self-serve REST and hosted MCP integrations with clear plan quotas. Build within rate/credit limits and confirm tier-specific features; no account or query was tested."},
        "confidence": "HIGH",
        "sources": [
            src("api", "https://docs.consensus.app/core-features/api", "Consensus API", "official_api_docs", "The first-party API reference documents REST literature search and paper result resources.", (0,)),
            src("mcp", "https://docs.consensus.app/core-features/mcp", "Consensus MCP", "official_docs", "The MCP guide documents https://mcp.consensus.app/mcp, account sign-in, reduced no-account limits, search capability and plan-dependent quotas.", (0,)),
            src("plans", "https://docs.consensus.app/api-plans-and-access", "API plans and access - Consensus", "official_pricing", "The API is self-serve across plans; keys are created in the dashboard, API and MCP share a monthly pool, and limits vary by plan. Enterprise custom access requires contacting sales.", (0,)),
            src("mcpplans", "https://docs.consensus.app/mcp-plans-and-access", "MCP plans and access - Consensus", "official_pricing", "MCP documentation maps plan result limits to available search features; no-account use is limited separately from paid/account entitlements.", (0,)),
        ],
        "evidence": [
            ("description", "Consensus provides academic-paper search through a REST API and hosted MCP.", "api", "supports", "Official API and MCP docs describe the research use case."),
            ("auth", "Consensus API uses an x-api-key; hosted MCP connects a Consensus account and Enterprise supports Bearer-key authentication.", "plans", "supports", "API key setup and Enterprise authentication are documented; the MCP guide requires a Consensus sign-in for standard account limits."),
            ("self_serve", "Consensus API keys are self-serve across plans, with plan-dependent quotas and enterprise sales options.", "plans", "supports", "Plan table and dashboard instructions."),
            ("credential_access", "Users create a key in the API & MCP dashboard; API and MCP draw from one usage pool.", "plans", "supports", "Key setup and shared-usage section."),
            ("api", "Consensus offers REST search and paper retrieval with plan-dependent quotas and pagination.", "api", "supports", "Official API reference and plan page."),
            ("mcp", "Consensus hosts MCP at https://mcp.consensus.app/mcp with OAuth and plan-dependent result limits.", "mcp", "supports", "Official MCP guide."),
            ("buildability", "The documented integration is buildable within self-serve quotas, with enterprise access requiring sales.", "plans", "supports", "Official plan and API/MCP pages."),
        ],
        "notes": "Unauthenticated limited MCP use and signed-in account-plan API/MCP use are separate access modes.",
    },
    95: {
        "query": "Reducto official REST API MCP server API keys pricing credits docs",
        "description": "Reducto is a document-processing API platform with REST/SDK interfaces and official local and hosted MCP servers for parsing, extraction, classification, splitting and editing.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "Bearer/token", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Reducto documents free account signup and self-generated API keys, with credit-based usage and plan/contract rates. Hosted MCP tools require credentials; processing features incur account usage/credits.",
        "credential_access": {"status": "SELF_SERVE", "path": "Create an API key in Reducto Studio or authenticate the local MCP through its browser login/device flow; hosted MCP accepts the key as a Bearer token.", "plan_or_gate": "Free signup is documented; usage is credit-metered and contract rates may differ. Hosted MCP can read public URLs but not local files; the local server supports local file uploads."},
        "api": {"available": "YES", "types": ["REST", "SDK", "CLI"], "breadth": "MODERATE", "details": "Reducto exposes REST endpoints and Python, Node.js and Go SDKs plus a CLI for document upload, parse, extract, split, classify and edit workflows. Usage is credit-based; regional/on-prem base URLs may differ."},
        "mcp": {"status": "AVAILABLE", "details": "Official hosted server at https://mcp.reducto.ai/mcp and a local `uvx mcp-server-reducto` server. Hosted server accepts Bearer API keys and public URLs; local server supports local files and OAuth/device-code login or environment key. Tools include upload, parse, extract, split, classify and edit.", "search_scope": "Opened Reducto's first-party MCP server guide, API quickstart, official GitHub MCP repository and pricing/credits docs. The direct documentation specifies hosted/local modes and credentials; no Reducto account/key or document-processing call was used."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires Reducto account/key and credit budget; hosted MCP cannot read local files, which require local MCP/CLI handling.", "rationale": "Reducto documents a free signup path, REST/SDK/CLI, local/hosted MCP and core document workflows. Choose the server mode to match input locality and verify current credit/contract rates; no live processing was executed."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://docs.reducto.ai/mcp-server", "Reducto MCP Server - Reducto", "official_docs", "The guide documents hosted endpoint https://mcp.reducto.ai/mcp, local `uvx` server, Bearer key or browser login, local-vs-public URL differences, and document tools.", (0, 1)),
            src("api", "https://docs.reducto.ai/quickstart", "API Quickstart - Reducto", "official_api_docs", "The quickstart documents REST base URL, Bearer API key, free account/key setup, SDKs, CLI, and parse/extract/split/classify/edit API workflows.", (0,)),
            src("github", "https://github.com/reductoai/mcp-server-reducto", "Reducto MCP Server · GitHub", "official_github", "The official Reducto repository documents the MCP package, hosted/local options, environment variables and API key configuration.", (0,)),
            src("pricing", "https://reducto.ai/pricing", "Reducto Pricing", "official_pricing", "Reducto lists credit-based usage and plan/contract rates; exact costs can differ by contract and effective date.", (0,)),
        ],
        "evidence": [
            ("description", "Reducto documents document-processing APIs and an official MCP server with parse/extract/classify/split/edit tools.", "mcp", "supports", "The MCP guide and API quickstart enumerate tool types."),
            ("auth", "Reducto API/MCP uses a Bearer API key or supported browser login/device flow.", "mcp", "supports", "Hosted and local authentication steps."),
            ("self_serve", "Reducto documents free account signup and API-key creation; continued processing is credit-metered.", "api", "supports", "Quickstart prerequisites and pricing page."),
            ("credential_access", "Users can create a key in Studio or use browser login for the local MCP; hosted requests use a Bearer key.", "mcp", "supports", "The MCP guide documents both credential paths."),
            ("api", "Reducto provides REST, SDK and CLI document-processing interfaces.", "api", "supports", "Quickstart lists endpoints, SDKs and CLI."),
            ("mcp", "Reducto offers hosted and local official MCP servers with distinct local-file capabilities.", "mcp", "supports", "The guide's hosted-vs-local comparison."),
            ("buildability", "Reducto documents local and hosted implementation paths but requires account usage/credit management and mode selection.", "mcp", "supports", "Setup and limitations are explicit."),
        ],
        "notes": "This follow-up directly inspected Reducto's current MCP guide after earlier MCP configuration details were unresolved. No calls to the Reducto service were made.",
    },
    96: {
        "query": "Devin official remote MCP API v3 authentication pricing docs",
        "description": "Devin is an AI software-engineering platform with a v3 REST API and an authenticated hosted MCP server for repository and platform-management workflows.",
        "auth_status": "CONFIRMED", "auth_methods": ["Bearer/token", "API key"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "API/MCP access requires a Devin account and appropriate organization/service-user permissions. Enterprise API endpoints require Enterprise entitlements; enterprise PAT availability can be controlled by admin policy. Current pricing and feature access vary by plan.",
        "credential_access": {"status": "RESTRICTED", "path": "Create a v3 service user/API key in Devin settings for automation or a Personal Access Token for user-scoped calls; send as Bearer auth to API/MCP. Assign the service user a least-privilege role.", "plan_or_gate": "Service-user/API-key management requires the proper organization/enterprise permissions. Enterprise endpoints and some PAT policies are gated by enterprise plan/admin settings; legacy v1/v2 keys are deprecated for new API work."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "Devin API v3 is REST with organization-scoped endpoints for sessions, knowledge, playbooks and secrets plus Enterprise endpoints for cross-organization analytics, audit, user, billing and infrastructure workflows. Endpoint access is role/permission-gated."},
        "mcp": {"status": "AVAILABLE", "details": "Devin's authenticated MCP is hosted at https://mcp.devin.ai/mcp. Official docs describe repository documentation/search plus session, playbook, knowledge and scheduling tools; authentication uses v3 service-user keys or Personal Access Tokens with organization/enterprise scope and RBAC.", "search_scope": "Opened Devin's official MCP guide, API v3 overview, authentication, pricing and service-user documentation. These identify hosted MCP, API bases, token principals and permissions; no Devin account/service-user was provisioned."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires Devin account, service-user/PAT credentials and explicit RBAC; enterprise-wide endpoints require enterprise access.", "rationale": "Devin documents REST v3 and authenticated MCP for automation. Use v3 credentials and least-privilege roles, avoid deprecated legacy keys and confirm plan-level features; no session or MCP tool was executed."},
        "confidence": "HIGH",
        "sources": [
            src("mcp", "https://docs.devin.ai/work-with-devin/devin-mcp", "Devin MCP - Devin Docs", "official_docs", "The official MCP guide describes authenticated remote server https://mcp.devin.ai/mcp, API-key authentication, service-user/PAT token types and platform/repository tools.", (0, 1)),
            src("api", "https://docs.devin.ai/api-reference/overview", "API Overview - Devin Docs", "official_api_docs", "Devin API v3 has organization and enterprise REST scopes with sessions, knowledge, playbooks, secrets, analytics, audit, users and billing resources.", (0,)),
            src("auth", "https://docs.devin.ai/api-reference/authentication", "Authentication - Devin Docs", "official_auth_docs", "The docs distinguish service-user API keys and human PATs, require Bearer tokens, and describe RBAC, account-level key permissions and enterprise policies.", (0,)),
            src("pricing", "https://devin.ai/pricing", "Devin Pricing", "official_pricing", "Devin's pricing page describes plan tiers and product-feature availability; entitlement details must be checked against the account.", (0,)),
        ],
        "evidence": [
            ("description", "Devin provides a v3 REST API and authenticated remote MCP for platform/repository workflows.", "api", "supports", "Official API overview and MCP guide."),
            ("auth", "Devin v3 API/MCP accepts Bearer service-user keys or PATs, with identity-specific permissions.", "auth", "supports", "Authentication guide documents both principals."),
            ("self_serve", "API/MCP use requires Devin account and role permissions; enterprise scope is enterprise-gated.", "api", "supports", "API overview says enterprise endpoints are for enterprise customers."),
            ("credential_access", "Service users and PATs are created under settings with role/permission controls; enterprise PAT policy may restrict access.", "auth", "supports", "Official authentication and token-management docs."),
            ("api", "Devin API v3 exposes REST organization and enterprise resource surfaces.", "api", "supports", "Official API overview."),
            ("mcp", "Devin documents the hosted authenticated MCP endpoint https://mcp.devin.ai/mcp.", "mcp", "supports", "Official MCP guide."),
            ("buildability", "Devin integration is documented but depends on API v3 roles, credential management and account/enterprise scope.", "auth", "supports", "Authentication and API scope requirements."),
        ],
        "notes": "Use API v3 service-user credentials for automation; v1/v2 legacy keys are deprecated for new API work.",
    },
    97: {
        "query": "Higgsfield official MCP REST API CLI developer account pricing credits",
        "description": "Higgsfield is an AI image/video generation platform with two distinct programmatic surfaces: a prepaid-balance REST API and account-credit MCP/CLI connections.",
        "auth_status": "CONFIRMED", "auth_methods": ["API key", "Bearer/token", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "The separate Higgsfield API uses its own developer account, key and prepaid USD balance (minimum top-up $5); no web subscription is required. MCP/CLI instead connect to an existing Higgsfield account via OAuth and consume plan credits; web-only free/unlimited access does not apply to automated tools.",
        "credential_access": {"status": "RESTRICTED", "path": "For REST, create API key ID/secret in the Higgsfield Console and send Authorization: Key ID:SECRET server-side. For MCP/CLI, sign in to the existing Higgsfield account through OAuth; no API key is used for MCP.", "plan_or_gate": "REST API requires a separate API account/payment method/prepaid balance. MCP/CLI use account plan credits; generations consume credits at standard rates even when web UI generations are free/unlimited. Model access may be account-restricted."},
        "api": {"available": "YES", "types": ["REST", "SDK", "Webhooks"], "breadth": "MODERATE", "details": "Higgsfield API supports asynchronous image/video generation through REST and official Python/TypeScript SDKs, request status/cancel endpoints and webhooks. It is metered from a separate prepaid USD balance; failed generations are refunded and output retention is time-limited."},
        "mcp": {"status": "AVAILABLE", "details": "Official hosted MCP at https://mcp.higgsfield.ai/mcp connects an AI agent to the user's existing Higgsfield account by OAuth, without an API key. It supports image/video/character/audio generation and credit-balance checks; MCP/CLI consume plan credits, unlike the separate REST API balance.", "search_scope": "Opened Higgsfield's first-party MCP/API/CLI help articles, API quickstart/authentication, pricing and official CLI repository documentation. These distinguish the two products, credentials and billing; no account, API key or generation was used."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Must choose between distinct API and MCP/CLI accounts and billing; REST secrets are server-only and MCP/CLI consume plan credits rather than web-only unlimited entitlements.", "rationale": "Higgsfield documents REST, SDK, webhooks, MCP and CLI surfaces. Build with server-side key storage, prepaid-balance controls, async status handling and separate account/billing assumptions; no live generation was run."},
        "confidence": "HIGH",
        "sources": [
            src("api", "https://higgsfield.ai/creator-hub/help-center/integrations/what-is-the-higgsfield-api", "What Is the Higgsfield API and How Do I Get Started", "official_support", "Higgsfield explains that API is separate from web plan, uses a developer account/key and prepaid USD balance, offers REST/SDKs/webhooks and $5 minimum top-up, and is distinct from MCP/CLI.", (0,)),
            src("mcp", "https://higgsfield.ai/creator-hub/help-center/integrations/what-is-higgsfield-mcp", "What Is Higgsfield MCP and How It Differs", "official_support", "Higgsfield documents https://mcp.higgsfield.ai/mcp, OAuth/no API key, existing account/plan credits and the restriction that free/unlimited web generations do not apply through MCP.", (0,)),
            src("cli", "https://higgsfield.ai/creator-hub/help-center/integrations/how-do-i-access-higgsfield-via-cli", "How to Access Higgsfield via CLI and Skills", "official_support", "The official CLI setup uses Higgsfield account login, no API key, and plan credits; CLI/Skills are distinct from the REST API.", (0,)),
            src("quickstart", "https://docs.higgsfield.ai/docs/quickstart", "Quickstart - Higgsfield API Docs", "official_api_docs", "The API quickstart documents key ID/secret, Authorization header, async request lifecycle and status/cancel URLs.", (0,)),
            src("auth", "https://docs.higgsfield.ai/docs/authentication", "Authentication - Higgsfield API Docs", "official_auth_docs", "Higgsfield API credentials are a key ID and secret sent as Authorization: Key ID:SECRET; credentials must remain server-side.", (0,)),
        ],
        "evidence": [
            ("description", "Higgsfield distinguishes a prepaid-balance REST API from MCP/CLI connections to an existing creator account.", "api", "supports", "The first-party API help page has a direct API-versus-MCP/CLI comparison."),
            ("auth", "REST API uses a key ID/secret; MCP/CLI use OAuth/account sign-in without an API key.", "mcp", "supports", "Official API and MCP/CLI help pages."),
            ("self_serve", "REST signup is separate from the web plan and requires a prepaid balance; MCP/CLI use existing account plan credits.", "api", "supports", "Higgsfield's API-versus-plan explanation."),
            ("credential_access", "API credentials are generated in the Console and must remain server-side; MCP uses OAuth and no API key.", "auth", "supports", "Official auth and MCP docs."),
            ("api", "Higgsfield publishes REST generation/status operations, SDKs and webhooks.", "quickstart", "supports", "API quickstart and API product help."),
            ("mcp", "Higgsfield operates a hosted OAuth MCP endpoint at https://mcp.higgsfield.ai/mcp.", "mcp", "supports", "Official MCP article names endpoint and auth."),
            ("buildability", "Higgsfield has buildable API/MCP/CLI paths with distinct billing, credentials and asynchronous generation constraints.", "api", "supports", "First-party product and quickstart docs."),
        ],
        "notes": "Do not transfer web subscription credits/free/unlimited claims to the separate API; MCP/CLI and REST are distinct products.",
    },
    98: {
        "query": "Mermaid CLI official GitHub MCP server local rendering API npm",
        "extra_queries": [{"query": 'site:github.com/mermaid-js/mermaid-cli OR site:mermaid.js.org/ "MCP" "Mermaid CLI"', "depth": "2", "search_status": "SUCCESS", "lead_only": True, "note": "Targeted first-party search for Mermaid CLI MCP ownership; snippets were discovery only and not claim evidence."}],
        "description": "Mermaid CLI is an open-source local command-line renderer that converts Mermaid diagram source into image/vector/document outputs.",
        "auth_status": "CONFIRMED", "auth_methods": ["Other"],
        "self_serve_status": "SELF_SERVE",
        "self_serve_details": "The official Mermaid CLI is an open-source npm/GitHub tool with local installation; its documented render workflow has no vendor account or paid plan prerequisite. Node.js and local runtime dependencies are required.",
        "credential_access": {"status": "SELF_SERVE", "path": "Install `@mermaid-js/mermaid-cli` via npm/npx and run the CLI against local Mermaid source; no vendor API key is shown in the documented local render path.", "plan_or_gate": "No vendor account/license gate is documented for the open-source local renderer. Node.js and browser/Puppeteer runtime requirements apply; no package was installed or executed in this research step."},
        "api": {"available": "YES", "types": ["CLI"], "breadth": "NARROW", "details": "Mermaid CLI is a local command-line interface to render Mermaid syntax to SVG/PNG/PDF and related formats. This record does not assert a hosted Mermaid product API; the CLI is the documented programmatic surface."},
        "mcp": {"status": "NOT_FOUND", "details": "No first-party Mermaid CLI MCP server is documented. Community wrappers that call Mermaid CLI surfaced separately and are not the named official product.", "search_scope": "Assessment target is the named official Mermaid CLI product. Inspected its repository README and ran a targeted first-party MCP search across the repository and official docs. Community wrappers are third-party projects and were excluded. The retrieved first-party materials did not identify an official Mermaid CLI MCP offering."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Local Node.js and the CLI's browser/Puppeteer runtime are required; this is not a hosted SaaS/API or first-party MCP service.", "rationale": "The open-source CLI has documented local install/render commands and supports standard diagram output formats. Build a local process wrapper if needed; no installation or rendering was executed here."},
        "confidence": "HIGH",
        "sources": [
            src("github", "https://github.com/mermaid-js/mermaid-cli", "mermaid-js/mermaid-cli · GitHub", "official_github", "The official repository describes Mermaid CLI as a command-line renderer and publishes installation, command usage, output formats and runtime dependencies; no product login is part of local rendering.", (0,)),
        ],
        "evidence": [
            ("description", "Mermaid CLI is the official local renderer for Mermaid diagrams.", "github", "supports", "Repository title and README describe a command-line renderer."),
            ("auth", "The documented local Mermaid CLI render command uses local source files and does not require a vendor service credential.", "github", "supports", "README setup and usage are local npm/CLI commands."),
            ("self_serve", "The Mermaid CLI is an open-source local npm package with no vendor subscription step in its setup instructions.", "github", "supports", "Official repository installation path."),
            ("credential_access", "The CLI can be installed and run locally; no vendor API credential is documented for rendering.", "github", "supports", "Official local install/use instructions."),
            ("api", "Mermaid's documented programmatic surface for this app is a local CLI, not a hosted REST API.", "github", "supports", "The official repository documents a local command-line renderer."),
            ("mcp", "No first-party Mermaid CLI MCP product was identified in the official repository/docs material reviewed.", "github", "supports", "The official repository describes the CLI; third-party/community wrappers are separately owned."),
            ("buildability", "The local CLI is buildable with Node.js and the documented rendering runtime, without a vendor account.", "github", "supports", "Official install and usage guide."),
        ],
        "notes": "MCP NOT_FOUND applies to the official Mermaid CLI product, not to every community wrapper that invokes it.",
        "extra_attempts": [{"url": "https://mermaid.js.org/ecosystem/mermaid-cli.html", "status": "NOT_FOUND", "note": "Direct page fetch returned 404; the failed URL is not retained as evidence."}],
    },
    99: {
        "query": "TranscriptAPI official REST API MCP OAuth pricing 100 free credits $5 plan",
        "description": "The manifest's “YouTube Transcript” entry maps to TranscriptAPI, a hosted REST/MCP service for YouTube transcripts, video search, channel data and playlists.",
        "auth_status": "CONFIRMED", "auth_methods": ["Bearer/token", "API key", "OAuth 2.0"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "TranscriptAPI offers 100 free credits without a card. Its homepage lists a $5/month plan and an annual plan billed at $54/year ($4.50/month), each with 1,000 monthly credits; MCP calls share usage/credit rules with REST. Pricing is shown on the homepage rather than a separate /pricing route.",
        "credential_access": {"status": "SELF_SERVE", "path": "Sign up for TranscriptAPI and create an API key in the dashboard, or authorize a supported MCP client with OAuth/DCR; ChatGPT static OAuth clients require generated client credentials.", "plan_or_gate": "Free tier starts with 100 credits. Paid successful operations consume credits; the REST API and MCP share the account/credit allowance. Some MCP clients need OAuth or explicit API key configuration."},
        "api": {"available": "YES", "types": ["REST"], "breadth": "MODERATE", "details": "TranscriptAPI exposes REST v2 endpoints for transcripts, metadata, video search, channel resolution/info/search/videos and playlists. Many calls consume credits, some endpoints are free, and plan-based rate limits apply."},
        "mcp": {"status": "AVAILABLE", "details": "Hosted MCP at https://transcriptapi.com/mcp with 12 documented tools for transcripts, metadata, YouTube search, channels and playlists. Supports OAuth 2.1/DCR or static OAuth client credentials and API-key Bearer auth; MCP calls use the same credits as API calls. The MCP guide states 200 requests/minute across REST and MCP, while the REST reference states 300/minute; preserve the discrepancy rather than silently reconciling it.", "search_scope": "Opened TranscriptAPI's official homepage/pricing section, REST API reference and MCP setup/tool docs. These document endpoint, auth, free credits, paid plans, shared credit model and tool list; no account, key or transcript call was used."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "Requires an account/key or OAuth grant, consumes monthly credits on paid endpoints, and rate limits vary by billing tier.", "rationale": "TranscriptAPI documents self-serve access, REST v2 and hosted MCP with clear auth and usage. Implement with error/rate handling and confirm billing limits; no live transcript operation was run."},
        "confidence": "HIGH",
        "sources": [
            src("home", "https://transcriptapi.com/", "YouTube Transcript API with Search, Channels & Playlists | TranscriptAPI", "official_product", "The homepage pricing section documents 100 free credits without a card and $5/month or $54/year plans with 1,000 monthly credits; it also displays different monthly versus annual rate limits.", (7, 8)),
            src("api", "https://transcriptapi.com/docs/api/", "YouTube Transcript API Reference | TranscriptAPI.com", "official_api_docs", "The API reference gives base URL https://transcriptapi.com/api/v2, endpoint catalog, Bearer API-key authentication, per-endpoint credit costs and a stated 300-requests/minute rate limit.", (0, 1, 2, 3, 4, 5, 6)),
            src("mcp", "https://transcriptapi.com/docs/mcp/", "MCP (Model Context Protocol) | TranscriptAPI.com", "official_docs", "The MCP guide documents https://transcriptapi.com/mcp, OAuth 2.1 with DCR/static registration, API-key Bearer auth, 12 tools, shared REST/MCP credits and a stated 200-requests/minute limit.", (0, 1, 2, 3)),
        ],
        "evidence": [
            ("description", "TranscriptAPI provides YouTube transcript, search, channel and playlist workflows through REST API and MCP.", "api", "supports", "The REST API and MCP documentation list transcript, search, channel and playlist workflows."),
            ("auth", "REST uses a Bearer API key; hosted MCP supports OAuth 2.1/DCR or API-key authentication.", "mcp", "supports", "Official MCP and API auth sections."),
            ("self_serve", "TranscriptAPI offers 100 free credits and paid monthly/annual plans with 1,000 credits per month, priced at $5/month or $54/year.", "home", "supports", "Official homepage pricing section in directly retrieved chunks 7 and 8."),
            ("credential_access", "Users can create dashboard keys or authorize an MCP OAuth connection; API and MCP draw from the account's credits.", "mcp", "supports", "Setup and credit sections."),
            ("api", "TranscriptAPI's REST v2 covers transcripts, search, channels and playlists with per-call credit costs.", "api", "supports", "Official API endpoint table."),
            ("mcp", "TranscriptAPI hosts MCP at https://transcriptapi.com/mcp and documents 12 tools with OAuth and API-key paths.", "mcp", "supports", "Official MCP guide."),
            ("api", "TranscriptAPI's REST reference states a 300-requests-per-minute rate limit.", "api", "supports", "Official REST reference rate-limit statement."),
            ("mcp", "TranscriptAPI's MCP guide states a 200-requests-per-minute limit shared across REST and MCP.", "mcp", "supports", "Official MCP page rate-limit statement; this differs from the REST reference."),
            ("buildability", "The documented API/MCP is self-serve but credit/rate-limited and requires account authorization.", "mcp", "supports", "Official setup, auth and pricing sections; rate-limit statements conflict by documentation surface."),
        ],
        "conflicts": [{"field": "api", "summary": "TranscriptAPI's official REST reference states 300 requests/minute, while the MCP documentation says 200 requests/minute across REST and MCP; the homepage pricing display also shows 200 RPM for Monthly and 300 RPM for Annual.", "resolution": "Retain the exact surface/tier statements without choosing one global cap. Confirm the applicable limit for the account and plan before implementation; use the stricter documented 200 RPM until clarified."}],
        "notes": "Canonical manifest display name remains “YouTube Transcript”; TranscriptAPI is the first-party service brand. The documented rate limits conflict across REST, MCP and pricing-tier text and are preserved separately; the separate /pricing route failure is retained only in the attempt trace.",
        "extra_attempts": [{"url": "https://transcriptapi.com/pricing", "status": "NOT_FOUND", "note": "The route returned Not Found; pricing was inspected on the official homepage pricing section."}],
    },
    100: {
        "query": "Grain official MCP API pricing OAuth Basic MCP Advanced MCP API version",
        "description": "Grain is an AI meeting-recording/notetaking product with a public REST API, webhooks and a first-party hosted MCP connection for meeting/workspace data.",
        "auth_status": "CONFIRMED", "auth_methods": ["OAuth 2.0", "Bearer/token", "API key"],
        "self_serve_status": "SELF_SERVE_WITH_RESTRICTIONS",
        "self_serve_details": "Grain pricing advertises Basic MCP on Free, Personal API on Starter ($15/seat/month annually or $19 monthly), and Workspace API plus Advanced MCP on Business ($29 annually or $39 monthly); Enterprise pricing is custom. The support article says Free does not include API access and workspace tokens require admin/Business+ access.",
        "credential_access": {"status": "RESTRICTED", "path": "API: create a PAT for personal access, a WAT from workspace settings as an admin, or an OAuth2 integration. MCP: Grain's release note gives the hosted URL https://api.grain.com/_/mcp; directly accessible release/pricing materials establish availability but the detailed MCP auth flow could not be inspected in the current developer docs.", "plan_or_gate": "Personal API is Starter+; Workspace API/WAT requires Business or Enterprise and admin access. Pricing lists Basic MCP on Free and Advanced MCP on Business/Enterprise. Version docs conflict: developer docs label 2026-10-01 current while the support API article labels 2025-10-31 current; confirm the required header with Grain."},
        "api": {"available": "YES", "types": ["REST", "Webhooks"], "breadth": "MODERATE", "details": "Grain's public REST API covers recordings, transcripts, AI notes/action items, participants, tags, teams, meeting types, uploads, sharing and related events; webhooks notify downstream systems of recording/clip changes. API requires a Public-Api-Version header, but current-version status conflicts between official developer and support pages."},
        "mcp": {"status": "AVAILABLE", "details": "Grain announced its official hosted MCP at https://api.grain.com/_/mcp and says the MCP is available for all users; current pricing labels Basic MCP on Free and Advanced MCP on Business/Enterprise. The release note documents setup but the inaccessible detailed MCP page prevented verification of auth/tool-level entitlements; do not infer those from REST auth.", "search_scope": "Opened Grain's first-party MCP release note, pricing page, public API support article, developer overview/authentication/version docs. The developer MCP route redirected to API overview and the `.html` MCP page was AccessDenied; the official release note confirms endpoint/availability, while exact MCP auth/tool entitlements remain unverified. No Grain workspace was connected."},
        "buildability": {"verdict": "BUILDABLE_WITH_CONSTRAINTS", "blocker": "API is plan-gated; workspace-wide tokens require admin/Business+, MCP detail page was inaccessible, and official API version documentation conflicts.", "rationale": "Grain documents usable REST/API/webhook and hosted MCP surfaces, but production code must confirm plan and header version and the accessible MCP technical setup is incomplete. No token, workspace or MCP session was tested."},
        "confidence": "MEDIUM",
        "sources": [
            src("release", "https://grain.com/release-note/06-18-2025", "Official Grain MCP Server - Grain release note", "official_product", "Grain announces an official MCP server, says it is available for all users, gives endpoint https://api.grain.com/_/mcp and an mcp-remote setup snippet.", (0,)),
            src("pricing", "https://grain.com/pricing", "Pricing | Grain", "official_pricing", "The pricing page lists Basic MCP on Free, Personal API on Starter, Workspace API and Advanced MCP on Business, and custom Enterprise pricing.", (0, 1)),
            src("support", "https://support.grain.com/en/articles/15507288-grain-api", "Grain API | Grain", "official_support", "Grain support docs describe REST API/webhooks, PAT/WAT/OAuth2, Starter+ personal API, Business/Enterprise admin WAT access, 300 requests/minute and claim 2025-10-31 is current.", (0,)),
            src("overview", "https://developers.grain.com/overview.html", "Overview — Grain Developers", "official_api_docs", "Developer overview shows bearer PAT request with Public-Api-Version 2026-10-01 and links authentication, versions, rate limits and endpoints.", (0,)),
            src("versions", "https://developers.grain.com/versions.html", "Versions — Grain Developers", "official_api_docs", "Developer versions page labels 2026-10-01 current and 2025-10-31 deprecated, in conflict with the support article's current-version statement.", (0,)),
        ],
        "evidence": [
            ("description", "Grain describes meeting-recording/API workflows and an official hosted MCP for meeting data.", "release", "supports", "Official release note names meetings, notes, transcripts, deals and scorecards."),
            ("auth", "Grain REST API documents PAT, WAT and OAuth2 authentication; detailed MCP auth could not be verified from the accessible setup sources.", "support", "supports", "Support article documents three API auth methods."),
            ("self_serve", "Grain pricing lists Basic MCP on Free, Personal API on Starter and Workspace API/Advanced MCP on Business, with Enterprise custom pricing.", "pricing", "supports", "Pricing feature matrix."),
            ("credential_access", "Grain API access is plan- and role-gated: personal API Starter+, workspace API Business/Enterprise and admin-generated WAT.", "support", "supports", "Support API article states plan/role requirements."),
            ("api", "Grain public API covers meeting data and webhooks; its version header requirement is documented but current-version labels conflict.", "support", "supports", "Support article describes data/webhooks/version header."),
            ("mcp", "Grain's official release note identifies hosted MCP URL https://api.grain.com/_/mcp and advertises availability; pricing differentiates Basic and Advanced MCP.", "release", "supports", "Release note endpoint plus pricing feature matrix."),
            ("api", "The developer versions page calls 2026-10-01 current and 2025-10-31 deprecated.", "versions", "supports", "Official versions table."),
            ("api", "The Grain support API article calls 2025-10-31 the current version, contradicting the developer versions page.", "support", "contradicts", "Official support page's current version statement."),
            ("buildability", "Grain integration requires plan/role checks, accessible MCP setup details are incomplete, and official version status is contradictory.", "support", "supports", "Support and developer documentation."),
        ],
        "conflicts": [{"field": "api", "summary": "The official developer versions page (and overview example) labels API version 2026-10-01 current, while the official support API article labels 2025-10-31 current; the newer date is also after the 2026-09-25 capture date.", "resolution": "Preserve both first-party statements and do not silently select a production header. Confirm with Grain before deployment; the dataset records a required version header but treats current-version status as unresolved."}],
        "notes": "The direct MCP release note confirms endpoint and availability; the detailed developer MCP route did not return its own setup content, so OAuth/tool entitlements for MCP remain unresolved. API PAT/WAT/OAuth statements refer to REST API, not necessarily MCP.",
        "extra_attempts": [{"url": "https://developers.grain.com/mcp.html", "status": "ACCESS_DENIED", "note": "AccessDenied; not treated as evidence for MCP authentication or tools."}, {"url": "https://developers.grain.com/mcp", "status": "REDIRECTED", "note": "The MCP route redirected to /overview.html rather than serving detailed MCP setup/auth/tool entitlements."}],
    },
}


def build() -> dict:
    manifest = json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8"))
    manifest_by_id = {r["app_id"]: r for r in manifest}
    if set(SPECS) != set(IDS):
        raise ValueError(f"Spec IDs mismatch. Missing={sorted(set(IDS)-set(SPECS))}; extra={sorted(set(SPECS)-set(IDS))}")
    if any(i not in manifest_by_id for i in IDS):
        raise ValueError("Batch scope contains an ID not present in apps/apps.json")

    raw_hashes_before = {"json": sha(RAW_JSON), "csv": sha(RAW_CSV)}
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    records: list[dict] = []
    traces: list[dict] = []

    for app_id in IDS:
        spec = SPECS[app_id]
        manifest_row = manifest_by_id[app_id]
        sources = copy.deepcopy(spec["sources"])
        by_key = {s["key"]: s for s in sources}
        evidence = [ev(field, claim, by_key[key], support, excerpt) for field, claim, key, support, excerpt in spec["evidence"]]
        query_specs = [{"query": spec["query"], "depth": spec.get("query_depth", "1"), "search_status": "SUCCESS", "lead_only": True, "note": "Native search response used for discovery only; search snippets were not claim evidence."}]
        query_specs.extend(copy.deepcopy(spec.get("extra_queries", [])))
        queries = [
            {"query": q["query"], "depth": q["depth"], "search_status": q.get("search_status", "SUCCESS"), "lead_only": q.get("lead_only", True), "note": q.get("note", "Search results were discovery only; not claim evidence.")}
            for q in query_specs
        ]
        attempts = [
            {"tool": "web_search", "query": q["query"], "depth": q["depth"], "status": q["search_status"], "note": q["note"]}
            for q in queries
        ]
        attempts.extend(
            {"tool": "fetch_page", "url": s["url"], "chunk_index": chunk_index, "status": "SUCCESS", "note": "Direct page chunk opened; source observation retained in the source packet."}
            for s in sources for chunk_index in s["retrieved_chunk_indexes"]
        )
        for item in copy.deepcopy(spec.get("extra_attempts", [])):
            attempts.append({"tool": item.pop("tool", "fetch_page"), **item})
        source_trace = [{k: v for k, v in s.items() if k != "key"} for s in sources]
        trace = {
            "app_id": app_id,
            "app": manifest_row["app"],
            "source_mode": "LIVE_AGENT",
            "status": "COMPLETE",
            "research_run_id": RUN_ID,
            "research_tool": TOOL,
            "queries": queries,
            "sources": source_trace,
            "attempts": attempts,
        }
        record = {
            "schema_version": "1.0",
            "app_id": app_id,
            "app": manifest_row["app"],
            "category": manifest_row["category"],
            "website_hint": manifest_row["website_hint"],
            "description": spec["description"],
            "auth_status": spec["auth_status"],
            "auth_methods": spec["auth_methods"],
            "self_serve_status": spec["self_serve_status"],
            "self_serve_details": spec["self_serve_details"],
            "credential_access": spec["credential_access"],
            "api": spec["api"],
            "mcp": spec["mcp"],
            "buildability": spec["buildability"],
            "evidence": evidence,
            "confidence": spec["confidence"],
            "research_timestamp": timestamp,
            "research_status": "COMPLETE",
            "verification_status": "NOT_CHECKED",
            "source_mode": "LIVE_AGENT",
            "research_tool": TOOL,
            "query_count": len(trace["queries"]),
            "source_count": len(trace["sources"]),
            "attempt_count": len(trace["attempts"]),
            "research_run_id": RUN_ID,
            "failure_reason": None,
            "quality_gate": {"status": "PASS", "errors": [], "warnings": []},
            "source_conflicts": copy.deepcopy(spec.get("conflicts", [])),
            "limitations": [
                "No vendor account, workspace/tenant, API key, API request, MCP session/tool call, deployment or human review was performed.",
                "Account-specific plan, region, role, usage and feature entitlements remain untested.",
            ],
            "researcher_notes": spec.get("notes", ""),
        }
        if app_id == 84:
            record["limitations"].append("Product identity for manifest ID84 remains unresolved; candidate-product facts are not attributed to it.")
        if app_id == 100:
            record["limitations"].append("Official Grain API version sources conflict; detailed developer MCP documentation was not accessible, so MCP authentication/tool entitlements remain unverified.")
        record["quality_gate"] = validate_record_quality(record, source_urls={s["url"] for s in source_trace})
        structural = validate_record(record)
        if structural:
            raise ValueError(f"app_id={app_id} schema/record validation failed: {structural}")
        if record["quality_gate"]["status"] == "FAIL":
            raise ValueError(f"app_id={app_id} quality gate failed: {record['quality_gate']}")
        records.append(record)
        traces.append(trace)

    raw_hashes_after = {"json": sha(RAW_JSON), "csv": sha(RAW_CSV)}
    if raw_hashes_before != raw_hashes_after:
        raise RuntimeError("Raw first-pass files changed during standalone batch build")

    artifact = {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "run_started_at": timestamp,
        "run_completed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_mode": "LIVE_AGENT",
        "tool": TOOL,
        "provider_credentials": {
            "TAVILY_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL",
            "OPENAI_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL",
        },
        "raw_dataset_hashes_before_and_after": {
            "before": raw_hashes_before,
            "after": raw_hashes_after,
            "unchanged": raw_hashes_before == raw_hashes_after,
        },
        "scope": "Manifest IDs 80-91 and 93-100 only; ID92 excluded because it is a prior capture. Standalone Batch07 research; not merged into the authoritative raw first-pass JSON/CSV.",
        "search_result_policy": "Search snippets are discovery leads only and excluded from claim evidence; evidence cites directly opened first-party product/developer/support/pricing/GitHub sources or official integration-provider docs.",
        "records": records,
        "traces": traces,
        "trace_limitations": [
            "Native search query strings, direct-page URLs, retrieved chunk indexes, and failed navigation/search attempts are retained separately. Search response snippets are not claim evidence.",
            "fetch_page exposes date-only retrieval precision, not per-page clock time. Only directly retrieved chunks are listed; failed routes are attempts, not source evidence.",
            "LIVE_AGENT means native web research only. No provider credentials, Composio call, vendor account/tenant check, API request, MCP session/action, deployment or human review is claimed.",
            "ID84 remains unresolved by explicit scope decision. Grain's official API-version statements conflict and detailed MCP documentation could not be accessed; these are preserved, not repaired.",
            "This standalone capture is not merged into data/raw/final_full_research.json or CSV. Full-population reconciliation, independent sample verification, human QA, corrected-dataset analysis, HTML regeneration, tests and deployment remain separate later gates.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact


if __name__ == "__main__":
    artifact = build()
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Records: {len(artifact['records'])}; traces: {len(artifact['traces'])}")
    print(f"Quality counts: {json.dumps({s: sum(r['quality_gate']['status'] == s for r in artifact['records']) for s in ('PASS','WARN','FAIL')})}")
    print(f"Raw hashes before/after equal: {artifact['raw_dataset_hashes_before_and_after']['unchanged']}")

#!/usr/bin/env python3
"""Record the separately performed post-correction source reinspection.

The values below were transcribed from direct official-page reopens after the
corrected dataset had been generated on 2026-09-25. They are deliberately
hard-coded observations, not copied from the verification ledger or corrected
dataset. The corrected dataset is read only to assert that every recheck row
addresses an actually corrected field and that its direct observation agrees.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_final_verification_inputs import DATE, SOURCES

OUT = ROOT / "data/evidence/final_post_recheck_input.json"
AUDIT_ID = "final-post-correction-audit-20260925"
COMMON_METHOD = (
    "Separate post-correction direct source reinspection performed on 2026-09-25 after "
    "data/verified/final_dataset.json had been generated. The named official page was reopened "
    "with Arena.ai fetch_page and the value below was transcribed from the newly displayed page, "
    "not copied from verified_value. This was public-page review only: no account, API, MCP, "
    "credential, signup, or human operation was performed. Exact per-request time was not exposed."
)


def source_ref(key: str, observation: str) -> dict:
    spec = SOURCES[key]
    return {
        "source_url": spec["source_url"],
        "source_title": spec["source_title"],
        "source_type": spec["source_type"],
        "observation": observation,
        "source_capture_key": key,
        "retrieved_on": DATE,
        "retrieval_timestamp_precision": "DATE_ONLY; fetch_page does not expose a per-request timestamp",
    }


# Actual values transcribed from the fresh post-correction page inspections.
# The recheck covers every one of the 12 corrected rows (3 critical + 9
# supplemental), including the changed text/labels rather than only status.
OBSERVATIONS: list[dict[str, Any]] = [
    {
        "app_id": 49, "app": "Amazon Selling Partner", "field_path": "mcp.status",
        "value": "AVAILABLE", "source_key": "amazon_local_mcp", "supporting_keys": [],
        "observation": "The reopened Amazon repository README labels this a Local MCP for SP-API and explicitly says it is an educational example, not a supported product. It lists local developer tools and states SP-API credentials are needed for live sp_api_execute/workflow calls.",
    },
    {
        "app_id": 4, "app": "Attio", "field_path": "auth_methods",
        "value": ["OAuth 2.0", "API key", "Bearer/token", "Basic"], "source_key": "attio_auth", "supporting_keys": [],
        "observation": "The reopened Attio authentication guide directly lists OAuth 2.0 and workspace API keys, Authorization: Bearer, and HTTP Basic with the token as username and a blank password.",
    },
    {
        "app_id": 4, "app": "Attio", "field_path": "self_serve_status",
        "value": "SELF_SERVE_WITH_RESTRICTIONS", "source_key": "attio_pricing", "supporting_keys": ["attio_mcp", "attio_admin_key"],
        "observation": "The reopened pricing page says start today/no credit card, links a Free signup route, and lists API/webhook access and MCP server in the plan matrix. The reopened MCP page describes self-serve OAuth user connection with no API key; the help page says keys are available on all plans but only workspace admins create/manage them.",
    },
    {
        "app_id": 1, "app": "Salesforce", "field_path": "api.types",
        "value": ["REST", "SOAP"], "source_key": "salesforce_soap", "supporting_keys": ["salesforce_rest"],
        "observation": "The reopened Salesforce SOAP guide directly describes SOAP API availability. The separately reopened REST guide directly describes REST API, confirming the distinct REST and SOAP interfaces.",
    },
    {
        "app_id": 1, "app": "Salesforce", "field_path": "api.details",
        "value": "Salesforce REST API supports records, query results, metadata and additional resources; the SOAP API is separately documented for Enterprise, Performance, Unlimited and Developer editions, subject to API Enabled permission. No endpoint count is estimated.",
        "source_key": "salesforce_soap", "supporting_keys": ["salesforce_rest"],
        "observation": "Both REST and SOAP first-party guides were reopened after correction. The REST page states that REST creates/manipulates/searches records and accesses query results/metadata; the SOAP page specifies supported editions, API Enabled permission, and a free Developer Edition test path.",
    },
    {
        "app_id": 9, "app": "Copper", "field_path": "api.types",
        "value": ["REST", "Webhooks"], "source_key": "copper_webhooks", "supporting_keys": ["copper_api"],
        "observation": "The reopened Copper developer guide describes its RESTful JSON Dev API. The separately reopened Webhooks guide describes event subscriptions and HTTPS notifications, confirming both documented interfaces while keeping webhook subscriptions distinct from a general REST Webhooks API.",
    },
    {
        "app_id": 9, "app": "Copper", "field_path": "api.details",
        "value": "Copper's Developer API is a RESTful JSON interface for most CRM resources. The separate documented Webhooks interface supports subscriptions for near-real-time create/update/delete notifications on supported entities, HTTPS endpoints, up to 100 active subscriptions and stated delivery limits; this is not described as a general REST Webhooks API.",
        "source_key": "copper_webhooks", "supporting_keys": ["copper_api"],
        "observation": "The reopened webhook overview lists create/update/delete event types, supported CRM entities, HTTPS-only callback URLs, up to 100 active subscriptions, notification limits, and at-most-once delivery/no retries. The reopened developer landing page describes a RESTful JSON interface for most Copper resources.",
    },
    {
        "app_id": 13, "app": "Freshdesk", "field_path": "api.details",
        "value": "The official REST v2 reference documents ticket CRUD, conversations/replies, contacts, companies, agents, ticket fields/forms and other helpdesk resources; quotas are plan-based. Freshdesk automation rules also support outbound webhook actions to external URLs for ticket events. This is webhook-enabled automation, not a separately documented Webhooks API, so api.types remains REST.",
        "source_key": "freshdesk_webhook", "supporting_keys": ["freshdesk_api"],
        "observation": "The reopened Freshdesk REST reference exposes the REST v2 resource index. The reopened first-party automation guide distinguishes Trigger Webhook from Trigger API and describes external callback URLs, request methods, API-key authentication, and plan applicability; it documents an outbound automation action, not a standalone Webhooks API.",
    },
    {
        "app_id": 49, "app": "Amazon Selling Partner", "field_path": "mcp.details",
        "value": "Amazon's selling-partner-api-samples repository contains a first-party Local MCP for SP-API educational example. It is explicitly not a supported product in its own right and is not a hosted Amazon MCP service. Most local developer-assistance tools work without SP-API credentials; tools that execute live SP-API requests or workflows require SP-API credentials.",
        "source_key": "amazon_local_mcp", "supporting_keys": [],
        "observation": "The reopened README says the sample MCPs are not supported products, lists documentation/catalog/code tools, and separates them from sp_api_execute and live workflow calls that require SP-API credentials.",
    },
    {
        "app_id": 49, "app": "Amazon Selling Partner", "field_path": "mcp.search_scope",
        "value": "Opened Amazon's first-party Local MCP for SP-API README. It documents installation/client setup and states the repository example is educational and unsupported as a product; some developer tools are local while live SP-API calls require credentials. No Amazon-hosted MCP service is inferred.",
        "source_key": "amazon_local_mcp", "supporting_keys": [],
        "observation": "The same freshly reopened README exposes installation, client configuration, support-status caveat, included tools, and credential requirements; it does not establish a hosted Amazon MCP service.",
    },
    {
        "app_id": 9, "app": "Copper", "field_path": "mcp.search_scope",
        "value": "Opened Copper's official Developer API landing page, authentication/OAuth material and webhook overview, and ran a targeted official-domain MCP search. The opened pages establish REST, OAuth/API-key and webhook surfaces but do not establish MCP ownership or absence. Search was bounded; status remains UNKNOWN.",
        "source_key": "copper_api", "supporting_keys": ["copper_webhooks", "copper_oauth"],
        "observation": "After correction, a new targeted site:developer.copper.com MCP/Model Context Protocol search was run. Its results were discovery only and did not surface a first-party MCP guide; the Copper REST landing page, OAuth quickstart and webhook overview were reopened directly. This bounded review still cannot establish availability or absence.",
    },
    {
        "app_id": 91, "app": "NotebookLM", "field_path": "mcp.search_scope",
        "value": "Opened Google Cloud NotebookLM Enterprise API, setup and licensing documentation and ran a targeted first-party Google Cloud search for NotebookLM MCP/Model Context Protocol. Search results included generic Google Cloud MCP references but no NotebookLM Enterprise-specific endpoint/setup; generic services are not attributed to NotebookLM. Status remains UNKNOWN, not NO.",
        "source_key": "notebooklm_api", "supporting_keys": ["notebooklm_setup", "notebooklm_licensing"],
        "observation": "After correction, a new targeted Google Cloud/NotebookLM Enterprise MCP search returned generic Google Cloud MCP documentation as discovery leads, not a NotebookLM-specific setup. The NotebookLM API, setup and licensing guides were reopened directly; they confirm the enterprise API and prerequisites but do not establish product-specific MCP availability or absence.",
    },
]

SEARCH_EVENTS = [
    {
        "audit_id": AUDIT_ID,
        "stage": "POST_CORRECTION_RECHECK",
        "query": "site:developer.copper.com \"MCP\" OR \"Model Context Protocol\" Copper",
        "tool": "web_search", "status": "SUCCESS", "retrieved_on": DATE,
        "timestamp_precision": "DATE_ONLY", "used_as_evidence": False,
        "purpose": "Repeat a bounded official-domain MCP discovery search after correction; not evidence that Copper MCP does not exist.",
        "follow_up": "Directly reopened Copper REST API landing page, OAuth quickstart, and webhook overview. Search result snippets were discovery leads only; MCP status remains UNKNOWN.",
        "follow_up_source_keys": ["copper_api", "copper_oauth", "copper_webhooks"],
    },
    {
        "audit_id": AUDIT_ID,
        "stage": "POST_CORRECTION_RECHECK",
        "query": "site:cloud.google.com OR site:docs.cloud.google.com \"NotebookLM Enterprise\" MCP \"Model Context Protocol\"",
        "tool": "web_search", "status": "SUCCESS", "retrieved_on": DATE,
        "timestamp_precision": "DATE_ONLY", "used_as_evidence": False,
        "purpose": "Repeat a bounded first-party Google Cloud search for a NotebookLM Enterprise-specific MCP after correction; not evidence of absence.",
        "follow_up": "Directly reopened the NotebookLM Enterprise API, setup and licensing documentation. Generic Google Cloud MCP results were not attributed to NotebookLM; status remains UNKNOWN.",
        "follow_up_source_keys": ["notebooklm_api", "notebooklm_setup", "notebooklm_licensing"],
    },
]


def main() -> int:
    corrected = json.loads((ROOT / "data/verified/final_dataset.json").read_text(encoding="utf-8"))
    by_id = {record["app_id"]: record for record in corrected}
    if len(by_id) != len(corrected):
        raise ValueError("corrected dataset contains duplicate app IDs")
    for item in OBSERVATIONS:
        record = by_id[item["app_id"]]
        parts = item["field_path"].split(".")
        current: Any = record
        for part in parts:
            current = current[part]
        if current != item["value"]:
            raise ValueError(f"post-recheck observation does not match generated correction at {item['app_id']}.{item['field_path']}")
        source = SOURCES[item["source_key"]]
        for support_key in item["supporting_keys"]:
            if support_key not in SOURCES:
                raise ValueError(f"unknown supporting source {support_key}")
        item["source"] = source_ref(item["source_key"], item["observation"])
        item["supporting_sources"] = [
            source_ref(support_key, SOURCES[support_key]["observation"])
            for support_key in item["supporting_keys"]
        ]
        item["status"] = "CONFIRMED"
        item["verifier_type"] = "automated_independent"
        item["method"] = COMMON_METHOD
        item["independence_level"] = "FRESH_REINSPECTION"
        item["audit_id"] = AUDIT_ID
        item["rechecked_after_corrected_dataset"] = True
        item["verified_at"] = DATE
        item["verified_at_precision"] = "DATE_ONLY; exact page fetch timestamp unavailable"
        item["corrected_dataset_value_checked_against"] = item["field_path"]
    output = {
        "audit_id": AUDIT_ID,
        "created_on": DATE,
        "created_at_precision": "DATE_ONLY; exact per-request times are not exposed",
        "verification_capture_mode": "LIVE_AGENT_WEB_REINSPECTION_AFTER_CORRECTION",
        "checks": OBSERVATIONS,
        "search_events": SEARCH_EVENTS,
        "status": "SEPARATE_POST_CORRECTION_RECHECK_CAPTURED",
        "notes": [
            "The corrected dataset was generated before this separate second-pass capture.",
            "All 12 changed ledger rows were reopened and checked (3 critical + 9 supplemental); no unchanged critical rows were rechecked.",
            "Values in this file were transcribed from the direct post-correction page inspections. Corrected dataset reads in this script are validation only; they do not populate observed values.",
            "MCP search-scope rechecks use bounded searches plus directly opened pages. Copper and NotebookLM remain UNKNOWN; search-result snippets are not treated as proof of absence.",
            "No human review, account/API/MCP call, package test, or tenant operation occurred.",
        ],
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(OBSERVATIONS)} explicit post-correction observations; corrected values were validation-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

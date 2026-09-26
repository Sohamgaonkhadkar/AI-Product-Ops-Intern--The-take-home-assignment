#!/usr/bin/env python3
"""Generate deterministic aggregate analysis from the corrected final dataset.

This script never edits raw or verified records. It reports all 100 manifest
records with mixed LIVE_AGENT/PRIOR_CAPTURE provenance, and limits Easy-win,
Outreach, and Constrained classifications to fully adjudicated records in the
final verification sample. Unknown, mixed, and unchecked records remain
NEEDS_REVIEW. A separate post-correction source recheck and human QA remain
unperformed and are reported as blockers, never inferred.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.quality import normalize_url

DATASET_PATH = "data/verified/final_dataset.json"
LEDGER_PATH = "data/verified/final_verification_ledger.json"
SELECTION_PATH = "data/evidence/verification_sample_selection.json"
SOURCE_CAPTURE_PATH = "data/evidence/final_sample_source_captures.json"
ATTEMPT_LOG_PATH = "data/raw/final_full_attempts.json"
QUALITY_PATH = "data/verified/final_quality_report.json"
PILOT_LEDGER_PATH = "data/verified/pilot_verification_ledger.json"
ANALYSIS_PATH = "data/analysis/final_analysis.json"
ANALYSIS_MD_PATH = "reports/final_analysis.md"
ERROR_MD_PATH = "reports/final_error_analysis.md"
CATEGORY_CSV_PATH = "data/analysis/category_summary.csv"
TRIAGE_CSV_PATH = "data/analysis/verified_sample_triage.csv"

PREVENTION = {
    "mcp_false_negative": "Add a targeted first-party MCP discovery checklist and inspect first-party repositories/indexes; distinguish local examples, hosted products, and unsupported samples in separate fields.",
    "auth_method_omission": "Inspect the dedicated authentication guide and enumerate every documented wire-level method (including alternate HTTP authorization schemes) before normalizing the list.",
    "credential_path_conflation": "Model API-key, OAuth/MCP, and admin-issued paths separately; determine the record-level self-serve label from all viable documented paths rather than one credential route.",
    "api_interface_omission": "Enumerate separately documented interfaces and webhooks/SOAP/GraphQL/SDK distinctions; do not assume the REST guide is the complete API surface.",
    "api_scope_detail_added": "Add an interface-completeness checklist to supplemental API review and ensure `api.types` changes are reflected in `api.details` with their exact limits.",
    "outbound_webhook_capability_clarified": "Keep outbound webhook/HTTP automation distinct from a product's dedicated webhook-management API; verify both the main REST reference and automation guide before describing it.",
    "credential_path_nuance_added": "Write blockers per access path and distinguish OAuth user authorization from API-key issuance/admin controls.",
    "mcp_scope_omission": "Separate MCP presence from product support/hosting and credential requirements; quote repository caveats in the claim rather than collapsing them into a single availability label.",
    "source_scope_detail_added": "Persist search/opened-page scope in the first-pass record and update it only from directly inspected pages; retain partial extraction limitations.",
    "mcp_access_constraint_omitted": "Capture provider-account app-install permission and external client-plan requirements as distinct constraints; label which company owns each gate.",
    "mcp_announcement_conflict_preserved": "Track announcement dates and current setup pages side by side; an announced future/early-access feature remains UNKNOWN until current endpoint/setup is directly documented.",
    "bounded_search_limitation_documented": "Use bounded-scope language for inconclusive official searches and keep UNKNOWN unless authoritative evidence supports availability or a scoped NOT_FOUND classification.",
}

ERROR_LABELS = {
    "mcp_false_negative": "First-pass MCP false negative / unresolved value",
    "auth_method_omission": "Authentication-method omission",
    "credential_path_conflation": "Credential-path conflation",
    "api_interface_omission": "API interface omission",
    "api_scope_detail_added": "API scope/detail completeness change",
    "outbound_webhook_capability_clarified": "Outbound webhook capability clarified", 
    "credential_path_nuance_added": "Credential-path nuance added",
    "mcp_scope_omission": "MCP product-versus-sample scope omission",
    "source_scope_detail_added": "Search/evidence scope note updated",
    "mcp_access_constraint_omitted": "MCP access constraint omitted",
    "mcp_announcement_conflict_preserved": "MCP announcement/current-state conflict preserved",
    "bounded_search_limitation_documented": "Bounded MCP-search limitation clarified",
}

CORE_ACCESSORS: dict[str, Callable[[dict], Any]] = {
    "auth": lambda r: r.get("auth_status", "UNKNOWN"),
    "self_serve": lambda r: r.get("self_serve_status", "UNKNOWN"),
    "credential_access": lambda r: (r.get("credential_access") or {}).get("status", "UNKNOWN"),
    "api_availability": lambda r: (r.get("api") or {}).get("available", "UNKNOWN"),
    "mcp": lambda r: (r.get("mcp") or {}).get("status", "UNKNOWN"),
    "buildability": lambda r: (r.get("buildability") or {}).get("verdict", "UNKNOWN"),
}


def read_json(rel: str) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_json(rel: str, value: Any) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def counts(records: list[dict], accessor: Callable[[dict], Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(accessor(r)) for r in records).items()))


def format_counts(values: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in values.items()) or "none"


def format_cohort_counts(values: dict[str, dict[str, int]]) -> str:
    return " | ".join(f"{cohort}: {format_counts(cohort_counts)}" for cohort, cohort_counts in values.items())


def source_urls(row: dict) -> list[str]:
    urls: list[str] = []
    for ref in [row.get("source") or {}, *(row.get("supporting_sources") or [])]:
        url = ref.get("source_url")
        if url and url not in urls:
            urls.append(url)
    for item in row.get("evidence_patch", []) or []:
        url = item.get("source_url")
        if url and url not in urls:
            urls.append(url)
    return urls


def classify_for_outreach(record: dict) -> tuple[str, str]:
    """Apply the documented rule only to six-field AUTO_VERIFIED records."""
    if record.get("verification_status") != "AUTO_VERIFIED":
        status = record.get("verification_status", "NOT_CHECKED")
        return "NEEDS_REVIEW", f"critical verification is {status}; unknown/unchecked values are not auto-classified"

    facts = [accessor(record) for accessor in CORE_ACCESSORS.values()]
    if any(value in {None, "UNKNOWN", ""} for value in facts):
        return "NEEDS_REVIEW", "one or more critical access/API/MCP/buildability facts remain UNKNOWN"
    if not record.get("auth_methods"):
        return "NEEDS_REVIEW", "no documented authentication method is recorded"

    api = record.get("api", {})
    credential = record.get("credential_access", {})
    build = record.get("buildability", {})
    self_serve = record.get("self_serve_status")
    outreach_gates = {"PARTNER_OR_CONTACT_SALES", "ENTERPRISE_ONLY", "PAID_PLAN_REQUIRED"}
    if self_serve in outreach_gates or build.get("verdict") == "OUTREACH_REQUIRED":
        return "OUTREACH", "verified partner/sales, enterprise, material paid-plan, or OUTREACH_REQUIRED gate"

    easy_win = (
        api.get("available") == "YES"
        and credential.get("status") == "SELF_SERVE"
        and bool(record.get("auth_methods"))
        and api.get("breadth") in {"BROAD", "MODERATE"}
        and build.get("verdict") == "BUILDABLE_NOW"
        and self_serve not in outreach_gates
    )
    if easy_win:
        return "EASY_WIN", "all documented easy-win conditions are satisfied"

    if api.get("available") == "NO":
        return "CONSTRAINED", "API non-availability is evidenced, but no separate plausible outreach path is established"
    return "CONSTRAINED", "known access, plan, permission, scope, or buildability constraints prevent the easy-win rule"


def _row_summary(row: dict) -> dict:
    return {
        "app_id": row.get("app_id"),
        "app": row.get("app"),
        "field": row.get("field_path"),
        "metric_group": row.get("metric_group"),
        "first_pass": row.get("initial_value"),
        "verified": row.get("verified_value"),
        "error_type": row.get("error_type") or "unclassified_observed_change",
        "label": ERROR_LABELS.get(row.get("error_type"), row.get("error_type") or "Observed first-pass change"),
        "cause": row.get("reason", ""),
        "correction": row.get("correction", ""),
        "prevention": PREVENTION.get(row.get("error_type"), "Review the specific ledger row and add a narrow validation rule only if the observed pattern recurs."),
        "source_urls": source_urls(row),
        "post_recheck_correctness": row.get("post_recheck_correctness"),
        "independence_level": ((row.get("post_recheck") or {}).get("independence_level") or row.get("independence_level")), 
    }


def build_analysis() -> dict:
    records = read_json(DATASET_PATH)
    manifest = read_json("apps/apps.json")
    ledger = read_json(LEDGER_PATH)
    selection = read_json(SELECTION_PATH)
    capture = read_json(SOURCE_CAPTURE_PATH)
    attempts = read_json(ATTEMPT_LOG_PATH)
    quality = read_json(QUALITY_PATH)
    pilot = read_json(PILOT_LEDGER_PATH)

    manifest_by_id = {r["app_id"]: r for r in manifest}
    by_id = {r["app_id"]: r for r in records}
    if len(records) != 100 or set(by_id) != set(manifest_by_id):
        raise ValueError("analysis requires the exact 100-record final dataset reconciled to apps/apps.json")
    if len(by_id) != len(records):
        raise ValueError("analysis input has duplicate app_id")

    sample_ids = list(selection.get("selected_ids", []))
    sample = [by_id[i] for i in sample_ids]
    captured = [r for r in records if r.get("source_mode") in {"PRIOR_CAPTURE", "LIVE_AGENT"}]
    prior_capture = [r for r in records if r.get("source_mode") == "PRIOR_CAPTURE"]
    live_agent = [r for r in records if r.get("source_mode") == "LIVE_AGENT"]
    not_run = [r for r in records if r.get("source_mode") == "NOT_RUN"]
    verified_sample = [r for r in sample if r.get("verification_status") == "AUTO_VERIFIED"]

    categories = list(dict.fromkeys(r["category"] for r in manifest))
    category_summary = []
    for category in categories:
        manifest_category = [r for r in manifest if r["category"] == category]
        category_records = [r for r in records if r.get("category") == category]
        captured_category = [r for r in category_records if r in captured]
        sample_category = [r for r in sample if r.get("category") == category]
        verified_category = [r for r in sample_category if r.get("verification_status") == "AUTO_VERIFIED"]
        category_summary.append({
            "category": category,
            "manifest_count": len(manifest_category),
            "prior_capture_count": sum(r.get("source_mode") == "PRIOR_CAPTURE" for r in category_records),
            "live_agent_count": sum(r.get("source_mode") == "LIVE_AGENT" for r in category_records),
            "not_run_count": sum(r.get("source_mode") == "NOT_RUN" for r in category_records),
            "captured_complete_or_partial_count": sum(r.get("research_status") in {"COMPLETE", "PARTIAL"} and r.get("source_mode") in {"PRIOR_CAPTURE", "LIVE_AGENT"} for r in category_records),
            "selected_sample_count": len(sample_category),
            "fully_adjudicated_sample_count": len(verified_category),
            "captured_api_yes_count": sum((r.get("api") or {}).get("available") == "YES" for r in captured_category),
            "captured_mcp_available_count": sum((r.get("mcp") or {}).get("status") == "AVAILABLE" for r in captured_category),
            "captured_mcp_unknown_count": sum((r.get("mcp") or {}).get("status") == "UNKNOWN" for r in captured_category),
            "selected_easy_win_count": sum(classify_for_outreach(r)[0] == "EASY_WIN" for r in sample_category),
            "selected_outreach_count": sum(classify_for_outreach(r)[0] == "OUTREACH" for r in sample_category),
            "selected_needs_review_count": sum(classify_for_outreach(r)[0] == "NEEDS_REVIEW" for r in sample_category),
        })

    field_distributions = {}
    cohorts = {
        "manifest_all_100": records,
        "captured_prior_or_live_100": captured,
        "selected_sample_20": sample,
        "fully_adjudicated_selected_15": verified_sample,
    }
    for field, accessor in CORE_ACCESSORS.items():
        field_distributions[field] = {
            cohort_name: counts(cohort, accessor)
            for cohort_name, cohort in cohorts.items()
        }

    def list_item_counts(cohort: list[dict], path: str) -> dict[str, int]:
        out: Counter[str] = Counter()
        for record in cohort:
            current: Any = record
            for part in path.split("."):
                current = current.get(part) if isinstance(current, dict) else None
            if isinstance(current, list):
                out.update(str(x) for x in current)
        return dict(sorted(out.items()))

    api_breadth = lambda r: (r.get("api") or {}).get("breadth", "UNKNOWN")
    mcp_status = lambda r: (r.get("mcp") or {}).get("status", "UNKNOWN")
    build_verdict = lambda r: (r.get("buildability") or {}).get("verdict", "UNKNOWN")

    triage_rows = []
    for record in records:
        tier, reason = classify_for_outreach(record)
        triage_rows.append({
            "app_id": record["app_id"],
            "app": record["app"],
            "category": record["category"],
            "source_mode": record.get("source_mode"),
            "research_status": record.get("research_status"),
            "verification_status": record.get("verification_status"),
            "triage": tier,
            "reason": reason,
        })

    tiers = Counter(r["triage"] for r in triage_rows)
    sample_tiers = [r for r in triage_rows if r["app_id"] in set(sample_ids)]
    sample_tier_counts = Counter(r["triage"] for r in sample_tiers)

    changed_rows = [r for r in ledger.get("checks", []) if r.get("correctness") == "INCORRECT"]
    error_rows = [_row_summary(r) for r in changed_rows]
    error_groups: dict[str, list[dict]] = defaultdict(list)
    for row in error_rows:
        error_groups[row["error_type"]].append(row)
    error_type_summary = []
    for error_type in sorted(error_groups):
        rows = error_groups[error_type]
        error_type_summary.append({
            "error_type": error_type,
            "label": ERROR_LABELS.get(error_type, error_type),
            "count": len(rows),
            "critical_count": sum(bool(x.get("metric_group")) for x in rows),
            "supplemental_count": sum(not x.get("metric_group") for x in rows),
            "observed_examples": [{"app_id": x["app_id"], "app": x["app"], "field": x["field"], "first_pass": x["first_pass"], "verified": x["verified"]} for x in rows[:3]],
            "cause": rows[0]["cause"],
            "prevention": PREVENTION.get(error_type, "Review examples in the full error table."),
        })

    all_manifest_categories = set(categories)
    selected_categories = {r["category"] for r in sample}
    unrepresented_categories = sorted(all_manifest_categories - selected_categories)
    sample_ids_set = set(sample_ids)
    attempt_traces = attempts.get("traces", [])
    attempt_trace_count = len(attempt_traces)
    live_attempt_traces = [t for t in attempt_traces if t.get("source_mode") == "LIVE_AGENT"]
    prior_attempt_traces = [t for t in attempt_traces if t.get("source_mode") == "PRIOR_CAPTURE"]
    raw_source_packets = sum(len(t.get("sources") or []) for t in attempt_traces)

    def unique_urls_for_traces(trace_rows: list[dict]) -> set[str]:
        return {
            normalize_url(s.get("source_url") or s.get("url", ""))
            for t in trace_rows
            for s in (t.get("sources") or [])
            if isinstance(s, dict) and (s.get("source_url") or s.get("url"))
        }

    unique_raw_source_urls = unique_urls_for_traces(attempt_traces)
    live_source_packets = sum(len(t.get("sources") or []) for t in live_attempt_traces)
    prior_source_packets = sum(len(t.get("sources") or []) for t in prior_attempt_traces)
    live_unique_urls = unique_urls_for_traces(live_attempt_traces)
    prior_unique_urls = unique_urls_for_traces(prior_attempt_traces)
    total_claim_evidence = sum(len(r.get("evidence", [])) for r in records)
    captured_claim_evidence = sum(len(r.get("evidence", [])) for r in captured)

    app_matrix = []
    for record in records:
        tier, tier_reason = classify_for_outreach(record)
        app_matrix.append({
            "app_id": record["app_id"],
            "app": record["app"],
            "category": record["category"],
            "description": record.get("description", ""),
            "source_mode": record.get("source_mode"),
            "research_status": record.get("research_status"),
            "verification_status": record.get("verification_status"),
            "auth_status": record.get("auth_status"),
            "auth_methods": record.get("auth_methods", []),
            "self_serve_status": record.get("self_serve_status"),
            "credential_access_status": (record.get("credential_access") or {}).get("status"),
            "credential_plan_or_gate": (record.get("credential_access") or {}).get("plan_or_gate", ""),
            "api_available": (record.get("api") or {}).get("available"),
            "api_types": (record.get("api") or {}).get("types", []),
            "api_breadth": (record.get("api") or {}).get("breadth"),
            "api_details": (record.get("api") or {}).get("details", ""),
            "mcp_status": (record.get("mcp") or {}).get("status"),
            "mcp_details": (record.get("mcp") or {}).get("details", ""),
            "buildability_verdict": (record.get("buildability") or {}).get("verdict"),
            "blocker": (record.get("buildability") or {}).get("blocker", ""),
            "evidence_count": len(record.get("evidence", [])),
            "quality_gate": record.get("quality_gate", {}),
            "easy_win_outreach_triage": tier,
            "triage_reason": tier_reason,
            "source_urls": list(dict.fromkeys(e.get("source_url", "") for e in record.get("evidence", []) if e.get("source_url"))),
        })

    post_metrics = ledger.get("metrics", {}).get("post_recheck_all_rows", {})
    post_critical = ledger.get("metrics", {}).get("post_correction_overall", {})
    error_analysis = {
        "changed_row_count": len(error_rows),
        "critical_mismatch_count": sum(bool(r.get("metric_group")) for r in error_rows),
        "supplemental_change_count": sum(not r.get("metric_group") for r in error_rows),
        "error_type_summary": error_type_summary,
        "examples": error_rows,
        "post_correction_critical_concordance": post_critical,
        "post_recheck_all_changed_rows": post_metrics,
        "note": "Observed changes come only from the final sample's explicit ledger; supplemental narrative/detail changes are reported separately from critical-field label accuracy.",
    }

    artifact = {
        "analysis_version": "2.1",
        "generated_on": capture.get("created_on", "unknown"),
        "status": "FIRST_PASS_RESEARCH_RECONCILED; FIRST_PASS_VERIFICATION_AND_12_CHANGED_ROW_RECHECK_COMPLETE; HUMAN_QA_NOT_POSSIBLE; REPOSITORY_PUBLICATION_AND_DEPLOYMENT_NOT_DONE",
        "inputs": {
            "verified_dataset": DATASET_PATH,
            "verified_dataset_sha256": sha256(DATASET_PATH),
            "verification_ledger": LEDGER_PATH,
            "sample_selection": SELECTION_PATH,
            "source_capture": SOURCE_CAPTURE_PATH,
            "attempt_log": ATTEMPT_LOG_PATH,
            "manifest": "apps/apps.json",
        },
        "scope": {
            "manifest_count": len(manifest),
            "dataset_record_count": len(records),
            "manifest_reconciles_exactly": set(by_id) == set(manifest_by_id),
            "category_count": len(categories),
            "categories": categories,
            "complete_records": sum(r.get("research_status") == "COMPLETE" for r in records),
            "partial_records": sum(r.get("research_status") == "PARTIAL" for r in records),
            "failed_records": sum(r.get("research_status") == "FAILED" for r in records),
            "source_mode_counts": dict(sorted(Counter(r.get("source_mode", "MISSING") for r in records).items())),
            "research_status_counts": dict(sorted(Counter(r.get("research_status", "MISSING") for r in records).items())),
            "verification_status_counts": dict(sorted(Counter(r.get("verification_status", "MISSING") for r in records).items())),
            "captured_record_count": len(captured),
            "prior_capture_count": len(prior_capture),
            "live_agent_count": len(live_agent),
            "not_run_count": len(not_run),
            "all_records_evidence_item_count": total_claim_evidence,
            "captured_records_evidence_item_count": captured_claim_evidence,
            "source_modes_note": "Every manifest ID has a researched COMPLETE/PARTIAL record. LIVE_AGENT means native live-agent source capture on 2026-09-24/25; PRIOR_CAPTURE means preserved historical capture. The 20-app coverage sample contains both modes and does not relabel historical records. Native web research did not require Tavily/OpenAI keys; no provider-backed Tavily/OpenAI or Composio run is claimed.",
            "not_run_ids": sorted(r["app_id"] for r in not_run),
            "full_population_source_mode_counts": dict(sorted(Counter(r.get("source_mode", "MISSING") for r in records).items())),
            "sample_source_mode_counts": dict(sorted(Counter(r.get("source_mode", "MISSING") for r in sample).items())),
            "verification_status_note": "AUTO_VERIFIED means all six sample fields were adjudicable from public-source evidence; MIXED means at least one of those six remained unresolved. Neither status is human verification." ,
        },
        "sample": {
            "status": selection.get("status"),
            "seed": selection.get("seed"),
            "target_size": selection.get("target_size"),
            "eligible_count": selection.get("eligible_count"),
            "selected_count": len(sample),
            "selected_ids_in_selection_order": sample_ids,
            "selected_ids_sorted": sorted(sample_ids),
            "selection_method": selection.get("selection_method"),
            "selected_category_count": len(selected_categories),
            "selected_categories": [c for c in categories if c in selected_categories],
            "unrepresented_manifest_categories": unrepresented_categories,
            "selection_coverage": selection.get("coverage"),
            "source_mode_counts": dict(sorted(Counter(r.get("source_mode", "MISSING") for r in sample).items())),
            "note": "A deterministic weighted max-coverage sample was selected only after all 100 apps had COMPLETE/PARTIAL research. It contains 14 LIVE_AGENT and 6 PRIOR_CAPTURE records, covers the observed strata listed in the selection artifact, and is an audit coverage sample—not a probability sample or population accuracy estimator.",
            "selection_is_probability_sample": False,
            "observed_strata_count": selection.get("observed_strata_count"),
            "covered_strata_count": selection.get("covered_strata_count"),
            "uncovered_observed_strata": selection.get("uncovered_observed_strata", []),
        },
        "cohorts": {
            "captured_prior_or_live": {"count": len(captured), "source_mode_counts": dict(sorted(Counter(r.get("source_mode") for r in captured).items()))},
            "fully_adjudicated_sample": {"count": len(verified_sample), "app_ids": sorted(r["app_id"] for r in verified_sample)},
            "mixed_sample": {"count": sum(r.get("verification_status") == "MIXED" for r in sample), "app_ids": sorted(r["app_id"] for r in sample if r.get("verification_status") == "MIXED")},
            "unchecked_sample": {"count": sum(r.get("verification_status") == "NOT_CHECKED" for r in sample), "app_ids": sorted(r["app_id"] for r in sample if r.get("verification_status") == "NOT_CHECKED")},
            "not_run_full_manifest": {"count": len(not_run), "app_ids": sorted(r["app_id"] for r in not_run)},
        },
        "critical_field_distributions": field_distributions,
        "api": {
            "availability": field_distributions["api_availability"],
            "breadth": {cohort_name: counts(cohort, api_breadth) for cohort_name, cohort in cohorts.items()},
            "interface_type_counts": {cohort_name: list_item_counts(cohort, "api.types") for cohort_name, cohort in cohorts.items()},
            "details_note": "Types/breadth are counted only from recorded fields. The current Freshdesk supplemental correction describes outbound webhook automation without changing api.types=REST. A separate targeted Gorgias nomenclature audit (data/evidence/api_webhook_nomenclature_audit.json; outside the 20-app accuracy sample) records first-party outbound HTTP/webhook actions and preserves api.types=REST; neither product is represented as a dedicated Webhooks API. Public API documentation does not prove tenant entitlement.",
            "webhook_nomenclature_audit": {
                "file": "data/evidence/api_webhook_nomenclature_audit.json",
                "scope": "Targeted terminology check outside the 20-app accuracy sample; does not change sample denominators or correction metrics.",
                "gorgias_interface_classification": "REST; outbound HTTP/webhook capability is described separately, not a dedicated Webhooks API.",
                "freshdesk_interface_classification": "REST; outbound webhook automation is described separately, not a dedicated Webhooks API.",
            },
        },
        "auth": {
            "status": field_distributions["auth"],
            "method_counts": {cohort_name: list_item_counts(cohort, "auth_methods") for cohort_name, cohort in cohorts.items()},
        },
        "access": {
            "self_serve_status": field_distributions["self_serve"],
            "credential_access_status": field_distributions["credential_access"],
            "note": "Credential access is a separate field from API availability. Gated/restricted labels describe documented paths and do not establish a particular tenant's entitlement.",
        },
        "mcp": {
            "status": field_distributions["mcp"],
            "note": "UNKNOWN is retained for unresolved product identity or bounded first-party source limits (including ID84 identity, ID27 cloud/MCP facts, ID9 Copper MCP, and ID91 NotebookLM MCP); it is not a negative MCP finding. Amazon's documented local educational example is distinct from a supported hosted product. Zoho Cliq MCP is first-party documented; its current REST/OAuth page extraction did not verify detailed auth mechanics." ,
        },
        "buildability": {
            "verdict": field_distributions["buildability"],
            "blocker_pattern_counts": {
                cohort_name: blocker_pattern_counts(cohort)
                for cohort_name, cohort in cohorts.items()
            },
            "note": "Blocker-pattern counts are overlapping text-keyword review aids; the record-level blocker remains the source of truth.",
        },
        "easy_win_outreach": {
            "rule": {
                "easy_win": "Only a fully AUTO_VERIFIED record with API YES, SELF_SERVE credential access, documented auth, BROAD/MODERATE API, BUILDABLE_NOW, and no partner/enterprise/paid gate.",
                "outreach": "Only a fully AUTO_VERIFIED record with PARTNER_OR_CONTACT_SALES, ENTERPRISE_ONLY, PAID_PLAN_REQUIRED, or OUTREACH_REQUIRED; API absence alone is not enough without a plausible documented outreach path.",
                "constrained": "Fully verified known combinations that do not meet Easy-win or Outreach.",
                "needs_review": "MIXED, NOT_CHECKED, any UNKNOWN critical value, or missing auth method. Never auto-classified as Easy-win/Outreach.",
            },
            "all_100_triage_counts": dict(sorted(tiers.items())),
            "selected_20_triage_counts": dict(sorted(sample_tier_counts.items())),
            "classified_only_from_fully_adjudicated_sample": True,
            "rows": triage_rows,
        },
        "category_summary": category_summary,
        "verification": {
            "metrics": ledger.get("metrics", {}),
            "ledger_row_count": len(ledger.get("checks", [])),
            "critical_rows": sum(bool(r.get("metric_group")) for r in ledger.get("checks", [])),
            "supplemental_rows": sum(not r.get("metric_group") for r in ledger.get("checks", [])),
            "post_recheck_row_count": len(read_json("data/evidence/final_post_recheck.json").get("checks", [])),
            "post_recheck_status": read_json("data/evidence/final_post_recheck.json").get("status"),
            "post_recheck_concordance": ledger.get("metrics", {}).get("post_correction_overall", {}),
            "all_changed_row_recheck_concordance": ledger.get("metrics", {}).get("post_recheck_all_rows", {}),
            "source_capture_id": capture.get("capture_id"),
            "verification_type": "automated independent public-page review; no human/account/MCP operation claimed",
        },
        "observed_error_analysis": error_analysis,
        "quality_gate": {
            "status": quality.get("status"),
            "record_quality_counts": quality.get("record_quality_counts", {}),
            "warning_count": len(quality.get("warnings", [])),
            "warnings": quality.get("warnings", []),
            "record_quality": quality.get("record_quality", []),
        },
        "provenance": {
            "raw_first_pass_dataset": "data/raw/final_full_research.json",
            "corrected_dataset": DATASET_PATH,
            "source_capture_mode": capture.get("verification_capture_mode"),
            "source_capture_id": capture.get("capture_id"),
            "capture_created_on": capture.get("created_on"),
            "capture_timestamp_precision": capture.get("created_at_precision"),
            "full_run_id": attempts.get("run_id"),
            "full_run_mode": attempts.get("mode"),
            "full_run_started_at": attempts.get("run_started_at"),
            "full_run_completed_at": attempts.get("run_completed_at"),
            "full_population_queries_recorded": sum(len(t.get("queries") or []) for t in attempt_traces),
            "full_population_source_entries_recorded": raw_source_packets,
            "full_population_unique_source_urls": len(unique_raw_source_urls),
            "live_agent_queries_recorded": sum(len(t.get("queries") or []) for t in live_attempt_traces),
            "live_agent_source_entries_recorded": live_source_packets,
            "live_agent_unique_source_urls": len(live_unique_urls),
            "prior_capture_queries_recorded": sum(len(t.get("queries") or []) for t in prior_attempt_traces),
            "prior_capture_source_entries_recorded": prior_source_packets,
            "prior_capture_unique_source_urls": len(prior_unique_urls),
            "sample_verification_search_events": len(capture.get("search_events", [])) - len(capture.get("post_recheck_search_events", [])),
            "post_recheck_search_events": len(capture.get("post_recheck_search_events", [])),
            "sample_source_packets_unique_by_url": capture.get("source_packet_count"),
            "sample_first_pass_evidence_items": capture.get("first_pass_evidence_packet_count"),
            "sample_verification_ledger_rows": len(ledger.get("checks", [])),
            "sample_post_recheck_rows": len(read_json("data/evidence/final_post_recheck.json").get("checks", [])),
            "post_recheck_audit_id": read_json("data/evidence/final_post_recheck.json").get("audit_id"),
            "recorded_capture_failures_and_limits": len(capture.get("fetch_failures_and_extraction_limits", [])),
            "provider_credentials": attempts.get("provider_credentials", {}),
            "retry_note": "The 76 LIVE_AGENT records came from preserved native Arena.ai web_search/fetch_page batches; they are not Tavily/OpenAI or Composio runs. The 24 PRIOR_CAPTURE records retain incomplete historical per-call retry detail, so those retry counts are unmeasurable. Verification and post-correction reopens are distinct page inspections, not provider retries.", 
        },
        "human_review": {
            "status": "HUMAN VERIFICATION NOT POSSIBLE",
            "human_verification_claimed": False,
            "authorized_tenant_access_available": False,
            "final_sample_rows_recorded_not_possible": 120,
            "checklist": "reports/human_qa.md",
            "template": "data/evidence/human_qa_template.csv",
            "note": "No authorized vendor tenant, credentials, or human reviewer with account access was provided. This is a blocker, not completed human QA; the CSV records a reason and checklist for each critical-field row.",
        }, 
        "pilot_metrics_separate": {
            "scope": "Five-app engineering pilot only; excluded from all final-sample and 100-app denominators.",
            "ledger": PILOT_LEDGER_PATH,
            "metrics": pilot.get("metrics", {}),
        },
        "reproduction": {
            "research_assembly": "Preserved first-pass output: data/raw/final_full_research.json and data/raw/final_full_attempts.json; native web batches 01–07 plus 24 historical captures. Research/reconciliation is complete for this snapshot; this is provenance, not a rerunnable fetch command. Do not rerun scripts/assemble_native_capture_population.py against the reconciled files; it expects the archived initial 24+76 baseline.",
            "sample_selection": "python scripts/select_verification_sample.py --research data/raw/final_full_research.json --target-size 20 --seed 20260924",
            "verification_input_builder": "python scripts/build_final_verification_inputs.py --post-recheck-input data/evidence/final_post_recheck_input.json",
            "verification": "python scripts/run_verification.py --research data/raw/final_full_research.json --ledger data/evidence/final_verification_ledger_input.json --post-recheck data/evidence/final_post_recheck.json --source-capture data/evidence/final_sample_source_captures.json --manifest apps/apps.json --attempt-log data/raw/final_full_attempts.json --output data/verified/final_dataset.json --ledger-output data/verified/final_verification_ledger.json --quality-report data/verified/final_quality_report.json --report reports/final_verification_report.md",
            "human_qa": "python scripts/build_human_qa_template.py  # records HUMAN VERIFICATION NOT POSSIBLE; does not perform human review",
            "analysis": "python scripts/analyze_verified_dataset.py",
            "html": "python scripts/render_final_case_study.py",
            "package_site": "python scripts/package_public_site.py  # copies the local QA guide/checklist; does not deploy",
            "tests": "python -m unittest discover -s tests -v",
        },
        "matrix": app_matrix,
    }
    return artifact


def blocker_pattern_counts(records: list[dict]) -> dict[str, int]:
    patterns = {
        "admin_or_role_permission": ("admin", "role", "permission", "approval"),
        "paid_or_commercial_gate": ("paid", "enterprise", "sales", "partner", "subscription", "plan"),
        "credential_or_scope": ("credential", "token", "api key", "oauth", "scope"),
        "rate_or_usage_limit": ("rate limit", "quota", "usage", "limit"),
        "unknown_or_unresolved": ("unknown", "unresolved", "not established", "not verified"),
    }
    out = {}
    for name, terms in patterns.items():
        count = 0
        for r in records:
            text = str((r.get("buildability") or {}).get("blocker", "")).lower()
            if any(term in text for term in terms):
                count += 1
        out[name] = count
    out["no_blocker_text"] = sum(not str((r.get("buildability") or {}).get("blocker", "")).strip() for r in records)
    return out


def write_reports(analysis: dict) -> None:
    metrics = analysis["verification"]["metrics"]
    field_accuracy = metrics.get("field_accuracy", {})
    lines = [
        "# Final dataset analysis", "",
        "**Status: 100-app first-pass research is reconciled (76 LIVE_AGENT, 24 PRIOR_CAPTURE; 97 COMPLETE, 3 PARTIAL). The final project remains INCOMPLETE pending public repository/deployment; account-dependent human QA is explicitly recorded as HUMAN VERIFICATION NOT POSSIBLE, not as a completed pass. No probability-sample claim is made.**", "",
        "## Scope and denominator", "",
        f"- Manifest rows: **{analysis['scope']['manifest_count']}**; final dataset rows: **{analysis['scope']['dataset_record_count']}**; exact reconciliation: **{'PASS' if analysis['scope']['manifest_reconciles_exactly'] else 'FAIL'}**.",
        f"- Research mode: **{format_counts(analysis['scope']['source_mode_counts'])}**; research status: **{format_counts(analysis['scope']['research_status_counts'])}**.",
        f"- All 100 apps have a researched record: {analysis['scope']['live_agent_count']} native `LIVE_AGENT` captures and {analysis['scope']['prior_capture_count']} historical `PRIOR_CAPTURE` records; `NOT_RUN`={analysis['scope']['not_run_count']}. Historical rows are not relabeled as live.",
        f"- Source evidence items in corrected dataset: **{analysis['scope']['all_records_evidence_item_count']}** total; **{analysis['scope']['captured_records_evidence_item_count']}** among researched records. These counts include verification evidence patches in the selected sample.",
        "- Any retained UNKNOWN is a bounded identity/source or product-status uncertainty; it is not silently treated as NO.", 
        "",
        "## Auth, access, API, MCP and buildability", "",
        "Counts below separate the entire 100-row manifest, selected audit sample and fully adjudicated sample. `UNKNOWN` remains distinct from `NO`; all denominators and unresolved rows are stated explicitly.",
        "",
    ]
    label_map = {"auth": "Authentication status", "self_serve": "Self-serve status", "credential_access": "Credential-access status", "api_availability": "API availability", "mcp": "MCP status", "buildability": "Buildability verdict"}
    for group, label in label_map.items():
        lines.append(f"### {label}")
        for cohort, cohort_counts in analysis["critical_field_distributions"][group].items():
            lines.append(f"- `{cohort}`: {format_counts(cohort_counts)}")
        lines.append("")
    lines += [
        "### API interfaces and breadth", "",
        f"- Interface types by cohort: {format_cohort_counts(analysis['api']['interface_type_counts'])}.",
        f"- Breadth by cohort: {format_cohort_counts(analysis['api']['breadth'])}.",
        "- SDKs and documented webhook interfaces remain separate from REST. Freshdesk's corrected selected-sample record describes outbound webhook automation while retaining `api.types=REST`. A separate Gorgias terminology audit (`data/evidence/api_webhook_nomenclature_audit.json`, outside the accuracy sample) records outbound HTTP/webhook actions and keeps REST; it does not amend the current final record or sample metrics. Neither capability is labeled a dedicated Webhooks API. Public references do not prove tenant-specific entitlement.",
        "",
        "### Easy-win / outreach rule result", "",
        f"- Selected 20-app sample: {format_counts(analysis['easy_win_outreach']['selected_20_triage_counts'])}.",
        f"- Full manifest status: {format_counts(analysis['easy_win_outreach']['all_100_triage_counts'])} (only fully adjudicated sample records can receive Easy-win/Outreach/Constrained labels; every other app stays NEEDS_REVIEW).",
        "- Full deterministic rule is recorded in `data/analysis/final_analysis.json`; PAID_PLAN_REQUIRED, ENTERPRISE_ONLY and PARTNER_OR_CONTACT_SALES count as outreach gates. Admin-only/restricted paths are not automatically called outreach.",
        "",
        "## Ten-category coverage", "",
        "| Category | Manifest | Prior capture | Live agent | Not run | Selected sample | Fully adjudicated sample | Captured API YES | Captured MCP available |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in analysis["category_summary"]:
        lines.append(f"| {row['category']} | {row['manifest_count']} | {row['prior_capture_count']} | {row['live_agent_count']} | {row['not_run_count']} | {row['selected_sample_count']} | {row['fully_adjudicated_sample_count']} | {row['captured_api_yes_count']} | {row['captured_mcp_available_count']} |")
    v = metrics.get("field_accuracy", {})
    ra = metrics.get("record_accuracy", {})
    lines += [
        "", "## Final verification sample metrics (separate from the pilot)", "",
        f"- Selected IDs (selection order): {', '.join(map(str, analysis['sample']['selected_ids_in_selection_order']))}; deterministic seed `{analysis['sample']['seed']}`; provenance {format_counts(analysis['sample']['source_mode_counts'])}; categories covered {analysis['sample']['selected_category_count']}/10; observed strata covered {analysis['sample']['covered_strata_count']}/{analysis['sample']['observed_strata_count']}.",
        f"- Critical rows: {metrics.get('critical_rows_present')}; adjudicable: {metrics.get('critical_rows_adjudicable')}; unresolved: {metrics.get('critical_rows_unresolved')}.",
    ]
    for group, data in v.items():
        lines.append(f"- **{group}:** {data['correct']}/{data['checked']} = {100*data['correct']/data['checked']:.1f}%" if data["checked"] else f"- **{group}:** N/A; unresolved {data['unresolved']}")
    lines += [
        f"- Record accuracy: {ra.get('correct')}/{ra.get('checked')} fully adjudicable records; partial/unadjudicable: {ra.get('partial_or_unadjudicable')}.",
        f"- Critical post-correction concordance: {format_counts(metrics.get('post_correction_overall', {}))}.",
        f"- All changed-row post-recheck concordance (critical + supplemental): {format_counts(metrics.get('post_recheck_all_rows', {}))}.",
        f"- Post-recheck capture: {analysis['verification']['post_recheck_row_count']} explicit observations; independence levels {format_counts(metrics.get('post_recheck_audit', {}).get('independence_level_counts', {}))}; date-only retrieval precision. Twelve changed rows were re-opened; {metrics.get('post_correction_overall', {}).get('not_rechecked', 0)} other critical rows were not rechecked.",
        "- These are source-assisted audit-sample measurements, not held-out truth, estimates of population accuracy, or independent human quality. The sample is a deterministic weighted coverage sample, not a probability sample; no statistical generalization to all 100 apps is warranted.", 
        "",
        "### Engineering pilot (reported separately)", "",
        f"- Pilot field metrics: {format_cohort_counts(analysis['pilot_metrics_separate']['metrics'].get('field_accuracy', {}))}.",
        f"- Pilot record accuracy: {format_counts(analysis['pilot_metrics_separate']['metrics'].get('record_accuracy', {}))}; pilot post-correction: {format_counts(analysis['pilot_metrics_separate']['metrics'].get('post_correction_overall', {}))}.",
        "- Pilot numbers are not pooled with final-sample metrics.",
        "",
        "## Observed error analysis", "",
        f"- Critical-label mismatches: **{analysis['observed_error_analysis']['critical_mismatch_count']}**; supplemental changes: **{analysis['observed_error_analysis']['supplemental_change_count']}**.",
        "- Detailed observed examples, causes, exact changes, source URLs, second-pass outcomes, and prevention actions are in `reports/final_error_analysis.md`.",
        "",
        "## Provenance and quality limits", "",
        f"- Full manifest run: `{analysis['provenance']['full_run_mode']}`; credentials: `{analysis['provenance']['provider_credentials']}`.",
        f"- First-pass trace breakdown: LIVE_AGENT={analysis['provenance']['live_agent_queries_recorded']} queries/{analysis['provenance']['live_agent_source_entries_recorded']} source entries/{analysis['provenance']['live_agent_unique_source_urls']} unique URLs; PRIOR_CAPTURE={analysis['provenance']['prior_capture_queries_recorded']} queries/{analysis['provenance']['prior_capture_source_entries_recorded']} source entries/{analysis['provenance']['prior_capture_unique_source_urls']} unique URLs; total={analysis['provenance']['full_population_queries_recorded']} queries/{analysis['provenance']['full_population_source_entries_recorded']} source entries/{analysis['provenance']['full_population_unique_source_urls']} unique URLs.",
        f"- Sample capture: {analysis['provenance']['sample_source_packets_unique_by_url']} unique-by-URL source packets; {analysis['provenance']['sample_verification_search_events']} search events; {analysis['provenance']['sample_verification_ledger_rows']} ledger rows; {analysis['provenance']['sample_post_recheck_rows']} separate post-recheck rows; {analysis['provenance']['recorded_capture_failures_and_limits']} recorded fetch failures/limits.",
        f"- Corrected-dataset quality gate: **{analysis['quality_gate']['status']}**; record counts `{format_counts(analysis['quality_gate']['record_quality_counts'])}`; warnings {analysis['quality_gate']['warning_count']}.",
        "- Exact retrieval times were not exposed by web tools; the captures preserve date-only precision. The post-correction check independently reopened all 12 changed rows (3 critical + 9 supplemental); concordance is reported separately and is not held-out truth.",
        "- Human QA is recorded as **HUMAN VERIFICATION NOT POSSIBLE** because no authorized vendor tenant/credentials or reviewer were available; it is not a completed human pass. See `reports/human_qa.md` and the 120 row-level checklists in `data/evidence/human_qa_template.csv`.", 
        "",
        "## Reproduction", "",
        "Run commands and artifact paths are in `README.md` and `data/analysis/final_analysis.json`. The analysis reads the corrected dataset and audit artifacts; the HTML renderer reads only this analysis JSON and `data/verified/final_dataset.json`.",
        "",
    ]
    (ROOT / ANALYSIS_MD_PATH).write_text("\n".join(lines), encoding="utf-8")

    error_lines = [
        "# Observed verification errors and corrections", "",
        "This report includes only rows actually changed by the final sample verification ledger. Critical label mismatches are separated from supplemental detail/scope changes; no hypothetical error is counted.", "",
        f"- Critical first-pass mismatches: **{analysis['observed_error_analysis']['critical_mismatch_count']}**.",
        f"- Supplemental observed changes: **{analysis['observed_error_analysis']['supplemental_change_count']}**.",
        f"- Critical post-correction recheck: `{format_counts(analysis['observed_error_analysis']['post_correction_critical_concordance'])}`.",
        f"- All changed rows rechecked: `{format_counts(analysis['observed_error_analysis']['post_recheck_all_changed_rows'])}`.",
        "",
    ]
    for group in analysis["observed_error_analysis"]["error_type_summary"]:
        error_lines += [
            f"## {group['label']} (`{group['error_type']}`) — {group['count']} row(s)", "",
            f"**Observed cause:** {group['cause']}", "",
            f"**Prevention:** {group['prevention']}", "",
        ]
    error_lines += [
        "## Row-level examples", "",
        "| App | Field | First pass | Verified | Type | Cause / evidence basis | Correction | Source(s) | Post-recheck |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in analysis["observed_error_analysis"]["examples"]:
        def cell(v: Any) -> str:
            return json.dumps(v, ensure_ascii=False).replace("|", "\\|").replace("\n", " ")
        src = ", ".join(f"[{i+1}]({url})" for i, url in enumerate(row["source_urls"]))
        error_lines.append(f"| {row['app']} | `{row['field']}` | `{cell(row['first_pass'])}` | `{cell(row['verified'])}` | `{row['error_type']}` | {row['cause'].replace('|', '\\|')} | {row['correction'].replace('|', '\\|')} | {src} | {row['post_recheck_correctness'] or 'not rechecked'} ({row['independence_level'] or 'n/a'}) |")
    error_lines += ["", "No person performed these checks. This is automated/source-assisted verification and is not a human review record.", ""]
    (ROOT / ERROR_MD_PATH).write_text("\n".join(error_lines), encoding="utf-8")

    category_path = ROOT / CATEGORY_CSV_PATH
    category_path.parent.mkdir(parents=True, exist_ok=True)
    with category_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(analysis["category_summary"][0].keys()))
        writer.writeheader()
        writer.writerows(analysis["category_summary"])
    triage_path = ROOT / TRIAGE_CSV_PATH
    triage_path.parent.mkdir(parents=True, exist_ok=True)
    with triage_path.open("w", newline="", encoding="utf-8") as f:
        triage_output_rows = analysis["easy_win_outreach"]["rows"]
        writer = csv.DictWriter(f, fieldnames=list(triage_output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(triage_output_rows)


def main() -> int:
    analysis = build_analysis()
    write_json(ANALYSIS_PATH, analysis)
    write_reports(analysis)
    print(f"Analyzed {analysis['scope']['dataset_record_count']} manifest rows; captured={analysis['scope']['captured_record_count']}, NOT_RUN={analysis['scope']['not_run_count']}, sample={analysis['sample']['selected_count']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

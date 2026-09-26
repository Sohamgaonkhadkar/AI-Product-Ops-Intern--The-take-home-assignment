#!/usr/bin/env python3
"""Record the final sample's human-QA blocker and a field-specific checklist.

No human review is claimed. Rows explicitly say HUMAN VERIFICATION NOT
POSSIBLE when no authorized account/reviewer is available, with a reason and
concrete steps for a later authorized reviewer. The checklist never stores
secrets and never converts public documentation into a tenant test.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/evidence/human_qa_template.csv"

CHECKS = {
    "auth_methods": [
        "Review the current first-party authentication page for the exact API/version and compare each documented method with the normalized value; public docs alone do not prove tenant policy.",
        "Where the claim depends on org policy or OAuth-client enablement, confirm with an authorized administrator without creating or exposing a secret.",
        "Record any missing/unsupported method and a non-sensitive official source or admin confirmation.",
    ],
    "self_serve_status": [
        "Confirm the current signup/trial/plan route for the intended product and region using an authorized account.",
        "Check whether payment, identity verification, admin approval, partner review, a paid tier, or sales contact is required for the specific access path.",
        "Distinguish product signup from API/MCP feature entitlement; record the account-specific result without payment or account changes unless authorized.",
    ],
    "credential_access.status": [
        "Using an authorized target tenant, identify which role can create or authorize the required credential and where that UI/flow exists.",
        "Confirm scope, approval, expiry and plan gates; never copy passwords, API keys, OAuth codes or tokens into this file.",
        "Record only non-sensitive role/path/outcome and the supporting page or administrator confirmation.",
    ],
    "api.available": [
        "Confirm API enablement for the actual tenant/edition/plan and the interface used by the proposed integration.",
        "Check required API roles, permissions, developer tokens, rate/access level and any regional/organization gate.",
        "Do not infer tenant API access from a public reference or signup page; retain UNKNOWN if the check is unavailable.",
    ],
    "mcp.status": [
        "Confirm a product-specific first-party MCP endpoint/setup guide and the target account's plan, OAuth/client, admin and tool prerequisites.",
        "If availability is unknown, check first-party developer/support/repository sources and obtain an authorized product owner confirmation; an empty search is not proof of NO.",
        "Test only with an authorized tenant, least privilege and non-production data; record endpoint/feature status, not secrets.",
    ],
    "buildability.verdict": [
        "Re-evaluate the proposed integration against the actual tenant's API, auth, role, plan, approval, policy and operational constraints.",
        "For local tooling, follow the first-party install/runtime steps in a clean, authorized environment; do not claim a build/test unless executed.",
        "Record any changed blocker and evidence; do not equate public documentation with a successful tenant or package test.",
    ],
}


def scalar(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def main() -> int:
    selection = json.loads((ROOT / "data/evidence/verification_sample_selection.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "data/raw/final_full_research.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/verified/final_verification_ledger.json").read_text(encoding="utf-8"))
    capture = json.loads((ROOT / "data/evidence/final_sample_source_captures.json").read_text(encoding="utf-8"))
    raw_by_id = {r["app_id"]: r for r in raw}
    checks = {(r["app_id"], r["field_path"]): r for r in ledger["checks"] if r.get("metric_group")}
    candidate_urls = {}
    for packet in capture.get("source_packets", []):
        for app_id in packet.get("candidate_identity_context_apps", []):
            candidate_urls.setdefault(app_id, []).append(packet.get("source_url", ""))
    rows = []
    for app_id in selection["selected_ids"]:
        app = raw_by_id[app_id]
        for field, checklist in CHECKS.items():
            item = checks[(app_id, field)]
            sources = [item.get("source") or {}, *(item.get("supporting_sources") or [])]
            urls = list(dict.fromkeys(s.get("source_url", "") for s in sources if s.get("source_url")))
            titles = list(dict.fromkeys(s.get("source_title", "") for s in sources if s.get("source_title")))
            blocker = "No authorized vendor tenant/credentials and no human reviewer with access were provided in the workspace. This row was not manually checked; public-source verification is not an account/tenant test."
            specific = item.get("reason", "")
            tailored_checklist = list(checklist)
            if app_id == 84:
                blocker = "Product identity is unresolved and no authorized account/reviewer is available. Do not select Paygent Japan, NMI, or another candidate by guess; all product-specific values remain UNKNOWN."
                tailored_checklist.insert(0, "First identify the manifest's exact Paygent Connect product with the user or a first-party identity link. Candidate Paygent/NMI URLs below are identity context only, not evidence attributed to this app.")
            elif app_id == 27:
                tailored_checklist.append("Telegram core documentation returned HTTP 403 in the research pass; verify cloud bot credential onboarding from an authorized official account path. The TDLib self-hosted server path does not settle standard cloud account/plan facts.")
            elif app_id == 23 and field == "auth_methods":
                tailored_checklist.append("Reopen the current Cliq REST/OAuth documentation or ask an authorized Zoho administrator; the extracted OAuth page rendered 'No Results Found'. Do not reuse the historical OAuth/bearer observation as a new check.")
            elif app_id == 9 and field == "mcp.status":
                tailored_checklist.append("Keep MCP UNKNOWN unless Copper first-party product documentation or an authorized Copper owner confirms a product-specific MCP; lack of a search result is not NO.")
            elif app_id == 91 and field == "mcp.status":
                tailored_checklist.append("Keep NotebookLM Enterprise MCP UNKNOWN unless a product-specific first-party Google Cloud endpoint/setup is confirmed; do not substitute a generic Google Cloud MCP.")
            elif app_id == 98 and field == "buildability.verdict":
                tailored_checklist.append("No npm installation or Mermaid render was executed. If the local CLI verdict is in scope, install in a clean environment and render a fixture without claiming hosted API/MCP behavior.")
            rows.append({
                "status": "HUMAN VERIFICATION NOT POSSIBLE",
                "access_available": "NO",
                "status_reason": blocker,
                "reviewer": "",
                "review_date": "",
                "app_id": app_id,
                "app": app["app"],
                "category": app["category"],
                "field": field,
                "first_pass_value": scalar(item["initial_value"]),
                "current_verified_value": scalar(item["verified_value"]),
                "human_checklist": json.dumps(tailored_checklist, ensure_ascii=False),
                "public_verification_reason_or_limit": specific,
                "evidence_urls": " ; ".join(urls),
                "evidence_titles": " ; ".join(titles),
                "candidate_identity_context_only_urls": " ; ".join(dict.fromkeys(candidate_urls.get(app_id, []))) if app_id == 84 else "",
                "human_result": "",
                "correction": "",
                "review_notes": "",
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} HUMAN VERIFICATION NOT POSSIBLE rows for {len(selection['selected_ids'])} selected apps to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

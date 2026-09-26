#!/usr/bin/env python3
"""Reconcile native-web captures with the preserved historical first-pass baseline.

This step does not fabricate new research and does not relabel PRIOR_CAPTURE rows.
It replaces only the original NOT_RUN placeholders with the matching standalone
LIVE_AGENT capture records after verifying exact manifest coverage and per-record
trace counts. The original incomplete baseline is archived byte-for-byte first.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.quality import validate_final_dataset
from src.utils.validation import validate_manifest, validate_record

MANIFEST = ROOT / "apps/apps.json"
RAW_JSON = ROOT / "data/raw/final_full_research.json"
RAW_CSV = ROOT / "data/raw/final_full_research.csv"
RAW_ATTEMPTS = ROOT / "data/raw/final_full_attempts.json"
RAW_QUALITY = ROOT / "data/raw/final_full_quality_report.json"
RAW_REPORT = ROOT / "reports/final_research_run_report.md"
CAPTURE_FILES = [
    *(ROOT / f"data/evidence/native_web_capture_batch{i:02d}_2026-09-24.json" for i in range(1, 7)),
    ROOT / "data/evidence/native_web_capture_batch07_2026-09-25.json",
]
ARCHIVE_DIR = ROOT / "data/archive/pre_native_capture_reconciliation_2026-09-25"
OUTPUTS = {
    "records": RAW_JSON,
    "csv": RAW_CSV,
    "attempts": RAW_ATTEMPTS,
    "quality": RAW_QUALITY,
    "report": RAW_REPORT,
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(records: list[dict], path: Path) -> None:
    columns = [
        "app_id", "app", "category", "description", "auth_status", "auth_methods",
        "self_serve_status", "credential_access_status", "api_available", "api_types",
        "api_breadth", "mcp_status", "buildability_verdict", "source_mode",
        "research_tool", "research_timestamp", "query_count", "source_count",
        "attempt_count", "research_status", "verification_status", "quality_gate_status",
        "evidence_count",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in records:
            w.writerow({
                "app_id": r.get("app_id"), "app": r.get("app"), "category": r.get("category"),
                "description": r.get("description"), "auth_status": r.get("auth_status"),
                "auth_methods": "; ".join(r.get("auth_methods", [])),
                "self_serve_status": r.get("self_serve_status"),
                "credential_access_status": (r.get("credential_access") or {}).get("status"),
                "api_available": (r.get("api") or {}).get("available"),
                "api_types": "; ".join((r.get("api") or {}).get("types", [])),
                "api_breadth": (r.get("api") or {}).get("breadth"),
                "mcp_status": (r.get("mcp") or {}).get("status"),
                "buildability_verdict": (r.get("buildability") or {}).get("verdict"),
                "source_mode": r.get("source_mode"), "research_tool": r.get("research_tool"),
                "research_timestamp": r.get("research_timestamp"), "query_count": r.get("query_count"),
                "source_count": r.get("source_count"), "attempt_count": r.get("attempt_count"),
                "research_status": r.get("research_status"), "verification_status": r.get("verification_status"),
                "quality_gate_status": (r.get("quality_gate") or {}).get("status"),
                "evidence_count": len(r.get("evidence", [])),
            })


def preserve_baseline() -> dict:
    """Copy pre-reconciliation files once and confirm every copy is byte-identical."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archived = {}
    for name, path in OUTPUTS.items():
        if not path.exists():
            continue
        target = ARCHIVE_DIR / f"initial_{path.name}"
        if target.exists():
            if sha(target) != sha(path):
                raise RuntimeError(f"Refusing to overwrite archive with a different baseline: {target}")
        else:
            shutil.copy2(path, target)
        if sha(target) != sha(path):
            raise RuntimeError(f"Baseline preservation hash mismatch for {path}")
        archived[name] = {"original_path": str(path.relative_to(ROOT)), "archive_path": str(target.relative_to(ROOT)), "sha256": sha(target)}
    return archived


def main() -> int:
    started = now()
    manifest = read_json(MANIFEST)
    manifest_errors = validate_manifest(manifest)
    if manifest_errors:
        raise ValueError("Canonical manifest invalid: " + "; ".join(manifest_errors))
    manifest_by_id = {r["app_id"]: r for r in manifest}

    baseline = read_json(RAW_JSON)
    if not isinstance(baseline, list) or len(baseline) != len(manifest):
        raise ValueError("Initial raw first-pass dataset is not an exact manifest-sized list")
    baseline_by_id = {r.get("app_id"): r for r in baseline}
    if len(baseline_by_id) != len(baseline) or set(baseline_by_id) != set(manifest_by_id):
        raise ValueError("Initial raw dataset IDs do not exactly match apps/apps.json")
    prior = {i: copy.deepcopy(r) for i, r in baseline_by_id.items() if r.get("source_mode") == "PRIOR_CAPTURE"}
    not_run = {i: r for i, r in baseline_by_id.items() if r.get("source_mode") == "NOT_RUN"}
    if len(prior) != 24 or len(not_run) != 76:
        raise ValueError(f"Expected the audited 24 prior + 76 NOT_RUN baseline; found {len(prior)} + {len(not_run)}")

    baseline_attempt_log = read_json(RAW_ATTEMPTS)
    if baseline_attempt_log.get("mode") != "PRIOR_CAPTURE_ASSEMBLY_NO_PROVIDER_CREDENTIALS":
        raise ValueError("Initial attempt log is not the expected prior-capture baseline")
    prior_ids = set(prior)
    prior_traces = {t.get("app_id"): copy.deepcopy(t) for t in baseline_attempt_log.get("traces", []) if t.get("app_id") in prior_ids}
    if set(prior_traces) != prior_ids:
        raise ValueError(f"Prior capture trace coverage mismatch: missing={sorted(prior_ids-set(prior_traces))}")

    baseline_ids = set(not_run)
    capture_records: dict[int, dict] = {}
    capture_traces: dict[int, dict] = {}
    capture_metadata = []
    for path in CAPTURE_FILES:
        if not path.exists():
            raise FileNotFoundError(path)
        artifact = read_json(path)
        if artifact.get("source_mode") != "LIVE_AGENT":
            raise ValueError(f"Capture is not labeled LIVE_AGENT: {path}")
        recs = artifact.get("records", [])
        traces = artifact.get("traces", [])
        record_ids = [r.get("app_id") for r in recs]
        trace_ids = [t.get("app_id") for t in traces]
        if len(record_ids) != len(set(record_ids)) or set(record_ids) != set(trace_ids):
            raise ValueError(f"Record/trace coverage mismatch within {path}")
        capture_metadata.append({
            "file": str(path.relative_to(ROOT)),
            "sha256": sha(path),
            "run_id": artifact.get("run_id"),
            "source_mode": artifact.get("source_mode"),
            "record_count": len(recs),
            "app_ids": sorted(record_ids),
        })
        for record, trace in zip(recs, traces):
            app_id = record.get("app_id")
            if app_id in capture_records:
                raise ValueError(f"Duplicate native capture record app_id={app_id}")
            if app_id not in manifest_by_id:
                raise ValueError(f"Native capture app_id={app_id} is not in apps/apps.json")
            expected = manifest_by_id[app_id]
            for field in ("app", "category"):
                if record.get(field) != expected.get(field):
                    raise ValueError(f"app_id={app_id} {field} does not match canonical manifest")
            if app_id not in baseline_ids:
                raise ValueError(f"Native capture attempts to replace a non-NOT_RUN baseline row: app_id={app_id}")
            if record.get("source_mode") != "LIVE_AGENT" or trace.get("source_mode") != "LIVE_AGENT":
                raise ValueError(f"app_id={app_id} must remain LIVE_AGENT in both record and trace")
            if trace.get("status") not in {"COMPLETE", "OK", "PARTIAL"}:
                raise ValueError(f"app_id={app_id} has unrecognized capture trace status {trace.get('status')!r}")
            if trace.get("status") == "PARTIAL" and record.get("research_status") != "PARTIAL":
                raise ValueError(f"app_id={app_id} partial trace is not reflected in research_status")
            if record.get("query_count") != len(trace.get("queries", [])):
                raise ValueError(f"app_id={app_id} query_count does not match native trace")
            if record.get("source_count") != len(trace.get("sources", [])):
                raise ValueError(f"app_id={app_id} source_count does not match native trace")
            if record.get("attempt_count") != len(trace.get("attempts", [])):
                raise ValueError(f"app_id={app_id} attempt_count does not match native trace")
            structural = validate_record(record)
            if structural:
                raise ValueError(f"app_id={app_id} structural validation failed: {structural}")
            capture_records[app_id] = copy.deepcopy(record)
            capture_traces[app_id] = copy.deepcopy(trace)

    if set(capture_records) != baseline_ids:
        raise ValueError(f"Native captures do not exactly replace NOT_RUN rows: missing={sorted(baseline_ids-set(capture_records))}; extra={sorted(set(capture_records)-baseline_ids)}")

    records_by_id = {**prior, **capture_records}
    traces_by_id = {**prior_traces, **capture_traces}
    if set(records_by_id) != set(manifest_by_id) or set(traces_by_id) != set(manifest_by_id):
        raise ValueError("Merged records or traces do not reconcile exactly to the canonical manifest")
    records = [records_by_id[i] for i in sorted(records_by_id)]
    traces = [traces_by_id[i] for i in sorted(traces_by_id)]

    completed_at = now()
    run = "native-capture-reconciliation-20260925"
    attempt_log = {
        "schema_version": "1.0",
        "run_id": run,
        "mode": "NATIVE_WEB_CAPTURE_RECONCILIATION",
        "run_started_at": started,
        "run_completed_at": completed_at,
        "manifest_file": "apps/apps.json",
        "provider_credentials": {
            "TAVILY_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL",
            "OPENAI_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL",
        },
        "initial_baseline": {
            "file": "data/raw/final_full_research.json",
            "source_mode_counts": {"PRIOR_CAPTURE": len(prior), "NOT_RUN": len(not_run)},
            "preserved_original_files": "data/archive/pre_native_capture_reconciliation_2026-09-25/",
        },
        "native_capture_batches": capture_metadata,
        "trace_limitations": [
            "PRIOR_CAPTURE traces retain the original query/source packets from the prior-capture assembly, but original per-call attempt arrays and attempt counts were not preserved; record attempt_count remains null where the original dataset did not have it.",
            "LIVE_AGENT records are native web_search + directly opened fetch_page captures; they are not provider-backed Tavily/OpenAI runs and do not imply authenticated vendor, API, MCP, Composio, or human checks.",
            "Search snippets are discovery only. Source URLs and observed chunks are preserved in the standalone capture artifacts and joined traces.",
            "This reconciliation does not select a verification sample or apply corrections. Verification and human QA remain later stages.",
        ],
        "traces": traces,
    }
    quality = validate_final_dataset(records, manifest, attempt_log)
    if quality["status"] == "FAIL":
        raise ValueError("Manifest-wide validation failed; outputs were not written: " + "; ".join(quality["errors"]))

    modes = Counter(r.get("source_mode") for r in records)
    statuses = Counter(r.get("research_status") for r in records)
    unknown_slots = sum(sum((
        r.get("auth_status") == "UNKNOWN",
        r.get("self_serve_status") == "UNKNOWN",
        (r.get("credential_access") or {}).get("status") == "UNKNOWN",
        (r.get("api") or {}).get("available") == "UNKNOWN",
        (r.get("mcp") or {}).get("status") == "UNKNOWN",
        (r.get("buildability") or {}).get("verdict") == "UNKNOWN",
    )) for r in records)
    query_total = sum(len(t.get("queries", [])) for t in traces)
    source_total = sum(len(t.get("sources", [])) for t in traces)
    live_attempt_total = sum(len(t.get("attempts", [])) for t in traces if t.get("source_mode") == "LIVE_AGENT")
    evidence_total = sum(len(r.get("evidence", [])) for r in records)
    initial_hashes = {name: sha(path) for name, path in OUTPUTS.items() if path.exists()}

    report_lines = [
        "# Full-population native capture reconciliation", "",
        "- **Status:** 100/100 manifest IDs have a research record; 76 new LIVE_AGENT native-web captures replace the previous NOT_RUN placeholders, while 24 historical rows remain PRIOR_CAPTURE. This is not an all-live provider run.",
        f"- **Run ID:** `{run}`",
        f"- **Started/completed (UTC):** {started} / {completed_at}",
        "- **Canonical manifest:** `apps/apps.json`",
        "- **Initial raw dataset:** preserved byte-for-byte in `data/archive/pre_native_capture_reconciliation_2026-09-25/`; the original values remain auditable.",
        "- **Reconciled first-pass raw dataset:** `data/raw/final_full_research.json` and `.csv` (still separate from `data/verified/final_dataset.json`).",
        "- **Attempt log:** `data/raw/final_full_attempts.json`; **quality audit:** `data/raw/final_full_quality_report.json`.",
        f"- **Source modes:** {dict(sorted(modes.items()))}",
        f"- **Research status:** {dict(sorted(statuses.items()))}",
        f"- **Record/trace coverage:** {len(records)}/{len(manifest)} records and {len(traces)}/{len(manifest)} traces, exact ID match.",
        f"- **Queries / source packets:** {query_total} / {source_total}",
        f"- **Logged LIVE_AGENT attempts:** {live_attempt_total}; historical PRIOR_CAPTURE per-call attempt counts were not preserved and were not reconstructed.",
        f"- **Claim-linked evidence rows:** {evidence_total}",
        f"- **Unknown critical-field slots:** {unknown_slots} (UNKNOWN remains distinct from NO).",
        f"- **Manifest-wide quality:** {quality['status']} — {quality['record_quality_counts']}; blocking errors: {len(quality['errors'])}; warnings: {len(quality['warnings'])}.",
        "- **Verification sample:** not selected by this reconciliation step; it must be selected only after this full-population gate passes.",
        "- **Human checks / authenticated access:** not performed or claimed.",
        "", "## Capture batches", "", "| Capture | Run ID | Apps | IDs | SHA-256 |", "|---|---|---:|---|---|",
    ]
    for b in capture_metadata:
        report_lines.append(f"| `{b['file']}` | `{b['run_id']}` | {b['record_count']} | {', '.join(map(str, b['app_ids']))} | `{b['sha256']}` |")
    report_lines += ["", "## Quality warnings", ""]
    if quality["warnings"]:
        report_lines.extend(f"- {w}" for w in quality["warnings"])
    else:
        report_lines.append("No quality warnings.")
    report_lines += [
        "", "## Provenance and unresolved findings", "",
        "- `LIVE_AGENT` means native web search and direct page inspection only. It is never used for the historical 24 `PRIOR_CAPTURE` rows.",
        "- ID84 Paygent Connect remains unresolved by explicit instruction; product-specific API/auth/MCP fields remain UNKNOWN.",
        "- ID100 Grain retains the first-party API-version conflict and unverified MCP authentication/tool entitlements.",
        "- ID99 TranscriptAPI preserves conflicting official rate-limit statements across REST, MCP, and pricing tiers.",
        "- No sample correction, human account check, deployment, or repository publication occurred in this stage.",
    ]
    run_report = "\n".join(report_lines) + "\n"

    archived = preserve_baseline()
    reconciliation = {
        "schema_version": "1.0",
        "run_id": run,
        "run_started_at": started,
        "run_completed_at": completed_at,
        "manifest_file": "apps/apps.json",
        "initial_baseline_source_mode_counts": {"PRIOR_CAPTURE": len(prior), "NOT_RUN": len(not_run)},
        "initial_raw_hashes": initial_hashes,
        "preserved_original_files": archived,
        "native_capture_batches": capture_metadata,
        "reconciled_counts": {
            "records": len(records), "traces": len(traces), "source_modes": dict(sorted(modes.items())),
            "research_status": dict(sorted(statuses.items())), "queries": query_total,
            "source_packets": source_total, "live_attempts": live_attempt_total,
            "evidence_rows": evidence_total, "unknown_critical_slots": unknown_slots,
        },
        "quality_report": quality,
        "status": "PASS_WITH_WARNINGS" if quality["status"] == "WARN" else "PASS",
        "verification_sample_selected": False,
        "human_verification_performed": False,
        "deployment_performed": False,
        "repository_published": False,
    }

    write_json(RAW_JSON, records)
    write_csv(records, RAW_CSV)
    write_json(RAW_ATTEMPTS, attempt_log)
    write_json(RAW_QUALITY, quality)
    RAW_REPORT.parent.mkdir(parents=True, exist_ok=True)
    RAW_REPORT.write_text(run_report, encoding="utf-8")
    write_json(ROOT / "data/evidence/final_native_capture_reconciliation.json", reconciliation)

    # Re-open outputs and confirm the standard records and trace counts survived serialization.
    persisted = read_json(RAW_JSON)
    persisted_attempts = read_json(RAW_ATTEMPTS)
    if len(persisted) != 100 or len(persisted_attempts.get("traces", [])) != 100:
        raise RuntimeError("Persisted manifest-wide files failed post-write row-count check")
    print(f"Reconciled {len(persisted)} records; modes={dict(sorted(modes.items()))}; research={dict(sorted(statuses.items()))}; quality={quality['status']} {quality['record_quality_counts']}; baseline archived={ARCHIVE_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Manifest-wide research runner with explicit live and prior-capture modes.

`live` runs the Tavily + OpenAI-compatible adapter for every manifest row and
fails closed if credentials are missing. `prior-capture` assembles preserved
historical batches and explicit NOT_RUN rows for missing apps; it never calls
that assembly a live research run.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.research.agent import ResearchFailure, live_research_one, unknown_record
from src.utils.quality import normalize_url, validate_final_dataset
from src.utils.validation import validate_manifest

DEFAULT_BATCHES = [
    ("data/raw/pilot_results.json", "data/raw/pilot_attempts.json", "data/evidence/pilot_capture.json"),
    ("data/raw/crm_batch_02_results.json", "data/raw/crm_batch_02_attempts.json", "data/evidence/crm_batch_02_capture.json"),
    ("data/raw/support_batch_11_results.json", "data/raw/support_batch_11_attempts.json", "data/evidence/support_batch_11_capture.json"),
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_id(prefix: str) -> str:
    return prefix + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_csv(records: list[dict], path: Path) -> None:
    columns = [
        "app_id", "app", "category", "description", "auth_status", "auth_methods",
        "self_serve_status", "credential_access_status", "api_available", "api_types",
        "api_breadth", "mcp_status", "buildability_verdict", "source_mode",
        "research_tool", "research_timestamp", "query_count", "source_count",
        "attempt_count", "research_status", "verification_status", "quality_gate_status",
        "evidence_count",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for r in records:
            writer.writerow({
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
                "research_status": r.get("research_status"),
                "verification_status": r.get("verification_status"),
                "quality_gate_status": (r.get("quality_gate") or {}).get("status"),
                "evidence_count": len(r.get("evidence", [])),
            })


def _evidence_source_types(record: dict) -> dict[str, str]:
    result = {}
    for item in record.get("evidence", []):
        if isinstance(item, dict) and item.get("source_url"):
            result.setdefault(normalize_url(item["source_url"]), item.get("source_type", "unclassified"))
    return result


def _standardize_source(source: dict, source_types: dict[str, str], retrieved_at: str | None = None) -> dict:
    item = copy.deepcopy(source)
    url = item.get("source_url") or item.get("url") or ""
    title = item.get("source_title") or item.get("title") or ""
    item["source_url"] = url
    item["source_title"] = title
    item.setdefault("source_type", source_types.get(normalize_url(url), "unclassified_or_discovery_only"))
    if "retrieved_at" not in item:
        item["retrieved_at"] = retrieved_at
    if item.get("retrieved_at") is None:
        item.setdefault("retrieval_timestamp_status", "NOT_CAPTURED_IN_PRIOR_TRACE")
    return item


def _baseline_bundle(manifest: list[dict], batches: list[tuple[str, str, str]], run: str, timestamp: str) -> tuple[list[dict], dict]:
    manifest_by_id = {x["app_id"]: x for x in manifest}
    records_by_id: dict[int, dict] = {}
    traces_by_id: dict[int, dict] = {}
    for results_rel, attempts_rel, capture_rel in batches:
        results = load_json(ROOT / results_rel)
        if isinstance(results, dict):
            result_records = results.get("records", [])
        else:
            result_records = results
        attempts_obj = load_json(ROOT / attempts_rel)
        attempt_traces = {x.get("app_id"): x for x in attempts_obj.get("traces", [])}
        capture_obj = load_json(ROOT / capture_rel)
        capture_traces = {x.get("app_id"): x for x in capture_obj.get("traces", [])}
        captured_at = attempts_obj.get("captured_at") or capture_obj.get("captured_at") or capture_obj.get("capture_date")
        for raw_record in result_records:
            app_id = raw_record.get("app_id")
            if app_id in records_by_id:
                raise ValueError(f"duplicate prior-capture app_id {app_id} across {results_rel}")
            if app_id not in manifest_by_id:
                raise ValueError(f"prior-capture app_id {app_id} is outside the manifest")
            record = copy.deepcopy(raw_record)
            trace = copy.deepcopy(attempt_traces.get(app_id, {}))
            capture_trace = copy.deepcopy(capture_traces.get(app_id, {}))
            source_types = _evidence_source_types(record)
            sources = trace.get("sources") or capture_trace.get("sources") or []
            normalized_sources = [_standardize_source(s, source_types, None) for s in sources if isinstance(s, dict)]
            query_list = trace.get("queries") or capture_trace.get("queries") or []
            original_attempts = trace.get("attempts")
            attempt_count = len(original_attempts) if isinstance(original_attempts, list) else None
            record.update({
                "source_mode": "PRIOR_CAPTURE",
                "research_tool": trace.get("research_tool") or capture_trace.get("research_tool") or "historical tool-assisted capture; exact provider call log unavailable",
                "research_timestamp": record.get("research_timestamp") or captured_at or timestamp,
                "query_count": len(query_list),
                "source_count": len(normalized_sources),
                "attempt_count": attempt_count,
                "research_run_id": run,
                "prior_capture_files": {"results": results_rel, "attempts": attempts_rel, "capture": capture_rel},
            })
            if not trace:
                record.setdefault("limitations", []).append("Prior-capture query/source trace was not found during final assembly.")
            traces_by_id[app_id] = {
                **trace,
                "app_id": app_id,
                "source_mode": "PRIOR_CAPTURE",
                "status": "PRIOR_CAPTURE",
                "queries": query_list,
                "sources": normalized_sources,
                "attempts": original_attempts,
                "capture_failures": capture_trace.get("failures", []),
                "capture_date": capture_obj.get("capture_date"),
                "batch_captured_at": captured_at,
                "source_retrieval_timestamp_status": "PER_SOURCE_TIMESTAMPS_NOT_PRESERVED_IN_PRIOR_CAPTURE",
                "prior_capture_files": {"results": results_rel, "attempts": attempts_rel, "capture": capture_rel},
            }
            records_by_id[app_id] = record

    for app in manifest:
        app_id = app["app_id"]
        if app_id in records_by_id:
            continue
        reason = "NOT_RUN: no TAVILY_API_KEY and/or OPENAI_API_KEY was present; no live query or extraction was attempted."
        record = unknown_record(app, reason, research_status="FAILED")
        record.update({
            "source_mode": "NOT_RUN",
            "research_tool": "not run; live provider credentials unavailable",
            "research_timestamp": timestamp,
            "query_count": 0,
            "source_count": 0,
            "attempt_count": 0,
            "research_run_id": run,
            "failure_reason": reason,
        })
        records_by_id[app_id] = record
        traces_by_id[app_id] = {
            "app_id": app_id,
            "source_mode": "NOT_RUN",
            "status": "NOT_RUN",
            "queries": [],
            "sources": [],
            "attempts": [],
            "errors": [{"stage": "preflight", "type": "missing_credentials", "message": reason}],
            "retrieved_at": None,
        }
    records = [records_by_id[i] for i in sorted(records_by_id)]
    attempt_log = {
        "run_id": run,
        "mode": "PRIOR_CAPTURE_ASSEMBLY_NO_PROVIDER_CREDENTIALS",
        "run_started_at": timestamp,
        "run_completed_at": now(),
        "provider_credentials": {"TAVILY_API_KEY": "MISSING", "OPENAI_API_KEY": "MISSING"},
        "manifest_file": "apps/apps.json",
        "baseline_batches": [{"results": r, "attempts": a, "capture": c} for r, a, c in batches],
        "traces": [traces_by_id[i] for i in sorted(traces_by_id)],
    }
    return records, attempt_log


def _live_bundle(manifest: list[dict], run: str, started: str) -> tuple[list[dict], dict]:
    records: list[dict] = []
    traces: list[dict] = []
    missing = [name for name in ("TAVILY_API_KEY", "OPENAI_API_KEY") if not os.getenv(name)]
    if missing:
        raise RuntimeError("live mode was not run; missing required environment variables: " + ", ".join(missing))
    for app in manifest:
        try:
            record, trace = live_research_one(app)
            trace = copy.deepcopy(trace)
            sources = trace.get("sources", [])
            events = trace.get("attempts", [])
            source_types = _evidence_source_types(record)
            standardized_sources = []
            for source in sources:
                query = source.get("query") if isinstance(source, dict) else None
                matching_events = [e for e in events if e.get("query") == query and e.get("status") == "OK"]
                retrieved_at = matching_events[-1].get("retrieved_at") if matching_events else None
                standardized_sources.append(_standardize_source(source, source_types, retrieved_at))
            trace["sources"] = standardized_sources
            trace["source_mode"] = "LIVE_AGENT"
            trace["status"] = "OK"
            record.update({
                "source_mode": "LIVE_AGENT",
                "research_tool": "Tavily advanced search + OpenAI-compatible structured extraction",
                "research_timestamp": record.get("research_timestamp") or now(),
                "query_count": len(trace.get("queries", [])),
                "source_count": len(standardized_sources),
                "attempt_count": len(events),
                "research_run_id": run,
            })
            records.append(record)
            traces.append(trace)
        except Exception as exc:
            trace = copy.deepcopy(getattr(exc, "trace", {}))
            if not isinstance(trace, dict):
                trace = {}
            trace.setdefault("app_id", app["app_id"])
            trace.setdefault("queries", [])
            trace.setdefault("sources", [])
            trace.setdefault("attempts", [])
            trace.setdefault("errors", []).append({"stage": trace.get("failed_stage", "research"), "type": type(exc).__name__, "message": str(exc), "retrieved_at": now()})
            trace.update({"source_mode": "LIVE_AGENT", "status": "FAILED"})
            record = unknown_record(app, f"Live research failed: {exc}", research_status="FAILED")
            record.update({
                "source_mode": "LIVE_AGENT",
                "research_tool": "Tavily advanced search + OpenAI-compatible structured extraction",
                "research_timestamp": now(),
                "query_count": len(trace.get("queries", [])),
                "source_count": len(trace.get("sources", [])),
                "attempt_count": len(trace.get("attempts", [])),
                "research_run_id": run,
                "failure_reason": str(exc),
            })
            records.append(record)
            traces.append(trace)
    attempt_log = {
        "run_id": run,
        "mode": "LIVE_AGENT_TAVILY_OPENAI_COMPATIBLE",
        "run_started_at": started,
        "run_completed_at": now(),
        "provider_credentials": {"TAVILY_API_KEY": "PRESENT", "OPENAI_API_KEY": "PRESENT"},
        "manifest_file": "apps/apps.json",
        "traces": sorted(traces, key=lambda x: x["app_id"]),
    }
    return sorted(records, key=lambda x: x["app_id"]), attempt_log


def _retry_count(trace: dict) -> int:
    retries = 0
    for event in trace.get("attempts", []) or []:
        if not isinstance(event, dict):
            continue
        index = event.get("attempt", event.get("extract_attempt", 1))
        try:
            retries += int(index) > 1
        except (TypeError, ValueError):
            pass
    return retries


def build_run_report(records: list[dict], attempt_log: dict, quality: dict, manifest: list[dict]) -> str:
    mode = attempt_log.get("mode", "UNKNOWN")
    traces = attempt_log.get("traces", [])
    complete = sum(r.get("research_status") == "COMPLETE" for r in records)
    partial = sum(r.get("research_status") == "PARTIAL" for r in records)
    failed = sum(r.get("research_status") == "FAILED" for r in records)
    not_run = sum(r.get("source_mode") == "NOT_RUN" for r in records)
    provider_failed = sum(r.get("source_mode") == "LIVE_AGENT" and r.get("research_status") == "FAILED" for r in records)
    unknown_fields = sum(
        r.get("auth_status") == "UNKNOWN"
        or (r.get("self_serve_status") == "UNKNOWN")
        for r in []
    )
    unknown_critical_slots = 0
    for r in records:
        unknown_critical_slots += sum((
            r.get("auth_status") == "UNKNOWN",
            r.get("self_serve_status") == "UNKNOWN",
            (r.get("credential_access") or {}).get("status") == "UNKNOWN",
            (r.get("api") or {}).get("available") == "UNKNOWN",
            (r.get("mcp") or {}).get("status") == "UNKNOWN",
            (r.get("buildability") or {}).get("verdict") == "UNKNOWN",
        ))
    evidence_count = sum(len(r.get("evidence", [])) for r in records)
    source_count = sum(len(t.get("sources", [])) for t in traces)
    query_count = sum(len(t.get("queries", [])) for t in traces)
    capture_failures = sum(len(t.get("capture_failures", [])) for t in traces)
    missing_credential_events = sum(
        1 for t in traces for e in (t.get("errors", []) or [])
        if isinstance(e, dict) and e.get("type") == "missing_credentials"
    )
    live_errors = sum(1 for t in traces for e in (t.get("attempts", []) or []) if isinstance(e, dict) and e.get("status") == "ERROR")
    live_errors += sum(len(t.get("errors", [])) for t in traces if t.get("source_mode") == "LIVE_AGENT")
    retries = sum(_retry_count(t) for t in traces if t.get("source_mode") == "LIVE_AGENT")
    unique_source_urls = {
        normalize_url(s.get("source_url") or s.get("url", ""))
        for t in traces for s in t.get("sources", []) if isinstance(s, dict) and (s.get("source_url") or s.get("url"))
    }
    source_modes = {}
    for r in records:
        source_modes[r.get("source_mode", "MISSING")] = source_modes.get(r.get("source_mode", "MISSING"), 0) + 1
    manifest_ids = {a["app_id"] for a in manifest}
    result_ids = {r.get("app_id") for r in records}
    reconciliation = "PASS" if len(records) == 100 and len(result_ids) == 100 and result_ids == manifest_ids else "FAIL"

    if mode == "LIVE_AGENT_TAVILY_OPENAI_COMPATIBLE":
        retry_text = f"{retries} retries across logged calls; {live_errors} logged live errors."
        limitation = "This is a provider-backed agent run; source snippets/raw extracts and model outputs are retained in the attempt log. Independent verification is still separate."
    else:
        retry_text = f"Not measurable for prior captures (per-call retry events were not preserved); live retry count is not applicable. Recorded redirect/404/access failures in capture traces: {capture_failures}."
        limitation = "No live search or extraction was run because TAVILY_API_KEY and OPENAI_API_KEY were absent. The output is a manifest-complete assembly of 24 historical prior_capture records and 76 explicit NOT_RUN placeholders, not 100 researched apps."

    lines = [
        "# Final manifest-wide research run report", "",
        f"- **Status:** {'LIVE_AGENT_RUN' if mode == 'LIVE_AGENT_TAVILY_OPENAI_COMPATIBLE' else 'INCOMPLETE — PRIOR CAPTURE ASSEMBLY ONLY'}",
        f"- **Run mode:** `{mode}`",
        f"- **Run ID:** `{attempt_log.get('run_id', 'unknown')}`",
        f"- **Started at (UTC):** {attempt_log.get('run_started_at', 'not recorded')}",
        f"- **Completed at (UTC):** {attempt_log.get('run_completed_at', 'not recorded')}",
        f"- **Exact manifest app count:** {len(manifest)}",
        f"- **Output record count:** {len(records)}",
        f"- **Attempt trace count:** {len(traces)}",
        f"- **Complete:** {complete}", f"- **Partial:** {partial}", f"- **Failed (research_status=FAILED):** {failed}",
        f"- **NOT_RUN (subset of failed status):** {not_run}", f"- **Live provider failures:** {provider_failed}",
        f"- **Explicit missing-credential trace events:** {missing_credential_events}",
        f"- **Recorded historical capture failures/limits:** {capture_failures}",
        f"- **Unknown critical-field slots (six groups):** {unknown_critical_slots}",
        f"- **Claim-linked evidence items:** {evidence_count}",
        f"- **Source packets in traces:** {source_count}",
        f"- **Unique source URLs:** {len(unique_source_urls)}",
        f"- **Recorded queries:** {query_count}",
        f"- **Retry/error accounting:** {retry_text}",
        f"- **Source-mode counts:** {', '.join(f'{k}={v}' for k, v in sorted(source_modes.items()))}",
        f"- **Manifest reconciliation:** {reconciliation}; IDs must be exactly 1–100 with no duplicates.",
        f"- **Dataset-wide quality gate:** {quality.get('status')} ({quality.get('record_quality_counts')})",
        "", "## Provenance and limitations", "", limitation,
        "", "The unchanged historical records remain in their original files under `data/raw/`; this run writes a separate `final_full_research` output. `PRIOR_CAPTURE` rows retain their historical tool/query/source trace and do not claim per-call retry counts or per-source retrieval timestamps when those were not captured. `NOT_RUN` rows are explicit failures-to-run, not evidence that an app lacks an API, auth method, MCP server, or credential path.",
        "", "## Validation findings", "",
    ]
    if quality.get("errors"):
        lines.extend([f"- **ERROR:** {e}" for e in quality["errors"][:100]])
        if len(quality["errors"]) > 100:
            lines.append(f"- … {len(quality['errors']) - 100} additional errors are preserved in `data/raw/final_full_quality_report.json`.")
    else:
        lines.append("No blocking structural/logical quality errors were found in this run.")
    if quality.get("warnings"):
        lines.append(f"- **Warnings:** {len(quality['warnings'])}; full list is in `data/raw/final_full_quality_report.json`.")
    lines += [
        "", "## Required next action", "",
        "The full research requirement remains **INCOMPLETE** until the live agent is run for all 100 apps with authorized provider credentials (or an equivalent auditable live source workflow). A source-mode rerun may use `--mode live`; it will fail closed rather than silently fall back if credentials are absent.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the finalized manifest-wide research pipeline without conflating live runs and historical capture replay.")
    parser.add_argument("--manifest", default="apps/apps.json")
    parser.add_argument("--mode", required=True, choices=("live", "prior-capture"), help="live performs provider-backed research; prior-capture assembles preserved batches and explicit NOT_RUN rows")
    parser.add_argument("--output", default="data/raw/final_full_research.json")
    parser.add_argument("--attempt-log", default="data/raw/final_full_attempts.json")
    parser.add_argument("--run-report", default="reports/final_research_run_report.md")
    parser.add_argument("--quality-report", default="data/raw/final_full_quality_report.json")
    parser.add_argument("--baseline-results", nargs=3, metavar=("PILOT", "CRM", "SUPPORT"), default=[x[0] for x in DEFAULT_BATCHES])
    parser.add_argument("--baseline-attempts", nargs=3, metavar=("PILOT", "CRM", "SUPPORT"), default=[x[1] for x in DEFAULT_BATCHES])
    parser.add_argument("--baseline-captures", nargs=3, metavar=("PILOT", "CRM", "SUPPORT"), default=[x[2] for x in DEFAULT_BATCHES])
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    manifest = load_json(manifest_path)
    manifest_errors = validate_manifest(manifest)
    if manifest_errors:
        print("Invalid manifest:\n- " + "\n- ".join(manifest_errors), file=sys.stderr)
        return 2

    started = now()
    prefix = "final-live" if args.mode == "live" else "final-prior-capture"
    run = run_id(prefix)
    if args.mode == "live":
        try:
            records, attempt_log = _live_bundle(manifest, run, started)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 3
    else:
        batches = list(zip(args.baseline_results, args.baseline_attempts, args.baseline_captures))
        records, attempt_log = _baseline_bundle(manifest, batches, run, started)

    quality = validate_final_dataset(records, manifest, attempt_log)
    # Preserve the raw run, attempt trace, and quality output even if a gate fails.
    output = ROOT / args.output
    attempts_path = ROOT / args.attempt_log
    quality_path = ROOT / args.quality_report
    write_json(output, records)
    write_json(attempts_path, attempt_log)
    write_json(quality_path, quality)
    csv_path = output.with_suffix(".csv")
    to_csv(records, csv_path)
    report_path = ROOT / args.run_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_run_report(records, attempt_log, quality, manifest), encoding="utf-8")

    print(f"Wrote manifest rows={len(records)}; source modes={attempt_log['mode']}; quality={quality['status']}; output={output}")
    print(f"CSV={csv_path}; attempt log={attempts_path}; report={report_path}; quality report={quality_path}")
    return 2 if quality["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

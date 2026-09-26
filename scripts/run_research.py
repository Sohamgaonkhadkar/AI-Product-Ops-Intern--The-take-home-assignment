#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.research.agent import live_research_one, unknown_record, validate_capture_against_manifest
from src.utils.validation import validate_manifest


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def to_csv(records: list[dict], path: Path) -> None:
    fields = ["app_id", "app", "category", "description", "auth_status", "auth_methods", "self_serve_status", "self_serve_details", "api_available", "api_types", "api_breadth", "api_details", "mcp_status", "mcp_details", "buildability_verdict", "blocker", "buildability_rationale", "evidence_count", "confidence", "research_timestamp", "research_status", "verification_status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "app_id": r["app_id"], "app": r["app"], "category": r["category"], "description": r["description"],
                "auth_status": r["auth_status"], "auth_methods": "; ".join(r["auth_methods"]),
                "self_serve_status": r["self_serve_status"], "self_serve_details": r["self_serve_details"],
                "api_available": r["api"]["available"], "api_types": "; ".join(r["api"]["types"]), "api_breadth": r["api"]["breadth"], "api_details": r["api"]["details"],
                "mcp_status": r["mcp"]["status"], "mcp_details": r["mcp"]["details"],
                "buildability_verdict": r["buildability"]["verdict"], "blocker": r["buildability"]["blocker"], "buildability_rationale": r["buildability"]["rationale"],
                "evidence_count": len(r["evidence"]), "confidence": r["confidence"], "research_timestamp": r["research_timestamp"],
                "research_status": r["research_status"], "verification_status": r["verification_status"],
            })


def main() -> int:
    parser = argparse.ArgumentParser(description="Run tool-capture replay or optional provider-backed app research.")
    parser.add_argument("--manifest", default="apps/apps.json")
    parser.add_argument("--input", help="JSON object with a records array (capture/replay mode)")
    parser.add_argument("--output", default="data/raw/research_results.json")
    parser.add_argument("--attempt-log", default="data/raw/research_attempts.json")
    parser.add_argument("--run-report", default="reports/research_run_report.md")
    parser.add_argument("--live", action="store_true", help="Use Tavily + OpenAI-compatible API; requires keys in environment")
    parser.add_argument("--ids", help="Comma-separated manifest IDs to select, e.g. 1,22,49")
    parser.add_argument("--require-all", action="store_true", help="Fail unless selected output covers every selected manifest app")
    args = parser.parse_args()
    manifest_path = ROOT / args.manifest
    manifest = load_json(manifest_path)
    manifest_errors = validate_manifest(manifest)
    if manifest_errors:
        print("Invalid manifest:\n- " + "\n- ".join(manifest_errors), file=sys.stderr)
        return 2
    selected_ids = {int(x.strip()) for x in args.ids.split(",")} if args.ids else None
    selected = [a for a in manifest if selected_ids is None or a["app_id"] in selected_ids]
    if not selected:
        print("No manifest rows selected", file=sys.stderr)
        return 2

    records, trace = [], []
    if args.live:
        for app in selected:
            try:
                record, log = live_research_one(app)
                records.append(record)
                trace.append(log)
            except Exception as exc:
                failure_trace = getattr(exc, "trace", {})
                record = unknown_record(app, f"Live research failed: {exc}")
                records.append(record)
                trace.append({
                    **failure_trace,
                    "app_id": app["app_id"],
                    "status": "FAILED",
                    "error": str(exc),
                    "retrieved_at": now(),
                })
    else:
        if not args.input:
            parser.error("--input is required unless --live is selected")
        capture = load_json(ROOT / args.input)
        records = capture.get("records", []) if isinstance(capture, dict) else capture
        trace = capture.get("traces", []) if isinstance(capture, dict) else []
        if selected_ids is not None:
            records = [r for r in records if r.get("app_id") in selected_ids]
        # A replay is an exact evidence capture, not an invisible rewrite.
        records = sorted(records, key=lambda x: x.get("app_id", 1000))

    errors = validate_capture_against_manifest(records, selected)
    if args.require_all:
        out_ids = {r.get("app_id") for r in records}
        expected_ids = {a["app_id"] for a in selected}
        if out_ids != expected_ids:
            errors.append(f"selected manifest reconciliation failed; missing={sorted(expected_ids-out_ids)}, extra={sorted(out_ids-expected_ids)}")
    if errors:
        print("Research output failed validation:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 2

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    csv_path = output_path.with_suffix(".csv")
    to_csv(records, csv_path)
    attempt_path = ROOT / args.attempt_log
    attempt_path.parent.mkdir(parents=True, exist_ok=True)
    attempt_path.write_text(json.dumps({"captured_at": now(), "mode": "live" if args.live else "capture_replay", "traces": trace}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total = len(records)
    complete = sum(r["research_status"] == "COMPLETE" for r in records)
    partial = sum(r["research_status"] == "PARTIAL" for r in records)
    failed = sum(r["research_status"] == "FAILED" for r in records)
    unknowns = sum(sum(1 for v in (
        r["auth_status"] == "UNKNOWN",
        r["self_serve_status"] == "UNKNOWN",
        r["credential_access"]["status"] == "UNKNOWN",
        r["api"]["available"] == "UNKNOWN",
        r["mcp"]["status"] == "UNKNOWN",
        r["buildability"]["verdict"] == "UNKNOWN",
    ) if v) for r in records)
    evidence_count = sum(len(r["evidence"]) for r in records)
    source_count = sum(len(t.get("sources", [])) for t in trace)
    attempt_events = []
    for item in trace:
        events = item.get("attempts", [])
        if isinstance(events, list):
            attempt_events.extend(events)
    failed_attempts = sum(event.get("status") == "ERROR" for event in attempt_events)
    retry_attempts = sum(int(event.get("attempt", event.get("extract_attempt", 1))) > 1 for event in attempt_events)
    retry_note = (
        f"Recorded {len(attempt_events)} individual call attempts, {failed_attempts} failed attempts, and {retry_attempts} retries; see `{args.attempt_log}`."
        if args.live else
        f"Capture/replay stores per-app query/source traces in `{args.attempt_log}` but has no per-call retry/error events; no retry count is claimed."
    )
    report = f"""# Research run report\n\n- **Mode:** {'Live (Tavily + configured OpenAI-compatible model)' if args.live else 'Capture replay (tool-assisted source captures)'}\n- **Captured at:** {now()}\n- **Apps in this run:** {total}\n- **Complete records:** {complete}\n- **Partial records:** {partial}\n- **Failed records:** {failed}\n- **Unknown critical field slots:** {unknowns} (not counted as failures; see per-record limitations)\n- **Claim-linked evidence items:** {evidence_count}\n- **Retrieved source packets logged:** {source_count}\n- **Retries/errors:** {retry_note}\n- **Manifest reconciliation:** passed for selected IDs {', '.join(str(a['app_id']) for a in selected)}\n\n## Method and limitations\n\nThis report describes the actual run mode. Capture replay validates and writes source-captured research; it does not claim to have called a search provider. Live mode performs targeted web search and structured extraction, but still requires independent verification. Unknown is not silently converted to a negative.\n"""
    report_path = ROOT / args.run_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote {total} records ({complete} complete, {partial} partial, {failed} failed) to {output_path}")
    print(f"CSV: {csv_path}; report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

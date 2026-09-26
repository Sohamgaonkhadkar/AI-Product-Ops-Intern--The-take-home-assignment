#!/usr/bin/env python3
"""Independent read-only validation of Batch04 capture and provenance.

This script does not import the Batch04 builder and never edits the artifact or
raw data. It recomputes schema/quality checks and validates trace reconciliation.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.quality import validate_record_quality
from src.utils.validation import validate_record

ARTIFACT = ROOT / "data/evidence/native_web_capture_batch04_2026-09-24.json"
MANIFEST_PATH = ROOT / "apps/apps.json"
RAW_JSON = ROOT / "data/raw/final_full_research.json"
RAW_CSV = ROOT / "data/raw/final_full_research.csv"
EXPECTED_IDS = list(range(52, 61))
EXPECTED_RAW_HASHES = {
    "json": "eb12c32a3ad7cd92b2e20c3a96974e8040ab104beaa47344d2ad0bdde443516c",
    "csv": "d5e844ebcb6503fee7e9c16cb9355e97aeac0c414a8e69926eeaf3a04e7a068d",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(messages: list[str]) -> int:
    print("BATCH04 VALIDATION: FAIL")
    for message in messages:
        print("-", message)
    return 1


def main() -> int:
    if not ARTIFACT.exists():
        return fail([f"artifact not found: {ARTIFACT}"])
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    raw_records = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    traces = payload.get("traces", [])
    manifest_by_id = {row["app_id"]: row for row in manifest}
    records_by_id = {row.get("app_id"): row for row in records}
    traces_by_id = {row.get("app_id"): row for row in traces}
    problems: list[str] = []

    if payload.get("run_id") != "arena-native-web-batch04-20260924":
        problems.append("unexpected or missing Batch04 run_id")
    if payload.get("source_mode") != "LIVE_AGENT":
        problems.append("top-level source_mode must be LIVE_AGENT")
    if records and [r.get("app_id") for r in records] != EXPECTED_IDS:
        problems.append("artifact record IDs/order must be exactly 52-60")
    if len(records) != 9 or len(traces) != 9:
        problems.append(f"expected 9 records and 9 traces; found {len(records)} and {len(traces)}")
    if set(records_by_id) != set(EXPECTED_IDS):
        problems.append("record IDs do not equal expected Batch04 scope")
    if set(traces_by_id) != set(EXPECTED_IDS):
        problems.append("trace IDs do not equal expected Batch04 scope")
    if len(raw_records) != 100:
        problems.append(f"authoritative raw dataset should remain 100 rows; found {len(raw_records)}")

    current_hashes = {"json": sha256(RAW_JSON), "csv": sha256(RAW_CSV)}
    if current_hashes != EXPECTED_RAW_HASHES:
        problems.append(f"authoritative raw JSON/CSV hashes differ from pre-Batch04 baseline: {current_hashes}")
    if payload.get("raw_dataset_hashes_before_and_after") != {
        "json": EXPECTED_RAW_HASHES["json"],
        "csv": EXPECTED_RAW_HASHES["csv"],
    }:
        problems.append("artifact raw hash manifest is missing or does not match baseline")

    per_record = []
    for app_id in EXPECTED_IDS:
        record = records_by_id.get(app_id)
        trace = traces_by_id.get(app_id)
        if not record or not trace:
            continue
        expected_manifest = manifest_by_id.get(app_id)
        if not expected_manifest:
            problems.append(f"app_id={app_id} missing from manifest")
        elif (record.get("app"), record.get("category")) != (expected_manifest.get("app"), expected_manifest.get("category")):
            problems.append(f"app_id={app_id} app/category identity does not match manifest")

        if record.get("source_mode") != "LIVE_AGENT" or trace.get("source_mode") != "LIVE_AGENT":
            problems.append(f"app_id={app_id} is not consistently labeled LIVE_AGENT")
        if record.get("research_status") != "COMPLETE" or trace.get("status") != "COMPLETE":
            problems.append(f"app_id={app_id} is not consistently marked COMPLETE")
        if record.get("research_run_id") != payload.get("run_id") or trace.get("research_run_id") != payload.get("run_id"):
            problems.append(f"app_id={app_id} run_id mismatch")

        queries = trace.get("queries", [])
        sources = trace.get("sources", [])
        attempts = trace.get("attempts", [])
        if record.get("query_count") != len(queries):
            problems.append(f"app_id={app_id} query_count mismatch")
        if record.get("source_count") != len(sources):
            problems.append(f"app_id={app_id} source_count mismatch")
        if record.get("attempt_count") != len(attempts):
            problems.append(f"app_id={app_id} attempt_count mismatch")
        if not all(q.get("lead_only") is True for q in queries):
            problems.append(f"app_id={app_id} includes a search query not marked lead-only")
        if any(q.get("tool") == "web_search" for q in record.get("evidence", [])):
            problems.append(f"app_id={app_id} appears to use search snippets as evidence")

        urls = {s.get("url") for s in sources if isinstance(s, dict)}
        evidence_urls = {e.get("source_url") for e in record.get("evidence", []) if isinstance(e, dict)}
        if not evidence_urls.issubset(urls):
            problems.append(f"app_id={app_id} evidence URL absent from first-party source trace: {sorted(evidence_urls-urls)}")
        for conflict in record.get("source_conflicts", []):
            for url in conflict.get("source_urls", []):
                if url not in urls:
                    problems.append(f"app_id={app_id} unresolved conflict source absent from trace: {url}")

        # Reconcile each source's declared chunk indexes against successful fetch attempts.
        successful_chunks: dict[str, set[int]] = {}
        for attempt in attempts:
            if attempt.get("tool") == "fetch_page" and attempt.get("status") == "SUCCESS":
                successful_chunks.setdefault(attempt.get("url"), set()).add(attempt.get("chunk_index"))
        for source in sources:
            if not isinstance(source, dict):
                continue
            url = source.get("url")
            declared = set(source.get("retrieved_chunk_indexes", []))
            observed = successful_chunks.get(url, set())
            if not declared or not declared.issubset(observed):
                problems.append(f"app_id={app_id} source chunk metadata is not backed by successful attempts: {url} declared={sorted(declared)} observed={sorted(observed)}")

        recomputed = validate_record_quality(record, source_urls=urls)
        structural = validate_record(record)
        if structural:
            problems.append(f"app_id={app_id} structural validation errors: {structural}")
        if recomputed.get("status") != "PASS":
            problems.append(f"app_id={app_id} recomputed quality gate is not PASS: {recomputed}")
        if record.get("quality_gate") != recomputed:
            problems.append(f"app_id={app_id} stored and recomputed quality gates differ")
        per_record.append((app_id, record.get("app"), len(record.get("evidence", [])), len(sources), len(queries), len(attempts), recomputed["status"]))

    # Consequential scope checks: preserve unknowns and source conflicts rather than normalizing them away.
    for app_id in (58, 59):
        record = records_by_id.get(app_id, {})
        if (record.get("mcp") or {}).get("status") != "UNKNOWN":
            problems.append(f"app_id={app_id} MCP must remain UNKNOWN within the bounded official-source review")
    if not records_by_id.get(54, {}).get("source_conflicts"):
        problems.append("MrScraper pricing/token conflicts were silently removed")
    if not records_by_id.get(59, {}).get("source_conflicts"):
        problems.append("Waterfall auth-header/access conflicts were silently removed")

    if problems:
        return fail(problems)
    print("BATCH04 VALIDATION: PASS")
    print("Scope: 9 standalone records, IDs 52-60; raw authoritative population: 100 rows, unchanged")
    print("Raw hashes:", json.dumps(current_hashes, sort_keys=True))
    print("ID | app | evidence | sources | queries | attempts | gate")
    for row in per_record:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent, read-only validation for Batch05 native-web capture.

Does not import the Batch05 builder, does not rewrite the artifact, and checks
scope, provenance, evidence/source trace linkage, chunk attempts, quality gates,
and unchanged authoritative raw-data hashes.
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

ARTIFACT = ROOT / "data/evidence/native_web_capture_batch05_2026-09-24.json"
MANIFEST_PATH = ROOT / "apps/apps.json"
RAW_JSON = ROOT / "data/raw/final_full_research.json"
RAW_CSV = ROOT / "data/raw/final_full_research.csv"
EXPECTED_IDS = list(range(62, 71))
EXPECTED_RUN_ID = "arena-native-web-batch05-20260924"
EXPECTED_RAW_HASHES = {
    "json": "eb12c32a3ad7cd92b2e20c3a96974e8040ab104beaa47344d2ad0bdde443516c",
    "csv": "d5e844ebcb6503fee7e9c16cb9355e97aeac0c414a8e69926eeaf3a04e7a068d",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(messages: list[str]) -> int:
    print("BATCH05 VALIDATION: FAIL")
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

    if payload.get("run_id") != EXPECTED_RUN_ID:
        problems.append("unexpected or missing Batch05 run_id")
    if payload.get("source_mode") != "LIVE_AGENT":
        problems.append("top-level source_mode must be LIVE_AGENT")
    if [r.get("app_id") for r in records] != EXPECTED_IDS:
        problems.append("record IDs/order must be exactly 62-70")
    if len(records) != 9 or len(traces) != 9:
        problems.append(f"expected 9 records and 9 traces; found {len(records)} and {len(traces)}")
    if set(records_by_id) != set(EXPECTED_IDS):
        problems.append("record IDs do not equal Batch05 scope")
    if set(traces_by_id) != set(EXPECTED_IDS):
        problems.append("trace IDs do not equal Batch05 scope")
    if len(raw_records) != 100:
        problems.append(f"authoritative raw dataset should remain 100 rows; found {len(raw_records)}")

    hashes = {"json": sha256(RAW_JSON), "csv": sha256(RAW_CSV)}
    if hashes != EXPECTED_RAW_HASHES:
        problems.append(f"authoritative raw JSON/CSV hashes changed: {hashes}")
    if payload.get("raw_dataset_hashes_before_and_after") != EXPECTED_RAW_HASHES:
        problems.append("artifact before/after raw hash manifest differs from baseline")

    per_record = []
    for app_id in EXPECTED_IDS:
        record = records_by_id.get(app_id)
        trace = traces_by_id.get(app_id)
        if not record or not trace:
            continue
        expected = manifest_by_id.get(app_id)
        if not expected:
            problems.append(f"app_id={app_id} missing from apps manifest")
        elif any(record.get(k) != expected.get(k) for k in ("app", "category", "website_hint")):
            problems.append(f"app_id={app_id} identity/category/website differs from manifest")
        if record.get("source_mode") != "LIVE_AGENT" or trace.get("source_mode") != "LIVE_AGENT":
            problems.append(f"app_id={app_id} source mode is not consistently LIVE_AGENT")
        if record.get("research_status") != "COMPLETE" or trace.get("status") != "COMPLETE":
            problems.append(f"app_id={app_id} not consistently marked COMPLETE")
        if record.get("verification_status") != "NOT_CHECKED":
            problems.append(f"app_id={app_id} verification status is not truthfully NOT_CHECKED")
        if record.get("research_run_id") != EXPECTED_RUN_ID or trace.get("research_run_id") != EXPECTED_RUN_ID:
            problems.append(f"app_id={app_id} run_id mismatch")
        if record.get("research_tool") != payload.get("tool") or trace.get("research_tool") != payload.get("tool"):
            problems.append(f"app_id={app_id} research tool provenance mismatch")

        queries = trace.get("queries", [])
        sources = trace.get("sources", [])
        attempts = trace.get("attempts", [])
        if record.get("query_count") != len(queries):
            problems.append(f"app_id={app_id} query_count mismatch")
        if record.get("source_count") != len(sources):
            problems.append(f"app_id={app_id} source_count mismatch")
        if record.get("attempt_count") != len(attempts):
            problems.append(f"app_id={app_id} attempt_count mismatch")
        if any(q.get("lead_only") is not True for q in queries):
            problems.append(f"app_id={app_id} has a query not marked discovery-only")
        if any(q.get("search_status") != "SUCCESS" for q in queries):
            problems.append(f"app_id={app_id} has a non-success search in the query inventory")

        urls = {s.get("url") for s in sources if isinstance(s, dict)}
        evidence_urls = {e.get("source_url") for e in record.get("evidence", []) if isinstance(e, dict)}
        if not evidence_urls.issubset(urls):
            problems.append(f"app_id={app_id} evidence URL absent from source trace: {sorted(evidence_urls-urls)}")
        for conflict in record.get("source_conflicts", []):
            for url in conflict.get("source_urls", []):
                if url not in urls:
                    problems.append(f"app_id={app_id} conflict source absent from trace: {url}")

        successful_chunks: dict[str, set[int]] = {}
        for attempt in attempts:
            if attempt.get("tool") == "fetch_page" and attempt.get("status") == "SUCCESS":
                successful_chunks.setdefault(attempt.get("url"), set()).add(attempt.get("chunk_index"))
        for src in sources:
            if not isinstance(src, dict):
                continue
            url = src.get("url")
            declared = set(src.get("retrieved_chunk_indexes", []))
            observed = successful_chunks.get(url, set())
            if not declared or not declared.issubset(observed):
                problems.append(f"app_id={app_id} source chunk indexes not backed by successful attempts: {url}; declared={sorted(declared)}, observed={sorted(observed)}")
            if src.get("capture_status") != "OPENED" or src.get("capture_method") != "fetch_page":
                problems.append(f"app_id={app_id} source capture provenance incomplete: {url}")
        for attempt in attempts:
            if attempt.get("tool") == "web_search" and attempt.get("status") != "SUCCESS":
                problems.append(f"app_id={app_id} failed search represented in trace query inventory")
            if attempt.get("tool") == "fetch_page" and attempt.get("status") not in {"SUCCESS", "HTTP_404", "REDIRECTED_NOT_RELEVANT", "SUCCESS_NOT_USED"}:
                problems.append(f"app_id={app_id} fetch attempt has unexpected status {attempt.get('status')!r}")

        recomputed = validate_record_quality(record, source_urls=urls)
        structural = validate_record(record)
        if structural:
            problems.append(f"app_id={app_id} structural validation errors: {structural}")
        if recomputed.get("status") != "PASS":
            problems.append(f"app_id={app_id} recomputed quality not PASS: {recomputed}")
        if record.get("quality_gate") != recomputed:
            problems.append(f"app_id={app_id} stored and recomputed quality gates differ")
        per_record.append((app_id, record.get("app"), len(record.get("evidence", [])), len(sources), len(queries), len(attempts), recomputed["status"]))

    # Consequential scope/evidence distinctions that must not be lost.
    neo = records_by_id.get(66, {})
    if "hosted aura mcp authentication flow was not resolved" not in (neo.get("mcp") or {}).get("details", "").lower():
        problems.append("Neo4j hosted Aura MCP authentication uncertainty was not preserved")
    if any("https://neo4j.com/docs/query-api/current/authentication-authorization/" in e.get("source_url", "") for e in neo.get("evidence", []) if e.get("field") == "mcp"):
        problems.append("Neo4j Query API auth evidence was conflated with hosted Aura MCP auth")
    for app_id in EXPECTED_IDS:
        record = records_by_id.get(app_id, {})
        if record.get("verification_status") == "COMPLETE":
            problems.append(f"app_id={app_id} improperly represented as independently verified")

    if problems:
        return fail(problems)
    print("BATCH05 VALIDATION: PASS")
    print("Scope: 9 standalone records, IDs 62-70; raw authoritative population: 100 rows, unchanged")
    print("Raw hashes:", json.dumps(hashes, sort_keys=True))
    print("ID | app | evidence | sources | queries | attempts | gate")
    for row in per_record:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

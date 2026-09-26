#!/usr/bin/env python3
"""Independent, read-only validation for Batch06 native-web capture.

Does not import the Batch06 builder or rewrite its artifact. Checks exact scope,
raw-data preservation, provenance, evidence/source/chunk linkage, conflicts,
and independently recomputed schema and quality gates.
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

ARTIFACT = ROOT / "data/evidence/native_web_capture_batch06_2026-09-24.json"
MANIFEST_PATH = ROOT / "apps/apps.json"
RAW_JSON = ROOT / "data/raw/final_full_research.json"
RAW_CSV = ROOT / "data/raw/final_full_research.csv"
EXPECTED_IDS = list(range(71, 80))
EXPECTED_RUN_ID = "arena-native-web-batch06-20260924"
EXPECTED_RAW_HASHES = {
    "json": "eb12c32a3ad7cd92b2e20c3a96974e8040ab104beaa47344d2ad0bdde443516c",
    "csv": "d5e844ebcb6503fee7e9c16cb9355e97aeac0c414a8e69926eeaf3a04e7a068d",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(messages: list[str]) -> int:
    print("BATCH06 VALIDATION: FAIL")
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
    raw_by_id = {row["app_id"]: row for row in raw_records}
    records_by_id = {row.get("app_id"): row for row in records}
    traces_by_id = {row.get("app_id"): row for row in traces}
    problems: list[str] = []

    if payload.get("run_id") != EXPECTED_RUN_ID:
        problems.append("unexpected or missing Batch06 run_id")
    if payload.get("source_mode") != "LIVE_AGENT":
        problems.append("top-level source_mode must be LIVE_AGENT")
    if [row.get("app_id") for row in records] != EXPECTED_IDS:
        problems.append("record IDs/order must be exactly 71-79")
    if len(records) != 9 or len(traces) != 9:
        problems.append(f"expected 9 records and 9 traces; found {len(records)} and {len(traces)}")
    if set(records_by_id) != set(EXPECTED_IDS) or set(traces_by_id) != set(EXPECTED_IDS):
        problems.append("record/trace IDs do not exactly equal Batch06 scope")
    if len(raw_records) != 100:
        problems.append(f"authoritative raw dataset should remain 100 rows; found {len(raw_records)}")

    hashes = {"json": sha256(RAW_JSON), "csv": sha256(RAW_CSV)}
    if hashes != EXPECTED_RAW_HASHES:
        problems.append(f"authoritative raw JSON/CSV hashes changed: {hashes}")
    if payload.get("raw_dataset_hashes_before_and_after") != EXPECTED_RAW_HASHES:
        problems.append("artifact before/after raw hash manifest differs from baseline")
    for app_id in EXPECTED_IDS:
        raw = raw_by_id.get(app_id, {})
        if raw.get("source_mode") != "NOT_RUN" or raw.get("research_status") != "FAILED" or raw.get("evidence"):
            problems.append(f"authoritative raw ID {app_id} was unexpectedly merged or mutated")

    per_record = []
    for app_id in EXPECTED_IDS:
        record = records_by_id.get(app_id)
        trace = traces_by_id.get(app_id)
        if not record or not trace:
            continue
        expected = manifest_by_id.get(app_id)
        if not expected:
            problems.append(f"app_id={app_id} missing from apps manifest")
        elif any(record.get(key) != expected.get(key) for key in ("app", "category", "website_hint")):
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
        if any(query.get("lead_only") is not True for query in queries):
            problems.append(f"app_id={app_id} has a query not marked discovery-only")
        if any(query.get("search_status") != "SUCCESS" for query in queries):
            problems.append(f"app_id={app_id} has a non-success search in query inventory")

        urls = {row.get("url") for row in sources if isinstance(row, dict)}
        evidence_urls = {row.get("source_url") for row in record.get("evidence", []) if isinstance(row, dict)}
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
        for source in sources:
            if not isinstance(source, dict):
                continue
            url = source.get("url")
            declared = set(source.get("retrieved_chunk_indexes", []))
            observed = successful_chunks.get(url, set())
            if not declared or not declared.issubset(observed):
                problems.append(f"app_id={app_id} source chunks lack successful fetch attempts: {url}; declared={sorted(declared)}, observed={sorted(observed)}")
            if source.get("capture_status") != "OPENED" or source.get("capture_method") != "fetch_page":
                problems.append(f"app_id={app_id} source capture provenance incomplete: {url}")
        for attempt in attempts:
            if attempt.get("tool") == "fetch_page" and attempt.get("status") not in {"SUCCESS", "HTTP_404", "REDIRECTED_NOT_RELEVANT", "SUCCESS_NOT_USED"}:
                problems.append(f"app_id={app_id} fetch attempt has unexpected status {attempt.get('status')!r}")

        structural = validate_record(record)
        if structural:
            problems.append(f"app_id={app_id} structural validation errors: {structural}")
        recomputed = validate_record_quality(record, source_urls=urls)
        if recomputed.get("status") != "PASS":
            problems.append(f"app_id={app_id} recomputed quality not PASS: {recomputed}")
        if record.get("quality_gate") != recomputed:
            problems.append(f"app_id={app_id} stored and recomputed quality gates differ")
        per_record.append((app_id, record.get("app"), len(record.get("evidence", [])), len(sources), len(queries), len(attempts), recomputed["status"]))

    # Preserve unresolved or consequential findings; do not silently normalize them.
    smartsheet = records_by_id.get(79, {})
    if len(smartsheet.get("source_conflicts", [])) != 2:
        problems.append("Smartsheet free-plan and AWM token-plan discrepancies were not both preserved")
    if "not tell a new user" not in str(smartsheet.get("source_conflicts", [{}])[0].get("resolution", "")):
        problems.append("Smartsheet new-user Free-plan conflict resolution is missing")
    clickup = records_by_id.get(77, {})
    if len(clickup.get("source_conflicts", [])) != 1 or "Preserve the discrepancy" not in str(clickup.get("source_conflicts", [{}])[0].get("resolution", "")):
        problems.append("ClickUp daily MCP-limit conflict was not retained")
    coda = records_by_id.get(78, {})
    if (coda.get("mcp") or {}).get("status") != "AVAILABLE" or "deprecat" not in (coda.get("mcp") or {}).get("details", "").lower():
        problems.append("Coda/Superhuman Docs native MCP availability or legacy-endpoint deprecation note was lost")
    for app_id in EXPECTED_IDS:
        record = records_by_id.get(app_id, {})
        if record.get("verification_status") in {"AUTO_VERIFIED", "HUMAN_VERIFIED", "MIXED"}:
            problems.append(f"app_id={app_id} is improperly represented as independently verified")

    if problems:
        return fail(problems)
    print("BATCH06 VALIDATION: PASS")
    print("Scope: 9 standalone records, IDs 71-79; authoritative raw population remains unchanged")
    print("Raw hashes:", json.dumps(hashes, sort_keys=True))
    print("ID | app | evidence | sources | queries | attempts | gate")
    for row in per_record:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

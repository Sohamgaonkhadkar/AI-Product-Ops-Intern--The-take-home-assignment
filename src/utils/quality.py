"""Dataset-wide quality gates for auditable app research records.

The gates never rewrite a finding. They return explicit errors/warnings so callers
can retain a raw record while preventing an invalid record from being treated as
verified or analysis-ready.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from urllib.parse import urlsplit

from src.utils.validation import validate_manifest, validate_record

FINAL_SOURCE_MODES = {"LIVE_AGENT", "PRIOR_CAPTURE", "NOT_RUN"}
CRITICAL_GROUPS = {
    "auth_methods": "auth",
    "self_serve_status": "self_serve",
    "credential_access.status": "credential_access",
    "api.available": "api",
    "mcp.status": "mcp",
    "buildability.verdict": "buildability",
}
GATING_SELF_SERVE = {
    "PAID_PLAN_REQUIRED", "ADMIN_APPROVAL_REQUIRED",
    "PARTNER_OR_CONTACT_SALES", "ENTERPRISE_ONLY",
}
_INCOMPLETE_MCP_SCOPE = (
    "incomplete", "not complete", "not comprehensive", "no comprehensive",
    "not audited", "not inspected", "not inspect", "only searched",
    "bounded to", "limited to", "no repository", "no repo",
)
_GENERIC_PATHS = {"", "/", "/index.html", "/index.htm", "/home", "/home/"}


def normalize_url(url: str) -> str:
    """Canonicalize only enough for duplicate/source-trace comparisons."""
    try:
        p = urlsplit(url.strip())
        host = (p.hostname or "").lower()
        port = p.port
        if port and not ((p.scheme.lower() == "https" and port == 443) or (p.scheme.lower() == "http" and port == 80)):
            host = f"{host}:{port}"
        path = p.path.rstrip("/") or "/"
        return f"{p.scheme.lower()}://{host}{path}".lower()
    except (ValueError, AttributeError):
        return ""


def is_valid_http_url(url: object) -> bool:
    if not isinstance(url, str) or not url or any(ch.isspace() for ch in url):
        return False
    try:
        p = urlsplit(url)
        return p.scheme.lower() in {"http", "https"} and bool(p.hostname) and p.port != 0
    except (ValueError, AttributeError):
        return False


def is_generic_homepage(url: str) -> bool:
    if not is_valid_http_url(url):
        return False
    p = urlsplit(url)
    return p.path.lower() in _GENERIC_PATHS and not p.query


def _known_supported_fields(record: dict) -> set[str]:
    known: set[str] = set()
    if str(record.get("description", "")).strip().lower() not in {"", "unknown", "not established"}:
        known.add("description")
    if record.get("auth_status") not in {None, "UNKNOWN"}:
        known.add("auth")
    if record.get("self_serve_status") not in {None, "UNKNOWN"}:
        known.add("self_serve")
    if (record.get("credential_access") or {}).get("status") not in {None, "UNKNOWN"}:
        known.add("credential_access")
    if (record.get("api") or {}).get("available") not in {None, "UNKNOWN"}:
        known.add("api")
    if (record.get("mcp") or {}).get("status") not in {None, "UNKNOWN"}:
        known.add("mcp")
    if (record.get("buildability") or {}).get("verdict") not in {None, "UNKNOWN"}:
        known.add("buildability")
    return known


def validate_record_quality(record: dict, source_urls: set[str] | None = None) -> dict:
    """Return record-level quality errors and warnings without correcting data."""
    errors = list(validate_record(record))
    warnings: list[str] = []
    if not isinstance(record, dict):
        return {"status": "FAIL", "errors": errors, "warnings": warnings}

    evidence = record.get("evidence", [])
    if record.get("research_status") == "COMPLETE" and not evidence:
        errors.append("COMPLETE record has no evidence")

    valid_support: dict[str, list[dict]] = defaultdict(list)
    url_counts: Counter[str] = Counter()
    duplicate_claims: Counter[tuple[str, str, str]] = Counter()
    for item in evidence if isinstance(evidence, list) else []:
        if not isinstance(item, dict):
            continue
        url = item.get("source_url", "")
        if not is_valid_http_url(url):
            # The structural validator also reports this; keep one stable quality error.
            continue
        normalized = normalize_url(url)
        url_counts[normalized] += 1
        duplicate_claims[(normalized, item.get("field", ""), item.get("claim", ""))] += 1
        if item.get("support") == "supports":
            valid_support[item.get("field", "")].append(item)

    for field in sorted(_known_supported_fields(record)):
        supporting = valid_support.get(field, [])
        if not supporting:
            errors.append(f"known {field} claim has no claim-linked supporting evidence")
            continue
        generic_only = all(is_generic_homepage(x.get("source_url", "")) for x in supporting)
        if generic_only and field in {"auth", "self_serve", "credential_access", "api", "mcp", "buildability"}:
            warnings.append(f"generic homepage is the only supporting source for specific {field} claim")

    exact_dupes = [key for key, count in duplicate_claims.items() if count > 1]
    if exact_dupes:
        warnings.append(f"{len(exact_dupes)} exact duplicate evidence claim/source row(s) detected")
    for normalized, count in url_counts.items():
        if count >= 4:
            warnings.append(f"evidence URL reused {count} times; review for over-broad source reuse: {normalized}")

    api = record.get("api", {})
    build = record.get("buildability", {})
    credential = record.get("credential_access", {})
    if api.get("available") == "NO":
        if api.get("breadth") != "UNKNOWN":
            errors.append("api.available=NO conflicts with a non-UNKNOWN api.breadth")
        if api.get("types"):
            errors.append("api.available=NO conflicts with asserted API interface types")
        if build.get("verdict") == "BUILDABLE_NOW":
            errors.append("BUILDABLE_NOW conflicts with api.available=NO")
    if api.get("available") == "YES" and not api.get("types"):
        warnings.append("api.available=YES but no API interface type is recorded")
    if build.get("verdict") == "BUILDABLE_NOW":
        if api.get("available") != "YES":
            errors.append("BUILDABLE_NOW requires api.available=YES")
        if credential.get("status") == "GATED" or record.get("self_serve_status") in GATING_SELF_SERVE:
            errors.append("BUILDABLE_NOW conflicts with a documented material credential/plan/admin/partner gate")
    if record.get("mcp", {}).get("status") == "NOT_FOUND":
        scope = str(record.get("mcp", {}).get("search_scope", "")).strip()
        if not scope:
            errors.append("mcp.status=NOT_FOUND has empty search_scope")
        elif any(token in scope.lower() for token in _INCOMPLETE_MCP_SCOPE):
            errors.append("mcp.status=NOT_FOUND conflicts with an explicitly incomplete/limited search_scope")

    known = _known_supported_fields(record)
    if record.get("research_status") == "COMPLETE":
        missing = known - set(valid_support)
        if missing:
            errors.append(f"COMPLETE record has critical claim(s) without field evidence: {sorted(missing)}")
        if record.get("confidence") == "LOW":
            warnings.append("COMPLETE record has LOW confidence; review completion classification")

    if source_urls is not None:
        normalized_sources = {normalize_url(u) for u in source_urls if is_valid_http_url(u)}
        for item in evidence if isinstance(evidence, list) else []:
            url = item.get("source_url", "") if isinstance(item, dict) else ""
            if is_valid_http_url(url) and normalize_url(url) not in normalized_sources:
                warnings.append(f"claim evidence URL is absent from the recorded source trace: {url}")

    # Stable order makes quality reports and tests reproducible.
    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return {"status": status, "errors": errors, "warnings": warnings}


def validate_final_dataset(
    records: list[dict],
    manifest: list[dict],
    attempt_log: dict | None = None,
    source_urls_by_app: dict[int, set[str]] | None = None,
) -> dict:
    """Validate exact manifest reconciliation, provenance, trace counts and quality gates."""
    errors = list(validate_manifest(manifest))
    warnings: list[str] = []
    manifest_by_id = {r.get("app_id"): r for r in manifest if isinstance(r, dict)}
    record_ids = [r.get("app_id") for r in records if isinstance(r, dict)]
    if len(records) != 100:
        errors.append(f"final raw dataset must have exactly 100 records; found {len(records)}")
    if len(set(record_ids)) != len(record_ids):
        errors.append("final raw dataset contains duplicate app_id values")
    if set(record_ids) != set(manifest_by_id):
        errors.append(f"final raw dataset does not reconcile to manifest; missing={sorted(set(manifest_by_id)-set(record_ids))}, extra={sorted(set(record_ids)-set(manifest_by_id))}")

    trace_list = (attempt_log or {}).get("traces", [])
    traces_by_id: dict[int, dict] = {}
    for trace in trace_list:
        app_id = trace.get("app_id")
        if app_id in traces_by_id:
            errors.append(f"attempt log has duplicate trace for app_id={app_id}")
        traces_by_id[app_id] = trace
    if set(traces_by_id) != set(manifest_by_id):
        errors.append(f"attempt log does not reconcile to manifest; missing={sorted(set(manifest_by_id)-set(traces_by_id))}, extra={sorted(set(traces_by_id)-set(manifest_by_id))}")

    for record in records:
        if not isinstance(record, dict):
            errors.append("final dataset contains non-object record")
            continue
        app_id = record.get("app_id")
        expected = manifest_by_id.get(app_id)
        if expected and (record.get("app") != expected.get("app") or record.get("category") != expected.get("category")):
            errors.append(f"app_id={app_id} identity/category differs from manifest")
        missing_provenance = [k for k in ("source_mode", "research_tool", "research_timestamp", "query_count", "source_count", "attempt_count", "research_run_id") if k not in record]
        if missing_provenance:
            errors.append(f"app_id={app_id} missing provenance fields: {missing_provenance}")
            continue
        if record.get("source_mode") not in FINAL_SOURCE_MODES:
            errors.append(f"app_id={app_id} has invalid source_mode={record.get('source_mode')!r}")
        for count_name in ("query_count", "source_count"):
            if not isinstance(record.get(count_name), int) or record[count_name] < 0:
                errors.append(f"app_id={app_id} {count_name} must be a nonnegative integer")
        if record.get("attempt_count") is not None and (not isinstance(record.get("attempt_count"), int) or record["attempt_count"] < 0):
            errors.append(f"app_id={app_id} attempt_count must be a nonnegative integer or null when not recorded")
        mode = record.get("source_mode")
        if mode == "NOT_RUN":
            if record.get("research_status") != "FAILED":
                errors.append(f"app_id={app_id} NOT_RUN record must use research_status=FAILED")
            if record.get("evidence"):
                errors.append(f"app_id={app_id} NOT_RUN record must not contain evidence")
        if mode == "PRIOR_CAPTURE" and record.get("attempt_count") is not None:
            warnings.append(f"app_id={app_id} prior capture has an attempt_count; verify original per-call logs support it")
        trace = traces_by_id.get(app_id)
        if trace:
            queries = trace.get("queries", [])
            sources = trace.get("sources", [])
            if record.get("query_count") != len(queries):
                errors.append(f"app_id={app_id} query_count does not match attempt trace")
            if record.get("source_count") != len(sources):
                errors.append(f"app_id={app_id} source_count does not match attempt trace")
            if mode == "LIVE_AGENT" and record.get("attempt_count") != len(trace.get("attempts", [])):
                errors.append(f"app_id={app_id} attempt_count does not match live attempt trace")
            source_urls = {s.get("url", s.get("source_url", "")) for s in sources if isinstance(s, dict)}
            source_urls.update((source_urls_by_app or {}).get(app_id, set()))
            gate = validate_record_quality(record, source_urls=source_urls)
        else:
            source_urls = (source_urls_by_app or {}).get(app_id)
            gate = validate_record_quality(record, source_urls=source_urls)
        record["quality_gate"] = gate
        if gate["status"] == "FAIL":
            errors.extend(f"app_id={app_id} quality gate: {message}" for message in gate["errors"])
        warnings.extend(f"app_id={app_id} quality warning: {message}" for message in gate["warnings"])

    return {
        "status": "FAIL" if errors else ("WARN" if warnings else "PASS"),
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "record_quality_counts": {
            status: sum(1 for r in records if isinstance(r, dict) and r.get("quality_gate", {}).get("status") == status)
            for status in ("PASS", "WARN", "FAIL")
        },
        "traces": len(trace_list),
    }

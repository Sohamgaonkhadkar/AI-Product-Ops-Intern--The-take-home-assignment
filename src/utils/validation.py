from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

CATEGORIES = {
    "CRM and Sales", "Support and Helpdesk", "Communications and Messaging",
    "Marketing, Ads, Email and Social", "Ecommerce", "Data, SEO and Scraping",
    "Developer, Infra and Data platforms", "Productivity and Project Management",
    "Finance and Fintech", "AI, Research and Media-native",
}
AUTH = {"OAuth 2.0", "API key", "Bearer/token", "Basic", "Service account", "Custom", "Other"}
SELF_SERVE = {
    "SELF_SERVE", "SELF_SERVE_WITH_RESTRICTIONS", "PAID_PLAN_REQUIRED",
    "ADMIN_APPROVAL_REQUIRED", "PARTNER_OR_CONTACT_SALES", "ENTERPRISE_ONLY", "UNKNOWN",
}
API_AVAILABLE = {"YES", "NO", "UNKNOWN"}
API_TYPES = {"REST", "GraphQL", "SDK", "Webhooks", "SOAP", "RPC", "CLI", "Other"}
BREADTH = {"BROAD", "MODERATE", "NARROW", "UNKNOWN"}
MCP = {"AVAILABLE", "NOT_FOUND", "UNKNOWN"}
BUILDABILITY = {
    "BUILDABLE_NOW", "BUILDABLE_WITH_CONSTRAINTS", "OUTREACH_REQUIRED",
    "NOT_REALISTIC_TODAY", "UNKNOWN",
}
EVIDENCE_FIELDS = {
    "description", "auth", "self_serve", "credential_access", "api", "mcp",
    "buildability", "other",
}
SOURCE_TYPES = {
    "official_docs", "official_api_docs", "official_auth_docs", "official_blog",
    "official_github", "official_support", "official_product", "official_pricing",
    "third_party", "community",
}


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _is_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _is_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_record(record: dict, require_evidence_for_known: bool = True) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version", "app_id", "app", "category", "website_hint", "description",
        "auth_status", "auth_methods", "self_serve_status", "self_serve_details",
        "credential_access", "api", "mcp", "buildability", "evidence", "confidence",
        "research_timestamp", "research_status", "verification_status",
    }
    _require(isinstance(record, dict), "record must be an object", errors)
    if not isinstance(record, dict):
        return errors
    _require(required.issubset(record), f"missing keys: {sorted(required - record.keys())}", errors)
    if not required.issubset(record):
        return errors
    _require(record["schema_version"] == "1.0", "schema_version must be 1.0", errors)
    _require(isinstance(record["app_id"], int) and 1 <= record["app_id"] <= 100, "app_id must be 1..100", errors)
    _require(isinstance(record["app"], str) and bool(record["app"].strip()), "app must be non-empty text", errors)
    _require(record["category"] in CATEGORIES, "category is not in the assignment's 10 categories", errors)
    _require(isinstance(record["website_hint"], str), "website_hint must be text", errors)
    if record["website_hint"]:
        _require(bool(urlparse(record["website_hint"]).scheme), "website_hint must be URL-shaped or empty", errors)
    _require(isinstance(record["description"], str), "description must be text", errors)
    _require(record["auth_status"] in {"CONFIRMED", "PARTIAL", "UNKNOWN"}, "invalid auth_status", errors)
    _require(isinstance(record["auth_methods"], list) and set(record["auth_methods"]).issubset(AUTH), "invalid auth_methods", errors)
    if record["auth_status"] == "UNKNOWN":
        _require(not record["auth_methods"], "UNKNOWN auth_status must not assert methods", errors)
    else:
        _require(bool(record["auth_methods"]), "known auth_status requires at least one method", errors)
    _require(record["self_serve_status"] in SELF_SERVE, "invalid self_serve_status", errors)
    _require(isinstance(record["self_serve_details"], str), "self_serve_details must be text", errors)
    ca = record["credential_access"]
    _require(isinstance(ca, dict) and {"status", "path", "plan_or_gate"}.issubset(ca), "credential_access requires status/path/plan_or_gate", errors)
    if isinstance(ca, dict):
        _require(ca.get("status") in {"SELF_SERVE", "RESTRICTED", "GATED", "UNKNOWN"}, "invalid credential_access.status", errors)
        _require(isinstance(ca.get("path"), str) and isinstance(ca.get("plan_or_gate"), str), "credential_access path/gate must be text", errors)
    api = record["api"]
    _require(isinstance(api, dict) and {"available", "types", "breadth", "details"}.issubset(api), "api requires available/types/breadth/details", errors)
    if isinstance(api, dict):
        _require(api.get("available") in API_AVAILABLE, "invalid api.available", errors)
        _require(isinstance(api.get("types"), list) and set(api.get("types", [])).issubset(API_TYPES), "invalid api.types", errors)
        _require(api.get("breadth") in BREADTH, "invalid api.breadth", errors)
        _require(isinstance(api.get("details"), str), "api.details must be text", errors)
    mcp = record["mcp"]
    _require(isinstance(mcp, dict) and {"status", "details", "search_scope"}.issubset(mcp), "mcp requires status/details/search_scope", errors)
    if isinstance(mcp, dict):
        _require(mcp.get("status") in MCP, "invalid mcp.status", errors)
        _require(isinstance(mcp.get("details"), str) and isinstance(mcp.get("search_scope"), str), "mcp details/scope must be text", errors)
    build = record["buildability"]
    _require(isinstance(build, dict) and {"verdict", "blocker", "rationale"}.issubset(build), "buildability requires verdict/blocker/rationale", errors)
    if isinstance(build, dict):
        _require(build.get("verdict") in BUILDABILITY, "invalid buildability.verdict", errors)
        _require(all(isinstance(build.get(k), str) for k in ("blocker", "rationale")), "buildability text fields must be strings", errors)
    _require(isinstance(record["evidence"], list), "evidence must be a list", errors)
    if isinstance(record["evidence"], list):
        for i, item in enumerate(record["evidence"]):
            path = f"evidence[{i}]"
            _require(isinstance(item, dict), f"{path} must be an object", errors)
            if not isinstance(item, dict):
                continue
            for key in ("claim", "field", "source_url", "source_title", "source_type", "accessed_at", "support"):
                _require(key in item, f"{path}.{key} missing", errors)
            if not all(k in item for k in ("claim", "field", "source_url", "source_title", "source_type", "accessed_at", "support")):
                continue
            parsed = urlparse(str(item["source_url"]))
            _require(parsed.scheme in {"http", "https"} and bool(parsed.netloc), f"{path}.source_url must be an http(s) URL", errors)
            _require(item["field"] in EVIDENCE_FIELDS, f"{path}.field invalid", errors)
            _require(item["source_type"] in SOURCE_TYPES, f"{path}.source_type invalid", errors)
            _require(item["support"] in {"supports", "contradicts", "context"}, f"{path}.support invalid", errors)
            _require(all(isinstance(item[k], str) for k in ("claim", "source_title")), f"{path} claim/title must be strings", errors)
            _require(_is_date(item["accessed_at"]), f"{path}.accessed_at must be ISO date (YYYY-MM-DD)", errors)
    _require(record["confidence"] in {"HIGH", "MEDIUM", "LOW"}, "invalid confidence", errors)
    _require(_is_datetime(record["research_timestamp"]), "research_timestamp must be ISO datetime", errors)
    _require(record["research_status"] in {"COMPLETE", "PARTIAL", "FAILED"}, "invalid research_status", errors)
    _require(record["verification_status"] in {"NOT_CHECKED", "AUTO_VERIFIED", "HUMAN_VERIFIED", "MIXED", "UNRESOLVED"}, "invalid verification_status", errors)

    if require_evidence_for_known:
        fields = {e.get("field") for e in record["evidence"] if isinstance(e, dict) and e.get("support") == "supports"}
        expected = set()
        if record["description"] and record["description"].strip().lower() not in {"unknown", "not established"}:
            expected.add("description")
        if record["auth_status"] != "UNKNOWN": expected.add("auth")
        if record["self_serve_status"] != "UNKNOWN": expected.add("self_serve")
        if record["credential_access"]["status"] != "UNKNOWN": expected.add("credential_access")
        if record["api"]["available"] != "UNKNOWN": expected.add("api")
        if record["mcp"]["status"] != "UNKNOWN": expected.add("mcp")
        if record["buildability"]["verdict"] != "UNKNOWN": expected.add("buildability")
        missing = expected - fields
        _require(not missing, f"known claims lack field-specific supporting evidence: {sorted(missing)}", errors)
    return errors


def validate_manifest(apps: list[dict]) -> list[str]:
    errors: list[str] = []
    if len(apps) != 100:
        errors.append(f"manifest must contain 100 apps; found {len(apps)}")
    ids = [a.get("app_id") for a in apps]
    names = [str(a.get("app", "")).casefold() for a in apps]
    if sorted(ids) != list(range(1, 101)):
        errors.append("manifest IDs must be exactly 1..100")
    if len(set(names)) != len(names):
        errors.append("manifest contains duplicate app names")
    if any(a.get("category") not in CATEGORIES for a in apps):
        errors.append("manifest contains an unexpected category")
    return errors

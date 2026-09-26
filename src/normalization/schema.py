"""
Data schema definitions for the Composio research pipeline.
Strict schema ensures consistency across all 100 apps.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime
import json


# ── Enum-like constants ──

AUTH_METHODS = [
    "OAUTH2", "API_KEY", "BEARER_TOKEN", "BASIC_AUTH",
    "CUSTOM_AUTH", "SERVICE_ACCOUNT", "BOT_TOKEN", "HMAC",
    "NONE", "UNKNOWN"
]

SELF_SERVE_STATUSES = [
    "SELF_SERVE", "SELF_SERVE_WITH_RESTRICTIONS", "PAID_PLAN_REQUIRED",
    "ADMIN_APPROVAL_REQUIRED", "PARTNER_OR_CONTACT_SALES",
    "ENTERPRISE_ONLY", "OPEN_SOURCE", "UNKNOWN"
]

API_TYPES = [
    "REST", "GRAPHQL", "SOAP", "GRPC", "WEBSOCKET",
    "SDK_ONLY", "CLI", "WEBHOOK"
]

API_BREADTHS = [
    "COMPREHENSIVE", "BROAD", "MODERATE", "NARROW", "MINIMAL", "UNKNOWN"
]

MCP_STATUSES = ["AVAILABLE", "NOT_FOUND", "UNKNOWN"]

BUILDABILITY_VERDICTS = [
    "BUILDABLE_NOW", "BUILDABLE_WITH_CONSTRAINTS",
    "OUTREACH_REQUIRED", "NOT_REALISTIC_TODAY", "UNKNOWN"
]

BLOCKERS = [
    "NONE", "PARTNER_APPROVAL", "PAID_PLAN", "ADMIN_APPROVAL",
    "LIMITED_API", "NO_PUBLIC_API", "COMPLEX_OAUTH", "RATE_LIMITS",
    "ENTERPRISE_ONLY", "DEPRECATED_API", "CLOSED_PLATFORM",
    "UNCLEAR_DOCS", "MULTIPLE"
]

SOURCE_TYPES = [
    "official_docs", "official_blog", "official_github",
    "official_support", "third_party", "community"
]

CONFIDENCE_LEVELS = ["HIGH", "MEDIUM", "LOW", "VERY_LOW"]


@dataclass
class Evidence:
    claim: str
    source_url: str
    source_title: str
    source_type: str  # one of SOURCE_TYPES
    accessed_at: str  # ISO 8601


@dataclass
class APIInfo:
    available: bool
    types: List[str]  # subset of API_TYPES
    breadth: str  # one of API_BREADTHS
    details: str


@dataclass
class MCPInfo:
    available: str  # one of MCP_STATUSES
    details: str


@dataclass
class BuildabilityInfo:
    verdict: str  # one of BUILDABILITY_VERDICTS
    blocker: str  # one of BLOCKERS
    details: str = ""


@dataclass
class AppResearchResult:
    """Complete research result for a single app."""
    id: int
    app: str
    category: str
    category_id: int
    website: str
    description: str
    auth_methods: List[str]  # subset of AUTH_METHODS
    self_serve_status: str  # one of SELF_SERVE_STATUSES
    self_serve_details: str
    api: dict  # APIInfo as dict
    mcp: dict  # MCPInfo as dict
    buildability: dict  # BuildabilityInfo as dict
    evidence: List[dict]  # list of Evidence as dict
    confidence: str  # one of CONFIDENCE_LEVELS
    research_timestamp: str  # ISO 8601
    verification_status: str = "UNVERIFIED"
    notes: str = ""


def validate_app_result(result: dict) -> List[str]:
    """Validate an app research result against the schema.
    Returns list of validation errors (empty = valid).
    """
    errors = []

    # Required fields
    required = [
        "id", "app", "category", "category_id", "website",
        "description", "auth_methods", "self_serve_status",
        "self_serve_details", "api", "mcp", "buildability",
        "evidence", "confidence", "research_timestamp"
    ]
    for f in required:
        if f not in result:
            errors.append(f"Missing required field: {f}")

    # Enum validations
    if "auth_methods" in result:
        for am in result["auth_methods"]:
            if am not in AUTH_METHODS:
                errors.append(f"Invalid auth_method: {am}")
        if not result["auth_methods"]:
            errors.append("auth_methods must not be empty")

    if "self_serve_status" in result:
        if result["self_serve_status"] not in SELF_SERVE_STATUSES:
            errors.append(f"Invalid self_serve_status: {result['self_serve_status']}")

    if "api" in result:
        api = result["api"]
        if "available" not in api:
            errors.append("api.available is required")
        if "types" in api:
            for t in api["types"]:
                if t not in API_TYPES:
                    errors.append(f"Invalid api.type: {t}")
        if "breadth" in api and api["breadth"] not in API_BREADTHS:
            errors.append(f"Invalid api.breadth: {api['breadth']}")

    if "mcp" in result:
        mcp = result["mcp"]
        if "available" in mcp and mcp["available"] not in MCP_STATUSES:
            errors.append(f"Invalid mcp.available: {mcp['available']}")

    if "buildability" in result:
        b = result["buildability"]
        if "verdict" in b and b["verdict"] not in BUILDABILITY_VERDICTS:
            errors.append(f"Invalid buildability.verdict: {b['verdict']}")
        if "blocker" in b and b["blocker"] not in BLOCKERS:
            errors.append(f"Invalid buildability.blocker: {b['blocker']}")

    if "confidence" in result:
        if result["confidence"] not in CONFIDENCE_LEVELS:
            errors.append(f"Invalid confidence: {result['confidence']}")

    # Evidence validation
    if "evidence" in result:
        if not result["evidence"]:
            errors.append("evidence must not be empty — at least one evidence entry required")
        for i, ev in enumerate(result["evidence"]):
            if "claim" not in ev or not ev["claim"]:
                errors.append(f"evidence[{i}]: missing claim")
            if "source_url" not in ev or not ev["source_url"]:
                errors.append(f"evidence[{i}]: missing source_url")
            if "source_type" in ev and ev["source_type"] not in SOURCE_TYPES:
                errors.append(f"evidence[{i}]: invalid source_type: {ev['source_type']}")

    return errors


def create_empty_result(app_def: dict, category_name: str, category_id: int) -> dict:
    """Create an empty result template for an app."""
    return {
        "id": app_def["id"],
        "app": app_def["name"],
        "category": category_name,
        "category_id": category_id,
        "website": app_def["website"],
        "description": "",
        "auth_methods": [],
        "self_serve_status": "UNKNOWN",
        "self_serve_details": "",
        "api": {
            "available": False,
            "types": [],
            "breadth": "UNKNOWN",
            "details": ""
        },
        "mcp": {
            "available": "UNKNOWN",
            "details": ""
        },
        "buildability": {
            "verdict": "UNKNOWN",
            "blocker": "NONE",
            "details": ""
        },
        "evidence": [],
        "confidence": "VERY_LOW",
        "research_timestamp": datetime.utcnow().isoformat() + "Z",
        "verification_status": "UNVERIFIED",
        "notes": ""
    }

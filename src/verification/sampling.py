"""Deterministic greedy max-coverage sample selection for final verification."""
from __future__ import annotations

import hashlib
from collections import defaultdict

from src.utils.quality import FINAL_SOURCE_MODES

DEFAULT_SEED = 20260924
STRATUM_WEIGHTS = {
    "category": 20,
    "auth_status": 3,
    "auth_method": 3,
    "self_serve_status": 8,
    "credential_status": 7,
    "api_available": 6,
    "api_type": 5,
    "api_breadth": 3,
    "mcp_status": 8,
    "buildability": 8,
    "low_confidence": 1,
    "partial_record": 2,
    "source_conflict": 2,
}


def record_strata(record: dict) -> set[str]:
    features = {
        f"category:{record.get('category', 'UNKNOWN')}",
        f"auth_status:{record.get('auth_status', 'UNKNOWN')}",
        f"self_serve_status:{record.get('self_serve_status', 'UNKNOWN')}",
        f"credential_status:{(record.get('credential_access') or {}).get('status', 'UNKNOWN')}",
        f"api_available:{(record.get('api') or {}).get('available', 'UNKNOWN')}",
        f"api_breadth:{(record.get('api') or {}).get('breadth', 'UNKNOWN')}",
        f"mcp_status:{(record.get('mcp') or {}).get('status', 'UNKNOWN')}",
        f"buildability:{(record.get('buildability') or {}).get('verdict', 'UNKNOWN')}",
    }
    features.update(f"auth_method:{x}" for x in record.get("auth_methods", []))
    features.update(f"api_type:{x}" for x in (record.get("api") or {}).get("types", []))
    if record.get("confidence") == "LOW":
        features.add("low_confidence:LOW")
    if record.get("research_status") == "PARTIAL":
        features.add("partial_record:PARTIAL")
    if record.get("source_conflicts"):
        features.add("source_conflict:PRESENT")
    return features


def _weight(feature: str) -> int:
    group = feature.split(":", 1)[0]
    return STRATUM_WEIGHTS.get(group, 1)


def _tie_break(seed: int, app_id: int) -> str:
    return hashlib.sha256(f"{seed}:{app_id}".encode("utf-8")).hexdigest()


def select_sample(records: list[dict], target_size: int = 20, seed: int = DEFAULT_SEED) -> dict:
    if target_size < 1:
        raise ValueError("target_size must be at least one")
    eligible = [
        r for r in records
        if r.get("source_mode") in FINAL_SOURCE_MODES - {"NOT_RUN"}
        and r.get("research_status") in {"COMPLETE", "PARTIAL"}
    ]
    if len({r.get("app_id") for r in eligible}) != len(eligible):
        raise ValueError("eligible records contain duplicate app_id")
    target = min(target_size, len(eligible))
    remaining = {r["app_id"]: r for r in eligible}
    selected: list[dict] = []
    covered: set[str] = set()
    while remaining and len(selected) < target:
        scored = []
        for app_id, record in remaining.items():
            novel = record_strata(record) - covered
            score = sum(_weight(x) for x in novel)
            scored.append((-score, _tie_break(seed, app_id), app_id, record))
        _, _, chosen_id, chosen = min(scored)
        selected.append(chosen)
        covered.update(record_strata(chosen))
        del remaining[chosen_id]
    return {
        "seed": seed,
        "target_size": target_size,
        "eligible_count": len(eligible),
        "selected_count": len(selected),
        "selected_ids": [r["app_id"] for r in selected],
        "covered_strata": sorted(covered),
        "selected_records": selected,
    }


def summarize_coverage(selected_records: list[dict], eligible_records: list[dict], manifest: list[dict]) -> dict:
    selected_features = set().union(*(record_strata(r) for r in selected_records)) if selected_records else set()
    eligible_features = set().union(*(record_strata(r) for r in eligible_records)) if eligible_records else set()
    expected_categories = {a.get("category") for a in manifest}
    selected_categories = {r.get("category") for r in selected_records}
    category_not_observed = sorted(expected_categories - {r.get("category") for r in eligible_records})
    return {
        "categories": {
            "selected": sorted(selected_categories),
            "covered_count": len(selected_categories),
            "manifest_category_count": len(expected_categories),
            "not_in_sample_but_observed": sorted({r.get("category") for r in eligible_records} - selected_categories),
            "not_observed_in_eligible_records": category_not_observed,
        },
        "strata_covered": sorted(selected_features),
        "strata_observed_but_not_in_sample": sorted(eligible_features - selected_features),
        "strata_not_observed_in_eligible_records": sorted({
            f"mcp_status:{x}" for x in ("AVAILABLE", "NOT_FOUND", "UNKNOWN")
        } - eligible_features) + sorted({
            f"buildability:{x}" for x in ("BUILDABLE_NOW", "BUILDABLE_WITH_CONSTRAINTS", "OUTREACH_REQUIRED", "NOT_REALISTIC_TODAY", "UNKNOWN")
        } - eligible_features),
    }

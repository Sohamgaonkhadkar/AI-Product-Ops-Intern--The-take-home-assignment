from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

CORE_GROUPS = ("auth", "self_serve", "credential_access", "api_availability", "mcp", "buildability")
POST_RECHECK_STATUSES = {"CONFIRMED", "CONFLICT", "UNRESOLVED", "NOT_RECHECKED"}
POST_RECHECK_INDEPENDENCE = {"ALTERNATIVE_SOURCE", "FRESH_REINSPECTION", "MULTI_SOURCE"}


def _equal(a, b) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        try:
            return set(a) == set(b)
        except TypeError:
            return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a == b
    return a == b


def get_path(record: dict, dotted_path: str):
    cur = record
    for part in dotted_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted_path)
        cur = cur[part]
    return cur


def set_path(record: dict, dotted_path: str, value) -> None:
    parts = dotted_path.split(".")
    cur = record
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            raise KeyError(dotted_path)
        cur = cur[part]
    cur[parts[-1]] = copy.deepcopy(value)


def _valid_http_url(url: str) -> bool:
    p = urlparse(url)
    return p.scheme in {"http", "https"} and bool(p.netloc)


def _validate_post_rechecks(post_rechecks: list[dict] | None) -> dict[tuple[int, str], dict]:
    indexed: dict[tuple[int, str], dict] = {}
    for check in post_rechecks or []:
        app_id = check.get("app_id")
        field_path = check.get("field_path")
        if not isinstance(app_id, int) or not field_path:
            raise ValueError("post-recheck row requires integer app_id and field_path")
        key = (app_id, field_path)
        if key in indexed:
            raise ValueError(f"duplicate post-recheck for app_id={app_id}, field_path={field_path}")
        if check.get("status") not in POST_RECHECK_STATUSES:
            raise ValueError(f"invalid post-recheck status for {key}")
        if check.get("verifier_type") not in {"automated_independent", "human", "pending_human"}:
            raise ValueError(f"invalid post-recheck verifier_type for {key}")
        if not check.get("audit_id") or not check.get("method"):
            raise ValueError(f"post-recheck row for {key} requires audit_id and method")
        if check.get("independence_level") not in POST_RECHECK_INDEPENDENCE:
            raise ValueError(f"post-recheck row for {key} requires a valid independence_level")
        source = check.get("source") or {}
        if check.get("status") == "CONFIRMED":
            if "value" not in check:
                raise ValueError(f"confirmed post-recheck for {key} requires an explicit observed value")
            if not _valid_http_url(source.get("source_url", "")):
                raise ValueError(f"confirmed post-recheck for {key} requires a valid source URL")
        for extra_source in check.get("supporting_sources", []):
            if not _valid_http_url(extra_source.get("source_url", "")):
                raise ValueError(f"invalid supporting source URL for post-recheck {key}")
        indexed[key] = copy.deepcopy(check)
    return indexed


def process_verification(
    records: list[dict],
    ledger: list[dict],
    post_rechecks: list[dict] | None = None,
) -> tuple[list[dict], list[dict], dict]:
    dataset = {r["app_id"]: copy.deepcopy(r) for r in records}
    if len(dataset) != len(records):
        raise ValueError("raw dataset contains duplicate app_id")
    post_by_key = _validate_post_rechecks(post_rechecks)
    out_ledger = []
    per_app_groups: dict[int, set] = {}
    for item in ledger:
        row = copy.deepcopy(item)
        app_id = row.get("app_id")
        if app_id not in dataset:
            raise ValueError(f"verification row references missing app_id {app_id}")
        if row.get("app") != dataset[app_id]["app"]:
            raise ValueError(f"verification app name mismatch for {app_id}")
        path = row.get("field_path")
        if not path:
            raise ValueError(f"verification row for {app_id} has no field_path")
        initial = get_path(dataset[app_id], path)
        if not _equal(initial, row.get("initial_value")):
            raise ValueError(f"verification initial_value does not match raw data for {app_id}.{path}: {initial!r} != {row.get('initial_value')!r}")
        row["correctness"] = "UNRESOLVED" if row.get("adjudicable") is False else ("CORRECT" if _equal(initial, row.get("verified_value")) else "INCORRECT")
        row["verified_at"] = row.get("verified_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        source = row.get("source", {})
        if source and not _valid_http_url(source.get("source_url", "")):
            raise ValueError(f"invalid verification source URL for {app_id}.{path}")
        for extra_source in row.get("supporting_sources", []):
            if not _valid_http_url(extra_source.get("source_url", "")):
                raise ValueError(f"invalid supporting verification source URL for {app_id}.{path}")
        if row.get("verifier_type") not in {"automated_independent", "human", "pending_human"}:
            raise ValueError(f"invalid verifier_type for {app_id}.{path}")

        post = post_by_key.get((app_id, path))
        row["post_recheck"] = copy.deepcopy(post) if post else None
        row["post_recheck_correctness"] = None
        if post:
            if post.get("app") != dataset[app_id]["app"]:
                raise ValueError(f"post-recheck app name mismatch for {app_id}.{path}")
            primary_url = (row.get("source") or {}).get("source_url")
            recheck_url = (post.get("source") or {}).get("source_url")
            if post.get("independence_level") == "ALTERNATIVE_SOURCE" and primary_url == recheck_url:
                raise ValueError(f"post-recheck marked ALTERNATIVE_SOURCE but reused primary URL for {app_id}.{path}")
            if post.get("independence_level") == "MULTI_SOURCE":
                all_urls = [recheck_url] + [s.get("source_url") for s in post.get("supporting_sources", [])]
                if not any(url and url != primary_url for url in all_urls):
                    raise ValueError(f"post-recheck marked MULTI_SOURCE but has no URL distinct from primary source for {app_id}.{path}")
            if post.get("status") == "CONFIRMED":
                row["post_recheck_correctness"] = "CORRECT" if _equal(post.get("value"), row.get("verified_value")) else "INCORRECT"
            elif post.get("status") == "CONFLICT":
                row["post_recheck_correctness"] = "CONFLICT"
            else:
                row["post_recheck_correctness"] = "UNRESOLVED"

        if row.get("apply_correction", True) and row.get("adjudicable") is not False:
            set_path(dataset[app_id], path, row.get("verified_value"))
        for evidence_item in row.get("evidence_patch", []):
            if evidence_item not in dataset[app_id]["evidence"]:
                dataset[app_id]["evidence"].append(copy.deepcopy(evidence_item))
        group = row.get("metric_group")
        if group:
            per_app_groups.setdefault(app_id, set()).add(group)
        out_ledger.append(row)

    unused_post = set(post_by_key) - {(r["app_id"], r["field_path"]) for r in out_ledger}
    if unused_post:
        raise ValueError(f"post-recheck rows do not match a verification ledger row: {sorted(unused_post)}")

    all_core_rows = [r for r in out_ledger if r.get("metric_group") in CORE_GROUPS]
    adjudicable_core_rows = [r for r in all_core_rows if r.get("adjudicable") is not False]
    rows_by_app: dict[int, list[dict]] = {}
    for row in all_core_rows:
        rows_by_app.setdefault(row["app_id"], []).append(row)

    for app_id, record in dataset.items():
        rows = rows_by_app.get(app_id, [])
        groups = {r.get("metric_group") for r in rows}
        complete = set(CORE_GROUPS).issubset(groups)
        fully_adjudicable = complete and all(r.get("adjudicable") is not False for r in rows if r.get("metric_group") in CORE_GROUPS)
        if fully_adjudicable:
            record["verification_status"] = "AUTO_VERIFIED"
        elif rows:
            record["verification_status"] = "MIXED"
        else:
            record["verification_status"] = "NOT_CHECKED"

    sample_ids = sorted(per_app_groups)
    metrics = {
        "sample_size": len(sample_ids),
        "sample_app_ids": sample_ids,
        "expected_critical_rows": len(sample_ids) * len(CORE_GROUPS),
        "critical_rows_present": len(all_core_rows),
        "critical_rows_adjudicable": len(adjudicable_core_rows),
        "critical_rows_unresolved": len(all_core_rows) - len(adjudicable_core_rows),
        "missing_critical_groups_by_app": {},
        "field_accuracy": {},
        "post_recheck_accuracy": {},
        "record_accuracy": {},
        "errors": [],
    }
    for app_id in sample_ids:
        groups = {r.get("metric_group") for r in rows_by_app.get(app_id, [])}
        missing = sorted(set(CORE_GROUPS) - groups)
        if missing:
            metrics["missing_critical_groups_by_app"][str(app_id)] = missing

    for group in CORE_GROUPS:
        group_rows = [r for r in adjudicable_core_rows if r.get("metric_group") == group]
        all_group_rows = [r for r in all_core_rows if r.get("metric_group") == group]
        correct = sum(r["correctness"] == "CORRECT" for r in group_rows)
        metrics["field_accuracy"][group] = {
            "correct": correct,
            "checked": len(group_rows),
            "unresolved": sum(r.get("adjudicable") is False for r in all_group_rows),
            "present": len(all_group_rows),
        }
        rechecked = [r for r in group_rows if r.get("post_recheck_correctness") is not None]
        metrics["post_recheck_accuracy"][group] = {
            "correct": sum(r["post_recheck_correctness"] == "CORRECT" for r in rechecked),
            "checked": len(rechecked),
            "incorrect": sum(r["post_recheck_correctness"] == "INCORRECT" for r in rechecked),
            "conflicts": sum(r["post_recheck_correctness"] == "CONFLICT" for r in rechecked),
            "unresolved": sum(r["post_recheck_correctness"] == "UNRESOLVED" for r in rechecked),
            "not_rechecked": len(group_rows) - len(rechecked),
        }

    adjudicable_by_app = {}
    for app_id in sample_ids:
        rows = rows_by_app.get(app_id, [])
        by_group = {r["metric_group"]: r for r in rows}
        complete = set(CORE_GROUPS).issubset(by_group)
        all_adjudicable = complete and all(by_group[g].get("adjudicable") is not False for g in CORE_GROUPS)
        if all_adjudicable:
            adjudicable_by_app[app_id] = all(by_group[g]["correctness"] == "CORRECT" for g in CORE_GROUPS)
    record_correct = sum(adjudicable_by_app.values())
    metrics["record_accuracy"] = {
        "correct": record_correct,
        "checked": len(adjudicable_by_app),
        "partial_or_unadjudicable": len(sample_ids) - len(adjudicable_by_app),
    }
    metrics["errors"] = [
        {
            "app_id": r["app_id"],
            "app": r["app"],
            "field": r["field_path"],
            "initial_value": r["initial_value"],
            "verified_value": r["verified_value"],
            "error_type": r.get("error_type", "field_mismatch"),
            "reason": r.get("reason", ""),
            "metric_group": r.get("metric_group"),
        }
        for r in out_ledger if r["correctness"] == "INCORRECT"
    ]
    post_checked = [r for r in adjudicable_core_rows if r.get("post_recheck_correctness") is not None]
    metrics["post_correction_overall"] = {
        "correct": sum(r["post_recheck_correctness"] == "CORRECT" for r in post_checked),
        "checked": len(post_checked),
        "incorrect": sum(r["post_recheck_correctness"] == "INCORRECT" for r in post_checked),
        "conflicts": sum(r["post_recheck_correctness"] == "CONFLICT" for r in post_checked),
        "unresolved": sum(r["post_recheck_correctness"] == "UNRESOLVED" for r in post_checked),
        "not_rechecked": len(adjudicable_core_rows) - len(post_checked),
    }
    audit_ids = sorted({p["audit_id"] for p in post_by_key.values()})
    independence_counts: dict[str, int] = {}
    for p in post_by_key.values():
        level = p["independence_level"]
        independence_counts[level] = independence_counts.get(level, 0) + 1
    metrics["post_recheck_audit"] = {
        "audit_ids": audit_ids,
        "rows": len(post_by_key),
        "independence_level_counts": independence_counts,
        "verifier_types": sorted({p["verifier_type"] for p in post_by_key.values()}),
    }
    all_rechecked_rows = [r for r in out_ledger if r.get("post_recheck_correctness") is not None]
    metrics["post_recheck_all_rows"] = {
        "correct": sum(r["post_recheck_correctness"] == "CORRECT" for r in all_rechecked_rows),
        "checked": len(all_rechecked_rows),
        "incorrect": sum(r["post_recheck_correctness"] == "INCORRECT" for r in all_rechecked_rows),
        "conflicts": sum(r["post_recheck_correctness"] == "CONFLICT" for r in all_rechecked_rows),
        "unresolved": sum(r["post_recheck_correctness"] == "UNRESOLVED" for r in all_rechecked_rows),
        "critical_rows": sum(bool(r.get("metric_group")) for r in all_rechecked_rows),
        "supplemental_rows": sum(not r.get("metric_group") for r in all_rechecked_rows),
    }
    return [dataset[k] for k in sorted(dataset)], out_ledger, metrics


def write_csv(records: list[dict], path: Path) -> None:
    import csv
    columns = ["app_id", "app", "category", "description", "auth_status", "auth_methods", "self_serve_status", "self_serve_details", "credential_access_status", "api_available", "api_types", "api_breadth", "mcp_status", "buildability_verdict", "blocker", "evidence_count", "confidence", "research_status", "verification_status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "app_id": r["app_id"], "app": r["app"], "category": r["category"], "description": r["description"],
                "auth_status": r["auth_status"], "auth_methods": "; ".join(r["auth_methods"]),
                "self_serve_status": r["self_serve_status"], "self_serve_details": r["self_serve_details"],
                "credential_access_status": r["credential_access"]["status"], "api_available": r["api"]["available"],
                "api_types": "; ".join(r["api"]["types"]), "api_breadth": r["api"]["breadth"],
                "mcp_status": r["mcp"]["status"], "buildability_verdict": r["buildability"]["verdict"],
                "blocker": r["buildability"]["blocker"], "evidence_count": len(r["evidence"]), "confidence": r["confidence"],
                "research_status": r["research_status"], "verification_status": r["verification_status"],
            })

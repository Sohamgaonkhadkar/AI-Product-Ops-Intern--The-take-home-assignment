"""Provider-backed research adapter and deterministic capture replay helpers.

Live mode is optional and requires Tavily + an OpenAI-compatible chat-completions
endpoint. The committed research data is produced from the actual tool-assisted
source captures in data/evidence/, not from an assumed live API call.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils.validation import validate_record

ROOT = Path(__file__).resolve().parents[2]


class ResearchFailure(RuntimeError):
    """Research failure that preserves all attempted queries/source packets for the run log."""
    def __init__(self, message: str, trace: dict):
        super().__init__(message)
        self.trace = trace


SYSTEM_PROMPT = """You are a cautious product-ops API researcher. Return exactly one JSON object matching the supplied record contract. Use only inspected official/primary source material in the supplied page extracts for factual claims. Search-result snippets are discovery hints, not evidence. Never guess; use UNKNOWN/empty fields and explain gaps. Attach separate evidence entries for each important claim; every URL must be one of the supplied retrieved URLs. Set evidence accessed_at as YYYY-MM-DD. Separate the product API from MCP, and developer credential access from documentation availability. Preserve conflicts in source_conflicts. Use the controlled enums exactly. For MCP, AVAILABLE requires first-party evidence; NOT_FOUND means the supplied official documentation/repository inspection was sufficient for a bounded negative; otherwise UNKNOWN. Derive buildability only from the specified decision rules and state the rationale. Do not invent endpoints, prices, plan gates, or auth methods."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _http_json(url: str, payload: dict, headers: dict[str, str], timeout: int = 60) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1500]
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc


def _normalize_url(url: str) -> str:
    return url.rstrip("/").split("#", 1)[0].lower()


def _tavily_search(query: str, api_key: str) -> dict:
    return _http_json(
        "https://api.tavily.com/search",
        {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5,
            "include_answer": False,
            "include_raw_content": True,
        },
        {},
        timeout=60,
    )


def _openai_extract(app: dict, source_packets: list[dict], api_key: str) -> tuple[dict, str]:
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = {
        "app": app,
        "retrieved_at": _utc_now(),
        "methodology": {
            "self_serve": "Do not equate docs with credentials. SELF_SERVE means documented self-created credentials with no material paid/admin/partner gate; state trial/plan restrictions explicitly.",
            "api_breadth": "Use BROAD for multiple core resource families and meaningful operations, MODERATE for useful but partial coverage, NARROW for focused/limited, UNKNOWN if source coverage is insufficient. Never invent endpoint counts.",
            "buildability": "OUTREACH_REQUIRED for explicit partner/contact-sales/enterprise approval without a generally adequate self-serve route; NOT_REALISTIC_TODAY only with evidence of no meaningful API/technical infeasibility; UNKNOWN when decisive facts are unresolved; WITH_CONSTRAINTS for usable but materially gated/limited integrations; NOW for documented API + practical credentials + adequate surface + no major barrier.",
            "source_priority": ["official developer/API/auth docs", "official support/pricing", "first-party GitHub", "official product", "reputable secondary"],
        },
        "record_contract": "Follow schemas/research-record.schema.json; schema_version=1.0; use values as defined in docs/research_methodology.md. website_hint and description come from the app manifest and source evidence respectively.",
        "sources": source_packets,
    }
    result = _http_json(
        os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/chat/completions",
        {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        },
        {"Authorization": f"Bearer {api_key}"},
        timeout=120,
    )
    content = result["choices"][0]["message"]["content"]
    return json.loads(content), content


def unknown_record(app: dict, reason: str, research_status: str = "FAILED") -> dict:
    stamp = _utc_now()
    return {
        "schema_version": "1.0",
        "app_id": app["app_id"],
        "app": app["app"],
        "category": app["category"],
        "website_hint": app.get("website_hint", ""),
        "description": "Unknown",
        "auth_status": "UNKNOWN",
        "auth_methods": [],
        "self_serve_status": "UNKNOWN",
        "self_serve_details": reason,
        "credential_access": {"status": "UNKNOWN", "path": reason, "plan_or_gate": reason},
        "api": {"available": "UNKNOWN", "types": [], "breadth": "UNKNOWN", "details": reason},
        "mcp": {"status": "UNKNOWN", "details": reason, "search_scope": "No complete official-source search was completed."},
        "buildability": {"verdict": "UNKNOWN", "blocker": reason, "rationale": "Insufficient evidence to apply the buildability rule."},
        "evidence": [],
        "confidence": "LOW",
        "research_timestamp": stamp,
        "research_status": research_status,
        "verification_status": "NOT_CHECKED",
        "source_conflicts": [],
        "limitations": [reason],
        "researcher_notes": "Failure/unknown placeholder; this is not a negative finding.",
    }


def live_research_one(app: dict, max_retries: int = 2) -> tuple[dict, dict]:
    """Search independent topics, inspect returned raw page extracts, then extract a record.

    The caller must record that this mode used Tavily and the configured OpenAI-compatible
    endpoint. Search snippets alone are not accepted as claim support by validation policy.
    """
    tavily_key = os.getenv("TAVILY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not tavily_key or not openai_key:
        raise RuntimeError("Live mode requires TAVILY_API_KEY and OPENAI_API_KEY; use capture/replay mode without them.")
    queries = [
        f'"{app["app"]}" official developer API authentication documentation',
        f'"{app["app"]}" official API credentials developer signup plan access',
        f'"{app["app"]}" official MCP server documentation GitHub',
    ]
    logs: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    for query in queries:
        for attempt in range(1, max_retries + 2):
            try:
                result = _tavily_search(query, tavily_key)
                retrieved_at = _utc_now()
                logs.append({"query": query, "attempt": attempt, "status": "OK", "retrieved_at": retrieved_at, "results": len(result.get("results", []))})
                for item in result.get("results", []):
                    packets.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": (item.get("raw_content") or item.get("content") or "")[:6000],
                        "discovery_excerpt": item.get("content", ""),
                        "query": query,
                        "retrieved_at": retrieved_at,
                        "retrieval_method": "tavily_search_include_raw_content",
                    })
                break
            except Exception as exc:
                logs.append({"query": query, "attempt": attempt, "status": "ERROR", "error": str(exc), "retrieved_at": _utc_now()})
                if attempt > max_retries:
                    continue
                time.sleep(min(2 ** (attempt - 1), 8))
    unique: dict[str, dict] = {}
    for item in packets:
        if item["url"]:
            unique.setdefault(_normalize_url(item["url"]), item)
    packets = list(unique.values())
    if not packets:
        raise ResearchFailure(
            "Search provider returned no usable source pages",
            {"app_id": app["app_id"], "queries": queries, "attempts": logs, "sources": packets, "failed_stage": "search"},
        )
    last_error = None
    for attempt in range(1, max_retries + 2):
        try:
            record, raw_text = _openai_extract(app, packets, openai_key)
            if record.get("app_id") != app["app_id"] or record.get("app") != app["app"]:
                raise RuntimeError("extracted record does not match manifest row")
            allowed_urls = {_normalize_url(s["url"]) for s in packets}
            invented = [e.get("source_url") for e in record.get("evidence", []) if _normalize_url(e.get("source_url", "")) not in allowed_urls]
            if invented:
                raise RuntimeError(f"evidence URLs not present in retrieval log: {invented}")
            errors = validate_record(record)
            if errors:
                raise RuntimeError("schema/evidence validation failed: " + "; ".join(errors))
            logs.append({"extract_attempt": attempt, "status": "OK", "retrieved_at": _utc_now()})
            return record, {"app_id": app["app_id"], "queries": queries, "attempts": logs, "sources": packets, "raw_model_output": raw_text}
        except Exception as exc:
            last_error = str(exc)
            logs.append({"extract_attempt": attempt, "status": "ERROR", "error": last_error, "retrieved_at": _utc_now()})
            if attempt <= max_retries:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise ResearchFailure(
        last_error or "extraction failed",
        {"app_id": app["app_id"], "queries": queries, "attempts": logs, "sources": packets, "failed_stage": "extraction"},
    )


def validate_capture_against_manifest(records: list[dict], manifest: list[dict]) -> list[str]:
    errors: list[str] = []
    expected = {a["app_id"]: a for a in manifest}
    seen: set[int] = set()
    for record in records:
        app_id = record.get("app_id")
        if app_id not in expected:
            errors.append(f"unexpected app_id {app_id}")
            continue
        if app_id in seen:
            errors.append(f"duplicate app_id {app_id}")
        seen.add(app_id)
        app = expected[app_id]
        if record.get("app") != app["app"] or record.get("category") != app["category"]:
            errors.append(f"app_id {app_id} does not match manifest name/category")
        errs = validate_record(record)
        errors.extend(f"app_id {app_id}: {e}" for e in errs)
    return errors

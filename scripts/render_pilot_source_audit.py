#!/usr/bin/env python3
"""Validate and render the row-by-row source audit for the five-app pilot.

This script checks the audit crosswalk and renders captured adjudications. It
cannot independently fetch or human-review vendor pages; those observations are
recorded in the ledger and separate recheck capture.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/raw/pilot_results.json"
LEDGER_PATH = ROOT / "data/evidence/verification_ledger_input.json"
POST_PATH = ROOT / "data/evidence/pilot_post_recheck.json"
OUT_PATH = ROOT / "reports/pilot_source_audit.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def get_path(record: dict, dotted: str):
    cur = record
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def same(a, b):
    if isinstance(a, list) and isinstance(b, list):
        try:
            return set(a) == set(b)
        except TypeError:
            return a == b
    return a == b


def short(value, limit=170):
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    text = text.replace("|", "\\|").replace("\n", " ")
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def md_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def source_link(source: dict) -> str:
    title = md_cell(source.get("source_title") or "source")
    url = source.get("source_url") or ""
    return f"[{title}]({url})" if url else title


def main() -> None:
    raw = load(RAW_PATH)
    ledger_obj = load(LEDGER_PATH)
    post_obj = load(POST_PATH)
    checks = ledger_obj["checks"]
    post_checks = post_obj["checks"]
    raw_by_id = {row["app_id"]: row for row in raw}
    check_by_key = {(row["app_id"], row["field_path"]): row for row in checks}
    post_by_key = {(row["app_id"], row["field_path"]): row for row in post_checks}

    if len(checks) != 45 or len(check_by_key) != 45:
        raise SystemExit(f"expected 45 unique ledger rows; got {len(checks)} rows / {len(check_by_key)} unique")
    if len(post_checks) != 30 or len(post_by_key) != 30:
        raise SystemExit(f"expected 30 unique post-recheck rows; got {len(post_checks)} rows / {len(post_by_key)} unique")

    raw_mismatches = []
    for row in checks:
        actual = get_path(raw_by_id[row["app_id"]], row["field_path"])
        # The source audit specifically requires exact JSON equality, including list order.
        if actual != row["initial_value"]:
            raw_mismatches.append((row["app_id"], row["field_path"], actual, row["initial_value"]))
    if raw_mismatches:
        raise SystemExit(f"ledger/raw initial-value mismatches: {raw_mismatches}")

    post_unmatched = []
    for row in post_checks:
        key = (row["app_id"], row["field_path"])
        if key not in check_by_key:
            post_unmatched.append(key)
            continue
        if row.get("status") == "CONFIRMED" and not same(row.get("value"), check_by_key[key]["verified_value"]):
            post_unmatched.append((key, row.get("value"), check_by_key[key]["verified_value"]))
    if post_unmatched:
        raise SystemExit(f"post-recheck values do not match adjudicated values: {post_unmatched}")

    critical = [r for r in checks if r.get("metric_group")]
    critical_correct = sum(same(r["initial_value"], r["verified_value"]) for r in critical)
    critical_incorrect = len(critical) - critical_correct
    supplemental = [r for r in checks if not r.get("metric_group")]
    changed_supplemental = sum(not same(r["initial_value"], r["verified_value"]) for r in supplemental)
    recheck_confirmed = sum(r.get("status") == "CONFIRMED" for r in post_checks)
    post_correct = sum(
        r.get("status") == "CONFIRMED"
        and same(r.get("value"), check_by_key[(r["app_id"], r["field_path"])]["verified_value"])
        for r in post_checks
    )
    if (len(critical), critical_correct, critical_incorrect, len(supplemental), changed_supplemental) != (30, 29, 1, 15, 15):
        raise SystemExit("unexpected pilot verification counts; inspect the ledger before rendering")
    if (recheck_confirmed, post_correct) != (30, 30):
        raise SystemExit("unexpected post-recheck counts; inspect the separate audit before rendering")

    app_order = {1: "Salesforce", 22: "Twilio", 49: "Amazon Selling Partner", 61: "GitHub", 92: "Otter AI"}
    raw_hash = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()
    salesforce_raw = raw_by_id[1]
    raw_sf_mcp_details = salesforce_raw["mcp"]["details"]
    raw_sf_buildability_blocker = salesforce_raw["buildability"]["blocker"]
    if "Flex Credits" in raw_sf_mcp_details or "Flex Credits" in raw_sf_buildability_blocker:
        raise SystemExit("Salesforce raw first-pass text unexpectedly mentions Flex Credits; inspect before rendering wording audit")
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    lines = [
        "# Pilot source audit — five-app verification",
        "",
        f"**Rendered:** {generated_at}  ",
        f"**Raw first-pass dataset:** `data/raw/pilot_results.json` — SHA-256 `{raw_hash}`  ",
        f"**Scope:** {len(checks)} source-verification ledger rows and {len(post_checks)} separate post-correction observations across app IDs 1, 22, 49, 61 and 92.",
        "",
        "## Audit method and result",
        "",
        "The original `initial_value` for every ledger field was compared with the corresponding path in the unchanged raw JSON using exact JSON equality. Each adjudication was checked against the direct first-party source recorded in the ledger; search snippets were treated only as discovery leads. For the later recheck, each explicit observation was compared with the adjudicated value and its fresh source path. This was automated/source-assisted public-source review—not human verification, account testing, or package execution.",
        "",
        f"- Raw/ledger crosswalk: **45/45 exact matches**; mismatches: **0**.",
        f"- First-pass critical checks: **{critical_correct}/{len(critical)}** match; **{critical_incorrect}** critical mismatch (Amazon MCP `UNKNOWN` → independently supported `AVAILABLE`).",
        f"- Supplemental checks: **{changed_supplemental}/{len(supplemental)}** were evidence-backed detail corrections/expansions.",
        f"- Separate second-pass observations: **{post_correct}/{len(post_checks)}** confirmed values agree with the final adjudicated values; unresolved: 0; missing: 0.",
        "- The raw first-pass files were not rewritten. Corrections are applied only when the verification runner builds `data/verified/pilot_final_dataset.json`.",
        "",
        "## Source-audit decisions requiring special care",
        "",
        "1. **Amazon MCP false negative corrected.** The first pilot source check searched SP-API documentation and the models catalogue but missed Amazon's separate `amzn/selling-partner-api-samples/use-cases/sp-api-dev-mcp` repository. The exact follow-up GitHub query was `site:github.com/amzn/selling-partner-api-samples \"Local MCP for SP-API\" \"@amazon-sp-api-release/sp-api-dev-mcp\"`. The direct README, maintainer announcement #382, and scoped npm listing establish a first-party **local example MCP**. Amazon explicitly calls these educational examples, not supported products in their own right. Most assistant tools work locally without credentials; live SP-API execution/workflows need SP-API credentials. No package was installed or run. The old bounded `NOT_FOUND` conclusion was withdrawn; the raw first-pass `UNKNOWN` remains unchanged and correctly counts as a miss. The full 26-part `llms.txt` index is still only partially inspected, but that does not override the separate repo evidence.",
        "2. **Salesforce Hosted MCP billing language.** The official page says Hosted MCP is intended only for customers with Flex Credits and usage may be billed. The verified wording preserves that intended-customer/billing language and does **not** convert it into an unstated hard prerequisite.",
        "3. **Otter API key scope.** The Help Center's no-public-key FAQ is specifically about custom MCP setup. The separate Enterprise Public API documents Bearer API keys. The corrected notes explicitly keep those two credential paths distinct.",
        "4. **Amazon buildability scope.** `OUTREACH_REQUIRED` remains for the evaluated general/public multi-seller integration: public developer/profile/role and distribution approval still apply. The newly found local sample does not remove that gate or establish a supported hosted product. A private single-organization route remains a documented alternative.",
        "5. **Salesforce Flex Credits wording corrected after raw comparison.** The unchanged raw first-pass `mcp.details` and `buildability.blocker` did not mention Flex Credits, so the initial record did not claim credits were required. A post-recheck source observation had incorrectly combined the documented org-setup requirement with Flex Credits as if both were hard requirements. A fresh read of the [official Hosted MCP guide](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide) states that Hosted MCP Servers are *intended only for customers with Flex Credits* and that customers may be billed for server usage. The corrected records preserve this as intended-audience/billing language—not a proven technical or credential requirement. The observed MCP/buildability values and accuracy metrics do not change; the amendment is recorded in `data/evidence/pilot_post_recheck.json` and `data/evidence/salesforce_flex_credit_wording_audit.json`.",
        "",
        "## 45-row claim ledger audit",
        "",
        "`First pass → adjudicated` shows the preserved raw value and the source-supported value. Critical rows report first-pass correctness; supplemental rows show detail edits outside the six-group accuracy denominator. Full text, evidence-patch observations, methods and timestamps remain in `data/evidence/verification_ledger_input.json` and the joined ledger.",
        "",
        "| # | App / field | First pass → adjudicated | Audit result | Direct source | Adjudication note |",
        "|---:|---|---|---|---|---|",
    ]
    for idx, row in enumerate(checks, 1):
        key = (row["app_id"], row["field_path"])
        first = short(row["initial_value"], 130)
        verified = short(row["verified_value"], 160)
        if row.get("metric_group"):
            result = "critical match" if same(row["initial_value"], row["verified_value"]) else "critical mismatch"
        else:
            result = "supplemental changed" if not same(row["initial_value"], row["verified_value"]) else "supplemental unchanged"
        note = md_cell(row.get("reason", ""))
        if len(note) > 220:
            note = note[:219] + "…"
        lines.append(
            f"| {idx} | {app_order.get(row['app_id'], row['app'])} · `{row['field_path']}` | `{md_cell(first)}` → `{md_cell(verified)}` | {result} | {source_link(row.get('source') or {})} | {note} |"
        )

    lines += [
        "",
        "## 30-row separate post-correction recheck audit",
        "",
        "Every row below was explicitly captured in `data/evidence/pilot_post_recheck.json`; the verification runner does not copy the adjudicated value into this file. All checks are labeled `automated_independent`; the independence level is retained per row. The current Amazon MCP recheck was amended after the first bounded-negative conclusion was overturned, and its row-level timestamp plus top-level amendment record preserve that chronology.",
        "",
        "| # | App / field | Observed value | Status / concordance | Independence | Fresh source(s) |",
        "|---:|---|---|---|---|---|",
    ]
    for idx, row in enumerate(post_checks, 1):
        key = (row["app_id"], row["field_path"])
        agrees = same(row.get("value"), check_by_key[key]["verified_value"]) if row.get("status") == "CONFIRMED" else False
        concordance = "matches adjudication" if agrees else ("conflict" if row.get("status") == "CONFIRMED" else row.get("status", "unresolved"))
        sources = [source_link(row.get("source") or {})]
        sources += [source_link(s) for s in row.get("supporting_sources", [])]
        lines.append(
            f"| {idx} | {app_order.get(row['app_id'], row['app'])} · `{row['field_path']}` | `{md_cell(short(row.get('value'), 110))}` | {row.get('status')} / {concordance} | {row.get('independence_level')} | {'<br>'.join(sources)} |"
        )

    lines += [
        "",
        "## Limitations and human-review status",
        "",
        "- **Human verification: none.** All source checks are automated/source-assisted. Account-specific plan access, tenant configuration, production credential creation, Amazon role approvals and Otter workspace/admin entitlement were not tested.",
        "- The Amazon Local MCP package was not installed, run, or security-reviewed. Its existence and documented behavior are supported by its first-party README, maintainer announcement, and package listing; the README itself says the examples are not supported products.",
        "- The Amazon SP-API `llms.txt` index was only partly inspected (chunk 0 of 26). This limits any exhaustive statement about documentation coverage, but does not invalidate the direct first-party repository evidence for `AVAILABLE`.",
        "- The five apps were selected as a heterogeneous engineering pilot, not as a random sample of the 100-app manifest. Accuracy figures are pilot cross-checks, not a statistical estimate of full-set truth.",
        "- Vendor pages can change after access; evidence links and source observations are recorded with the checks. See `reports/human_qa.md` for pending account-level review.",
        "",
        "## Artifact pointers",
        "",
        "- First-pass raw data and traces: `data/raw/pilot_results.json`, `data/raw/pilot_attempts.json`, `data/evidence/pilot_capture.json`.",
        "- Claim ledger and separate recheck capture: `data/evidence/verification_ledger_input.json`, `data/evidence/pilot_post_recheck.json`.",
        "- Corrected outputs and computed metrics: `data/verified/pilot_final_dataset.json`, `.csv`, and `data/verified/pilot_verification_ledger.json`.",
        "- Generator/check: `scripts/render_pilot_source_audit.py`; run with `python scripts/render_pilot_source_audit.py`.",
        "",
    ]
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rendered {OUT_PATH} — raw exact matches 45/45; critical {critical_correct}/{len(critical)}; recheck {post_correct}/{len(post_checks)}.")


if __name__ == "__main__":
    main()

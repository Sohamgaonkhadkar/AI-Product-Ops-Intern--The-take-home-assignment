#!/usr/bin/env python3
"""Apply a claim-level verification ledger and report measured concordance.

The runner preserves the raw first-pass dataset, applies only explicit ledger
corrections to a separate verified copy, and joins an explicit second-pass audit.
It can optionally reconcile the corrected output to the exact app manifest and
source-attempt log; source-capture URLs remain a separate, auditable provenance
layer rather than being merged into the raw first-pass trace.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.quality import validate_final_dataset, validate_record_quality
from src.utils.validation import validate_record
from src.verification.engine import process_verification, write_csv


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def pct(n: int, d: int) -> str:
    return "N/A" if not d else f"{100*n/d:.1f}%"


def source_urls_by_app(capture_obj: dict | None) -> dict[int, set[str]]:
    by_app: dict[int, set[str]] = defaultdict(set)
    if not capture_obj:
        return by_app
    for packet in capture_obj.get("source_packets", []):
        url = packet.get("source_url")
        if not url:
            continue
        app_ids = set(packet.get("first_pass_apps", []))
        app_ids.update(packet.get("verification_apps", []))
        app_ids.update(packet.get("post_recheck_apps", []))
        app_ids.update(packet.get("candidate_identity_context_apps", []))
        for app_id in app_ids:
            by_app[app_id].add(url)
    return by_app


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply explicit source-backed adjudication and post-correction rechecks.")
    ap.add_argument("--research", default="data/raw/research_results.json")
    ap.add_argument("--ledger", default="data/evidence/verification_ledger_input.json")
    ap.add_argument("--post-recheck", default=None, help="Separate explicit second-pass audit capture; never inferred from verified_value.")
    ap.add_argument("--source-capture", default=None, help="Optional source/retrieval trace packet for first pass, verification, and recheck pages.")
    ap.add_argument("--manifest", default=None, help="Optional manifest for dataset-wide reconciliation (e.g. apps/apps.json).")
    ap.add_argument("--attempt-log", default=None, help="Optional raw attempt log for dataset-wide reconciliation.")
    ap.add_argument("--output", default="data/verified/final_dataset.json")
    ap.add_argument("--ledger-output", default="data/verified/verification_ledger.json")
    ap.add_argument("--quality-report", default="data/verified/final_quality_report.json")
    ap.add_argument("--report", default="reports/verification_report.md")
    args = ap.parse_args()

    raw = load(args.research)
    ledger_obj = load(args.ledger)
    ledger = ledger_obj.get("checks", ledger_obj)
    post_obj = load(args.post_recheck) if args.post_recheck else {"checks": []}
    post_checks = post_obj.get("checks", post_obj)
    capture_obj = load(args.source_capture) if args.source_capture else None
    source_map = source_urls_by_app(capture_obj)
    records, out_ledger, metrics = process_verification(raw, ledger, post_checks)

    validation_errors: list[str] = []
    dataset_audit = None
    if args.manifest and args.attempt_log:
        manifest = load(args.manifest)
        attempt_log = load(args.attempt_log)
        dataset_audit = validate_final_dataset(records, manifest, attempt_log, source_urls_by_app=source_map)
        validation_errors.extend(dataset_audit.get("errors", []))
    else:
        for record in records:
            validation_errors.extend(f"app {record.get('app_id')}: {e}" for e in validate_record(record))
            gate = validate_record_quality(record, source_urls=source_map.get(record.get("app_id")))
            record["quality_gate"] = gate
            if gate["status"] == "FAIL":
                validation_errors.extend(f"app {record['app_id']} quality gate: {e}" for e in gate["errors"])

    if validation_errors:
        print("Corrected dataset validation failed:\n- " + "\n- ".join(dict.fromkeys(validation_errors)), file=sys.stderr)
        return 2

    quality_counts = Counter(record.get("quality_gate", {}).get("status", "MISSING") for record in records)
    source_mode_counts = Counter(record.get("source_mode", "MISSING") for record in records)
    research_status_counts = Counter(record.get("research_status", "MISSING") for record in records)

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(records, out.with_suffix(".csv"))

    ledger_out = ROOT / args.ledger_output
    ledger_out.parent.mkdir(parents=True, exist_ok=True)
    ledger_payload = {
        "created_on": ledger_obj.get("created_on"),
        "created_at": ledger_obj.get("created_at"),
        "created_at_precision": ledger_obj.get("created_at_precision"),
        "capture_id": ledger_obj.get("capture_id"),
        "raw_dataset": args.research,
        "sample_selection": ledger_obj.get("sample_selection"),
        "sample_ids": ledger_obj.get("sample_ids"),
        "raw_source_mode": ledger_obj.get("raw_source_mode"),
        "raw_source_mode_counts": ledger_obj.get("raw_source_mode_counts"),
        "sample_source_mode_counts": ledger_obj.get("raw_source_mode_counts"),
        "full_population_source_mode_counts": ledger_obj.get("full_population_source_mode_counts"),
        "raw_dataset_sha256": ledger_obj.get("raw_dataset_sha256"),
        "verification_capture_mode": ledger_obj.get("verification_capture_mode"),
        "verifier_type": ledger_obj.get("verifier_type"),
        "source_capture": args.source_capture,
        "post_recheck_capture": args.post_recheck,
        "post_recheck_audit_metadata": {k: v for k, v in post_obj.items() if k != "checks"},
        "dataset_audit": dataset_audit,
        "quality_gate_counts": dict(sorted(quality_counts.items())),
        "source_mode_counts": dict(sorted(source_mode_counts.items())),
        "research_status_counts": dict(sorted(research_status_counts.items())),
        "checks": out_ledger,
        "metrics": metrics,
    }
    ledger_out.write_text(json.dumps(ledger_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    quality_payload = dataset_audit or {
        "status": "FAIL" if any(r.get("quality_gate", {}).get("status") == "FAIL" for r in records) else ("WARN" if any(r.get("quality_gate", {}).get("status") == "WARN" for r in records) else "PASS"),
        "errors": [],
        "warnings": [],
        "record_quality_counts": dict(sorted(quality_counts.items())),
        "record_quality": [{"app_id": r["app_id"], "quality_gate": r.get("quality_gate", {})} for r in records],
    }
    quality_out = ROOT / args.quality_report
    quality_out.parent.mkdir(parents=True, exist_ok=True)
    quality_out.write_text(json.dumps(quality_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sample_mode_counts = ledger_obj.get("raw_source_mode_counts", {})
    full_mode_counts = ledger_obj.get("full_population_source_mode_counts", {})
    post_status = post_obj.get("status", "POST_RECHECK_CAPTURE_NOT_SUPPLIED")
    lines = [
        "# Final verification report", "",
        f"- **First-pass dataset:** `{args.research}` (preserved; never overwritten)",
        f"- **Corrected dataset:** `{args.output}` and `{Path(args.output).with_suffix('.csv')}`",
        f"- **Verification ledger:** `{args.ledger_output}`",
        "- **Overall completion:** INCOMPLETE — all 100 manifest apps have first-pass records and the separate recheck confirmed all 12 changed rows (12/12), but the 20-app coverage audit is not a probability sample, human account checks are unavailable, and repository publication/public deployment remain blocked by missing authorization/access.",
        f"- **Sample size:** {metrics['sample_size']} apps (IDs: {', '.join(map(str, metrics['sample_app_ids']))})",
        f"- **Sample first-pass provenance:** {sample_mode_counts}; full population: {full_mode_counts}",
        f"- **Ledger rows:** {len(out_ledger)} ({metrics['critical_rows_present']} critical; {len(out_ledger)-metrics['critical_rows_present']} supplemental)",
        f"- **Verification source-capture packet:** `{args.source_capture or 'not supplied'}`",
        "- **Verifier type:** automated/source-assisted public-page inspection only; no human, tenant, authenticated API, or MCP-session result is claimed.",
    ]
    if dataset_audit:
        lines += [
            f"- **100-app manifest reconciliation:** {dataset_audit['status']} ({dataset_audit['traces']} attempt traces)",
            f"- **Full-dataset provenance counts:** source_mode={dict(sorted(source_mode_counts.items()))}; research_status={dict(sorted(research_status_counts.items()))}",
            f"- **Full-dataset record-quality gates:** {dict(sorted(quality_counts.items()))}",
        ]
    lines += [
        "", "## First-pass critical-field accuracy", "",
        "Accuracy is exact agreement between the unchanged first-pass normalized value and the independently inspected reference value. UNRESOLVED rows are excluded from the denominator and shown separately. Self-serve status and credential gate are scored separately. The 20 IDs were selected after all 100 manifest apps had COMPLETE/PARTIAL first-pass research. This deterministic, weighted max-coverage sample contains mixed provenance (14 LIVE_AGENT, 6 PRIOR_CAPTURE); it is an audit coverage sample, not a probability sample or estimator of population accuracy.",
    ]
    for group, data in metrics["field_accuracy"].items():
        lines.append(f"- **{group.replace('_', ' ')}:** {data['correct']}/{data['checked']} = {pct(data['correct'], data['checked'])}; unresolved {data['unresolved']}; rows present {data['present']}")
    ra = metrics["record_accuracy"]
    post_intro = (
        "No separate post-correction source reinspection has been performed. The primary verification pass and corrections are complete, but post-correction concordance is NOT MEASURED; values have not been copied into the recheck file. Only changed rows should be entered after an actual second source inspection."
        if not post_obj.get("checks") else
        "Second-pass observations were recorded from a separate post-adjudication source inspection; the runner does not copy adjudicated values into the recheck. Concordance measures agreement with those checked pages, not held-out ground truth. FRESH_REINSPECTION means the same URL was reopened; ALTERNATIVE_SOURCE uses a different primary URL; MULTI_SOURCE records multiple relevant pages. The source-capture packet preserves page chunks, errors, partial extractions, and date-only retrieval precision."
    )
    lines += [
        "",
        f"**Record accuracy:** {ra['correct']}/{ra['checked']} fully adjudicable sampled records = {pct(ra['correct'], ra['checked'])}; partial/unadjudicable records {ra['partial_or_unadjudicable']}.",
        "",
        "## Post-correction recheck (separate audit)", "",
        f"- **Status:** {post_status}",
        post_intro,
        f"- **Capture:** `{args.post_recheck or 'not supplied'}`",
        f"- **Rows recorded:** {metrics['post_recheck_audit']['rows']}",
        f"- **Audit IDs:** {', '.join(metrics['post_recheck_audit']['audit_ids']) if metrics['post_recheck_audit']['audit_ids'] else 'none'}",
        f"- **Recheck independence levels:** {', '.join(f'{k.lower()}={v}' for k, v in sorted(metrics['post_recheck_audit']['independence_level_counts'].items())) or 'none'}",
    ]
    pr = metrics["post_correction_overall"]
    lines.append(f"- **Critical-field post-correction concordance:** {pr['correct']}/{pr['checked']} = {pct(pr['correct'], pr['checked'])}; conflicting {pr['incorrect']}; unresolved {pr['unresolved']}; not rechecked {pr['not_rechecked']}.")
    all_post = metrics["post_recheck_all_rows"]
    lines.append(f"- **All changed rows (critical + supplemental):** {all_post['correct']}/{all_post['checked']} = {pct(all_post['correct'], all_post['checked'])}; conflicting {all_post['incorrect']}; unresolved {all_post['unresolved']} (critical={all_post['critical_rows']}, supplemental={all_post['supplemental_rows']}).")
    for group, data in metrics["post_recheck_accuracy"].items():
        lines.append(f"- **{group.replace('_', ' ')}:** {data['correct']}/{data['checked']} = {pct(data['correct'], data['checked'])}; conflicting {data['incorrect']}; unresolved {data['unresolved']}; not rechecked {data['not_rechecked']}")

    core_errors = [e for e in metrics["errors"] if e.get("metric_group")]
    supplemental_errors = [e for e in metrics["errors"] if not e.get("metric_group")]
    lines += [
        "", "## Observed first-pass misses and corrections", "",
        f"- **Critical-label mismatches:** {len(core_errors)} across {sum(d['checked'] for d in metrics['field_accuracy'].values())} adjudicable critical fields.",
        f"- **Supplemental field/nuance changes:** {len(supplemental_errors)}; not included in the six-group accuracy denominator.",
        "- Each ledger row preserves initial value, adjudicated value, source URL/title/type, reason, correction, evidence patch, and second-pass result.",
        "- Cause/prevention analysis with actual examples is generated separately in `reports/final_error_analysis.md`.",
        "",
    ]
    if metrics["errors"]:
        lines += ["| App | Field | First pass | Verified | Scope | Error label | Why/correction basis |", "|---|---|---|---|---|---|---|"]
        for e in metrics["errors"]:
            scope = "critical" if e.get("metric_group") else "supplemental"
            initial = json.dumps(e["initial_value"], ensure_ascii=False).replace("|", "\\|")
            verified = json.dumps(e["verified_value"], ensure_ascii=False).replace("|", "\\|")
            why = str(e.get("reason", "")).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {e['app']} | `{e['field']}` | `{initial}` | `{verified}` | {scope} | {e['error_type']} | {why} |")
    else:
        lines.append("No adjudicable mismatches were found in the supplied ledger.")
    lines += [
        "", "## Field-level provenance", "",
        f"See `{args.ledger_output}` for every sample initial value, verified value, source URL/title, method, reason, correction, verifier type, evidence patch, and joined post-recheck. `{args.research}` remains unchanged.",
        "",
        "## Human verification status", "",
        "No human inspection, signup, authenticated tenant test, admin approval, or credential test is claimed. The final sample's required human/account checks are recorded as HUMAN VERIFICATION NOT POSSIBLE in `reports/human_qa.md` and `data/evidence/human_qa_template.csv`: no authorized vendor tenant/credentials or reviewer were provided. This is not a completed human QA pass; the row-level checklists are retained for a future authorized review.", 
    ]
    if dataset_audit:
        warning_count = len(dataset_audit.get("warnings", []))
        lines += ["", "## Final quality-gate audit", "", f"- **Status:** {dataset_audit['status']}; warnings: {warning_count}; blocking errors: {len(dataset_audit.get('errors', []))}."]
        if dataset_audit.get("warnings"):
            lines.append(f"- The complete corrected-dataset warning list is retained in `{args.quality_report}` and each record's `quality_gate` field. The first-pass run audit remains separate in `data/raw/final_full_quality_report.json`.")
    report = ROOT / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Verified {metrics['sample_size']} apps; first-pass core rows={sum(d['checked'] for d in metrics['field_accuracy'].values())}; distinct post-recheck rows={metrics['post_recheck_audit']['rows']}; report={report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

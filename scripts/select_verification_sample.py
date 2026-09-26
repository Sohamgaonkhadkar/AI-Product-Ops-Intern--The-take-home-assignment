#!/usr/bin/env python3
"""Select a deterministic coverage-oriented verification sample.

The selector does not re-research records. Run it only after the full manifest
research dataset and its provenance/quality reconciliation have passed.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.verification.sampling import DEFAULT_SEED, STRATUM_WEIGHTS, record_strata, select_sample, summarize_coverage
from src.utils.validation import validate_manifest


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Select a reproducible 15–20 app sample after full-population research.")
    parser.add_argument("--research", default="data/raw/final_full_research.json")
    parser.add_argument("--target-size", type=int, default=20)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--selection-output", default="data/evidence/verification_sample_selection.json")
    parser.add_argument("--report", default="reports/verification_sample.md")
    args = parser.parse_args()

    records = json.loads((ROOT / args.research).read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "apps/apps.json").read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("Canonical manifest validation failed: " + "; ".join(errors))
    manifest_ids = {r["app_id"] for r in manifest}
    record_ids = [r.get("app_id") for r in records]
    exact_manifest = len(records) == len(manifest) and len(set(record_ids)) == len(record_ids) and set(record_ids) == manifest_ids
    if not exact_manifest:
        raise ValueError("Research dataset must contain exactly one record for every canonical manifest ID before sampling")

    selection = select_sample(records, target_size=args.target_size, seed=args.seed)
    eligible = [r for r in records if r.get("source_mode") in {"LIVE_AGENT", "PRIOR_CAPTURE"} and r.get("research_status") in {"COMPLETE", "PARTIAL"}]
    selected = selection["selected_records"]
    if not (15 <= selection["selected_count"] <= 20):
        raise ValueError(f"Selected sample size {selection['selected_count']} is outside the required 15–20 range")
    coverage = summarize_coverage(selected, eligible, manifest)
    sampled_features = set().union(*(record_strata(record) for record in selected)) if selected else set()
    eligible_features = set().union(*(record_strata(record) for record in eligible)) if eligible else set()
    modes = Counter(r.get("source_mode", "MISSING") for r in records)
    research_statuses = Counter(r.get("research_status", "MISSING") for r in records)
    full_population_researched = (
        exact_manifest
        and len(eligible) == len(manifest)
        and all(r.get("source_mode") in {"LIVE_AGENT", "PRIOR_CAPTURE"} for r in records)
        and all(r.get("research_status") in {"COMPLETE", "PARTIAL"} for r in records)
    )
    if not full_population_researched:
        raise ValueError("Full-population research gate did not pass; do not select or report a representative sample")

    artifact = {
        "created_at": now(),
        "status": "REPRODUCIBLE_COVERAGE_SAMPLE_FROM_FULLY_RESEARCHED_POPULATION",
        "research_dataset": args.research,
        "population_reconciliation": {
            "manifest_count": len(manifest),
            "record_count": len(records),
            "eligible_count": len(eligible),
            "source_mode_counts": dict(sorted(modes.items())),
            "research_status_counts": dict(sorted(research_statuses.items())),
            "full_population_gate": "PASS",
        },
        "selection_method": "Greedy weighted max-coverage over all COMPLETE/PARTIAL records; fixed seed affects deterministic SHA-256 tie-breaks; no replacement. This is a coverage-oriented audit sample, not a probability sample or an estimator of population accuracy.",
        "seed": selection["seed"],
        "target_size": selection["target_size"],
        "eligible_count": selection["eligible_count"],
        "selected_count": selection["selected_count"],
        "selected_ids": selection["selected_ids"],
        "selected_records": [
            {
                "app_id": r["app_id"], "app": r["app"], "category": r["category"],
                "source_mode": r["source_mode"], "research_status": r["research_status"],
                "strata": sorted(record_strata(r)),
            }
            for r in selected
        ],
        "coverage": coverage,
        "observed_strata_count": len(eligible_features),
        "covered_strata_count": len(sampled_features),
        "uncovered_observed_strata": sorted(eligible_features - sampled_features),
        "weights": STRATUM_WEIGHTS,
        "note": "All 100 canonical apps have COMPLETE or PARTIAL research records and are eligible; provenance remains mixed (76 LIVE_AGENT native-web captures and 24 PRIOR_CAPTURE records). The sample must receive an independent fresh-source audit. Selection does not imply human/account verification.",
    }
    out = ROOT / args.selection_output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Verification sample selection", "",
        "**Status: FULL-POPULATION RESEARCH GATE PASSED — reproducible coverage-oriented audit sample selected.**", "",
        f"- **Selection file:** `{args.selection_output}`",
        f"- **Research dataset:** `{args.research}`",
        f"- **Manifest / researched records / eligible:** {len(manifest)} / {len(records)} / {len(eligible)}",
        f"- **Source modes:** {dict(sorted(modes.items()))}",
        f"- **Research statuses:** {dict(sorted(research_statuses.items()))}",
        f"- **Target / selected:** {selection['target_size']} / {selection['selected_count']}",
        f"- **Deterministic seed:** `{selection['seed']}`",
        f"- **Selected IDs (selection order):** {', '.join(map(str, selection['selected_ids']))}",
        "", "## Selection rule", "",
        "The selector greedily maximizes newly covered, research-observed strata using the fixed weights below. If candidates tie, the lower SHA-256 digest of `seed:app_id` wins. Sampling is without replacement and is reproducible from the specified first-pass dataset. This is a purposive coverage sample, not a probability sample; its accuracy will not be generalized statistically to the 100-app population.",
        "", "| Stratum | Weight |", "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {value} |" for key, value in STRATUM_WEIGHTS.items())
    lines += ["", "## Selected apps", "", "| ID | App | Category | Provenance | Research status |", "|---:|---|---|---|---|"]
    lines.extend(f"| {r['app_id']} | {r['app']} | {r['category']} | {r['source_mode']} | {r['research_status']} |" for r in selected)
    lines += [
        "", "## Strata coverage", "",
        f"- **Categories covered:** {coverage['categories']['covered_count']}/{coverage['categories']['manifest_category_count']} manifest categories.",
        f"- **Categories not represented in the selected sample (but observed in research):** {', '.join(coverage['categories']['not_in_sample_but_observed']) or 'none'}.",
        f"- **Observed strata covered:** {len(sampled_features)}/{len(eligible_features)}.",
        f"- **Observed strata omitted:** {', '.join(sorted(eligible_features - sampled_features)) or 'none'}.",
        f"- **Critical MCP/buildability strata not observed anywhere in the researched population:** {', '.join(coverage['strata_not_observed_in_eligible_records']) or 'none'}.",
        "", "## Next steps and limits", "",
        "Independently re-open fresh official sources for each selected app and adjudicate all six critical groups: authentication, self-serve/plan gating, credential access, API, MCP, and buildability. Keep each first-pass value unchanged in the raw dataset; record corrections separately with source evidence and an audit reason. Human account/tenant checks remain pending until an authorized person performs them.",
        "",
        "The full researched population contains both `LIVE_AGENT` native-web captures and `PRIOR_CAPTURE` records. `PRIOR_CAPTURE` is not relabeled as live, and sample selection is not evidence of authenticated vendor access, human review, or public-source re-verification.",
        "",
    ]
    report = ROOT / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Selected {selection['selected_count']} apps from {len(eligible)} researched manifest rows; IDs={selection['selected_ids']}; categories={coverage['categories']['covered_count']}/10; strata={len(sampled_features)}/{len(eligible_features)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

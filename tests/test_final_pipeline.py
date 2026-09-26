import copy
import csv
import hashlib
import json
import re
import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from scripts.run_final_research import build_run_report
from src.utils.quality import validate_final_dataset, validate_record_quality
from src.utils.validation import validate_manifest, validate_record
from src.verification.engine import CORE_GROUPS, get_path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def counter_dict(records, accessor):
    return dict(sorted(Counter(str(accessor(r)) for r in records).items()))


def evidence_for(field, url="https://docs.example.test/reference"):
    return {
        "claim": f"Official documentation supports the {field} claim.",
        "field": field,
        "source_url": url,
        "source_title": "Reference documentation",
        "source_type": "official_docs",
        "accessed_at": "2026-09-24",
        "support": "supports",
        "excerpt_or_observation": "Directly inspected field-specific documentation.",
    }


class MatrixParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.matrix_rows = 0
        self.ids = set()
        self.external_assets = []
        self.sections = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr" and "data-category" in attrs:
            self.matrix_rows += 1
        if tag == "section" and attrs.get("id"):
            self.sections.add(attrs["id"])
        if tag in {"script", "img", "iframe", "link"}:
            src = attrs.get("src") or attrs.get("href")
            if src and (src.startswith("http://") or src.startswith("https://")):
                self.external_assets.append((tag, src))


class FinalManifestAndProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json("apps/apps.json")
        cls.raw = load_json("data/raw/final_full_research.json")
        cls.attempts = load_json("data/raw/final_full_attempts.json")
        cls.raw_quality = load_json("data/raw/final_full_quality_report.json")
        cls.final = load_json("data/verified/final_dataset.json")
        cls.final_quality = load_json("data/verified/final_quality_report.json")
        cls.analysis = load_json("data/analysis/final_analysis.json")
        cls.report = (ROOT / "reports/final_research_run_report.md").read_text(encoding="utf-8")

    def test_exact_manifest_dataset_and_attempt_trace_reconcile(self):
        self.assertEqual(validate_manifest(self.manifest), [])
        expected_ids = set(range(1, 101))
        self.assertEqual({r["app_id"] for r in self.raw}, expected_ids)
        self.assertEqual({r["app_id"] for r in self.final}, expected_ids)
        self.assertEqual(len(self.raw), 100)
        self.assertEqual(len(self.final), 100)
        self.assertEqual(len(self.attempts["traces"]), 100)
        self.assertEqual({t["app_id"] for t in self.attempts["traces"]}, expected_ids)
        self.assertEqual(len({t["app_id"] for t in self.attempts["traces"]}), 100)
        self.assertIn("100/100 traces, exact ID match", self.report)
        self.assertIn("100/100 manifest IDs have a research record", self.report)
        self.assertEqual(self.analysis["scope"]["manifest_reconciles_exactly"], True)

    def test_capture_modes_unknowns_and_missing_credentials_are_explicit(self):
        source_counts = Counter(r["source_mode"] for r in self.raw)
        self.assertEqual(source_counts, {"LIVE_AGENT": 76, "PRIOR_CAPTURE": 24})
        self.assertEqual(self.attempts["mode"], "NATIVE_WEB_CAPTURE_RECONCILIATION")
        self.assertEqual(self.attempts["provider_credentials"], {
            "TAVILY_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL", "OPENAI_API_KEY": "NOT_USED_BY_NATIVE_WEB_TOOL"
        })
        self.assertEqual(Counter(r["research_status"] for r in self.raw), {"COMPLETE": 97, "PARTIAL": 3})
        self.assertEqual(self.analysis["scope"]["source_mode_counts"], {"LIVE_AGENT": 76, "PRIOR_CAPTURE": 24})
        self.assertEqual(self.analysis["scope"]["not_run_count"], 0)
        self.assertEqual(self.analysis["scope"]["live_agent_count"], 76)
        self.assertEqual(self.analysis["scope"]["prior_capture_count"], 24)
        self.assertEqual(sum(len(t.get("capture_failures") or []) for t in self.attempts["traces"]), 7)
        self.assertIn("76 new LIVE_AGENT native-web captures", self.report)
        self.assertIn("Unknown critical-field slots:** 31", self.report)
        self.assertIn("Logged LIVE_AGENT attempts:** 641", self.report)
        self.assertIn("This is not an all-live provider run", self.report)
        self.assertIn("historical PRIOR_CAPTURE per-call attempt counts were not preserved", self.report)

    def test_query_source_counts_and_trace_counts_are_reconciled(self):
        traces = self.attempts["traces"]
        queries = sum(len(t.get("queries") or []) for t in traces)
        sources = [s for t in traces for s in (t.get("sources") or [])]
        unique_urls = {s.get("source_url") or s.get("url") for s in sources if s.get("source_url") or s.get("url")}
        self.assertEqual((queries, len(sources), len(unique_urls)), (236, 468, 467))
        by_mode = {}
        for mode in ("LIVE_AGENT", "PRIOR_CAPTURE"):
            subset = [t for t in traces if t.get("source_mode") == mode]
            mode_sources = [s for t in subset for s in (t.get("sources") or [])]
            mode_urls = {s.get("source_url") or s.get("url") for s in mode_sources if s.get("source_url") or s.get("url")}
            by_mode[mode] = (sum(len(t.get("queries") or []) for t in subset), len(mode_sources), len(mode_urls))
        self.assertEqual(by_mode, {"LIVE_AGENT": (161, 361, 361), "PRIOR_CAPTURE": (75, 107, 107)})
        self.assertIn("Claim-linked evidence rows:** 759", self.report)
        self.assertIn("Queries / source packets:** 236 / 468", self.report)
        self.assertIn("historical PRIOR_CAPTURE per-call attempt counts were not preserved", self.report)
        self.assertEqual(self.attempts["run_started_at"], self.attempts["run_completed_at"])

    def test_all_records_validate_and_raw_corrections_are_separate(self):
        self.assertTrue(all(not validate_record(r) for r in self.raw))
        self.assertTrue(all(not validate_record(r) for r in self.final))
        raw_by_id = {r["app_id"]: r for r in self.raw}
        final_by_id = {r["app_id"]: r for r in self.final}
        self.assertNotIn("Basic", raw_by_id[4]["auth_methods"])
        self.assertIn("Basic", final_by_id[4]["auth_methods"])
        self.assertEqual(raw_by_id[49]["mcp"]["status"], "UNKNOWN")
        self.assertEqual(final_by_id[49]["mcp"]["status"], "AVAILABLE")
        self.assertEqual(raw_by_id[4]["self_serve_status"], "ADMIN_APPROVAL_REQUIRED")
        self.assertEqual(final_by_id[4]["self_serve_status"], "SELF_SERVE_WITH_RESTRICTIONS")
        self.assertEqual(final_by_id[13]["api"]["types"], ["REST"])
        self.assertIn("not a separately documented Webhooks API", final_by_id[13]["api"]["details"])
        self.assertEqual(final_by_id[19]["api"]["types"], ["REST"])
        webhook_audit = load_json("data/evidence/api_webhook_nomenclature_audit.json")
        gorgias_audit = next(row for row in webhook_audit["findings"] if row["app_id"] == 19)
        self.assertIn("not a dedicated Webhooks API", gorgias_audit["conclusion"])
        self.assertEqual(len(gorgias_audit["official_sources"]), 2)
        self.assertIn("Gorgias", webhook_audit["guardrail"])

    def test_dataset_wide_quality_gates_and_run_quality_are_auditable(self):
        raw_copy = copy.deepcopy(self.raw)
        raw_result = validate_final_dataset(raw_copy, self.manifest, self.attempts)
        self.assertEqual(raw_result["status"], "WARN")
        self.assertEqual(raw_result["errors"], [])
        self.assertEqual(raw_result["record_quality_counts"], {"PASS": 72, "WARN": 28, "FAIL": 0})
        self.assertEqual(self.raw_quality["record_quality_counts"], {"PASS": 72, "WARN": 28, "FAIL": 0})
        self.assertEqual(self.raw_quality["traces"], 100)

        self.assertEqual(self.final_quality["status"], "WARN")
        self.assertEqual(self.final_quality["errors"], [])
        self.assertEqual(self.final_quality["record_quality_counts"], {"PASS": 75, "WARN": 25, "FAIL": 0})
        final_record_counts = Counter(r["quality_gate"]["status"] for r in self.final)
        self.assertEqual(final_record_counts, {"PASS": 75, "WARN": 25})
        self.assertEqual(len(self.final_quality["warnings"]), 26)
        self.assertTrue(any("Paygent Connect" in warning or "LOW confidence" in warning for warning in self.final_quality["warnings"]))
        self.assertTrue(all("quality warning" in w for w in self.final_quality["warnings"]))

    def test_csv_artifacts_match_json_manifest_rows(self):
        for rel in ("data/raw/final_full_research.csv", "data/verified/final_dataset.csv"):
            with (ROOT / rel).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 100)
            self.assertEqual({int(r["app_id"]) for r in rows}, set(range(1, 101)))
            self.assertEqual(len({int(r["app_id"]) for r in rows}), 100)


class DatasetQualityRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load_json("data/verified/final_dataset.json")[0]

    def test_complete_record_without_evidence_fails(self):
        record = copy.deepcopy(self.base)
        record["evidence"] = []
        report = validate_record_quality(record)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("COMPLETE record has no evidence" in e for e in report["errors"]))
        self.assertTrue(any("known auth claim has no claim-linked supporting evidence" in e for e in report["errors"]))

    def test_invalid_claim_url_fails_structural_quality(self):
        record = copy.deepcopy(self.base)
        auth_evidence = next(e for e in record["evidence"] if e["field"] == "auth")
        auth_evidence["source_url"] = "not a url"
        report = validate_record_quality(record)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("source_url" in e.lower() or "url" in e.lower() for e in report["errors"]))

    def test_generic_homepage_is_not_accepted_as_specific_claim_evidence(self):
        record = copy.deepcopy(self.base)
        record["evidence"] = [e for e in record["evidence"] if e.get("field") != "auth"]
        record["evidence"].append(evidence_for("auth", "https://example.test/"))
        report = validate_record_quality(record)
        self.assertEqual(report["status"], "WARN")
        self.assertTrue(any("generic homepage is the only supporting source for specific auth claim" in w for w in report["warnings"]))

    def test_logical_contradictions_and_mcp_scope_are_flags_not_silent_fixes(self):
        record = copy.deepcopy(self.base)
        original = copy.deepcopy(record)
        record["api"]["available"] = "NO"
        record["api"]["types"] = ["REST"]
        record["api"]["breadth"] = "BROAD"
        record["buildability"]["verdict"] = "BUILDABLE_NOW"
        record["mcp"]["status"] = "NOT_FOUND"
        record["mcp"]["search_scope"] = "Incomplete targeted search; no comprehensive repository audit."
        report = validate_record_quality(record)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("api.available=NO conflicts with a non-UNKNOWN api.breadth" in e for e in report["errors"]))
        self.assertTrue(any("api.available=NO conflicts with asserted API interface types" in e for e in report["errors"]))
        self.assertTrue(any("BUILDABLE_NOW conflicts with api.available=NO" in e for e in report["errors"]))
        self.assertTrue(any("NOT_FOUND conflicts with an explicitly incomplete/limited search_scope" in e for e in report["errors"]))
        # The gate returns findings; it does not rewrite the original record passed by the caller.
        self.assertEqual(original["api"]["available"], "YES")

    def test_evidence_url_missing_from_trace_is_reported(self):
        record = copy.deepcopy(self.base)
        report = validate_record_quality(record, source_urls=set())
        self.assertTrue(any("claim evidence URL is absent from the recorded source trace" in w for w in report["warnings"]))


class FinalVerificationArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_json("data/raw/final_full_research.json")
        cls.final = load_json("data/verified/final_dataset.json")
        cls.ledger_input = load_json("data/evidence/final_verification_ledger_input.json")
        cls.post = load_json("data/evidence/final_post_recheck.json")
        cls.ledger = load_json("data/verified/final_verification_ledger.json")
        cls.selection = load_json("data/evidence/verification_sample_selection.json")
        cls.report = (ROOT / "reports/final_verification_report.md").read_text(encoding="utf-8")

    def test_reproducible_sample_and_category_gaps(self):
        selected = self.selection["selected_ids"]
        expected_order = [22, 84, 49, 98, 4, 13, 31, 78, 67, 52, 27, 91, 45, 88, 65, 1, 23, 100, 62, 9]
        self.assertEqual(self.selection["status"], "REPRODUCIBLE_COVERAGE_SAMPLE_FROM_FULLY_RESEARCHED_POPULATION")
        self.assertEqual(self.selection["seed"], 20260924)
        self.assertEqual(self.selection["eligible_count"], 100)
        self.assertEqual(self.selection["selected_count"], 20)
        self.assertEqual(selected, expected_order)
        self.assertEqual(len(set(selected)), 20)
        selected_rows = {r["app_id"]: r for r in self.selection["selected_records"]}
        self.assertEqual(set(selected_rows), set(selected))
        self.assertEqual(Counter(selected_rows[i]["source_mode"] for i in selected), {"LIVE_AGENT": 14, "PRIOR_CAPTURE": 6})
        self.assertEqual(len({selected_rows[i]["category"] for i in selected}), 10)
        self.assertEqual(self.selection["observed_strata_count"], 54)
        self.assertEqual(self.selection["covered_strata_count"], 54)
        self.assertEqual(len(self.selection["coverage"]["categories"]["not_observed_in_eligible_records"]), 0)
        self.assertIn("not a probability sample", self.report.lower())

    def test_six_core_checks_match_raw_first_pass_and_recheck_is_distinct(self):
        raw_by_id = {r["app_id"]: r for r in self.raw}
        final_by_id = {r["app_id"]: r for r in self.final}
        checks = self.ledger_input["checks"]
        self.assertEqual(len(checks), 129)
        core = [r for r in checks if r.get("metric_group")]
        supplemental = [r for r in checks if not r.get("metric_group")]
        self.assertEqual(len(core), 120)
        self.assertEqual({r["metric_group"] for r in core}, set(CORE_GROUPS))
        self.assertEqual(len(supplemental), 9)
        self.assertEqual(len(self.ledger["checks"]), 129)
        self.assertEqual(len(self.post["checks"]), 12)
        self.assertEqual(len({(r["app_id"], r["field_path"]) for r in self.post["checks"]}), 12)
        self.assertTrue(all(r["verifier_type"] == "automated_independent" for r in self.post["checks"]))
        self.assertTrue(all(r["audit_id"] == self.post["audit_id"] for r in self.post["checks"]))
        self.assertTrue(all(r["value"] is not None for r in self.post["checks"]))
        self.assertTrue(all(r["independence_level"] == "FRESH_REINSPECTION" for r in self.post["checks"]))
        self.assertTrue(all(r["rechecked_after_corrected_dataset"] for r in self.post["checks"]))
        for row in checks:
            self.assertEqual(get_path(raw_by_id[row["app_id"]], row["field_path"]), row["initial_value"])
        for row in self.ledger["checks"]:
            if row["correctness"] == "INCORRECT" and row.get("apply_correction", True):
                self.assertEqual(get_path(final_by_id[row["app_id"]], row["field_path"]), row["verified_value"])
        post_core = self.ledger["metrics"]["post_correction_overall"]
        post_all = self.ledger["metrics"]["post_recheck_all_rows"]
        self.assertEqual((post_core["correct"], post_core["checked"], post_core["not_rechecked"]), (3, 3, 103))
        self.assertEqual((post_all["correct"], post_all["checked"]), (12, 12))
        self.assertEqual((post_all["critical_rows"], post_all["supplemental_rows"]), (3, 9))
        self.assertIn("Critical-field post-correction concordance:** 3/3", self.report)
        self.assertIn("All changed rows (critical + supplemental):** 12/12", self.report)
        self.assertIn("not rechecked 103", self.report)

    def test_first_pass_accuracy_and_observed_error_examples(self):
        metrics = self.ledger["metrics"]
        expected = {
            "auth": (16, 17, 3),
            "self_serve": (17, 18, 2),
            "credential_access": (18, 18, 2),
            "api_availability": (19, 19, 1),
            "mcp": (15, 16, 4),
            "buildability": (18, 18, 2),
        }
        for field, (correct, checked, unresolved) in expected.items():
            result = metrics["field_accuracy"][field]
            self.assertEqual((result["correct"], result["checked"], result["unresolved"]), (correct, checked, unresolved))
        self.assertEqual(metrics["record_accuracy"], {"correct": 13, "checked": 15, "partial_or_unadjudicable": 5})
        changed_rows = metrics["errors"]
        self.assertEqual(len(changed_rows), 12)
        errors = [row for row in changed_rows if row.get("metric_group")]
        self.assertEqual(len(errors), 3)
        critical_misses = {(r["app_id"], r["field"]) for r in errors}
        self.assertEqual(critical_misses, {
            (49, "mcp.status"), (4, "auth_methods"), (4, "self_serve_status")
        })
        self.assertEqual(sum(not row.get("metric_group") for row in changed_rows), 9)
        for row in changed_rows:
            self.assertTrue(row["reason"])
            self.assertTrue(row["error_type"])
        changed_ledger_rows = [row for row in self.ledger["checks"] if row.get("correctness") == "INCORRECT"]
        self.assertEqual(len(changed_ledger_rows), 12)
        self.assertTrue(all(row["post_recheck"]["independence_level"] == "FRESH_REINSPECTION" for row in changed_ledger_rows))
        report = (ROOT / "reports/final_error_analysis.md").read_text(encoding="utf-8")
        self.assertIn("Amazon Selling Partner", report)
        self.assertIn("Attio", report)
        self.assertIn("Freshdesk", report)
        self.assertIn("Copper", report)
        self.assertNotIn("CORRECT (ALTERNATIVE_SOURCE)", report)


class FinalAnalysisHtmlAndHumanQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json("apps/apps.json")
        cls.records = load_json("data/verified/final_dataset.json")
        cls.analysis = load_json("data/analysis/final_analysis.json")
        cls.selection = load_json("data/evidence/verification_sample_selection.json")
        cls.html = (ROOT / "case-study/index.html").read_text(encoding="utf-8")

    def test_analysis_counts_are_derived_consistently_from_corrected_dataset(self):
        records = self.records
        analysis = self.analysis
        self.assertEqual(analysis["scope"]["manifest_count"], 100)
        self.assertEqual(analysis["scope"]["dataset_record_count"], len(records))
        self.assertTrue(analysis["scope"]["manifest_reconciles_exactly"])
        self.assertEqual(analysis["scope"]["source_mode_counts"], {"LIVE_AGENT": 76, "PRIOR_CAPTURE": 24})
        self.assertEqual(analysis["scope"]["verification_status_counts"], {"AUTO_VERIFIED": 15, "MIXED": 5, "NOT_CHECKED": 80})
        digest = hashlib.sha256((ROOT / "data/verified/final_dataset.json").read_bytes()).hexdigest()
        self.assertEqual(analysis["inputs"]["verified_dataset_sha256"], digest)
        self.assertEqual(len(analysis["category_summary"]), 10)
        self.assertEqual(sum(r["manifest_count"] for r in analysis["category_summary"]), 100)

        cohorts = {
            "manifest_all_100": records,
            "captured_prior_or_live_100": [r for r in records if r["source_mode"] in {"PRIOR_CAPTURE", "LIVE_AGENT"}],
            "selected_sample_20": [r for r in records if r["app_id"] in set(self.selection["selected_ids"])],
            "fully_adjudicated_selected_15": [r for r in records if r["verification_status"] == "AUTO_VERIFIED"],
        }
        accessors = {
            "auth": lambda r: r["auth_status"],
            "self_serve": lambda r: r["self_serve_status"],
            "credential_access": lambda r: r["credential_access"]["status"],
            "api_availability": lambda r: r["api"]["available"],
            "mcp": lambda r: r["mcp"]["status"],
            "buildability": lambda r: r["buildability"]["verdict"],
        }
        for field, accessor in accessors.items():
            for cohort, subset in cohorts.items():
                self.assertEqual(
                    analysis["critical_field_distributions"][field][cohort],
                    counter_dict(subset, accessor),
                    f"distribution mismatch for {field}/{cohort}",
                )

    def test_triage_counts_keep_unknowns_in_needs_review(self):
        triage = self.analysis["easy_win_outreach"]
        all_rows = triage["rows"]
        self.assertEqual(len(all_rows), 100)
        full_counts = Counter(row["triage"] for row in all_rows)
        self.assertEqual(dict(full_counts), {"CONSTRAINED": 13, "NEEDS_REVIEW": 85, "OUTREACH": 2})
        selected_ids = set(self.selection["selected_ids"])
        selected_counts = Counter(row["triage"] for row in all_rows if row["app_id"] in selected_ids)
        self.assertEqual(dict(selected_counts), {"CONSTRAINED": 13, "NEEDS_REVIEW": 5, "OUTREACH": 2})
        self.assertEqual(sum(row["source_mode"] == "NOT_RUN" for row in all_rows), 0)
        self.assertTrue(all(row["triage"] == "NEEDS_REVIEW" for row in all_rows if row["app_id"] not in selected_ids))
        self.assertEqual(triage["selected_20_triage_counts"].get("EASY_WIN", 0), 0)
        self.assertEqual(self.analysis["human_review"]["status"], "HUMAN VERIFICATION NOT POSSIBLE")
        self.assertFalse(self.analysis["human_review"]["human_verification_claimed"])

    def test_human_qa_template_is_explicitly_not_possible_and_unfilled(self):
        with (ROOT / "data/evidence/human_qa_template.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 120)
        self.assertEqual({r["status"] for r in rows}, {"HUMAN VERIFICATION NOT POSSIBLE"})
        self.assertEqual({r["access_available"] for r in rows}, {"NO"})
        self.assertEqual({r["app_id"] for r in rows}, {str(i) for i in self.selection["selected_ids"]})
        by_app = Counter(r["app_id"] for r in rows)
        self.assertTrue(all(count == 6 for count in by_app.values()))
        self.assertEqual({r["field"] for r in rows}, {
            "auth_methods", "self_serve_status", "credential_access.status", "api.available", "mcp.status", "buildability.verdict"
        })
        for row in rows:
            for empty in ("reviewer", "review_date", "human_result", "correction", "review_notes"):
                self.assertEqual(row[empty], "")
            self.assertTrue(row["status_reason"])
            self.assertTrue(row["human_checklist"])
        id84_rows = [r for r in rows if r["app_id"] == "84"]
        self.assertEqual(len(id84_rows), 6)
        for row in id84_rows:
            if row["field"] == "auth_methods":
                self.assertEqual(row["current_verified_value"], "[]")
            else:
                self.assertIn("UNKNOWN", row["current_verified_value"])
            self.assertTrue(row["candidate_identity_context_only_urls"])
        guide = (ROOT / "reports/human_qa.md").read_text(encoding="utf-8")
        self.assertIn("**HUMAN VERIFICATION NOT POSSIBLE.**", guide)
        self.assertIn("no authorized vendor tenant", guide.lower())
        self.assertIn("Reviewer record and boundary", guide)

    def test_html_case_study_is_artifact_derived_offline_and_has_100_rows(self):
        parser = MatrixParser()
        parser.feed(self.html)
        self.assertEqual(parser.matrix_rows, 100)
        self.assertEqual(parser.external_assets, [])
        expected_sections = {
            "overview", "patterns", "categories", "triage", "verification", "errors",
            "architecture", "provenance", "matrix", "limitations", "reproduce"
        }
        self.assertTrue(expected_sections.issubset(parser.sections))
        self.assertIn("BASELINE ASSEMBLED · RELEASE BLOCKED", self.html)
        self.assertIn("<strong>12/12</strong>", self.html)
        self.assertIn("All changed rows concordant", self.html)
        self.assertIn("HUMAN VERIFICATION NOT POSSIBLE", self.html)
        self.assertIn("Gorgias:</strong> a separate terminology audit", self.html)
        self.assertIn("Neither observation establishes a dedicated Webhooks API", self.html)
        self.assertIn("29/30", self.html)
        self.assertIn("30/30", self.html)
        self.assertIn("class=\"id-pills\"", self.html)
        self.assertNotIn("`UNKNOWN`", self.html)
        self.assertIn(".audit-stat-grid{{grid-template-columns:1fr}}", (ROOT / "scripts/render_final_case_study.py").read_text(encoding="utf-8"))
        self.assertIn("103 other adjudicable critical", self.html)
        self.assertNotIn("76 NOT_RUN", self.html)
        self.assertNotIn("24 captured prior/live rows", self.html)
        self.assertNotRegex(self.html, r"<link[^>]+rel=[\"']stylesheet")
        self.assertNotRegex(self.html, r"<script[^>]+src=")
        self.assertNotIn("@import", self.html)
        self.assertNotRegex(self.html, r"url\([\"']?https?://")
        self.assertIn("data/analysis/final_analysis.json", (ROOT / "scripts/render_final_case_study.py").read_text(encoding="utf-8"))
        self.assertIn("data/verified/final_dataset.json", (ROOT / "scripts/render_final_case_study.py").read_text(encoding="utf-8"))

    def test_documentation_and_required_artifacts_exist(self):
        expected = [
            "reports/final_research_run_report.md",
            "reports/final_verification_report.md",
            "reports/final_analysis.md",
            "reports/final_error_analysis.md",
            "reports/human_qa.md",
            "reports/final_audit.md",
            "data/verified/final_quality_report.json",
            "data/analysis/category_summary.csv",
            "data/analysis/verified_sample_triage.csv",
            "data/evidence/api_webhook_nomenclature_audit.json",
            "case-study/index.html",
            "case-study/human_qa.md",
            "case-study/human_qa_template.csv",
            ".env.example",
            "netlify.toml",
        ]
        for rel in expected:
            self.assertTrue((ROOT / rel).is_file(), rel)
        self.assertIn("INCOMPLETE", (ROOT / "README.md").read_text(encoding="utf-8"))
        final_audit = (ROOT / "reports/final_audit.md").read_text(encoding="utf-8")
        self.assertIn("29 tests passed", final_audit)
        self.assertIn("No repository or deployment URL is claimed", final_audit)
        self.assertIn("HUMAN VERIFICATION NOT POSSIBLE", (ROOT / "case-study/human_qa.md").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / ".env.example").is_file())
        self.assertTrue((ROOT / "netlify.toml").is_file())
        research_method = (ROOT / "docs/research_methodology.md").read_text(encoding="utf-8")
        self.assertIn("separate Gorgias terminology audit", research_method)
        self.assertIn("data/evidence/api_webhook_nomenclature_audit.json", research_method)
        verification_method = (ROOT / "docs/verification_methodology.md").read_text(encoding="utf-8")
        self.assertIn("22, 84, 49, 98", verification_method)
        self.assertIn("not a probability sample", verification_method)
        self.assertIn("INCOMPLETE", (ROOT / "docs/architecture.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

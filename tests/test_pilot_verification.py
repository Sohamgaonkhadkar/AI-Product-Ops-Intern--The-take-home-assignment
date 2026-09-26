import copy
import json
import unittest
from pathlib import Path

from src.utils.validation import validate_manifest, validate_record
from src.verification.engine import get_path, process_verification, _validate_post_rechecks

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class PilotVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json("apps/apps.json")
        cls.raw = load_json("data/raw/pilot_results.json")
        cls.ledger_obj = load_json("data/evidence/verification_ledger_input.json")
        cls.post_obj = load_json("data/evidence/pilot_post_recheck.json")
        cls.final = load_json("data/verified/pilot_final_dataset.json")

    def test_exact_manifest_and_pilot_reconcile(self):
        self.assertEqual(validate_manifest(self.manifest), [])
        ids = {a["app_id"] for a in self.manifest}
        self.assertEqual({r["app_id"] for r in self.raw}, {1, 22, 49, 61, 92})
        self.assertTrue({r["app_id"] for r in self.raw}.issubset(ids))

    def test_all_ledger_initial_values_exactly_match_unchanged_raw(self):
        raw_by_id = {r["app_id"]: r for r in self.raw}
        checks = self.ledger_obj["checks"]
        self.assertEqual(len(checks), 45)
        for row in checks:
            self.assertEqual(
                get_path(raw_by_id[row["app_id"]], row["field_path"]),
                row["initial_value"],
                f"initial value mismatch for {row['app_id']}.{row['field_path']}",
            )

    def test_raw_and_corrected_records_validate(self):
        self.assertTrue(all(not validate_record(r) for r in self.raw))
        self.assertTrue(all(not validate_record(r) for r in self.final))
        self.assertTrue(all(r["verification_status"] == "AUTO_VERIFIED" for r in self.final))
        self.assertTrue(all(r["verification_status"] != "HUMAN_VERIFIED" for r in self.final))

    def test_pilot_accuracy_is_computed_from_initial_values(self):
        records, ledger, metrics = process_verification(
            self.raw,
            self.ledger_obj["checks"],
            self.post_obj["checks"],
        )
        self.assertEqual(metrics["sample_size"], 5)
        self.assertEqual(sum(x["checked"] for x in metrics["field_accuracy"].values()), 30)
        self.assertEqual(sum(x["correct"] for x in metrics["field_accuracy"].values()), 29)
        self.assertEqual(metrics["field_accuracy"]["mcp"]["correct"], 4)
        self.assertEqual(metrics["record_accuracy"], {"correct": 4, "checked": 5, "partial_or_unadjudicable": 0})
        self.assertEqual(metrics["post_correction_overall"], {
            "correct": 30, "checked": 30, "incorrect": 0, "conflicts": 0, "unresolved": 0, "not_rechecked": 0
        })
        self.assertEqual(len(metrics["errors"]), 16)  # 1 critical + 15 supplemental changes
        corrected = {r["app_id"]: r for r in records}
        self.assertEqual(corrected[49]["mcp"]["status"], "AVAILABLE")
        self.assertIn("not supported products", corrected[49]["mcp"]["details"])
        self.assertEqual(corrected[61]["api"]["types"], ["REST", "GraphQL", "Webhooks"])
        raw_salesforce = next(r for r in self.raw if r["app_id"] == 1)
        self.assertNotIn("Flex Credits", raw_salesforce["mcp"]["details"])
        self.assertNotIn("Flex Credits", raw_salesforce["buildability"]["blocker"])
        self.assertIn("intended only for customers with Flex Credits", corrected[1]["mcp"]["details"])
        self.assertIn("not proof of a separate technical or credential requirement", corrected[1]["mcp"]["details"])
        self.assertIn("intended only for customers with Flex Credits", corrected[1]["buildability"]["blocker"])
        current_sf_rechecks = [
            r for r in self.post_obj["checks"]
            if r["app_id"] == 1 and r["field_path"] in {"mcp.status", "buildability.verdict"}
        ]
        self.assertNotIn("requires org setup and Flex Credits", json.dumps(current_sf_rechecks, ensure_ascii=False))
        self.assertTrue(any(
            a.get("app_id") == 1 and "requires org setup and Flex Credits" in json.dumps(a.get("prior_observations", {}), ensure_ascii=False)
            for a in self.post_obj["amendments"]
        ))
        self.assertIn("custom MCP setup", corrected[92]["credential_access"]["plan_or_gate"])
        self.assertIn("separate Enterprise Public API", corrected[92]["credential_access"]["plan_or_gate"])
        amazon_post = next(r for r in self.post_obj["checks"] if r["app_id"] == 49 and r["field_path"] == "mcp.status")
        self.assertEqual(amazon_post["value"], "AVAILABLE")
        self.assertEqual(len(ledger), 45)

    def test_post_recheck_requires_explicit_value_and_separate_source(self):
        broken = copy.deepcopy(self.post_obj["checks"][0])
        broken.pop("value")
        with self.assertRaisesRegex(ValueError, "explicit observed value"):
            _validate_post_rechecks([broken])

        raw_row = next(r for r in self.raw if r["app_id"] == broken["app_id"])
        verify_row = next(
            r for r in self.ledger_obj["checks"]
            if r["app_id"] == broken["app_id"] and r["field_path"] == broken["field_path"]
        )
        same_url = copy.deepcopy(self.post_obj["checks"][0])
        same_url["source"]["source_url"] = verify_row["source"]["source_url"]
        same_url["independence_level"] = "ALTERNATIVE_SOURCE"
        with self.assertRaisesRegex(ValueError, "reused primary URL"):
            process_verification(self.raw, self.ledger_obj["checks"], [same_url])

    def test_post_recheck_is_a_separate_capture_not_in_ledger_input(self):
        self.assertTrue(all("post_recheck" not in row for row in self.ledger_obj["checks"]))
        self.assertEqual(len(self.post_obj["checks"]), 30)
        self.assertEqual(len({(r["app_id"], r["field_path"]) for r in self.post_obj["checks"]}), 30)
        self.assertEqual({r["verifier_type"] for r in self.post_obj["checks"]}, {"automated_independent"})
        self.assertTrue(all(r["audit_id"] == self.post_obj["audit_id"] for r in self.post_obj["checks"]))


if __name__ == "__main__":
    unittest.main()

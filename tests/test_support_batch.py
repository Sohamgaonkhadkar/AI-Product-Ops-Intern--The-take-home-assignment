import json
import unittest
from pathlib import Path

from src.utils.validation import validate_manifest, validate_record

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class SupportBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json("apps/apps.json")
        cls.capture = load_json("data/evidence/support_batch_11_capture.json")
        cls.raw = load_json("data/raw/support_batch_11_results.json")
        cls.attempts = load_json("data/raw/support_batch_11_attempts.json")

    def test_exact_manifest_and_batch_reconcile(self):
        self.assertEqual(validate_manifest(self.manifest), [])
        expected = set(range(11, 21))
        self.assertEqual({r["app_id"] for r in self.capture["records"]}, expected)
        self.assertEqual({r["app_id"] for r in self.raw}, expected)
        manifest_by_id = {r["app_id"]: r for r in self.manifest}
        self.assertEqual(len(self.capture["records"]), 10)
        for record in self.capture["records"]:
            app = manifest_by_id[record["app_id"]]
            self.assertEqual(record["app"], app["app"])
            self.assertEqual(record["category"], app["category"])
            self.assertEqual(record["website_hint"], app["website_hint"])

    def test_every_capture_and_replay_record_validates_and_is_unverified(self):
        self.assertTrue(all(not validate_record(r) for r in self.capture["records"]))
        self.assertTrue(all(not validate_record(r) for r in self.raw))
        self.assertTrue(all(r["research_status"] == "COMPLETE" for r in self.raw))
        self.assertTrue(all(r["verification_status"] == "NOT_CHECKED" for r in self.raw))
        self.assertEqual(self.raw, sorted(self.raw, key=lambda r: r["app_id"]))
        self.assertEqual(self.raw, self.capture["records"])

    def test_claim_evidence_and_traces_are_present(self):
        self.assertEqual({t["app_id"] for t in self.capture["traces"]}, set(range(11, 21)))
        self.assertEqual({t["app_id"] for t in self.attempts["traces"]}, set(range(11, 21)))
        for record in self.raw:
            fields = {item["field"] for item in record["evidence"]}
            self.assertTrue({"auth", "self_serve", "credential_access", "api", "mcp", "buildability"}.issubset(fields))
            self.assertTrue(all(item["source_url"].startswith("https://") for item in record["evidence"]))
            self.assertTrue(all(item["accessed_at"] == self.capture["capture_date"] for item in record["evidence"]))

    def test_known_unknowns_and_redirects_are_preserved(self):
        by_id = {r["app_id"]: r for r in self.raw}
        unknown_slots = sum(
            r["mcp"]["status"] == "UNKNOWN" or r["self_serve_status"] == "UNKNOWN"
            for r in self.raw
        )
        self.assertEqual(unknown_slots, 3)
        self.assertEqual(by_id[11]["mcp"]["status"], "UNKNOWN")  # Zendesk: bounded search, not a negative.
        self.assertEqual(by_id[15]["self_serve_status"], "UNKNOWN")  # Pylon pricing route redirected.
        self.assertEqual(by_id[20]["mcp"]["status"], "UNKNOWN")  # Gladly MCP search incomplete.
        pylon = next(t for t in self.capture["traces"] if t["app_id"] == 15)
        self.assertTrue(any(f.get("final_url") == "https://www.usepylon.com/schedule-demo" for f in pylon["failures"]))
        gladly = by_id[20]
        self.assertTrue(any(c["field"] == "description" for c in gladly["source_conflicts"]))
        self.assertIn("API-specific", gladly["self_serve_details"])
        self.assertIn("open beta", by_id[19]["mcp"]["details"])
        self.assertIn("YOUR-SUBDOMAIN", by_id[19]["mcp"]["details"])


if __name__ == "__main__":
    unittest.main()

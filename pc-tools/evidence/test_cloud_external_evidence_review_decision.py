import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULE_PATH = ROOT / "cloud_external_evidence_review_decision.py"
FIXTURE_ROOT = ROOT / "fixtures" / "cloud_external_evidence_review_decision"

spec = importlib.util.spec_from_file_location("cloud_external_evidence_review_decision", MODULE_PATH)
review = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(review)


class CloudExternalEvidenceReviewDecisionTest(unittest.TestCase):
    def build(self, fixture_name, expected_ref="external_evidence_ref_20260524_0001"):
        # 测试只读 fixture，不调用公网、云端、Robot 或手机控制路径。
        path = FIXTURE_ROOT / fixture_name
        artifact, summary, exit_code = review.build_review_decision(str(path), expected_ref)
        return artifact, summary, exit_code

    def assert_safe_contract(self, payload):
        # 输出必须是 phone-safe / support-safe，不能携带 raw endpoint、凭证、路径或控制授权。
        text = json.dumps(payload, ensure_ascii=False).lower()
        for forbidden in (
            "authorization",
            "bearer",
            "token",
            "oss ak",
            "oss sk",
            "access_key",
            "secret",
            "credential",
            "database url",
            "db url",
            "queue url",
            "postgres://",
            "https://",
            "/users/",
            "/private/",
            "/tmp/",
            "/ws/",
            "traceback",
            "raw artifact",
            "raw diagnostics",
            "raw pr payload",
            "github mutation",
            "checksum",
            "delivery_success\": true",
            "primary_actions_enabled\": true",
            "safe_to_control\": true",
        ):
            self.assertNotIn(forbidden, text)

    def test_accepts_complete_safe_intake_but_keeps_not_proven(self):
        artifact, summary, exit_code = self.build("accepted_intake.json")

        # accepted 只表示 review-decision 接受脱敏材料，不代表 O5 外部真实证明。
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], review.ACCEPTED)
        self.assertEqual(summary["review_decision"], review.ACCEPTED)
        self.assertEqual(summary["source_capability"], "trashbot.external_evidence_intake")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(summary["safe_to_control"], False)
        self.assertIn("not true phone/browser proof", summary["safe_phone_copy"])
        self.assertIn("no OKR percentage lift", summary["safe_phone_copy"])
        self.assert_safe_contract(artifact)

    def test_backfill_state_lists_missing_external_material_families(self):
        artifact, summary, exit_code = self.build("needs_backfill_intake.json")

        # 缺 worker/true phone/terminal result 时必须进入 backfill，不能说 accepted。
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], review.NEEDS_BACKFILL)
        self.assertEqual(summary["review_decision"], review.NEEDS_BACKFILL)
        self.assertIn("worker_cutover", summary["missing_materials"])
        self.assertIn("true_phone_browser_proof", summary["missing_materials"])
        self.assertIn("verified_terminal_result", summary["missing_materials"])
        self.assert_safe_contract(artifact)

    def test_unsafe_intake_is_rejected_without_echoing_secret_material(self):
        artifact, summary, exit_code = self.build("unsafe_intake.json")

        # raw endpoint / credential-bearing 文本只影响状态，不进入输出 safe fields。
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], review.REJECTED_UNSAFE)
        self.assertEqual(summary["review_decision"], review.REJECTED_UNSAFE)
        self.assert_safe_contract(artifact)

    def test_expected_evidence_ref_mismatch_is_deterministic(self):
        artifact, summary, exit_code = self.build("mismatch_intake.json", "expected_external_evidence_ref")

        # evidence_ref 不一致时优先阻断，避免跨材料链误收口。
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], review.REF_MISMATCH)
        self.assertEqual(summary["review_decision"], review.REF_MISMATCH)
        self.assert_safe_contract(artifact)

    def test_missing_intake_is_blocked_missing(self):
        artifact, summary, exit_code = review.build_review_decision("", "external_evidence_ref_20260524_0001")

        # 缺 intake 是正常 blocked 状态，不抛异常也不生成伪 accepted。
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], review.BLOCKED_MISSING)
        self.assertEqual(summary["review_decision"], review.BLOCKED_MISSING)
        self.assertIn("generate_trashbot.external_evidence_intake", summary["next_required_evidence"][0])
        self.assert_safe_contract(artifact)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""mobile field material retest request gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import mobile_field_material_retest_request as request  # noqa: E402


class MobileFieldMaterialRetestRequestTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、真实路线、硬件或云。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def review_payload(self, evidence_ref: str) -> dict:
        # ready 样本模拟上一轮 review 白名单输出，仍不是 route/elevator 或送达成功证据。
        return {
            "schema": "trashbot.mobile_field_material_review_decision.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_mobile_field_material_review_decision_gate",
            "review_decision": "ready_for_owner_handoff_not_proven",
            "status": "ready_for_owner_handoff_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_handoff": "Product closeout",
            "blocked_materials": [],
            "next_required_evidence": [
                "Product closeout reviews mobile_field_material_review_decision.",
                "Keep delivery_success=false and primary_actions_enabled=false.",
            ],
            "next-required-evidence": [
                "Product closeout reviews mobile_field_material_review_decision.",
                "Keep delivery_success=false and primary_actions_enabled=false.",
            ],
            "review_summary": {
                "schema": "trashbot.mobile_field_material_review_decision_summary.v1",
                "schema_version": 1,
                "source": "software_proof",
                "evidence_boundary": "software_proof_docker_mobile_field_material_review_decision_gate",
                "status": "ready_for_owner_handoff_not_proven",
                "review_decision": "ready_for_owner_handoff_not_proven",
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "owner_handoff": "Product closeout",
                "blocked_materials": [],
                "next_required_evidence": [
                    "Product closeout reviews mobile_field_material_review_decision.",
                ],
                "next-required-evidence": [
                    "Product closeout reviews mobile_field_material_review_decision.",
                ],
                "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_with_payload(self, root: Path, payload: dict) -> tuple[dict, dict, int]:
        # 公共 helper 让测试聚焦 request contract，而非文件读写样板。
        review_path = self.write_json(root, "review.json", payload)
        return request.build_retest_request(str(review_path))

    def test_ready_review_becomes_route_elevator_retest_request_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary, exit_code = self.build_with_payload(
                root,
                self.review_payload(str(root / "same-evidence-ref.json")),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.mobile_field_material_retest_request.v1")
        self.assertEqual(summary["schema"], "trashbot.mobile_field_material_retest_request_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_mobile_field_material_retest_request_gate",
        )
        self.assertEqual(
            artifact["request_verdict"],
            "ready_for_route_elevator_field_retest_request_not_proven",
        )
        self.assertEqual(artifact["evidence_ref"], "file:same-evidence-ref.json")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertIn("route/elevator material checklist", artifact)
        self.assertEqual(len(artifact["route_elevator_material_checklist"]), len(request.RETEST_MATERIALS))
        self.assertIn("next_required_evidence", artifact)
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_review_summary_input_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary, exit_code = self.build_with_payload(root, self.review_payload("summary-run")["review_summary"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            artifact["request_verdict"],
            "ready_for_route_elevator_field_retest_request_not_proven",
        )
        self.assertEqual(artifact["source_review"]["schema_status"], "supported")
        self.assertEqual(summary["evidence_ref"], "summary-run")

    def test_blocked_review_stays_blocked_and_carries_next_required_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-blocked")
            payload["review_decision"] = "blocked_missing_nav2_or_fixed_route_runtime_log"
            payload["review_summary"]["review_decision"] = "blocked_missing_nav2_or_fixed_route_runtime_log"
            payload["review_summary"]["status"] = "blocked_missing_nav2_or_fixed_route_runtime_log"
            payload["blocked_materials"] = [
                {
                    "name": "nav2_fixed_route_runtime_log",
                    "status": "missing_or_unreadable",
                    "owner": "Autonomy",
                    "reason": "runtime log missing",
                }
            ]
            payload["next_required_evidence"] = ["Collect Nav2 or fixed-route runtime log under evidence_ref=run-blocked."]
            payload["review_summary"]["next_required_evidence"] = [
                "Collect Nav2 or fixed-route runtime log under evidence_ref=run-blocked."
            ]
            artifact, _summary, exit_code = self.build_with_payload(root, payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["request_verdict"], "blocked_mobile_field_material_review_not_ready")
        self.assertIn("Collect Nav2", " ".join(artifact["next_required_evidence"]))
        self.assertIn("nav2_fixed_route_runtime_log", json.dumps(artifact["route_elevator_material_checklist"]))
        self.assertFalse(artifact["delivery_success"])

    def test_missing_bad_unsupported_or_weak_same_ref_review_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, _, missing_exit = request.build_retest_request(str(root / "missing.json"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _, bad_exit = request.build_retest_request(str(bad_path))
            unsupported = self.review_payload("run-unsupported")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _, unsupported_exit = self.build_with_payload(root, unsupported)
            weak_same_ref = self.review_payload("run-weak")
            weak_same_ref["same_evidence_ref_required"] = "false"
            weak_same_ref["review_summary"]["same_evidence_ref_required"] = "false"
            weak_artifact, _, weak_exit = self.build_with_payload(root, weak_same_ref)

        self.assertEqual(missing_exit, 2)
        self.assertEqual(bad_exit, 2)
        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(weak_exit, 2)
        self.assertEqual(missing_artifact["request_verdict"], "blocked_invalid_mobile_field_material_review")
        self.assertEqual(bad_artifact["request_verdict"], "blocked_invalid_mobile_field_material_review")
        self.assertEqual(unsupported_artifact["request_verdict"], "blocked_invalid_mobile_field_material_review")
        self.assertEqual(weak_artifact["source_review"]["schema_status"], "unsupported")
        self.assertFalse(weak_artifact["delivery_success"])

    def test_success_or_primary_action_claim_blocks_request(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-success")
            payload["review_summary"]["primary_actions_enabled"] = True
            payload["next_required_evidence"].append("delivery completed after route/elevator field pass")
            artifact, summary, exit_code = self.build_with_payload(root, payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["request_verdict"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])

    def test_unsafe_review_text_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-unsafe")
            payload["next_required_evidence"].append(
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            artifact, _summary, exit_code = self.build_with_payload(root, payload)

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["request_verdict"], "blocked_unsafe_copy")
        self.assertNotIn("Authorization", encoded)
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)


if __name__ == "__main__":
    unittest.main()

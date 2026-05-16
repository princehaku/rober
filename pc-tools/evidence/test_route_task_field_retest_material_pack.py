#!/usr/bin/env python3
"""route_task_field_retest_material_pack 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_material_pack as pack  # noqa: E402


class RouteTaskFieldRetestMaterialPackTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, evidence_ref: str = "ev-001", **extra: object) -> None:
        # 测试 fixture 只写脱敏元数据，保持 software proof 边界。
        payload = {
            "schema": f"fixture.{name}.v1",
            "evidence_ref": evidence_ref,
            "status": "provided",
            "observer_note": f"{name} collected for terminal review",
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        (root / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")

    def _complete_material_dir(self, root: Path, evidence_ref: str = "ev-001") -> None:
        # 八类材料文件名与 CLI 白名单对齐，避免测试靠任意文件发现通过。
        for name in pack.REQUIRED_MATERIALS:
            self._write_json(root, name, evidence_ref=evidence_ref)

    def test_complete_pack_is_ready_not_proven_and_safe_for_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._complete_material_dir(root, evidence_ref="ev-001")

            artifact, summary, exit_code = pack.build_route_task_field_retest_material_pack(str(root), "ev-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_material_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_material_pack_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_material_pack_gate",
        )
        self.assertEqual(artifact["material_pack_verdict"], "ready_for_field_retest_material_pack_not_proven")
        self.assertEqual(summary["material_completeness"]["accepted_count"], 8)
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("trashbot.route_task_field_retest_result_intake.v1", artifact["result_intake_hint"]["schema"])

    def test_missing_and_placeholder_materials_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._complete_material_dir(root, evidence_ref="ev-002")
            (root / "delivery_result.json").unlink()
            self._write_json(root, "human_assistance_note", evidence_ref="ev-002", status="placeholder")

            artifact, summary, _exit_code = pack.build_route_task_field_retest_material_pack(str(root), "ev-002")

        self.assertEqual(artifact["material_pack_verdict"], "blocked_missing_materials")
        self.assertIn("delivery_result", summary["missing_materials"])
        self.assertEqual(summary["rejected_materials"]["human_assistance_note"], ["placeholder_only"])
        self.assertFalse(summary["safe_copy"]["delivery_success"])

    def test_evidence_ref_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._complete_material_dir(root, evidence_ref="ev-003")
            self._write_json(root, "door_state", evidence_ref="other-ref")

            artifact, summary, _exit_code = pack.build_route_task_field_retest_material_pack(str(root), "ev-003")

        self.assertEqual(artifact["material_pack_verdict"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(summary["rejected_materials"]["door_state"], ["evidence_ref_mismatch"])

    def test_raw_path_credential_success_and_action_claims_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._complete_material_dir(root, evidence_ref="ev-004")
            self._write_json(root, "task_record", evidence_ref="ev-004", observer_note="raw file /Users/m4/secret.log")
            self._write_json(root, "delivery_result", evidence_ref="ev-004", delivery_success=True)

            artifact, summary, _exit_code = pack.build_route_task_field_retest_material_pack(str(root), "ev-004")

        self.assertEqual(artifact["material_pack_verdict"], "blocked_unsafe_material_copy")
        self.assertIn("raw_path_copy", summary["rejected_materials"]["task_record"])
        self.assertIn("success_or_control_claim", summary["rejected_materials"]["delivery_result"])
        encoded_summary = json.dumps(summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_missing_directory_keeps_all_materials_missing(self) -> None:
        artifact, summary, _exit_code = pack.build_route_task_field_retest_material_pack(
            "/tmp/route_task_field_retest_material_pack_missing_dir", "ev-005"
        )

        self.assertEqual(artifact["material_pack_verdict"], "blocked_missing_material_dir")
        self.assertEqual(len(summary["missing_materials"]), 8)
        self.assertEqual(summary["safe_copy"]["primary_actions_enabled"], False)


if __name__ == "__main__":
    unittest.main()

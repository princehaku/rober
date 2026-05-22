#!/usr/bin/env python3
"""reviewer ACK intake gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规包；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_material_resolution_owner_response_review_handoff as handoff_gate  # noqa: E402
import field_evidence_material_resolution_reviewer_ack_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe handoff，不模拟 raw 现场材料。
# 测试约束 02：acknowledged 只表示 reviewer 已接收，不代表 PR resolved。
# 测试约束 03：needs_reassignment 只表达 owner 路由变化，不触发控制。
# 测试约束 04：缺 handoff/source 必须 blocked_missing_handoff。
# 测试约束 05：unsafe success/control/hardware/PR-resolution copy 必须 rejected。
# 测试约束 06：Robot diagnostics safe alias 必须可消费。
# 测试约束 07：输出保持 source=software_proof 与 not_proven。
# 测试约束 08：输出保持 delivery_success=false。
# 测试约束 09：输出保持 primary_actions_enabled=false。
# 测试约束 10：输出保持 safe_to_control=false。
# 测试约束 11：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。


class FieldEvidenceMaterialResolutionReviewerAckIntakeTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _handoff_summary(
        self,
        evidence_ref: str,
        handoff_status: str = handoff_gate.HANDOFF_READY,
    ) -> dict[str, object]:
        # source 使用上一轮 owner-response review-handoff summary 的安全消费面。
        return {
            "schema": handoff_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": handoff_gate.CAPABILITY,
            "handoff_status": handoff_status,
            "field_evidence_material_resolution_owner_response_review_handoff": handoff_status,
            "evidence_boundary": handoff_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "next_required_evidence": ["reviewer/support/field owner ACK must stay sanitized"],
            "not_proven": ["not_proven"],
            "not_proven_items": ["real_reviewer_resolution"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": (
                f"{handoff_gate.CAPABILITY}: handoff_status={handoff_status}; evidence_ref={evidence_ref}; "
                "source=software_proof; not_proven; delivery_success=false; "
                "primary_actions_enabled=false; safe_to_control=false."
            ),
        }

    def _ack_packet(self, evidence_ref: str, ack_state: str = gate.ACK_ACKNOWLEDGED, unsafe: bool = False) -> dict[str, object]:
        # ACK packet 是 reviewer-safe 表单，不包含真实 runtime log 或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_material_resolution_reviewer_ack_packet.v1",
            "source": "software_proof",
            "status": "not_proven",
            "reviewer_ack_state": ack_state,
            "ack_owner": "reviewer",
            "acknowledged_at": "2026-05-22T16:20:00Z",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "ack_reasons": ["safe ACK material received for later review"],
            "reassignment_target": "field-owner-b",
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "not_proven": True,
        }
        if unsafe:
            payload["safe_note"] = "delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved"
        return payload

    def _build(
        self,
        root: Path,
        handoff_payload: dict[str, object],
        ack_payload: dict[str, object],
        evidence_ref: str,
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦四态映射和安全边界。
        handoff_path = self._write_json(root, "handoff.json", handoff_payload)
        ack_path = self._write_json(root, "ack.json", ack_payload)
        return gate.build_field_evidence_material_resolution_reviewer_ack_intake(
            str(handoff_path),
            str(ack_path),
            evidence_ref,
        )

    def test_acknowledged_packet_maps_to_canonical_ack_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-901"),
                self._ack_packet("reviewer-ack-901"),
                "reviewer-ack-901",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_ACKNOWLEDGED)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(summary["reviewer_acknowledgement"]["reviewer_ack_state"], gate.ACK_ACKNOWLEDGED)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_needs_reassignment_is_supported_without_control_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-902"),
                self._ack_packet("reviewer-ack-902", gate.ACK_NEEDS_REASSIGNMENT),
                "reviewer-ack-902",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_NEEDS_REASSIGNMENT)
        self.assertIn("route sanitized handoff", summary["next_required_evidence"][0])
        self.assertEqual(summary["reviewer_acknowledgement"]["reassignment_target"], "field-owner-b")
        self.assertFalse(summary["safe_to_control"])

    def test_missing_handoff_or_ack_maps_to_blocked_missing_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ack_path = self._write_json(root, "ack.json", self._ack_packet("reviewer-ack-903"))
            missing, missing_summary, missing_exit = gate.build_field_evidence_material_resolution_reviewer_ack_intake(
                str(root / "missing-handoff.json"),
                str(ack_path),
                "reviewer-ack-903",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write_json(root, "handoff.json", self._handoff_summary("reviewer-ack-904"))
            no_ack, _, no_ack_exit = gate.build_field_evidence_material_resolution_reviewer_ack_intake(
                str(handoff_path),
                str(root / "missing-ack.json"),
                "reviewer-ack-904",
            )

        self.assertEqual(missing_exit, 2)
        self.assertEqual(no_ack_exit, 2)
        self.assertEqual(missing["reviewer_ack_state"], gate.ACK_BLOCKED_MISSING_HANDOFF)
        self.assertEqual(no_ack["reviewer_ack_state"], gate.ACK_BLOCKED_MISSING_HANDOFF)
        self.assertIn("handoff_json_missing", missing["ack_reasons"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_unsafe_ack_and_evidence_ref_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unsafe, unsafe_summary, unsafe_exit = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-905"),
                self._ack_packet("reviewer-ack-905", unsafe=True),
                "reviewer-ack-905",
            )
        with tempfile.TemporaryDirectory() as tmp:
            mismatch, _, mismatch_exit = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-906"),
                self._ack_packet("other-ref"),
                "reviewer-ack-906",
            )

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(unsafe["reviewer_ack_state"], gate.ACK_REJECTED_UNSAFE)
        self.assertEqual(mismatch["reviewer_ack_state"], gate.ACK_BLOCKED_MISSING_HANDOFF)
        self.assertIn("delivery_success=false", encoded)
        self.assertNotIn("delivery_success=true", encoded)
        self.assertFalse(unsafe_summary["proof_flags"]["delivery_success"])

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {handoff_gate.ROBOT_ALIAS: self._handoff_summary("reviewer-ack-907")}
            artifact, summary, exit_code = self._build(
                Path(tmp),
                payload,
                self._ack_packet("reviewer-ack-907"),
                "reviewer-ack-907",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_ACKNOWLEDGED)
        self.assertEqual(artifact["safe_evidence_ref"], "reviewer-ack-907")
        self.assertEqual(summary["source_schema"], handoff_gate.SUMMARY_SCHEMA)

    def test_cli_prints_acknowledged_for_safe_ack_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write_json(root, "handoff.json", self._handoff_summary("reviewer-ack-908"))
            ack_path = self._write_json(root, "ack.json", self._ack_packet("reviewer-ack-908"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_material_resolution_reviewer_ack_intake.py"),
                    "--handoff-json",
                    str(handoff_path),
                    "--reviewer-ack-json",
                    str(ack_path),
                    "--evidence-ref",
                    "reviewer-ack-908",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.ACK_ACKNOWLEDGED, result.stdout)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate", result.stdout)

    def test_output_preserves_required_boundary_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _ = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-909"),
                self._ack_packet("reviewer-ack-909"),
                "reviewer-ack-909",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_material_resolution_reviewer_ack_intake", encoded)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate", encoded)
        self.assertIn(gate.ACK_ACKNOWLEDGED, encoded)
        self.assertIn(gate.ACK_NEEDS_REASSIGNMENT, encoded)
        self.assertIn(gate.ACK_BLOCKED_MISSING_HANDOFF, encoded)
        self.assertIn(gate.ACK_REJECTED_UNSAFE, encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()

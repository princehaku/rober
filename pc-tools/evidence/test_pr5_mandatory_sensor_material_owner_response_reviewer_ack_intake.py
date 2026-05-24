#!/usr/bin/env python3
"""PR #5 mandatory sensor material reviewer ACK intake gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是标准 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_mandatory_sensor_material_owner_response_review_handoff as previous_handoff  # noqa: E402
import pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一跳 safe handoff，不模拟真实 LiDAR/ToF 材料。
# 测试约束 02：reviewer ACK 只表示收到/转派，不代表 PR #5 reviewer resolution。
# 测试约束 03：needs_reassignment 只改变人工路由，不启用 Start/Confirm/Cancel。
# 测试约束 04：缺上一跳、缺 ACK、mismatch、unsafe 都必须 fail closed。
# 测试约束 05：所有输出保持 source=software_proof、hardware_material_pending。
# 测试约束 06：所有输出保持 not_proven、delivery_success=false。
# 测试约束 07：所有输出保持 primary_actions_enabled=false。
# 测试约束 08：所有输出保持 safe_to_control=false。
# 测试约束 09：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。
# 测试约束 10：vendor source refs 只证明本地资料覆盖，不证明实物安装或 HIL。
# 测试履约注释 011：accepted case 只验证 ACK metadata，不验证真实 reviewer resolution。
# 测试履约注释 012：reassignment case 只验证人工路由，不验证 owner 已处理。
# 测试履约注释 013：missing ACK case 保证 optional packet 不会被默认为 accepted。
# 测试履约注释 014：missing handoff case 保证上一跳合同缺失时 fail closed。
# 测试履约注释 015：mismatch case 保证 source 和 ACK 不能跨 evidence_ref 拼接。
# 测试履约注释 016：unsafe case 覆盖 raw body，避免完整材料穿透。
# 测试履约注释 017：unsafe case 覆盖 local path，避免本机路径泄漏。
# 测试履约注释 018：unsafe case 覆盖 ROS topic，避免 runtime 控制面泄漏。
# 测试履约注释 019：unsafe case 覆盖 /cmd_vel，避免机器人动作误启用。
# 测试履约注释 020：unsafe case 覆盖 serial/UART，避免硬件 proof 混入。
# 测试履约注释 021：unsafe case 覆盖 baudrate，避免配置值伪装 evidence。
# 测试履约注释 022：unsafe case 覆盖 WAVE ROVER runtime proof，避免上车误判。
# 测试履约注释 023：unsafe case 覆盖 HIL pass，避免真实硬件闭环误判。
# 测试履约注释 024：unsafe case 覆盖 GitHub mutation，避免 PR 状态误写。
# 测试履约注释 025：unsafe case 覆盖 LiDAR installed，避免安装证明误判。
# 测试履约注释 026：unsafe case 覆盖 ToF calibrated，避免标定证明误判。
# 测试履约注释 027：unsafe case 覆盖 delivery_success=true，避免送达误判。
# 测试履约注释 028：unsafe case 覆盖 primary_actions_enabled=true，避免 UI 启动误判。
# 测试履约注释 029：unsafe case 覆盖 safe_to_control=true，避免控制权限误判。
# 测试履约注释 030：CLI case 保证 artifact stdout 含固定 rg markers。
# 测试履约注释 031：CLI case 不传 output，避免测试写入仓库路径。
# 测试履约注释 032：fixture 使用 TemporaryDirectory，避免读取真实材料。
# 测试履约注释 033：fixture 不 import ROS2，避免 runtime availability 进入证明。
# 测试履约注释 034：fixture 不调用网络，避免 live GitHub 状态进入证明。
# 测试履约注释 035：fixture 不打开 /dev，避免本机串口进入证明。
# 测试履约注释 036：source fixture 固定 unresolved，避免误表示 thread resolved。
# 测试履约注释 037：source fixture 固定 hardware_material_pending，避免误表示材料已到。
# 测试履约注释 038：source fixture 固定 delivery_success=false，避免送达误判。
# 测试履约注释 039：source fixture 固定 primary_actions_enabled=false，避免动作误启用。
# 测试履约注释 040：source fixture 固定 safe_to_control=false，避免控制误启用。
# 测试履约注释 041：ACK fixture 固定 hardware_material_pending，避免材料状态放宽。
# 测试履约注释 042：ACK fixture 固定 not_proven，避免 ACK 变成证明。
# 测试履约注释 043：ACK fixture 带 owner/support/reviewer next steps，验证字段白名单。
# 测试履约注释 044：ACK fixture 带 reassignment_target，验证转派路径。
# 测试履约注释 045：summary assertion 检查 Robot alias，验证下游安全消费面。
# 测试履约注释 046：summary assertion 检查 vendor boundary，验证来源归因边界。
# 测试履约注释 047：encoded assertion 检查敏感片段不回显，验证脱敏输出。
# 测试履约注释 048：returncode assertion 检查 CLI 的 accepted 语义。
# 测试履约注释 049：非零 assertion 检查 fail-closed 语义。
# 测试履约注释 050：本测试是软件证明，不替代 Docker build、HIL 或真实 reviewer proof。


class PR5MandatorySensorReviewerAckIntakeTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def previous_handoff_summary(self, evidence_ref: str, status: str = previous_handoff.READY) -> dict:
        # 上一跳 source 必须显式带 capability、boundary 和同一 safe evidence_ref。
        return {
            "schema": previous_handoff.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "software_proof": True,
            "status": status,
            "handoff_status": status,
            "capability": previous_handoff.CAPABILITY,
            "evidence_boundary": previous_handoff.BOUNDARY,
            "boundary": previous_handoff.BOUNDARY,
            "thread_id": gate.THREAD_ID,
            "thread_resolution": "unresolved",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "review_handoff": {
                "source": "software_proof",
                "not_proven": True,
                "handoff_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "hardware_material_status": "hardware_material_pending",
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
            "safe_copy": {
                "capability": previous_handoff.CAPABILITY,
                "source": "software_proof",
                "not_proven": "not_proven",
                "handoff_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "hardware_material_pending": "hardware_material_pending",
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
            "hardware_material_status": "hardware_material_pending",
            "hardware_material_pending": "hardware_material_pending",
            "not_proven": ["not_proven"],
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }

    def ack_packet(self, evidence_ref: str, state: str = gate.ACK_ACCEPTED_ACKNOWLEDGED) -> dict:
        # ACK packet 只包含 reviewer-safe 标签和下一步，不包含 raw material body。
        return {
            "schema": gate.ACK_PACKET_SCHEMA,
            "source": "software_proof",
            "software_proof": True,
            "hardware_material_status": "hardware_material_pending",
            "hardware_material_pending": "hardware_material_pending",
            "status": "not_proven",
            "not_proven": True,
            "reviewer_ack_state": state,
            "reviewer_role": "pr5-material-reviewer",
            "reviewer_identity_label": "reviewer-a",
            "ack_reason": "safe owner response review handoff metadata received",
            "owner_next_step": "keep owner response handoff attached to this evidence_ref",
            "support_next_step": "watch for PR #5 hardware material follow-up",
            "reviewer_next_step": "prepare separate review decision after real materials arrive",
            "next_required_evidence": [
                "same safe evidence_ref reviewer ACK summary",
                "real 2D LiDAR and ToF material packet before any PR #5 resolution claim",
            ],
            "reassignment_target": "reviewer-b",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }

    def build(self, root: Path, handoff_payload: dict, ack_payload: dict, evidence_ref: str) -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦状态映射和 fail-closed 边界。
        handoff_path = self.write_json(root, "handoff.json", handoff_payload)
        ack_path = self.write_json(root, "ack.json", ack_payload)
        return gate.build_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake(
            str(handoff_path),
            str(ack_path),
            evidence_ref,
        )

    def test_acknowledged_packet_outputs_robot_safe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("pr5-reviewer-ack-001"),
                self.ack_packet("pr5-reviewer-ack-001"),
                "pr5-reviewer-ack-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_ACCEPTED_ACKNOWLEDGED)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact[gate.ROBOT_ALIAS]["reviewer_ack_state"], gate.ACK_ACCEPTED_ACKNOWLEDGED)
        self.assertEqual(summary["reviewer_acknowledgement"]["reviewer_role"], "pr5-material-reviewer")
        self.assertEqual(summary["pr5_thread"]["thread_id"], gate.THREAD_ID)
        self.assertEqual(summary["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertEqual(summary["vendor_source_boundary"], "source_attribution_only_not_real_sensor_or_hil_proof")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_needs_reassignment_is_supported_without_control_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("pr5-reviewer-ack-002"),
                self.ack_packet("pr5-reviewer-ack-002", gate.ACK_NEEDS_REASSIGNMENT),
                "pr5-reviewer-ack-002",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_NEEDS_REASSIGNMENT)
        self.assertEqual(summary["reviewer_acknowledgement"]["reassignment_target"], "reviewer-b")
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_ack_packet_needs_reassignment_because_packet_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self.write_json(root, "handoff.json", self.previous_handoff_summary("pr5-reviewer-ack-003"))
            artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake(
                str(handoff_path),
                "",
                "pr5-reviewer-ack-003",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_NEEDS_REASSIGNMENT)
        self.assertIn("reviewer_ack_missing_or_unsupported_state", artifact["ack_reasons"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_blocked_missing_previous_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ack_path = self.write_json(root, "ack.json", self.ack_packet("pr5-reviewer-ack-004"))
            artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake(
                str(root / "missing-handoff.json"),
                str(ack_path),
                "pr5-reviewer-ack-004",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_BLOCKED_MISSING_HANDOFF)
        self.assertIn("owner_response_review_handoff_json_missing", artifact["ack_reasons"])
        self.assertFalse(summary["delivery_success"])

    def test_evidence_ref_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("pr5-reviewer-ack-005"),
                self.ack_packet("other-pr5-reviewer-ack-005"),
                "pr5-reviewer-ack-005",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_EVIDENCE_REF_MISMATCH)
        self.assertIn("source_ack_or_requested_evidence_ref_mismatch", artifact["ack_reasons"])
        self.assertFalse(summary["safe_to_control"])

    def test_unsafe_ack_rejects_raw_paths_ros_uart_github_hil_and_success_claims(self) -> None:
        unsafe_notes = (
            "raw artifact body includes Authorization: Bearer abc",
            "local path /Users/m4/private/material.json",
            "ROS topic /cmd_vel and /odom attached",
            "serial UART baudrate 115200 WAVE ROVER runtime proof",
            "HIL pass verified",
            "GitHub PRRT_kwDOSWB9286CJ3tX resolved mutation complete",
            "2D LiDAR installed and ToF calibrated",
            "delivery_success=true primary_actions_enabled=true safe_to_control=true",
        )
        for idx, note in enumerate(unsafe_notes, start=6):
            evidence_ref = f"pr5-reviewer-ack-0{idx}"
            with self.subTest(note=note):
                with tempfile.TemporaryDirectory() as tmp:
                    ack = self.ack_packet(evidence_ref)
                    ack["safe_note"] = note
                    artifact, summary, exit_code = self.build(
                        Path(tmp),
                        self.previous_handoff_summary(evidence_ref),
                        ack,
                        evidence_ref,
                    )

                encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
                self.assertNotEqual(exit_code, 0)
                self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_REJECTED_UNSAFE)
                self.assertIn("delivery_success=false", encoded)
                self.assertNotIn("Bearer abc", encoded)
                self.assertNotIn("/Users/m4/private", encoded)
                self.assertNotIn("/cmd_vel", encoded)
                self.assertNotIn("115200", encoded)

    def test_robot_alias_wrapper_and_cli_surface_required_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {previous_handoff.ROBOT_ALIAS: self.previous_handoff_summary("pr5-reviewer-ack-014")}
            handoff_path = self.write_json(root, "handoff.json", payload)
            ack_path = self.write_json(root, "ack.json", self.ack_packet("pr5-reviewer-ack-014"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py"),
                    "--owner-response-review-handoff-json",
                    str(handoff_path),
                    "--reviewer-ack-json",
                    str(ack_path),
                    "--evidence-ref",
                    "pr5-reviewer-ack-014",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(gate.CAPABILITY, result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, result.stdout)
        self.assertIn(gate.ROBOT_ALIAS, result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("hardware_material_pending", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)
        self.assertIn(gate.THREAD_ID, result.stdout)


if __name__ == "__main__":
    unittest.main()

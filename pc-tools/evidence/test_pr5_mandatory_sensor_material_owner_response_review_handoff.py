#!/usr/bin/env python3
"""PR #5 mandatory sensor material owner-response review-handoff gate 围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 Python package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_mandatory_sensor_material_owner_response_review_decision as decision_gate  # noqa: E402
import pr5_mandatory_sensor_material_owner_response_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 sanitized review-decision summary。
# 测试约束 02：ready handoff 只表示人工交接可执行，不证明真实 LiDAR/ToF。
# 测试约束 03：needs/rejected/blocked 都必须保持 fail-closed flags。
# 测试约束 04：所有输出保持 source=software_proof 和 hardware_material_pending。
# 测试约束 05：所有输出保持 not_proven、delivery_success=false。
# 测试约束 06：所有输出保持 primary_actions_enabled=false 和 safe_to_control=false。
# 测试约束 07：单测不访问 ROS graph、GitHub 写接口、串口、硬件或网络。
# 测试约束 08：unsafe case 不能把 raw token、path、topic 或串口内容写回输出。
# 测试约束 09：accepted case 只验证 reviewer handoff，不验证真实材料。
# 测试约束 10：missing case 只验证补 safe refs，不要求 raw material body。
# 测试约束 11：rejected case 只验证 fail-closed 映射，不判断硬件真假。
# 测试约束 12：unsupported schema case 防止其它 gate summary 被误采信。
# 测试约束 13：evidence_ref mismatch case 防止不同材料链串案。
# 测试约束 14：true flag case 防止上游把控制权限伪装成 safe summary。
# 测试约束 15：vendor refs 不代表真实 LiDAR/ToF 采购材料。
# 测试约束 16：owner/support/reviewer handoff 只作为人工路由元数据。
# 测试约束 17：所有临时文件都在 TemporaryDirectory，避免读取仓库外材料。
# 测试约束 18：测试不使用网络，避免误把 live PR 状态写成证明。
# 测试约束 19：测试不打开 /dev，避免误把本机串口当上车证据。
# 测试约束 20：测试不 import ROS2，避免误把 runtime 可用性纳入证明。
# 测试约束 21：测试检查 boundary_note，保证 rg acceptance 词可审计。
# 测试约束 22：测试检查 docs/vendor/VENDOR_INDEX.md，保证来源入口被保留。
# 测试约束 23：测试检查 PRRT_kwDOSWB9286CJ3tX，保证 unresolved 语义可见。
# 测试约束 24：测试检查 delivery_success false，保证 delivery 不被误放行。
# 测试约束 25：测试检查 primary_actions_enabled false，保证主动作不启用。
# 测试约束 26：测试检查 safe_to_control false，保证控制权限不启用。
# 测试约束 27：测试中的 HIL pass 文案必须被拒绝，因为没有 HIL rig。
# 测试约束 28：测试中的 PR resolved 文案必须被拒绝，因为没有 GitHub live check。
# 测试约束 29：测试中的 O5 external proof 文案必须被拒绝，因为没有外部云材料。
# 测试约束 30：测试中的 delivery_success=true 必须被拒绝，因为没有真实送达。
# 测试约束 31：测试中的 LiDAR installed 文案必须被拒绝，因为没有安装证据。


class PR5MandatorySensorMaterialOwnerResponseReviewHandoffTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖真实 vendor、硬件或网络。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def decision_summary(self, evidence_ref: str, review_decision: str = decision_gate.ACCEPTED) -> dict:
        # source fixture 模拟上一 rung safe output，不夹带 raw owner response body。
        missing_refs: list[str] = [] if review_decision == decision_gate.ACCEPTED else [decision_gate.intake_gate.REQUIRED_RESPONSE_REFS[-1]]
        rejected_refs: list[str] = ["ToF SKU/source/receipt/procurement material owner response"] if review_decision == decision_gate.REJECTED_UNSAFE else []
        accepted_refs = [] if review_decision in {decision_gate.NEEDS_MORE, decision_gate.REJECTED_UNSAFE} else list(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS)
        return {
            "schema": decision_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "capability": decision_gate.CAPABILITY,
            "evidence_boundary": decision_gate.BOUNDARY,
            "boundary": decision_gate.BOUNDARY,
            "status": review_decision,
            "review_decision": review_decision,
            "thread_id": gate.THREAD_ID,
            "thread_resolution": "unresolved",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_status": {
                "required_refs": list(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS),
                "accepted_refs": accepted_refs,
                "missing_refs": missing_refs,
                "rejected_refs": rejected_refs,
                "accepted_count": len(accepted_refs),
                "required_count": len(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS),
                "is_complete": review_decision == decision_gate.ACCEPTED,
            },
            "owner_handoff": {
                "primary_owner": "Hardware Infra Engineer",
                "source_owner_id": "hardware-owner-a",
                "reviewer_next_step": "reviewer_closeout_candidate_not_proven",
                "ready_for_reviewer_closeout": review_decision == decision_gate.ACCEPTED,
            },
            "safe_copy": {
                "source": "software_proof",
                "status": review_decision,
                "review_decision": review_decision,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "hardware_material_status": "hardware_material_pending",
                "hardware_material_pending": "hardware_material_pending",
                "not_proven": "not_proven",
                "software_proof": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "hardware_material_status": "hardware_material_pending",
            "not_proven": list(decision_gate.NOT_PROVEN),
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict | str, evidence_ref: str = "pr5-review-handoff-001") -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦 handoff status、evidence_ref 和 fail-closed 规则。
        source_path = self.write_json(root, "owner_response_review_decision.json", payload)
        return gate.build_pr5_mandatory_sensor_material_owner_response_review_handoff(str(source_path), evidence_ref)

    def test_accepted_review_decision_becomes_handoff_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                {"payload": {"summary": self.decision_summary("pr5-review-handoff-001")}},
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["handoff_status"], gate.READY)
        self.assertIn(gate.BOUNDARY, artifact["boundary_note"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", artifact["boundary_note"])
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", artifact["boundary_note"])
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(summary["vendor_source_boundary"], "source_attribution_only_not_real_sensor_proof")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["review_handoff"]["ready_for_reviewer_closeout"])

    def test_needs_more_review_decision_maps_to_handoff_material_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.decision_summary("pr5-review-handoff-002", decision_gate.NEEDS_MORE),
                "pr5-review-handoff-002",
            )

        self.assertEqual(artifact["handoff_status"], gate.NEEDS_MORE)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_review_decision_needs_more_material_not_proven", artifact["handoff_reasons"])
        self.assertIn("PR #5 reviewer follow-up", "\n".join(summary["material_status"]["missing_refs"]))
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_rejected_source_stays_rejected_unsafe_for_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.decision_summary("pr5-review-handoff-003", decision_gate.REJECTED_UNSAFE),
                "pr5-review-handoff-003",
            )

        self.assertEqual(artifact["handoff_status"], gate.REJECTED_UNSAFE)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_review_decision_rejected_or_unsafe_not_proven", artifact["handoff_reasons"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_source_or_unsupported_schema_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_artifact, missing_summary, missing_exit = gate.build_pr5_mandatory_sensor_material_owner_response_review_handoff(
                str(root / "missing_review_decision.json"),
                "pr5-review-handoff-004",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_source = self.decision_summary("pr5-review-handoff-005")
            bad_source["schema"] = "trashbot.some_other_schema.v1"
            unsupported_artifact, unsupported_summary, unsupported_exit = self.build(root, bad_source, "pr5-review-handoff-005")

        self.assertEqual(missing_artifact["handoff_status"], gate.BLOCKED_MISSING)
        self.assertEqual(unsupported_artifact["handoff_status"], gate.BLOCKED_MISSING)
        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(unsupported_exit, 0)
        self.assertIn("owner_response_review_decision_json_missing", missing_artifact["handoff_reasons"])
        self.assertIn("missing_or_unsupported_pr5_mandatory_sensor_material_owner_response_review_decision", unsupported_artifact["handoff_reasons"])
        self.assertFalse(missing_summary["safe_to_control"])
        self.assertFalse(unsupported_summary["primary_actions_enabled"])

    def test_evidence_ref_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.decision_summary("pr5-review-handoff-006"),
                "different-pr5-review-handoff-006",
            )

        self.assertEqual(artifact["handoff_status"], gate.BLOCKED_REF)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_review_decision_evidence_ref_mismatch", artifact["handoff_reasons"])
        self.assertEqual(summary["safe_copy"]["handoff_status"], gate.BLOCKED_REF)

    def test_raw_credentials_paths_ros_uart_hil_pr_o5_and_delivery_claims_fail_closed(self) -> None:
        unsafe_patches = (
            {"raw_owner_response": {"body": "complete material payload"}},
            {"safe_notes": ["Authorization: Bearer abc token=secret"]},
            {"safe_notes": ["local path /Users/m4/private/material.json"]},
            {"safe_notes": ["ROS topic /cmd_vel and /odom attached"]},
            {"safe_notes": ["serial_port=/dev/ttyAMA0 baudrate=115200"]},
            {"safe_notes": ["real HIL passed with hil_pass copy"]},
            {"safe_notes": ["PRRT_kwDOSWB9286CJ3tX resolved by reviewer"]},
            {"safe_notes": ["Objective 5 external proof and OSS/CDN live traffic"]},
            {"safe_notes": ["delivery_success=true primary_actions_enabled=true safe_to_control=true"]},
            {"safe_notes": ["2D LiDAR installed and ToF wired"]},
        )
        for idx, patch in enumerate(unsafe_patches, start=7):
            evidence_ref = f"pr5-review-handoff-0{idx}"
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                payload = self.decision_summary(evidence_ref)
                payload.update(patch)
                artifact, summary, exit_code = self.build(root, payload, evidence_ref)

            encoded = json.dumps(artifact, ensure_ascii=False)
            self.assertEqual(artifact["handoff_status"], gate.REJECTED_UNSAFE)
            self.assertNotEqual(exit_code, 0)
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(summary["primary_actions_enabled"])
            self.assertNotIn("Bearer abc", encoded)
            self.assertNotIn("/Users/m4/private", encoded)
            self.assertNotIn("/cmd_vel", encoded)
            self.assertNotIn("/dev/ttyAMA0", encoded)
            self.assertNotIn("115200", encoded)

    def test_robot_alias_wrapper_and_cli_surface_required_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {decision_gate.ROBOT_ALIAS: self.decision_summary("pr5-review-handoff-017")}
            input_path = self.write_json(root, "review_decision.json", payload)
            artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_material_owner_response_review_handoff(
                str(input_path),
                "pr5-review-handoff-017",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "pr5_mandatory_sensor_material_owner_response_review_handoff.py"),
                    "--owner-response-review-decision-json",
                    str(input_path),
                    "--evidence-ref",
                    "pr5-review-handoff-017",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["handoff_status"], gate.READY)
        self.assertEqual(summary["thread_resolution"], "unresolved")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(gate.CAPABILITY, result.stdout)
        self.assertIn(gate.BOUNDARY, result.stdout)
        self.assertIn(gate.ROBOT_ALIAS, result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("hardware_material_pending", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)
        self.assertIn(gate.THREAD_ID, result.stdout)


if __name__ == "__main__":
    unittest.main()

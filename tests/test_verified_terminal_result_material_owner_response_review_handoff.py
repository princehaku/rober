#!/usr/bin/env python3
"""verified_terminal_result_material_owner_response_review_handoff gate 的离线围栏测试。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "verified_terminal_result_material_owner_response_review_handoff.py"
SPEC = importlib.util.spec_from_file_location("verified_terminal_result_material_owner_response_review_handoff", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


# 测试约束 01：fixture 只表达上一轮 owner-response review-decision safe metadata。
# 测试约束 02：accepted handoff 只表示人工交接包可派发，不证明真实结果。
# 测试约束 03：missing/rejected/unsafe/blocked 全部非 0 且 fail-closed。
# 测试约束 04：source 与 CLI 指定值必须使用同一个 safe evidence_ref。
# 测试约束 05：raw/path/credential/ROS/control/hardware/ACK/replay/reviewer claim 必须拒绝。
# 测试约束 06：PR #5 thread PRRT_kwDOSWB9286CJ3tX 必须保持 unresolved / hardware_material_pending。
# 测试约束 07：输出保持 source=software_proof、software_proof 和 not_proven。
# 测试约束 08：输出保持 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 测试约束 09：测试不访问 ROS graph、硬件、外部云、手机 runtime 或 raw logs。
# 测试说明 01：accepted case 验证 handoff packet ready，但仍保留 false flags。
# 测试说明 02：missing case 验证 backfill path，不把缺材料误判为 accepted。
# 测试说明 03：evidence_ref mismatch case 验证 same-ref 围栏优先阻断。
# 测试说明 04：unsafe raw fields case 验证 raw/path/ROS/hardware/resolution 文案被净化。
# 测试说明 05：true flags case 验证嵌套 true delivery/control flag 不能穿透。
# 测试说明 06：robot alias case 验证后续 Robot worker 的 safe alias 可被 PC gate 消费。
# 测试说明 07：CLI help case 验证验收命令可检索到关键 proof boundary 文案。
# 测试说明 08：所有 fixture 都是本地 JSON，不表示真实手机/browser 或真实云。
# 测试说明 09：所有 fixture 都是 software_proof，不表示 HIL 或 WAVE ROVER/UART proof。
# 测试说明 10：所有 fixture 都保留 PR #5 unresolved / hardware_material_pending。
# 测试说明 11：_source helper 默认生成可 accepted 的上一轮 decision summary。
# 测试说明 12：每个测试只覆盖一个 fail-closed 轴，避免 broad regression sweep。
# 测试说明 13：临时目录输出不会进入 repo，避免污染并行 worker 的 evidence 文件。
# 测试说明 14：encoded 检查用于确认 raw unsafe string 没有被复制到 artifact。
# 测试说明 15：exit_code 非 0 只用于 PC gate 分类，不代表机器人动作失败。
# 测试说明 16：source safe_copy 也带 false flags，模拟下游只读 summary surface。
# 测试说明 17：command_id 使用短安全标识，避免测试里引入路径或 URL。
# 测试说明 18：terminal_result_type 固定 delivery，其他类型由接口枚举覆盖。
# 测试说明 19：断言 owner/support/reviewer route 是用户触点收益的核心字段。
# 测试说明 20：断言 safe_to_control=false 防止 UI 或后端误启用控制动作。
# 测试说明 21：断言 primary_actions_enabled=false 防止 Start/Confirm/Cancel 误开。
# 测试说明 22：断言 delivery_success=false 防止 metadata rung 被误读成真实交付。
# 测试说明 23：断言 no OKR percentage lift 防止本地 gate 被计入 Objective 进展。
# 测试说明 24：断言 PRRT_kwDOSWB9286CJ3tX 保持 pending，避免伪造 reviewer closure。
# 测试说明 25：help 测试用 subprocess 只读运行，不触发 JSON 输出或外部 I/O。
# 测试说明 26：schema 断言防止 artifact/summary 名称在后续重构中漂移。
# 测试说明 27：source_review_decision 断言防止 handoff 丢失上一轮人工判断。
# 测试说明 28：owner/support/reviewer 断言防止用户触点路由字段缺失。
# 测试说明 29：mismatch 断言防止两个现场材料被拼成同一个交接包。
# 测试说明 30：unsafe 文本反查断言防止清洗失败导致 raw 路径或硬件词回显。
# 测试说明 31：true flag 断言防止嵌套对象绕过全局 fail-closed 扫描。
# 测试说明 32：alias 断言防止 Robot diagnostics safe alias 接入路径退化。
# 测试说明 33：CLI 输出文件断言防止 evidence bundle 文件名退化。
# 测试说明 34：help 文案断言防止人工验收看不到关键安全边界。
# 测试说明 35：所有测试都围绕 Task A 文件，不读取并行 Robot/mobile worker 改动。


class VerifiedTerminalResultMaterialOwnerResponseReviewHandoffTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线 gate 测试，不代表真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def _source(
        self,
        evidence_ref: str = "terminal-owner-handoff-101",
        review_decision: str = gate.SOURCE_ACCEPTED_STATUS,
    ) -> dict[str, object]:
        # source 使用上一轮 owner response review decision 的安全消费面。
        return {
            "schema": "trashbot.verified_terminal_result_material_owner_response_review_decision_summary.v1",
            "schema_version": 1,
            "capability": "verified_terminal_result_material_owner_response_review_decision",
            "source": "software_proof",
            "status": "not_proven",
            "software_proof": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "evidence_boundary": "software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate",
            "review_decision": review_decision,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "safe_command_id": "cmd-terminal-owner-handoff-001",
            "command_id": "cmd-terminal-owner-handoff-001",
            "terminal_result_type": "delivery",
            "field_owner": "field_terminal_result_material_owner",
            "support_owner": "support_terminal_result_material_owner",
            "reviewer_route": "terminal_result_material_reviewer",
            "accepted_materials": list(gate.REQUIRED_HANDOFF_MATERIALS),
            "missing_materials": [],
            "rejected_materials": [],
            "unsafe_materials": [],
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "software_proof": True,
                "not_proven": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
                "evidence_ref": evidence_ref,
            },
        }

    def _build(
        self,
        root: Path,
        source_payload: dict[str, object],
        evidence_ref: str = "terminal-owner-handoff-101",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦分类和安全边界。
        source_path = self._write_json(root, "owner-response-review-decision.json", source_payload)
        return gate.build_verified_terminal_result_material_owner_response_review_handoff(str(source_path), evidence_ref)

    def test_safe_owner_response_review_decision_is_accepted_handoff_not_proven_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), self._source())

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.ARTIFACT_SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["handoff_status"], gate.ACCEPTED_STATUS)
        self.assertEqual(summary["source_review_decision"], gate.SOURCE_ACCEPTED_STATUS)
        self.assertEqual(summary["safe_evidence_ref"], "terminal-owner-handoff-101")
        self.assertEqual(summary["safe_command_id"], "cmd-terminal-owner-handoff-001")
        self.assertEqual(summary["terminal_result_type"], "delivery")
        self.assertEqual(summary["owner_handoff"]["owner_route"], "field_terminal_result_material_owner")
        self.assertEqual(summary["support_handoff"]["support_route"], "support_terminal_result_material_owner")
        self.assertEqual(summary["reviewer_handoff"]["reviewer_route"], "terminal_result_material_reviewer")
        self.assertIn("software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate", encoded)
        self.assertIn("source=software_proof", encoded)
        self.assertIn("software_proof", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertEqual(artifact["pr5_thread"]["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["pr5_thread"]["state"], "unresolved")
        self.assertEqual(artifact["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_review_decision_material_is_missing_backfill_and_nonzero(self) -> None:
        source = self._source("terminal-owner-handoff-102", gate.SOURCE_MISSING_STATUS)
        source["accepted_materials"] = []
        source["missing_materials"] = ["support_handoff_route"]
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), source, "terminal-owner-handoff-102")

        self.assertEqual(artifact["handoff_status"], gate.MISSING_STATUS)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("support_handoff_route", artifact["missing_materials"])
        self.assertIn("support_handoff_route", artifact["next_required_evidence"][0])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_evidence_ref_mismatch_blocks_before_handoff(self) -> None:
        source = self._source("terminal-owner-handoff-103")
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                source,
                "other-terminal-owner-handoff-103",
            )

        self.assertEqual(artifact["handoff_status"], gate.BLOCKED_REF_STATUS)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("evidence_ref_mismatch", summary["blocked_reason"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_unsafe_raw_fields_are_sanitized_and_fail_closed(self) -> None:
        unsafe = self._source("terminal-owner-handoff-104")
        unsafe["operator_note"] = (
            "raw owner body /Users/m4/raw.json traceback /cmd_vel WAVE ROVER UART "
            "ack cursor replay command PRRT_kwDOSWB9286CJ3tX resolved delivery_success=true"
        )
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), unsafe, "terminal-owner-handoff-104")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(artifact["handoff_status"], gate.UNSAFE_STATUS)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("unsafe_raw_terminal_material_credential_ros_control_hardware_ack_replay_resolution_or_success_claim", artifact["blocked_reason"])
        self.assertNotIn("/Users/m4/raw.json", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("WAVE ROVER UART", encoded)
        self.assertNotIn("resolved delivery_success=true", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_true_state_flags_are_rejected_without_success_or_control(self) -> None:
        truthy = self._source("terminal-owner-handoff-105")
        truthy["nested_flags"] = {
            "delivery_success": True,
            "primary_actions_enabled": True,
            "safe_to_control": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), truthy, "terminal-owner-handoff-105")

        self.assertEqual(artifact["handoff_status"], gate.UNSAFE_STATUS)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("delivery_success_true_overclaim", artifact["handoff_reasons"])
        self.assertIn("primary_actions_enabled_true_overclaim", artifact["handoff_reasons"])
        self.assertIn("safe_to_control_true_overclaim", artifact["handoff_reasons"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_robot_alias_nested_wrapper_source_alias_and_cli_outputs(self) -> None:
        alias = self._source("terminal-owner-handoff-106")
        alias["schema"] = "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary"
        nested = {"summary": alias}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "nested-source.json", nested)
            output_dir = root / "out"
            exit_code = gate.main(["--source", str(source), "--evidence-ref", "terminal-owner-handoff-106", "--output-dir", str(output_dir)])
            artifact = json.loads((output_dir / "verified_terminal_result_material_owner_response_review_handoff.json").read_text())
            summary = json.loads((output_dir / "verified_terminal_result_material_owner_response_review_handoff_summary.json").read_text())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["handoff_status"], gate.ACCEPTED_STATUS)
        self.assertEqual(summary["summary_alias"], "robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary")
        self.assertTrue(summary["summary_only"])
        self.assertFalse(artifact["safe_to_control"])

    def test_cli_help_mentions_required_inputs_and_literals(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--input", result.stdout)
        self.assertIn("--source", result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", result.stdout)
        self.assertIn("hardware_material_pending", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)


if __name__ == "__main__":
    unittest.main()

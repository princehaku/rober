#!/usr/bin/env python3
"""verified terminal result reviewer ACK follow-up escalation gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status as gate  # noqa: E402
import verified_terminal_result_material_owner_response_reviewer_ack_review_handoff as handoff_gate  # noqa: E402


# 测试约束 01：fixture 只表达 reviewer ACK review-handoff safe summary。
# 测试约束 02：pending/due/overdue/escalated 都不代表真实材料到位。
# 测试约束 03：PR #5 thread 必须保持 unresolved / hardware_material_pending。
# 测试约束 04：缺 owner/reviewer/support route 必须 blocked。
# 测试约束 05：缺 next_required_evidence 必须 blocked。
# 测试约束 06：unsafe success/control/hardware/ACK mutation copy 必须 fail closed。
# 测试约束 07：Robot diagnostics safe alias wrapper 必须可消费。
# 测试约束 08：输出保持 source=software_proof 与 not_proven。
# 测试约束 09：输出保持 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 测试约束 10：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。
# 测试约束 11：fixture 只构造 safe summary，不包含真实材料路径。
# 测试约束 12：fixture 中 command_id 只是审计短标识，不代表可执行命令。
# 测试约束 13：所有状态 case 都必须断言 false flags，避免遗漏 UI 安全边界。
# 测试约束 14：pending case 只证明本地 schema 可生成，不证明材料已经到位。
# 测试约束 15：due case 只证明补证到期状态可表达，不证明 owner 已补证。
# 测试约束 16：overdue case 只证明升级时效可表达，不证明 support 已处理。
# 测试约束 17：escalated case 只证明路由升级可表达，不证明 reviewer resolved。
# 测试约束 18：PR #5 case 必须同时检查 thread id、unresolved 和 hardware pending。
# 测试约束 19：missing source case 必须看 exit code，避免 CLI 悄悄成功。
# 测试约束 20：non-ready source case 防止上一跳 missing material 被误当 follow-up ready。
# 测试约束 21：missing owner route case 防止无人负责的材料升级进入 ready 状态。
# 测试约束 22：missing next evidence case 防止不可执行的补证摘要进入 ready 状态。
# 测试约束 23：evidence_ref mismatch case 防止跨现场材料拼接。
# 测试约束 24：unsafe raw case 防止凭证、路径或控制 topic 泄漏。
# 测试约束 25：success claim case 防止 delivery_success=true 穿透。
# 测试约束 26：ACK mutation case 防止只读 gate 变成 reviewer update hint。
# 测试约束 27：robot command case 防止 follow-up 文案变成控制提示。
# 测试约束 28：safe_to_control case 防止 nested true flag 被忽略。
# 测试约束 29：Robot alias case 防止下游只传 alias 时断链。
# 测试约束 30：CLI case 覆盖真实命令入口和 stdout required literals。
# 测试约束 31：每个临时文件都在 tempfile 中生成，避免污染仓库。
# 测试约束 32：测试不依赖当前时间，避免 generated_at 导致不稳定断言。
# 测试约束 33：测试不检查完整 JSON，只检查合同字段和安全边界。
# 测试约束 34：测试不读取 OKR 或 sprint 文件，避免跨 owner 文件耦合。
# 测试约束 35：测试不调用 subprocess 以外的外部工具，保持围栏轻量。
# 测试约束 36：subprocess 只运行本 gate CLI，不运行 Robot/mobile 验收。
# 测试约束 37：fixture 的 owner/reviewer/support route 是人工路由，不是权限。
# 测试约束 38：fixture 的 next_required_evidence 是模板，不代表真实收齐。
# 测试约束 39：fixture 的 pr5_thread 是状态声明，不做 GitHub mutation。
# 测试约束 40：assertNotIn 检查 unsafe 原文未进入 artifact/summary。
# 测试约束 41：assertIn 检查 boundary literals，保证 closeout 可搜索。
# 测试约束 42：blocked state 统一检查 BLOCKED_MISSING_REAL_MATERIALS，避免分支漂移。
# 测试约束 43：required literals 覆盖 overdue 和 escalated，满足 Task A rg 要求。
# 测试约束 44：测试文件本身保留中文注释，解释为什么需要这些 fail-closed case。
# 测试约束 45：未来新增状态必须补充状态枚举 case 和 CLI literal case。
# 测试约束 46：未来放宽安全扫描必须同步调整 unsafe tests，不能只改实现。
# 测试约束 47：未来接入真实材料必须新增独立 gate 测试，不复用本地 fixture 宣称通过。
# 测试约束 48：未来 Robot/mobile 消费 alias 时仍应保持此 PC gate 的只读边界。
# 测试约束 49：这些测试证明的是 software_proof_docker gate，不是 HIL 或 field pass。
# 测试约束 50：所有测试预期都围绕 no OKR percentage lift 的证据边界。
# 测试约束 51：helper 明确写 JSON 文件，模拟 CLI 输入而不是内存捷径。
# 测试约束 52：helper 返回 artifact、summary、exit_code，覆盖库函数主合同。
# 测试约束 53：状态循环用 subTest，便于定位具体 followup_state 回归。
# 测试约束 54：overdue/escalated 单独测 route，避免状态只在 marker 中出现。
# 测试约束 55：PR5 单独测 blocker identity，避免只靠 boundary_note 间接覆盖。
# 测试约束 56：missing source 单独测 read_state，避免 FileNotFound 回归成 traceback。
# 测试约束 57：non-ready handoff 单独测 source_handoff_status 映射。
# 测试约束 58：route/evidence/ref 三个 blocked case 聚合，但分别断言原因。
# 测试约束 59：unsafe cases 用 subTest，保证每种风险都有独立失败点。
# 测试约束 60：CLI required literals 只检查必要片段，避免 generated_at 不稳定。
# 测试约束 61：测试不检查排序，JSON sort_keys 属于实现细节。
# 测试约束 62：测试不要求真实 output-dir 文件，Task A 验收只要求 CLI surface。
# 测试约束 63：测试不模拟真实硬件材料，因为那会越过本 gate 证据边界。
# 测试约束 64：测试不模拟 GitHub resolve，因为本 gate 不具备 mutation 权限。
# 测试约束 65：测试中的 safe copy 是下游摘要，不是原始 reviewer ACK。
# 测试约束 66：测试中的 blocked outputs 仍必须可 JSON 序列化。
# 测试约束 67：测试中的 unsafe strings 不能出现在最终 encoded output。
# 测试约束 68：测试中的 false flags 必须在 summary 层检查，而不只在 artifact 层。
# 测试约束 69：测试中的 alias wrapper 覆盖 nested safe JSON 路径。
# 测试约束 70：测试文件不触碰 Robot/mobile/OKR/sprint closeout 范围。


class VerifiedTerminalResultReviewerAckFollowupEscalationStatusTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _handoff_summary(
        self,
        evidence_ref: str,
        handoff_status: str = handoff_gate.READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF,
        next_required_evidence: list[str] | None = None,
    ) -> dict[str, object]:
        # source 使用上一轮 reviewer ACK review-handoff 的安全消费面。
        required_evidence = (
            ["real 2D LiDAR / ToF receipt and same safe evidence_ref HIL-entry materials"]
            if next_required_evidence is None
            else next_required_evidence
        )
        return {
            "schema": handoff_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": handoff_gate.CAPABILITY,
            "summary_alias": handoff_gate.ROBOT_ALIAS,
            "evidence_boundary": handoff_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "safe_command_id": "cmd-terminal-followup-001",
            "command_id": "cmd-terminal-followup-001",
            "same_evidence_ref_required": True,
            "source_review_decision": "accepted_for_material_review_not_proven",
            "reviewer_ack_state": "reviewer_acknowledged_not_proven",
            "handoff_status": handoff_status,
            "handoff_reasons": ["reviewer ACK handoff ready for follow-up only"],
            "owner_route": "field-terminal-result-material-owner",
            "reviewer_role": "real-material-reviewer",
            "support_route": "support-terminal-result-material-owner",
            "next_required_evidence": required_evidence,
            "pr5_thread": {
                "thread_id": gate.PR5_THREAD_ID,
                "state": "unresolved",
                "material_state": "hardware_material_pending",
            },
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "capability": handoff_gate.CAPABILITY,
                "source": "software_proof",
                "status": "not_proven",
                "handoff_status": handoff_status,
                "source_review_decision": "accepted_for_material_review_not_proven",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "safe_command_id": "cmd-terminal-followup-001",
                "owner_route": "field-terminal-result-material-owner",
                "reviewer_role": "real-material-reviewer",
                "support_route": "support-terminal-result-material-owner",
                "next_required_evidence": required_evidence,
                "pr5_thread": {
                    "thread_id": gate.PR5_THREAD_ID,
                    "state": "unresolved",
                    "material_state": "hardware_material_pending",
                },
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
        }

    def _build(
        self,
        root: Path,
        payload: dict[str, object],
        followup_state: str = gate.OVERDUE,
        evidence_ref: str = "",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦状态映射和安全边界。
        source_path = self._write_json(root, "reviewer_ack_review_handoff.json", payload)
        return gate.build_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status(
            str(source_path),
            followup_state,
            evidence_ref,
        )

    def test_ready_handoff_models_all_safe_followup_states_without_control(self) -> None:
        for state in (gate.PENDING, gate.DUE, gate.OVERDUE, gate.ESCALATED):
            with self.subTest(state=state):
                with tempfile.TemporaryDirectory() as tmp:
                    artifact, summary, exit_code = self._build(
                        Path(tmp),
                        self._handoff_summary(f"terminal-followup-{state}"),
                        state,
                    )

                self.assertEqual(exit_code, 0)
                self.assertEqual(artifact["schema"], gate.SCHEMA)
                self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
                self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
                self.assertEqual(artifact["followup_state"], state)
                self.assertEqual(summary["followup_state"], state)
                self.assertFalse(summary["delivery_success"])
                self.assertFalse(summary["primary_actions_enabled"])
                self.assertFalse(summary["safe_to_control"])
                self.assertIn(state, summary["allowed_followup_states"])
                self.assertIn("no OKR percentage lift", summary["boundary_note"])

    def test_overdue_and_escalated_expose_due_flags_and_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            overdue, overdue_summary, overdue_exit = self._build(
                Path(tmp),
                self._handoff_summary("terminal-followup-overdue-001"),
                gate.OVERDUE,
            )
            escalated, escalated_summary, escalated_exit = self._build(
                Path(tmp),
                self._handoff_summary("terminal-followup-escalated-001"),
                gate.ESCALATED,
            )

        self.assertEqual(overdue_exit, 0)
        self.assertEqual(escalated_exit, 0)
        self.assertTrue(overdue_summary["due_status"]["is_overdue"])
        self.assertTrue(escalated_summary["due_status"]["is_escalated"])
        self.assertEqual(overdue["owner_route"], "field-terminal-result-material-owner")
        self.assertEqual(escalated["reviewer_route"], "real-material-reviewer")
        self.assertIn("support", escalated["support_route"])
        self.assertIn("PR #5", escalated_summary["escalation_reason"])

    def test_pr5_thread_stays_unresolved_hardware_material_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("terminal-followup-pr5-001"),
                gate.DUE,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["pr5_thread"]["thread_id"], gate.PR5_THREAD_ID)
        self.assertEqual(summary["pr5_thread"]["state"], "unresolved")
        self.assertEqual(summary["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertIn("hardware_material_pending", summary["unresolved_blocker"])

    def test_missing_source_and_non_ready_handoff_block_missing_real_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, missing_exit = gate.build_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status(
                str(root / "missing-handoff.json"),
                gate.OVERDUE,
            )
            not_ready, _, not_ready_exit = self._build(
                root,
                self._handoff_summary("terminal-followup-blocked-001", handoff_gate.MISSING_MATERIAL),
                gate.OVERDUE,
            )

        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(not_ready_exit, 0)
        self.assertEqual(missing["followup_state"], gate.BLOCKED_MISSING_REAL_MATERIALS)
        self.assertEqual(not_ready["followup_state"], gate.BLOCKED_MISSING_REAL_MATERIALS)
        self.assertIn("reviewer_ack_review_handoff_json_missing", missing["followup_reasons"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_missing_routes_next_required_and_evidence_ref_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            no_route = self._handoff_summary("terminal-followup-route-001")
            no_route["owner_route"] = ""
            no_route["safe_copy"]["owner_route"] = ""  # type: ignore[index]
            no_next = self._handoff_summary("terminal-followup-next-001", next_required_evidence=[])
            mismatch, mismatch_summary, mismatch_exit = self._build(
                root,
                self._handoff_summary("terminal-followup-ref-001"),
                gate.PENDING,
                "terminal-followup-ref-other",
            )
            route, route_summary, route_exit = self._build(root, no_route, gate.PENDING)
            next_artifact, next_summary, next_exit = self._build(root, no_next, gate.PENDING)

        self.assertNotEqual(mismatch_exit, 0)
        self.assertNotEqual(route_exit, 0)
        self.assertNotEqual(next_exit, 0)
        self.assertEqual(mismatch["followup_state"], gate.BLOCKED_MISSING_REAL_MATERIALS)
        self.assertIn("evidence_ref_mismatch", mismatch_summary["followup_reasons"])
        self.assertIn("missing_owner_route", route_summary["followup_reasons"])
        self.assertIn("missing_next_required_evidence", next_artifact["followup_reasons"])
        self.assertFalse(next_summary["safe_to_control"])

    def test_unsafe_raw_fields_and_success_claims_reject_without_raw_copy(self) -> None:
        for key, value in (
            ("raw_material_body", "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact"),
            ("safe_note", "delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved"),
            ("ack_mutation_hint", "retry review mutation"),
            ("robot_command_hint", "start delivery command"),
            ("safe_to_control", True),
        ):
            with self.subTest(key=key):
                with tempfile.TemporaryDirectory() as tmp:
                    payload = self._handoff_summary(f"terminal-followup-{abs(hash(key))}")
                    payload[key] = value
                    artifact, summary, exit_code = self._build(Path(tmp), payload, gate.OVERDUE)

                encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
                self.assertNotEqual(exit_code, 0)
                self.assertEqual(artifact["followup_state"], gate.BLOCKED_MISSING_REAL_MATERIALS)
                self.assertIn("delivery_success=false", encoded)
                self.assertNotIn("Bearer abc", encoded)
                self.assertNotIn("/cmd_vel", encoded)
                self.assertNotIn("/dev/ttyUSB0", encoded)
                self.assertFalse(summary["safe_copy"]["safe_to_control"])

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {handoff_gate.ROBOT_ALIAS: self._handoff_summary("terminal-followup-alias-001")}
            artifact, summary, exit_code = self._build(Path(tmp), payload, gate.PENDING)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["followup_state"], gate.PENDING)
        self.assertEqual(artifact["safe_evidence_ref"], "terminal-followup-alias-001")
        self.assertEqual(summary["source_handoff_status"], handoff_gate.READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF)

    def test_cli_and_output_surface_required_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_json(root, "reviewer_ack_review_handoff.json", self._handoff_summary("terminal-followup-cli-001"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py"),
                    "--reviewer-ack-review-handoff-json",
                    str(input_path),
                    "--followup-state",
                    "overdue",
                    "--evidence-ref",
                    "terminal-followup-cli-001",
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
        self.assertIn(gate.PR5_THREAD_ID, result.stdout)
        self.assertIn("hardware_material_pending", result.stdout)
        self.assertIn("overdue", result.stdout)
        self.assertIn("escalated", result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("not_proven", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)


if __name__ == "__main__":
    unittest.main()

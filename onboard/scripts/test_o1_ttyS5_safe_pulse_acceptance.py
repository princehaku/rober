#!/usr/bin/env python3
"""O1 /dev/ttyS5 safe pulse runner 的 fake HTTP 单元测试。"""

from __future__ import annotations

import json
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import o1_ttyS5_safe_pulse_acceptance as runner  # noqa: E402


STATUS_PAYLOAD = {
    "schema": "trashbot.upper_robot_api.v1.status",
    "camera": {"http_status": 200, "status": "ready", "video_source": "camera0"},
    "radar": {"scan_status": "not_proven", "observed_lidar_port": "/dev/ttyACM0", "baudrate": 150000},
    "base": {
        "port": "/dev/ttyS5",
        "baudrate": 115200,
        "write_control_available": True,
        "safe_to_control": False,
        "feedback_ack": {
            "t1001_observed": False,
            "robot_ack_connected": False,
            "reason": "T=1001 not observed",
        },
    },
}

STATUS_WITH_T1001 = {
    **STATUS_PAYLOAD,
    "base": {
        **STATUS_PAYLOAD["base"],
        "feedback_ack": {
            "t1001_observed": True,
            "robot_ack_connected": True,
            "reason": "T=1001 observed after watched pulse",
        },
    },
}

COMPLETE_OPERATOR_REPORT = {
    "operator_present": True,
    "physical_clearance_confirmed": True,
    "emergency_stop_ready": True,
    "observed_motion": True,
    "observed_stop": True,
    "operator_notes": "watched low-speed pulse stopped within expected window",
    "reported_at": "2026-06-03T00:00:00Z",
}

# 测试边界说明：所有测试只使用 fake HTTP，不访问真实 8787。
# 测试边界说明：默认 dry-run 必须只 GET status，不能 POST manual。
# 测试边界说明：单独 `--execute-motion` 不能授权运动，必须双确认。
# 测试边界说明：执行路径测试只验证 payload 形态，不发送真实运动。
# 测试边界说明：fake HTTP 记录 method/path/body，用于断言 API guardrail。
# 测试边界说明：速度上限必须在 runner 层先收紧到 0.08。
# 测试边界说明：时长上限必须在 runner 层先收紧到 350ms。
# 测试边界说明：manual 后必须追加 stop，形成独立 stop evidence。
# 测试边界说明：status-json 模式不能访问网络，避免重复触达远端。
# 测试边界说明：atomic output 测试只写临时目录，不污染现场 artifact。
# 测试边界说明：所有结果必须保持 safe_to_control=false。
# 测试边界说明：T=1001 未观察到时必须保持 not_observed/unknown。
# 测试边界说明：测试不 import pyserial，也不打开 `/dev/ttyS5`。
# 测试边界说明：测试不构造 ROS `/cmd_vel`，runner 也不应接触 ROS。
# 测试边界说明：HTTP 结果由 fake 返回，避免环境偶然在线影响断言。
# 测试边界说明：schema 字段是下游 PC/OKR 消费的机器合同。
# 测试边界说明：执行模式即使 fake 成功，也不代表真实 HIL pass。
# 测试边界说明：测试关注安全护栏，不覆盖真实现场运动物理效果。
# 测试边界说明：本文件的中文注释记录测试为什么不能碰硬件。
# 测试边界说明：未来新增真实远端验证必须另建现场 runbook。
# 测试边界说明：任何失败都应先看 fake 调用序列定位根因。
# 测试边界说明：这些断言防止后续维护把默认路径改成 POST。
# 测试边界说明：这些断言防止后续维护移除额外 stop evidence。
# 测试边界说明：这些断言防止 status artifact 被误写成可控制。
# 测试边界说明：fake 成功只证明 runner 逻辑，不证明 WAVE ROVER 真实响应。
# 测试边界说明：真实执行必须由现场材料补充，不能由单测替代。
# 测试边界说明：显式 dry-run 比 execute/confirm 优先级更高，必须阻断 POST。
# 测试边界说明：执行后必须再 GET status，避免 manual 响应替代 ACK。
# 测试边界说明：acceptance_verdict 必须机器可读，供 OKR 收口自动消费。
# 测试边界说明：status/manual/stop 任一步失败都要 fail-closed。
# 测试边界说明：operator report 是人工材料，不是运动授权或 HIL pass。
# 测试边界说明：execute 缺 operator report 时必须阻断 manual POST。
# 测试边界说明：dry-run 携带完整 report 仍必须保持只读。


class SafePulseAcceptanceTest(unittest.TestCase):
    def write_operator_report(self, temp_dir: str, report: dict[str, object] | None = None) -> str:
        # 每个执行测试都显式提供现场报告，避免绕过新增 fail-closed 闸。
        path = Path(temp_dir) / "operator_report.json"
        path.write_text(json.dumps(COMPLETE_OPERATOR_REPORT if report is None else report), encoding="utf-8")
        return str(path)

    def test_default_dry_run_reads_status_without_motion_post(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            # fake HTTP 记录 method/path，证明默认路径不会 POST 运动接口。
            calls.append((method, path, payload))
            return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}

        with mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(["--dry-run", "--once-json"])
            result = runner.run_acceptance(args)

        self.assertEqual(calls, [("GET", "/api/status", None)])
        self.assertIsNone(result["operator_report"])
        self.assertEqual(result["operator_report_status"], "missing")
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertEqual(result["status_summary"]["base"]["port"], "/dev/ttyS5")
        self.assertEqual(result["status_summary"]["base"]["baudrate"], 115200)
        self.assertEqual(result["t1001_feedback_status"], "not_observed")
        self.assertEqual(result["acceptance_verdict"]["status"], "dry_run_only")
        self.assertFalse(result["acceptance_verdict"]["safe_to_control"])

    def test_execute_requires_both_confirmation_flags(self) -> None:
        calls: list[str] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append(path)
            return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}

        with mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(["--execute-motion", "--once-json"])
            result = runner.run_acceptance(args)

        self.assertEqual(calls, ["/api/status"])
        self.assertFalse(result["execution_gate"]["authorized"])
        self.assertFalse(result["sends_commands"])
        self.assertIsNone(result["manual_request"])
        self.assertEqual(result["acceptance_verdict"]["status"], "dry_run_only")

    def test_explicit_dry_run_blocks_execute_even_with_confirmation_flags(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            # dry-run 是最高优先级安全闸；这里记录调用序列防止后续误 POST。
            calls.append((method, path, payload))
            return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}

        with mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(["--dry-run", "--execute-motion", "--confirm-physical-clearance", "--once-json"])
            result = runner.run_acceptance(args)

        self.assertEqual(calls, [("GET", "/api/status", None)])
        self.assertFalse(result["execution_gate"]["authorized"])
        self.assertTrue(result["execution_gate"]["dry_run"])
        self.assertIn("dry-run blocks execution", result["execution_gate"]["reason"])
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertIsNone(result["manual_request"])
        self.assertIsNone(result["stop_request"])
        self.assertEqual(result["acceptance_verdict"]["status"], "dry_run_only")

    def test_execute_mode_clamps_speed_duration_posts_manual_and_stop(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((method, path, payload))
            if path == "/api/status":
                return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}
            if path == "/api/base/manual":
                return {
                    "ok": True,
                    "http_status": 200,
                    "elapsed_ms": 2.0,
                    "json": {
                        "accepted": True,
                        "manual_command_executed": True,
                        "auto_stop_attempted": True,
                        "auto_stop_executed": True,
                        "feedback_ack": {"t1001_observed": False, "robot_ack_connected": False},
                    },
                    "error": None,
                }
            return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": {"robot_control_executed": True}, "error": None}

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(
                [
                    "--execute-motion",
                    "--confirm-physical-clearance",
                    "--operator-report-json",
                    self.write_operator_report(temp_dir),
                    "--direction",
                    "forward",
                    "--speed",
                    "9.0",
                    "--duration-ms",
                    "9999",
                ]
            )
            result = runner.run_acceptance(args)

        self.assertEqual(calls[0], ("GET", "/api/status", None))
        self.assertEqual(calls[1], ("POST", "/api/base/manual", {"direction": "forward", "speed": runner.MAX_SPEED, "duration_ms": runner.MAX_DURATION_MS}))
        self.assertEqual(calls[2], ("POST", "/api/base/stop", {}))
        self.assertEqual(calls[3], ("GET", "/api/status", None))
        self.assertTrue(result["sends_commands"])
        self.assertTrue(result["sends_motion_commands"])
        self.assertTrue(result["robot_control_executed"])
        self.assertFalse(result["safe_to_control"])
        self.assertEqual(result["stop_request"]["path"], "/api/base/stop")
        self.assertEqual(result["post_t1001_feedback_status"], "not_observed")
        self.assertEqual(result["operator_report_status"], "ready_for_review")
        self.assertEqual(result["acceptance_verdict"]["status"], "motion_posted_without_ack")
        self.assertFalse(result["acceptance_verdict"]["safe_to_control"])
        self.assertFalse(result["acceptance_verdict"]["hil_pass"])

    def test_execute_mode_reports_post_status_t1001_without_hil_pass(self) -> None:
        calls: list[str] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            # 第二次 status 才返回 T=1001，模拟 watched pulse 后 API 观察到 ACK。
            calls.append(path)
            if path == "/api/status" and len([p for p in calls if p == "/api/status"]) == 2:
                return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_WITH_T1001, "error": None}
            if path == "/api/status":
                return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}
            return {
                "ok": True,
                "http_status": 200,
                "elapsed_ms": 1.0,
                "json": {"manual_command_executed": path == "/api/base/manual", "robot_control_executed": path == "/api/base/stop"},
                "error": None,
            }

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(
                [
                    "--execute-motion",
                    "--confirm-physical-clearance",
                    "--operator-report-json",
                    self.write_operator_report(temp_dir),
                ]
            )
            result = runner.run_acceptance(args)

        self.assertEqual(calls, ["/api/status", "/api/base/manual", "/api/base/stop", "/api/status"])
        self.assertEqual(result["post_t1001_feedback_status"], "observed")
        self.assertEqual(result["acceptance_verdict"]["status"], "motion_posted_with_t1001")
        self.assertTrue(result["acceptance_verdict"]["t1001_or_ack_observed"])
        self.assertFalse(result["acceptance_verdict"]["safe_to_control"])
        self.assertFalse(result["acceptance_verdict"]["hil_pass"])

    def test_execute_mode_blocks_before_motion_when_initial_status_fails(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            # 初始 status 不通时不能为了推进而 POST manual。
            calls.append((method, path))
            return {"ok": False, "http_status": None, "elapsed_ms": 3.0, "json": None, "error": {"type": "TimeoutError", "message": "timeout"}}

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(
                [
                    "--execute-motion",
                    "--confirm-physical-clearance",
                    "--operator-report-json",
                    self.write_operator_report(temp_dir),
                ]
            )
            result = runner.run_acceptance(args)

        self.assertEqual(calls, [("GET", "/api/status")])
        self.assertIsNone(result["manual_request"])
        self.assertEqual(result["acceptance_verdict"]["status"], "blocked_before_motion")
        self.assertEqual(result["acceptance_verdict"]["failed_step"], "status_request")
        self.assertTrue(result["acceptance_verdict"]["fail_closed"])

    def test_execute_mode_keeps_fail_closed_when_stop_fails(self) -> None:
        calls: list[str] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            # stop 失败时仍会追加 post-status，但 verdict 不能写成通过。
            calls.append(path)
            if path == "/api/status":
                return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}
            if path == "/api/base/manual":
                return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": {"manual_command_executed": True}, "error": None}
            return {"ok": False, "http_status": 500, "elapsed_ms": 1.0, "json": {"error": "stop failed"}, "error": {"type": "HTTPError", "message": "500"}}

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(
                [
                    "--execute-motion",
                    "--confirm-physical-clearance",
                    "--operator-report-json",
                    self.write_operator_report(temp_dir),
                ]
            )
            result = runner.run_acceptance(args)

        self.assertEqual(calls, ["/api/status", "/api/base/manual", "/api/base/stop", "/api/status"])
        self.assertEqual(result["acceptance_verdict"]["status"], "motion_posted_without_ack")
        self.assertEqual(result["acceptance_verdict"]["failed_step"], "stop_request")
        self.assertTrue(result["acceptance_verdict"]["fail_closed"])
        self.assertFalse(result["acceptance_verdict"]["safe_to_control"])

    def test_operator_report_json_path_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = self.write_operator_report(temp_dir)
            args = runner.parse_args(["--dry-run", "--operator-report-json", report_path, "--once-json"])

            with mock.patch.object(runner, "http_json", return_value={"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}) as fake_http:
                result = runner.run_acceptance(args)

        fake_http.assert_called_once()
        self.assertEqual(result["operator_report_status"], "ready_for_review")
        self.assertTrue(result["operator_report"]["operator_present"])
        self.assertTrue(result["operator_report"]["physical_clearance_confirmed"])
        self.assertTrue(result["operator_report"]["emergency_stop_ready"])
        self.assertEqual(result["acceptance_verdict"]["status"], "dry_run_only")
        self.assertEqual(result["acceptance_verdict"]["operator_report_status"], "ready_for_review")

    def test_operator_report_json_stdin_is_normalized(self) -> None:
        args = runner.parse_args(["--dry-run", "--operator-report-json", "-", "--once-json"])
        stdin = io.StringIO(json.dumps({**COMPLETE_OPERATOR_REPORT, "operator_present": "yes", "observed_stop": "true"}))

        with mock.patch.object(sys, "stdin", stdin), mock.patch.object(
            runner,
            "http_json",
            return_value={"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None},
        ):
            result = runner.run_acceptance(args)

        self.assertEqual(result["operator_report_status"], "ready_for_review")
        self.assertTrue(result["operator_report"]["operator_present"])
        self.assertTrue(result["operator_report"]["observed_stop"])

    def test_incomplete_operator_report_is_machine_readable(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((method, path, payload))
            return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_PAYLOAD, "error": None}

        incomplete = {
            **COMPLETE_OPERATOR_REPORT,
            "emergency_stop_ready": False,
            "observed_stop": "unknown",
        }
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(
                [
                    "--execute-motion",
                    "--confirm-physical-clearance",
                    "--operator-report-json",
                    self.write_operator_report(temp_dir, incomplete),
                ]
            )
            result = runner.run_acceptance(args)

        self.assertEqual(calls, [("GET", "/api/status", None)])
        self.assertEqual(result["operator_report_status"], "unsafe_or_incomplete")
        self.assertIn("observed_stop", result["operator_report"]["normalization"]["missing_or_invalid_fields"])
        self.assertIn("emergency_stop_ready", result["operator_report"]["normalization"]["unsafe_fields"])
        self.assertEqual(result["acceptance_verdict"]["status"], "blocked_before_motion")
        self.assertEqual(result["acceptance_verdict"]["failed_step"], "operator_report_missing_or_incomplete")
        self.assertIsNone(result["manual_request"])

    def test_execute_mode_missing_operator_report_is_not_hil(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((method, path, payload))
            return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_WITH_T1001, "error": None}

        with mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(["--execute-motion", "--confirm-physical-clearance"])
            result = runner.run_acceptance(args)

        self.assertEqual(calls, [("GET", "/api/status", None)])
        self.assertEqual(result["operator_report_status"], "missing")
        self.assertEqual(result["acceptance_verdict"]["failed_step"], "operator_report_missing_or_incomplete")
        self.assertFalse(result["acceptance_verdict"]["hil_pass"])
        self.assertFalse(result["acceptance_verdict"]["safe_to_control"])
        self.assertIsNone(result["manual_request"])

    def test_dry_run_with_complete_operator_report_still_sends_no_commands(self) -> None:
        calls: list[tuple[str, str, dict[str, object] | None]] = []

        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            calls.append((method, path, payload))
            return {"ok": True, "http_status": 200, "elapsed_ms": 1.0, "json": STATUS_WITH_T1001, "error": None}

        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(["--dry-run", "--operator-report-json", self.write_operator_report(temp_dir), "--once-json"])
            result = runner.run_acceptance(args)

        self.assertEqual(calls, [("GET", "/api/status", None)])
        self.assertEqual(result["operator_report_status"], "ready_for_review")
        self.assertEqual(result["acceptance_verdict"]["status"], "dry_run_only")
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertFalse(result["safe_to_control"])

    def test_dry_run_status_failure_keeps_dry_run_verdict(self) -> None:
        def fake_http(method: str, base_url: str, path: str, timeout_s: float, payload: dict[str, object] | None = None) -> dict[str, object]:
            # dry-run 网络失败只能说明没有采到 status，不能变成运动执行分支。
            return {"ok": False, "http_status": None, "elapsed_ms": 3.0, "json": None, "error": {"type": "TimeoutError", "message": "timeout"}}

        with mock.patch.object(runner, "http_json", side_effect=fake_http):
            args = runner.parse_args(["--dry-run", "--once-json"])
            result = runner.run_acceptance(args)

        self.assertEqual(result["acceptance_verdict"]["status"], "dry_run_only")
        self.assertEqual(result["acceptance_verdict"]["failed_step"], "status_request")
        self.assertTrue(result["acceptance_verdict"]["fail_closed"])
        self.assertFalse(result["sends_commands"])
        self.assertIsNone(result["manual_request"])

    def test_status_json_file_and_atomic_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            status_path = Path(temp_dir) / "status.json"
            output_path = Path(temp_dir) / "artifact.json"
            status_path.write_text(json.dumps(STATUS_PAYLOAD), encoding="utf-8")
            args = runner.parse_args(["--status-json", str(status_path), "--output", str(output_path), "--once-json"])

            with mock.patch.object(runner, "http_json") as fake_http:
                result = runner.run_acceptance(args)
                runner.write_output_atomic(str(output_path), result)

            fake_http.assert_not_called()
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(written["schema"], runner.SCHEMA)
            self.assertEqual(written["status_request"]["source"], "local_status_json")
            self.assertEqual(written["status_summary"]["base"]["port"], "/dev/ttyS5")
            self.assertEqual(written["acceptance_verdict"]["status"], "dry_run_only")


if __name__ == "__main__":
    unittest.main()

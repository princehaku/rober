#!/usr/bin/env python3
"""O1 maintenance runner 的 fixture、schema 与 hostile-input 回归。"""

# 测试只运行本地 fixture/纯函数，绝不调用 SSH、systemd、UART 或 motion。
# 每个 hostile case 都验证 fail closed，而不是只覆盖 happy path。
# 被测脚本通过 importlib 从固定文件路径加载，避免依赖 PYTHONPATH。
# 临时目录由 unittest 管理，不污染 sprint artifacts。
# 危险安全字段必须逐个锁定为 false。
# 测试合同一：happy fixture 也必须保持五个安全字段为 false。
# 测试合同二：fixture 的 window count 必须为零。
# 测试合同三：live validator 必须拒绝 fixture window count。
# 测试合同四：raw counter bool 必须拒绝。
# 测试合同五：危险 truth 必须给出字段名。
# 测试合同六：无 observability 的 motion 必须拒绝。
# 测试合同七：motion 后缺 post-stop 必须拒绝。
# 测试合同八：retry 与 second motion 必须拒绝。
# 测试合同九：远端 marker 缺失必须拒绝。
# 测试合同十：远端 marker 重复必须拒绝。
# 测试合同十一：远端非 object JSON 必须拒绝。
# 测试合同十二：host 漂移必须在 SSH 前拒绝。
# 测试合同十三：port 漂移必须在 SSH 前拒绝。
# 测试合同十四：vendor hash 必须覆盖全部 plan 来源。
# 测试合同十五：instrumentation contract hash 必须稳定。

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# 固定 repo root，确保从任意 cwd 运行 targeted unittest 都一致。
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "onboard/scripts/o1_runtime_identity_raw_encoder_maintenance.py"
SPEC = importlib.util.spec_from_file_location("o1_maintenance", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MaintenanceRunnerTest(unittest.TestCase):
    """锁定 exactly-once、安全字段、fixture 与 transport parser。"""

    # helper 只创建最小合法 fixture；所有边界变体均由单个测试显式改写。
    def valid_fixture(self) -> dict:
        return {
            "attempt_id": "fixture-attempt-1",
            "authorization_id": "fixture-authorization-1",
            "raw_encoder_a": [10, 11],
            "raw_encoder_b": [20, 22],
            "t1001_samples": [
                {"frame": {"T": 1001, "L": 0, "R": 0, "encA": 10, "encB": 20}},
                {"frame": {"T": 1001, "L": 0, "R": 0, "encA": 11, "encB": 22}},
            ],
        }

    # 纯函数 artifact 必须保留真实 delta，但仍不是 HIL。
    def test_fixture_artifact_is_fail_closed(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        self.assertEqual(MODULE.SCHEMA, artifact["schema"])
        self.assertEqual(1, artifact["raw_counter_delta_a"])
        self.assertEqual(2, artifact["raw_counter_delta_b"])
        self.assertTrue(artifact["counter_feedback_observability_gate"])
        self.assertEqual(0, artifact["maintenance_window_count"])
        for key in MODULE.SAFETY_FALSE_FIELDS:
            self.assertIs(artifact[key], False)
        self.assertEqual([], MODULE.validate_artifact(artifact, live=False))

    # CLI pass fixture 必须稳定生成可 parse JSON。
    def test_fixture_cli_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            fixture_dir = temp_path / "fixture"
            fixture_dir.mkdir()
            (fixture_dir / "fixture.json").write_text(json.dumps(self.valid_fixture()))
            output = temp_path / "result.json"
            completed = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--mode", "fixture",
                    "--fixture-dir", str(fixture_dir),
                    "--output", str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            artifact = json.loads(output.read_text())
            self.assertEqual("fixture_complete", artifact["status"])
            self.assertTrue(artifact["service_restored"])

    # 缺 fixture 文件时 exit 4，不能静默生成默认 happy path。
    def test_fixture_cli_missing_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            completed = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--mode", "fixture",
                    "--fixture-dir", temp,
                    "--output", str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(4, completed.returncode)
            self.assertFalse(output.exists())

    # bool 在 Python 中是 int 子类；raw counter 必须显式拒绝 bool。
    def test_fixture_rejects_boolean_counter(self) -> None:
        fixture = self.valid_fixture()
        fixture["raw_encoder_a"] = [False, 1]
        with self.assertRaisesRegex(ValueError, "must_be_integers"):
            MODULE.fixture_artifact(fixture)

    # dangerous true 即使其它结构正确也必须出现在 validation errors。
    def test_validator_rejects_dangerous_truth(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["safe_to_control"] = True
        self.assertIn("dangerous_truth:safe_to_control", MODULE.validate_artifact(artifact, live=False))

    # exactly-once motion 不得在 observability false 时发生。
    def test_validator_rejects_motion_without_observability(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["nonzero_motion_invocation_count"] = 1
        artifact["counter_feedback_observability_gate"] = False
        artifact["post_stop_invocation_count"] = 1
        self.assertIn("motion_without_observability", MODULE.validate_artifact(artifact, live=False))

    # motion 后缺 post-stop 同样必须 fail closed。
    def test_validator_rejects_motion_without_post_stop(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["nonzero_motion_invocation_count"] = 1
        artifact["post_stop_invocation_count"] = 0
        self.assertIn("motion_without_post_stop", MODULE.validate_artifact(artifact, live=False))

    # retry/second motion 任一非零都违反本轮授权。
    def test_validator_rejects_retry_and_second_motion(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["retry_count"] = 1
        artifact["second_motion_count"] = 1
        self.assertIn("retry_or_second_motion_nonzero", MODULE.validate_artifact(artifact, live=False))

    # live artifact 必须是一个 maintenance window，fixture 的 0 不得冒充 live。
    def test_validator_distinguishes_fixture_from_live(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        self.assertIn("maintenance_window_count_not_one", MODULE.validate_artifact(artifact, live=True))

    # 远端 marker 必须恰好一次；重复 marker 可能来自拼接日志，必须拒绝。
    def test_remote_result_requires_exactly_one_marker(self) -> None:
        payload = {"schema": MODULE.SCHEMA}
        line = "O1_MAINTENANCE_JSON:" + json.dumps(payload)
        self.assertEqual(payload, MODULE.parse_remote_result("noise\n" + line + "\n"))
        with self.assertRaisesRegex(ValueError, "marker_count:2"):
            MODULE.parse_remote_result(line + "\n" + line)

    # 非 object JSON 不可进入 artifact pipeline。
    def test_remote_result_rejects_non_object(self) -> None:
        with self.assertRaisesRegex(ValueError, "not_object"):
            MODULE.parse_remote_result("O1_MAINTENANCE_JSON:[]")

    # 真实入口必须拒绝 host/port 漂移，且拒绝发生在 subprocess.run 之前。
    def test_ssh_target_is_frozen(self) -> None:
        parser = MODULE.build_parser()
        args = parser.parse_args([
            "--mode", "ssh-maintenance",
            "--ssh-host", "root@127.0.0.1",
            "--ssh-port", "22",
            "--authorization-id", "a",
            "--attempt-id", "b",
            "--output", "unused.json",
        ])
        with self.assertRaisesRegex(ValueError, "ssh_target_not_frozen"):
            MODULE.run_ssh_maintenance(args)

    # vendor basename 不允许碰撞，否则 hash map 会丢失 provenance。
    def test_vendor_hashes_cover_all_required_sources(self) -> None:
        hashes = MODULE.vendor_hashes(ROOT)
        self.assertEqual(len(MODULE.VENDOR_FILES), len(hashes))
        self.assertTrue(all(len(value) == 64 for value in hashes.values()))

    # instrumentation contract hash 必须稳定，供 live artifact 冻结。
    def test_instrumentation_contract_hash_is_stable(self) -> None:
        first = MODULE.instrumentation_source_hash()
        second = MODULE.instrumentation_source_hash()
        self.assertEqual(first, second)
        self.assertEqual(64, len(first))

    # 外层 py_compile 不会编译字符串内的远端程序，因此单独锁定语法。
    def test_embedded_remote_script_compiles(self) -> None:
        compile(MODULE.REMOTE_SCRIPT, "<o1-maintenance-remote>", "exec")

    # 已批准的新 identity 必须精确冻结，旧 v8 或临时 attempt 都不能进入 SSH。
    def test_live_identity_constants_match_approved_plan(self) -> None:
        self.assertEqual(
            "ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance",
            MODULE.EXPECTED_AUTHORIZATION_ID,
        )
        self.assertEqual(
            "o1-runtime-identity-raw-encoder-maintenance-attempt-1",
            MODULE.EXPECTED_ATTEMPT_ID,
        )

    # live validator 必须把恢复缺口作为错误，不能只检查 dangerous true。
    def test_live_validator_requires_restoration(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["maintenance_window_count"] = 1
        artifact["attempt_id"] = MODULE.EXPECTED_ATTEMPT_ID
        artifact["authorization_id"] = MODULE.EXPECTED_AUTHORIZATION_ID
        artifact["service_restored"] = False
        errors = MODULE.validate_artifact(artifact, live=True)
        self.assertIn("restoration_not_true:service_restored", errors)


if __name__ == "__main__":
    unittest.main()

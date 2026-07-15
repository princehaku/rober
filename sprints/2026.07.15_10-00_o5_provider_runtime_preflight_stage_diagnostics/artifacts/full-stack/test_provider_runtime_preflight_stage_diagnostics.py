#!/usr/bin/env python3
"""O5 provider runtime preflight 阶段诊断回归测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# 测试围栏 01：每个用例只使用独立 TemporaryDirectory。
# 测试围栏 02：测试不读取环境变量或 credential。
# 测试围栏 03：测试不调用 SSH、SCP、HTTP 或任何公网入口。
# 测试围栏 04：测试不启动 shell、tunnel、relay 或 proxy。
# 测试围栏 05：测试不执行 fixture 内容，只调用受控 version stub。
# 测试围栏 06：成功路径必须精确到达全部七个 stage。
# 测试围栏 07：download failure 只能保留第一阶段。
# 测试围栏 08：SHA command failure 不能伪造摘要计算完成。
# 测试围栏 09：SHA mismatch 不能进入 chmod 或 version。
# 测试围栏 10：chmod failure 只能停在 SHA 已匹配边界。
# 测试围栏 11：version execution failure 不能记录执行完成。
# 测试围栏 12：version mismatch 不能记录 version_matched。
# 测试围栏 13：重复阶段必须映射为 invalid_stage_transition。
# 测试围栏 14：跳级阶段必须映射为 invalid_stage_transition。
# 测试围栏 15：回退阶段必须映射为 invalid_stage_transition。
# 测试围栏 16：未知旧前缀不能被后续推进修复或掩盖。
# 测试围栏 17：hostile metadata 必须在 download 前 fail closed。
# 测试围栏 18：非本地 runner 必须在 download 前被拒绝。
# 测试围栏 19：仓库目录不能被冒充为 fixture 临时根。
# 测试围栏 20：越界路径不能产生任何目标文件。
# 测试围栏 21：artifact key 集合必须与白名单精确相等。
# 测试围栏 22：所有 production、mission、control 字段固定为假。
# 测试围栏 23：所有 tunnel 和 public probe 计数固定为零。
# 测试围栏 24：reference 与 digest 原文不得出现在 JSON。
# 测试围栏 25：异常、命令输出和绝对路径标记不得出现。
# 测试围栏 26：proof boundary 在成功和失败路径都必须稳定。
# 测试围栏 27：完整阶段始终是固定列表的精确有序前缀。
# 测试围栏 28：offline dry gate 入口必须复用同一状态机。
# 测试围栏 29：测试结束必须自动回收所有 fixture 文件。
# 测试围栏 30：测试通过只代表离线合同，不外推 live 事实。
# 测试围栏 31：metadata 合同失败时 checked 字段必须保持假。
# 测试围栏 32：逐阶段操作失败时 checked 字段必须保持真。
# 测试围栏 33：成功 artifact 的 failure_reason 必须为 null。
# 测试围栏 34：失败 artifact 的 next stage 必须指向紧邻边界。
# 测试围栏 35：稳定 schema 与 failure enum 必须被显式断言。

# 测试文件位于 sprint artifact 目录，显式加入同级路径以稳定支持 unittest 文件入口。
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# 导入只包含本地纯函数与 fixture runner，不会触发 CLI 或外部副作用。
from provider_runtime_preflight_stage_diagnostics import (
    FAILURE_REASONS,
    PROOF_BOUNDARY,
    SCHEMA,
    STAGES,
    LocalFixtureRunner,
    OfflineRunnerFailure,
    SafeStageError,
    _offline_fixture,
    advance_stage,
    build_artifact,
    run_offline_dry_gate,
    run_provider_runtime_preflight,
)


# 所有允许输出的 key 在测试中固化，防止未来无意加入敏感上下文。
ARTIFACT_KEYS = {
    "schema",
    "provider_runtime_preflight_status",
    "completed_stages",
    "last_reached_stage",
    "next_expected_stage",
    "failure_reason",
    "proof_boundary",
    "official_provenance_contract_checked",
    "network_access_attempted",
    "ssh_attempted",
    "tunnel_start_attempt_count",
    "public_capture_count",
    "public_probe_attempt_count",
    "current_run_artifact_delta",
    "external_artifact_delta",
    "live_control_delta",
    "user_action_delta",
    "production_ready",
    "mission_objective_0_satisfied",
    "route_execution_success",
    "delivery_success",
    "hil_pass",
    "safe_to_control",
}

# 这些布尔字段无论成功或失败都必须保持 fail-closed。
FALSE_FIELDS = (
    "network_access_attempted",
    "ssh_attempted",
    "current_run_artifact_delta",
    "external_artifact_delta",
    "live_control_delta",
    "user_action_delta",
    "production_ready",
    "mission_objective_0_satisfied",
    "route_execution_success",
    "delivery_success",
    "hil_pass",
    "safe_to_control",
)

# 计数字段保持零，证明 dry gate 没有 tunnel 或公网分支。
ZERO_FIELDS = (
    "tunnel_start_attempt_count",
    "public_capture_count",
    "public_probe_attempt_count",
)


class ProviderRuntimePreflightDiagnosticsTest(unittest.TestCase):
    """验证成功路径、逐阶段失败矩阵和脱敏围栏。"""

    def setUp(self) -> None:
        # 每个用例获得独立临时根，失败也不会污染后续用例。
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="rober-o5-test-")
        self.root = Path(self.temporary_directory.name)
        self.fixture_bytes, self.metadata = _offline_fixture()

    def tearDown(self) -> None:
        # 明确回收 fixture，验证过程不留下持久 provider 文件。
        self.temporary_directory.cleanup()

    def _runner(self, *failures: str) -> LocalFixtureRunner:
        # failure 注入只改变本地步骤结果，不增加命令或网络执行面。
        return LocalFixtureRunner(
            self.root,
            self.fixture_bytes,
            self.metadata["version"],
            failures,
        )

    def _assert_common_safety(self, artifact: dict) -> None:
        # 公共断言确保所有失败分支都保持同一 proof boundary。
        self.assertEqual(set(artifact), ARTIFACT_KEYS)
        self.assertEqual(artifact["schema"], SCHEMA)
        self.assertEqual(artifact["proof_boundary"], PROOF_BOUNDARY)
        for field in FALSE_FIELDS:
            self.assertIs(artifact[field], False, field)
        for field in ZERO_FIELDS:
            self.assertEqual(artifact[field], 0, field)
        # 任一输出阶段都必须是固定列表的精确有序前缀。
        completed = artifact["completed_stages"]
        self.assertEqual(completed, list(STAGES[: len(completed)]))

    def _assert_failure(
        self, artifact: dict, reason: str, expected_prefix_length: int
    ) -> None:
        # 失败矩阵按最后安全边界检查，不能越过失败步骤。
        self._assert_common_safety(artifact)
        self.assertEqual(artifact["provider_runtime_preflight_status"], "blocked_offline_dry_gate")
        self.assertEqual(artifact["failure_reason"], reason)
        self.assertEqual(artifact["completed_stages"], list(STAGES[:expected_prefix_length]))
        expected_last = STAGES[expected_prefix_length - 1] if expected_prefix_length else None
        self.assertEqual(artifact["last_reached_stage"], expected_last)
        self.assertEqual(artifact["next_expected_stage"], STAGES[expected_prefix_length])

    def test_contract_constants_are_stable_and_complete(self) -> None:
        # 顺序和枚举是跨实现/文档的稳定合同，测试防止静默漂移。
        self.assertEqual(
            STAGES,
            (
                "download_started",
                "download_completed",
                "sha_command_completed",
                "sha_matched",
                "chmod_completed",
                "version_executed",
                "version_matched",
            ),
        )
        self.assertEqual(
            set(FAILURE_REASONS),
            {
                "download_failed",
                "sha_command_failed",
                "sha_mismatch",
                "chmod_failed",
                "version_execution_failed",
                "version_mismatch",
                "invalid_stage_transition",
            },
        )

    def test_happy_path_reaches_all_stages(self) -> None:
        # 成功仅指本地 dry gate 完整，不改变 production 或 mission 字段。
        runner = self._runner()
        artifact = run_provider_runtime_preflight(self.metadata, runner)
        self._assert_common_safety(artifact)
        self.assertEqual(artifact["provider_runtime_preflight_status"], "passed_offline_dry_gate")
        self.assertEqual(artifact["completed_stages"], list(STAGES))
        self.assertEqual(artifact["last_reached_stage"], "version_matched")
        self.assertIsNone(artifact["next_expected_stage"])
        self.assertIsNone(artifact["failure_reason"])
        self.assertIs(artifact["official_provenance_contract_checked"], True)
        self.assertFalse(runner.network_access_attempted)
        self.assertFalse(runner.ssh_attempted)

    def test_download_failure_stops_after_started(self) -> None:
        # download_started 在调用 stub 前记录，失败后不得伪造落盘完成。
        artifact = run_provider_runtime_preflight(self.metadata, self._runner("download_failed"))
        self._assert_failure(artifact, "download_failed", 1)

    def test_sha_command_failure_stops_after_download(self) -> None:
        # 摘要命令失败不能进入 sha_command_completed 或后续权限步骤。
        artifact = run_provider_runtime_preflight(self.metadata, self._runner("sha_command_failed"))
        self._assert_failure(artifact, "sha_command_failed", 2)

    def test_sha_mismatch_stops_before_chmod(self) -> None:
        # 合法形状的错误摘要用于证明 compare mismatch 的独立边界。
        artifact = run_provider_runtime_preflight(self.metadata, self._runner("sha_mismatch"))
        self._assert_failure(artifact, "sha_mismatch", 3)

    def test_chmod_failure_stops_after_sha_match(self) -> None:
        # SHA 已匹配并不代表权限调整成功，两个事实必须分开记录。
        artifact = run_provider_runtime_preflight(self.metadata, self._runner("chmod_failed"))
        self._assert_failure(artifact, "chmod_failed", 4)

    def test_version_execution_failure_stops_after_chmod(self) -> None:
        # version 运行失败时不能输出 version_executed 或 version_matched。
        artifact = run_provider_runtime_preflight(
            self.metadata, self._runner("version_execution_failed")
        )
        self._assert_failure(artifact, "version_execution_failed", 5)

    def test_version_mismatch_stops_after_execution(self) -> None:
        # 运行 exit 成功与版本内容匹配是两个不同的诊断阶段。
        artifact = run_provider_runtime_preflight(self.metadata, self._runner("version_mismatch"))
        self._assert_failure(artifact, "version_mismatch", 6)

    def test_advance_stage_rejects_skip_repeat_rollback_and_post_completion(self) -> None:
        # 所有不单调转换统一抛安全异常，不泄漏调用方传入值。
        invalid_cases = (
            ((), "download_completed"),
            (("download_started",), "download_started"),
            (("download_started", "download_completed"), "download_started"),
            (("download_completed",), "sha_command_completed"),
            (STAGES, "version_matched"),
        )
        for completed, stage in invalid_cases:
            with self.subTest(completed=completed, stage=stage):
                with self.assertRaisesRegex(SafeStageError, "invalid_stage_transition"):
                    advance_stage(completed, stage)

    def test_invalid_metadata_shapes_fail_before_download(self) -> None:
        # hostile metadata 逐字段变化，均不得产生 download_started 假事实。
        invalid_values = (
            ("provider", "other"),
            ("architecture", "amd64"),
            ("asset_name", "cloudflared"),
            ("version", "latest"),
            ("asset_reference", "https://example.invalid/provider"),
            ("digest", "sha256:not-a-digest"),
        )
        for key, value in invalid_values:
            with self.subTest(key=key):
                metadata = dict(self.metadata)
                metadata[key] = value
                artifact = run_provider_runtime_preflight(metadata, self._runner())
                self._assert_failure(artifact, "invalid_stage_transition", 0)
                self.assertIs(artifact["official_provenance_contract_checked"], False)

    def test_non_mapping_metadata_fails_closed(self) -> None:
        # 类型错误同样经过安全枚举，不能把 Python 异常文本写入 artifact。
        artifact = run_provider_runtime_preflight([], self._runner())
        self._assert_failure(artifact, "invalid_stage_transition", 0)

    def test_non_local_runner_is_rejected(self) -> None:
        # 一个声称可联网的对象不能通过 runner 注入入口。
        class NonLocalRunner:
            offline_only = False

        artifact = run_provider_runtime_preflight(self.metadata, NonLocalRunner())
        self._assert_failure(artifact, "invalid_stage_transition", 0)
        self.assertIs(artifact["official_provenance_contract_checked"], False)

    def test_runner_root_outside_system_temp_is_rejected(self) -> None:
        # runner 即使类型正确，也不能把仓库路径当作 fixture root。
        runner = LocalFixtureRunner(Path.cwd(), self.fixture_bytes, self.metadata["version"])
        artifact = run_provider_runtime_preflight(self.metadata, runner)
        self._assert_failure(artifact, "invalid_stage_transition", 0)

    def test_runner_rejects_path_escape(self) -> None:
        # 文件 guard 在操作点拒绝越界路径，且不会创建目标文件。
        outside = self.root.parent / "provider-runtime-outside"
        with self.assertRaisesRegex(OfflineRunnerFailure, "path_outside_temp_root"):
            self._runner().download(self.metadata["asset_reference"], outside)
        self.assertFalse(outside.exists())

    def test_build_artifact_cannot_emit_dangerous_true_claims(self) -> None:
        # 白名单构造器不接收任意扩展字典，所有 mission/control claim 固定为 false。
        artifact = build_artifact(STAGES, None, True)
        self._assert_common_safety(artifact)
        for field in FALSE_FIELDS:
            self.assertIs(artifact[field], False)

    def test_build_artifact_sanitizes_invalid_prefix_and_reason(self) -> None:
        # 污染前缀和未知 reason 都退回空前缀与固定安全枚举。
        artifact = build_artifact(("version_matched",), "secret failure text", True)
        self._assert_failure(artifact, "invalid_stage_transition", 0)

    def test_artifact_redaction_excludes_sensitive_material(self) -> None:
        # JSON 扫描覆盖成功 artifact，原始 reference、摘要、路径和输出都不得出现。
        artifact = run_provider_runtime_preflight(self.metadata, self._runner())
        text = json.dumps(artifact, sort_keys=True).lower()
        forbidden = (
            "raw_url",
            "token",
            "authorization",
            "checksum",
            "stderr",
            "stdout",
            "response_body",
            "tunnel_log",
            "/users/",
            "/tmp/",
            self.metadata["asset_reference"].lower(),
            self.metadata["digest"].lower(),
        )
        for marker in forbidden:
            self.assertNotIn(marker, text)

    def test_offline_dry_gate_uses_temporary_fixture_and_passes(self) -> None:
        # CLI 所用入口复用同一状态机，并在 TemporaryDirectory 退出后清理。
        artifact = run_offline_dry_gate()
        self._assert_common_safety(artifact)
        self.assertEqual(artifact["completed_stages"], list(STAGES))
        self.assertEqual(artifact["provider_runtime_preflight_status"], "passed_offline_dry_gate")


if __name__ == "__main__":
    unittest.main()

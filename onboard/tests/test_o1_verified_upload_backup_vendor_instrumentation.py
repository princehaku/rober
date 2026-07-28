#!/usr/bin/env python3
"""O1 verified upload/backup/vendor instrumentation runner 离线回归。"""

# 测试合同 001：全部测试仅执行本地纯函数、fixture 或临时 patch。
# 测试合同 002：测试绝不调用 SSH、systemd、UART、PlatformIO upload。
# 测试合同 003：fixture 即使 gates 为真也保持全部安全字段为 false。
# 测试合同 004：fixture runner count 为零，不能冒充 live。
# 测试合同 005：缺 fixture 时 exit 4 且不生成伪 artifact。
# 测试合同 006：危险字段 true 必须被 validator 指名拒绝。
# 测试合同 007：bool count 必须被拒绝，不能利用 Python int 子类行为。
# 测试合同 008：任一 gate 红时 build/flash/rollback 必须全零。
# 测试合同 009：build 或 flash 必须同时依赖 U/B/V-prebuild。
# 测试合同 010：diagnostic flash 必须绑定 exactly-one rollback。
# 测试合同 011：flash 还必须绑定 build provenance。
# 测试合同 012：remote marker 必须恰好一个且 JSON 必须为 object。
# 测试合同 013：patch 必须只修改 canonical `ugv_advance.h`。
# 测试合同 014：patch 必须加入七个计划字段并保留既有字段。
# 测试合同 015：patch 禁止 T=900、motor control 与 setGoalSpeed。
# 测试合同 016：toolchain lock 必须无重复 key、无缺项。
# 测试合同 017：PlatformIO platform/board/framework 必须与 lock 对齐。
# 测试合同 018：vendor hash 必须覆盖 Product 指定的全部来源。
# 测试合同 019：远端脚本字符串必须单独 compile，外层 py_compile 不足够。
# 测试合同 020：live host、port、authorization、attempt 必须冻结。
# 测试合同 021：CLI 必须要求 strict-no-motion 与 conditional gate 开关。
# 测试合同 022：backup export 必须校验 hash 后才允许落盘。
# 测试合同 023：backup export 只写 output 同目录的固定 basename。
# 测试合同 024：REMOTE_SCRIPT 不得包含 motion JSON 或 T=900 JSON。
# 测试合同 025：exactly-once counter 名称必须完整进入 live artifact。
# 测试合同 026：live validator 必须要求 service/holder/final stop 三项。
# 测试合同 027：run-owned residual 必须显式 false。
# 测试合同 028：测试临时目录由 unittest 管理，不污染 sprint artifacts。
# 测试合同 029：技术注释使用中文并解释安全原因。
# 测试合同 030：本测试不调整 OKR、不创建 closeout 文档。
# 测试合同 031：Gate U fixture 不替代 current stable alias。
# 测试合同 032：Gate B fixture 不替代 current flash bytes。
# 测试合同 033：Gate V fixture 不替代现场 tool version。
# 测试合同 034：patch dry-run 不修改 docs/vendor。
# 测试合同 035：patch apply 只发生在 unittest 临时 copy。
# 测试合同 036：backup bytes 只写 unittest 临时目录。
# 测试合同 037：remote compile 不执行 embedded source。
# 测试合同 038：parser test 不调用 run_ssh_maintenance。
# 测试合同 039：marker hostile test 不输出 artifact。
# 测试合同 040：live validator test 只构造内存 dict。
# 测试合同 041：vendor hash test 对本地来源只读。
# 测试合同 042：local contract test 对 config/patch/lock 只读。
# 测试合同 043：测试不运行 PlatformIO build。
# 测试合同 044：测试不运行 esptool。
# 测试合同 045：测试不消耗 live attempt。

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# 从固定路径加载被测 runner，避免依赖 PYTHONPATH。
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "onboard/scripts/o1_verified_upload_backup_vendor_instrumentation.py"
SPEC = importlib.util.spec_from_file_location("o1_verified_instrumentation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerifiedInstrumentationRunnerTest(unittest.TestCase):
    """锁定 provenance、gate ordering、exactly-once 与恢复合同。"""

    # 最小 fixture 只表达离线 gate contract，不包含 hardware identity。
    def valid_fixture(self) -> dict:
        return {
            "attempt_id": "fixture-attempt",
            "authorization_id": "fixture-authorization",
            "gate_u": True,
            "gate_b": True,
            "gate_v_prebuild": True,
            "build_provenance_green": True,
        }

    # 所有 gates true 也不能把 fixture 提升为 HIL 或 OKR credit。
    def test_fixture_artifact_is_fail_closed(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        self.assertEqual(MODULE.SCHEMA, artifact["schema"])
        self.assertEqual(0, artifact["runner_invocation_count"])
        self.assertEqual(0, artifact["current_run_artifact_delta"])
        for field in MODULE.SAFETY_FALSE_FIELDS:
            self.assertIs(artifact[field], False)
        self.assertEqual([], MODULE.validate_artifact(artifact, live=False))

    # Engineer 验收使用的 fixture CLI 必须生成稳定 JSON。
    def test_fixture_cli_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            fixture_dir = temp_path / "fixture"
            fixture_dir.mkdir()
            (fixture_dir / "fixture.json").write_text(json.dumps(self.valid_fixture()))
            output = temp_path / "result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mode",
                    "fixture",
                    "--fixture-dir",
                    str(fixture_dir),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual("fixture_complete", json.loads(output.read_text())["status"])

    # 缺 fixture 不允许产生带默认 happy path 的结果。
    def test_fixture_cli_missing_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mode",
                    "fixture",
                    "--fixture-dir",
                    temp,
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(4, completed.returncode)
            self.assertFalse(output.exists())

    # 危险字段 true 必须独立显示，不能被其它正确字段抵消。
    def test_validator_rejects_dangerous_truth(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["safe_to_control"] = True
        errors = MODULE.validate_artifact(artifact, live=False)
        self.assertIn("dangerous_truth:safe_to_control", errors)

    # bool 是 int 子类，因此 count 类型要显式排除 bool。
    def test_validator_rejects_boolean_count(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["retry_count"] = False
        errors = MODULE.validate_artifact(artifact, live=False)
        self.assertIn("invalid_count_type:retry_count", errors)

    # Gate U 红时任何 build 都违反 prebuild ordering。
    def test_validator_rejects_build_when_gate_red(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["gate_u"] = False
        artifact["instrumentation_build_count"] = 1
        errors = MODULE.validate_artifact(artifact, live=False)
        self.assertIn("build_or_flash_without_all_prebuild_gates", errors)
        self.assertIn("gate_red_but_count_nonzero:instrumentation_build_count", errors)

    # diagnostic flash 必须有 exactly-one rollback 和 build provenance。
    def test_validator_rejects_flash_without_rollback_or_provenance(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact["instrumentation_build_count"] = 1
        artifact["diagnostic_flash_count"] = 1
        artifact["rollback_flash_count"] = 0
        artifact["build_provenance_green"] = False
        errors = MODULE.validate_artifact(artifact, live=False)
        self.assertIn("diagnostic_flash_without_exactly_one_rollback", errors)
        self.assertIn("diagnostic_flash_without_build_provenance", errors)

    # marker 重复或非 object 都不能进入 artifact pipeline。
    def test_remote_marker_is_exactly_once_object(self) -> None:
        line = (
            "O1_VERIFIED_UPLOAD_BACKUP_VENDOR_INSTRUMENTATION_JSON:"
            + json.dumps({"schema": MODULE.SCHEMA})
        )
        parsed = MODULE.parse_remote_result("noise\n" + line + "\n")
        self.assertEqual(MODULE.SCHEMA, parsed["schema"])
        with self.assertRaisesRegex(ValueError, "marker_count:2"):
            MODULE.parse_remote_result(line + "\n" + line)
        with self.assertRaisesRegex(ValueError, "not_object"):
            MODULE.parse_remote_result(
                "O1_VERIFIED_UPLOAD_BACKUP_VENDOR_INSTRUMENTATION_JSON:[]"
            )

    # patch contract 只允许 additive feedback 字段。
    def test_patch_contract_is_additive_and_single_target(self) -> None:
        root = (
            ROOT
            / "onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic"
        )
        text = (root / "patches/additive_diagnostic.patch").read_text()
        self.assertEqual([], MODULE.validate_patch_contract(text))

    # 实际 canonical source copy 必须能 cleanly 应用 patch。
    def test_patch_applies_to_canonical_vendor_source(self) -> None:
        source = ROOT / "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9"
        patch = (
            ROOT
            / "onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic"
            / "patches/additive_diagnostic.patch"
        )
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "vendor"
            shutil.copytree(source, target)
            # 模拟远端 portable 路径，只在 temp copy 统一 vendor CRLF。
            patch_target = target / "ugv_advance.h"
            patch_target.write_bytes(
                patch_target.read_bytes().replace(b"\r\n", b"\n")
            )
            completed = subprocess.run(
                [
                    "patch",
                    "--batch",
                    "--forward",
                    "--ignore-whitespace",
                    "-p1",
                    "-i",
                    str(patch),
                ],
                cwd=target,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            changed = (target / "ugv_advance.h").read_text()
            for key in (
                "firmwareBuildId",
                "mainType",
                "moduleType",
                "encA",
                "encB",
                "speedGetA",
                "speedGetB",
            ):
                self.assertIn(f'jsonInfoHttp["{key}"]', changed)

    # lock 的版本字段必须完整且与 platformio.ini 对齐。
    def test_local_contract_has_pinned_toolchain(self) -> None:
        contract = MODULE.local_contract(ROOT)
        lock = contract["toolchain"]
        self.assertEqual("esp32dev", lock["board"])
        self.assertEqual("arduino", lock["framework"])
        self.assertRegex(lock["platformio_core"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(lock["esptool"], r"^\d+\.\d+\.\d+$")

    # 所有 Product 指定来源都必须进入 hash map。
    def test_vendor_hashes_cover_required_sources(self) -> None:
        hashes = MODULE.vendor_hashes(ROOT)
        self.assertEqual(set(MODULE.VENDOR_FILES), set(hashes))
        self.assertTrue(all(len(value) == 64 for value in hashes.values()))

    # 外层 py_compile 不会编译字符串中的 remote runner，所以单独锁定。
    def test_embedded_remote_script_compiles(self) -> None:
        compile(MODULE.REMOTE_SCRIPT, "<o1-verified-instrumentation-remote>", "exec")

    # 授权 identity 必须与 planning docs 完全一致。
    def test_live_identity_constants_match_plan(self) -> None:
        self.assertEqual("root@192.168.1.11", MODULE.EXPECTED_HOST)
        self.assertEqual(37878, MODULE.EXPECTED_PORT)
        self.assertEqual(
            "ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance",
            MODULE.EXPECTED_AUTHORIZATION_ID,
        )
        self.assertEqual(
            "o1-verified-upload-backup-vendor-instrumentation-attempt-1",
            MODULE.EXPECTED_ATTEMPT_ID,
        )

    # CLI 必须暴露且要求 strict-no-motion 与条件式 build/flash 开关。
    def test_cli_parses_frozen_live_flags(self) -> None:
        args = MODULE.build_parser().parse_args(
            [
                "--mode",
                "ssh-maintenance",
                "--ssh-host",
                MODULE.EXPECTED_HOST,
                "--ssh-port",
                str(MODULE.EXPECTED_PORT),
                "--authorization-id",
                MODULE.EXPECTED_AUTHORIZATION_ID,
                "--attempt-id",
                MODULE.EXPECTED_ATTEMPT_ID,
                "--strict-no-motion",
                "--allow-exactly-one-diagnostic-build-flash-after-all-gates",
                "--output",
                "unused.json",
            ]
        )
        self.assertTrue(args.strict_no_motion)
        self.assertTrue(
            args.allow_exactly_one_diagnostic_build_flash_after_all_gates
        )

    # backup export hash 不一致时必须拒绝，不能保存不可信 rollback image。
    def test_backup_export_requires_matching_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            payload = b"current-flash-backup-fixture"
            result = {
                "_backup_export_b64": base64.b64encode(payload).decode(),
                "backup_manifest": {"sha256": "0" * 64},
            }
            with self.assertRaisesRegex(ValueError, "hash_mismatch"):
                MODULE.persist_backup_export(output, result)
            self.assertFalse((output.parent / "current_flash_backup.bin").exists())

    # 正确 hash 才允许保存固定 basename，并回写 local artifact provenance。
    def test_backup_export_persists_verified_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            payload = b"current-flash-backup-fixture"
            digest = hashlib.sha256(payload).hexdigest()
            result = {
                "_backup_export_b64": base64.b64encode(payload).decode(),
                "backup_manifest": {"sha256": digest},
            }
            MODULE.persist_backup_export(output, result)
            backup = output.parent / "current_flash_backup.bin"
            self.assertEqual(payload, backup.read_bytes())
            self.assertEqual(digest, result["backup_manifest"]["local_artifact_sha256"])

    # embedded remote source 不得包含具体 motion/T900 JSON payload。
    def test_remote_script_has_no_motion_or_t900_json(self) -> None:
        self.assertNotIn('{"T":900', MODULE.REMOTE_SCRIPT)
        self.assertNotIn('{"T":11,"L":164', MODULE.REMOTE_SCRIPT)
        self.assertNotIn("/cmd_vel", MODULE.REMOTE_SCRIPT)
        self.assertNotIn("/api/base/manual", MODULE.REMOTE_SCRIPT)

    # live validator 需要三项恢复与无 residual。
    def test_live_validator_requires_restoration(self) -> None:
        artifact = MODULE.fixture_artifact(self.valid_fixture())
        artifact.update(
            {
                "runner_invocation_count": 1,
                "attempt_count": 1,
                "inventory_invocation_count": 1,
                "pre_stop_invocation_count": 1,
                "final_stop_verification_count": 1,
                "attempt_id": MODULE.EXPECTED_ATTEMPT_ID,
                "authorization_id": MODULE.EXPECTED_AUTHORIZATION_ID,
                "service_restored": False,
            }
        )
        errors = MODULE.validate_artifact(artifact, live=True)
        self.assertIn("restoration_not_true:service_restored", errors)


if __name__ == "__main__":
    unittest.main()

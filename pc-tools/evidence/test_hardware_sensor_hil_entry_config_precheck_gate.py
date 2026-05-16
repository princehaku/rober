#!/usr/bin/env python3
"""hardware_sensor_hil_entry_config_precheck gate 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_hil_entry_config_precheck_gate as gate  # noqa: E402


# 测试约束 01：测试 fixture 只表达 future config shape，不表达真实硬件存在。
# 测试约束 02：ready 测试必须同时断言 schema、boundary 和 not_proven。
# 测试约束 03：ready 测试必须断言 delivery_success=false，避免成功文案漂移。
# 测试约束 04：ready 测试必须断言 primary_actions_enabled=false，避免控制放行。
# 测试约束 05：默认样例测试只证明 PC gate 可运行，不证明 HIL。
# 测试约束 06：缺 config 测试必须使用 --no-default-sample 等价路径。
# 测试约束 07：sensor count 缺口必须 fail closed，防止单一 SKU 写死。
# 测试约束 08：ToF channel count 缺口必须 fail closed，防止产品目标伪装事实。
# 测试约束 09：thresholds 缺口必须 fail closed，防止近场安全没有阈值。
# 测试约束 10：frame IDs 缺口必须 fail closed，防止 launch 隐式默认 frame。
# 测试约束 11：safety policy 缺口必须 fail closed，防止 warn-only 放行。
# 测试约束 12：evidence refs 缺口必须 fail closed，防止无材料引用进入 HIL entry。
# 测试约束 13：unsupported schema 必须 fail closed，防止错误 artifact 被消费。
# 测试约束 14：success claim 必须 fail closed，防止 HIL/delivery 成功断言泄漏。
# 测试约束 15：unsafe raw copy 必须 fail closed，防止串口/topic/raw JSON 泄漏。
# 测试约束 16：测试用临时目录，避免污染真实 sprint evidence。
# 测试约束 17：测试不读取 ROS graph，保持 dependency-free。
# 测试约束 18：测试不访问串口，保持 Docker-only 可运行。
# 测试约束 19：测试不访问网络，避免把外部可达性当证据。
# 测试约束 20：测试不检查真实文件存在，因为 refs 是材料引用。
# 测试约束 21：测试 fixture 中的 frame 只是参数名，不代表 TF 已发布。
# 测试约束 22：测试 fixture 中的 threshold 只是配置值，不代表安全通过。
# 测试约束 23：测试 fixture 中的 evidence refs 只是安全引用，不代表材料已验收。
# 测试约束 24：测试 fixture 中的 owner_handoff 是人工动作，不是机器人动作。
# 测试约束 25：测试必须覆盖 summary safe_copy，保证 mobile/diagnostics 可读。
# 测试约束 26：测试必须覆盖 boundary_note，保证 rg 可见 delivery_success=false。
# 测试约束 27：测试必须覆盖 not_proven 列表，避免 ready 被误解成 pass。
# 测试约束 28：测试必须覆盖 exact status，方便 Product closeout 引用。
# 测试约束 29：测试必须覆盖 exact schema，方便 Robot consumer 做白名单。
# 测试约束 30：测试必须覆盖 exact evidence boundary，避免证据边界漂移。
# 测试约束 31：测试中的 unsafe copy 同时包含 serial 和 control topic。
# 测试约束 32：测试中的 success claim 同时包含 delivery 与 HIL 断言。
# 测试约束 33：测试中的 missing refs 使用 placeholder，覆盖占位符阻断。
# 测试约束 34：测试中的 weak policy 使用 warn_only，覆盖非 fail-closed 阻断。
# 测试约束 35：测试中的 ToF count 为 0，覆盖无效 numeric 阻断。
# 测试约束 36：测试不使用 mock 框架，降低 dependency 和维护成本。
# 测试约束 37：测试可由 `python3 -m unittest` 直接运行。
# 测试约束 38：测试输出失败时定位到具体 contract 缺口。
# 测试约束 39：测试保持 hardware worker 范围，不触碰 Robot/mobile 文件。
# 测试约束 40：测试不更新 OKR，因为它只证明 software proof gate。
# 测试约束 41：测试不检查真实 vendor PDF 内容，因为本 gate 只引用 source boundary。
# 测试约束 42：测试不模拟真实 ToF 数据，因为本轮只检查 config 参数化。
# 测试约束 43：测试不模拟真实 LiDAR scan，因为本轮不声明 sensor driver 可用。
# 测试约束 44：测试不模拟 TF tree，因为 frame IDs 只是 future config 字段。
# 测试约束 45：测试不模拟 phone panel，因为 Full-stack worker 单独负责 UI 消费。
# 测试约束 46：测试保留英文字段名断言，保护 Robot/mobile JSON contract。


def complete_config() -> dict:
    # fixture 是未来 HIL-entry 配置样本，不代表真实 LiDAR/ToF 已采购或 HIL 通过。
    return {
        "schema": "trashbot.hardware_sensor_hil_entry_config_precheck.v1",
        "sensor_config": {
            "sensor_count": 3,
            "tof_channel_count": 4,
            "sensors": [
                {"role": "2d_lidar", "count": 1},
                {"role": "tof", "count": 4},
                {"role": "monocular", "count": 1},
            ],
        },
        "thresholds": {
            "near_field_safety_m": 0.35,
            "confidence_min": 0.7,
            "validation_min_observations": 3,
        },
        "frame_ids": {
            "sensor_frame": "sensor_array_frame",
            "base_frame": "base_link",
            "mount_or_calibration_frame": "sensor_mount_calibration_frame",
        },
        "safety_policy": {
            "mode": "fail_closed",
            "missing_config_action": "block_primary_actions",
            "missing_evidence_action": "block_hil_entry",
            "primary_actions_enabled": False,
        },
        "evidence_refs": {
            "source": "source_ref.md",
            "procurement": "procurement_ref.md",
            "install_wiring": "install_wiring_ref.md",
            "power": "power_budget_ref.md",
            "calibration": "calibration_ref.md",
            "hil_entry": "hil_entry_ref.md",
        },
        "owner_handoff": [
            {"owner": "Hardware Infra Engineer", "action": "review refs before bench/HIL entry"},
        ],
    }


class HardwareSensorHilEntryConfigPrecheckGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，避免污染 sprint evidence 目录。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_complete_config_outputs_not_proven_summary(self):
        with tempfile.TemporaryDirectory() as td:
            config = self.write_json(Path(td), "config.json", complete_config())
            artifact, summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(config)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_hil_entry_config_precheck.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate",
        )
        self.assertEqual(artifact["overall_status"], "ready_for_hardware_sensor_hil_entry_config_precheck_not_proven")
        self.assertEqual(artifact["parameterization_checks"]["sensor count"]["sensor count"], 3)
        self.assertEqual(artifact["parameterization_checks"]["sensor count"]["tof_channel_count"], 4)
        self.assertEqual(summary["threshold_summary"]["thresholds"]["near_field_safety_m"], 0.35)
        self.assertEqual(summary["frame_id_summary"]["frame IDs"]["base_frame"], "base_link")
        self.assertEqual(summary["safety_policy_summary"]["safety policy"]["mode"], "fail_closed")
        self.assertIn("real_sensor_hil_entry_pass", artifact["not_proven"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("delivery_success=false", summary["boundary_note"])

    def test_default_sample_runs_without_hardware_and_stays_not_proven(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck()

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["config_ref"], "builtin_default_sample_not_hardware_evidence")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["safe_copy"]["delivery_success"])
        self.assertFalse(summary["safe_copy"]["primary_actions_enabled"])

    def test_missing_config_can_fail_closed_when_default_disabled(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(
            None,
            use_default_sample=False,
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_hardware_sensor_hil_entry_config")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_sensor_count_and_tof_channel_count_must_be_parameterized(self):
        payload = complete_config()
        del payload["sensor_config"]["sensor_count"]
        payload["sensor_config"]["tof_channel_count"] = 0
        with tempfile.TemporaryDirectory() as td:
            config = self.write_json(Path(td), "config.json", payload)
            artifact, _summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_hardware_sensor_hil_entry_config_parameterization")
        self.assertIn("sensor_config.sensor_count", artifact["missing_config"])
        self.assertIn("sensor_config.tof_channel_count", artifact["missing_config"])

    def test_thresholds_frame_ids_and_safety_policy_are_required(self):
        payload = complete_config()
        del payload["thresholds"]["near_field_safety_m"]
        payload["frame_ids"]["mount_or_calibration_frame"] = "TBD"
        payload["safety_policy"]["mode"] = "warn_only"
        with tempfile.TemporaryDirectory() as td:
            config = self.write_json(Path(td), "config.json", payload)
            artifact, _summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(config)

        self.assertEqual(exit_code, 2)
        self.assertIn("thresholds.near_field_safety_m", artifact["missing_config"])
        self.assertIn("frame_ids.mount_or_calibration_frame", artifact["missing_config"])
        self.assertIn("safety_policy.mode=fail_closed", artifact["missing_config"])

    def test_missing_evidence_refs_fail_closed(self):
        payload = complete_config()
        payload["evidence_refs"]["hil_entry"] = "unknown"
        with tempfile.TemporaryDirectory() as td:
            config = self.write_json(Path(td), "config.json", payload)
            artifact, summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_hardware_sensor_hil_entry_config_evidence_refs")
        self.assertIn("evidence_refs.hil_entry", summary["missing_evidence_refs"])

    def test_unsupported_schema_fails_closed(self):
        payload = complete_config()
        payload["schema"] = "trashbot.unsupported.v1"
        with tempfile.TemporaryDirectory() as td:
            config = self.write_json(Path(td), "config.json", payload)
            artifact, _summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_unsupported_hardware_sensor_hil_entry_config_schema")

    def test_success_claim_fails_closed(self):
        payload = complete_config()
        payload["note"] = "delivery_success=true and hil_pass=true"
        with tempfile.TemporaryDirectory() as td:
            config = self.write_json(Path(td), "config.json", payload)
            artifact, _summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_hardware_sensor_hil_entry_config_success_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_unsafe_raw_copy_fails_closed(self):
        payload = complete_config()
        payload["debug"] = "serial probe /dev/ttyUSB0 and /cmd_vel raw JSON"
        with tempfile.TemporaryDirectory() as td:
            config = self.write_json(Path(td), "config.json", payload)
            artifact, _summary, exit_code = gate.build_hardware_sensor_hil_entry_config_precheck(config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_unsafe_hardware_sensor_hil_entry_config_precheck_copy")


if __name__ == "__main__":
    unittest.main()

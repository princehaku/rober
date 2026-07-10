import copy
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout


PACKAGE_SRC = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_SRC.parents[2]
HISTORICAL_ARTIFACT = (
    REPO_ROOT
    / "sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/"
    / "01_upper_manual_samesession_012.json"
)
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def _material_module():
    return importlib.import_module("ros2_trashbot_hardware.wave_rover_same_session_wheel_feedback_material")


def _historical_artifact() -> dict:
    # 测试直接读取历史真实上位机 artifact，避免把 fixture 写成另一个手工 wrapper。
    return json.loads(HISTORICAL_ARTIFACT.read_text(encoding="utf-8"))


def _render(payload: dict) -> str:
    # 所有泄露断言都看最终 JSON 文本，因为 CLI 和后续消费方看到的就是这层合同。
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


class WaveRoverSameSessionWheelFeedbackMaterialTest(unittest.TestCase):
    def test_positive_historical_artifact_outputs_ready_safe_summary(self):
        material = _material_module()

        # 正例必须直接消费历史真实 artifact，证明 intake 不是只验证人工 fixture。
        summary = material.build_same_session_wheel_feedback_material_summary(
            _historical_artifact(), HISTORICAL_ARTIFACT
        )

        # 合同字段锁定 proof scope，避免后续把它误接成 HIL pass 或 delivery proof。
        self.assertEqual(summary["schema"], "trashbot.wave_rover_same_session_wheel_feedback_material.v1")
        self.assertEqual(summary["status"], "same_session_wheel_feedback_material_ready_not_delivery_proof")
        self.assertEqual(
            summary["proof_scope"],
            "software_proof_o1_same_session_wheel_feedback_material_intake_only",
        )
        # 五个 material flag 对应 tech-plan 要求的 same-session 阶段链路。
        self.assertTrue(summary["same_session_material_present"])
        self.assertTrue(summary["motion_command_present"])
        self.assertTrue(summary["feedback_request_present"])
        self.assertTrue(summary["wheel_feedback_material_present"])
        self.assertTrue(summary["stop_zero_readback_present"])
        # 只允许输出 L/R 数值摘要，不允许输出整帧 vendor payload。
        self.assertEqual(summary["latest_nonzero_pair"]["left_speed"], 61.0)
        self.assertEqual(summary["latest_nonzero_pair"]["right_speed"], 61.0)
        self.assertEqual(summary["latest_nonzero_pair"]["sign_pattern"], "both_positive")
        self.assertEqual(summary["counts"]["motion_window_nonzero_pair_count"], 1)
        self.assertEqual(summary["counts"]["after_stop_zero_pair_count"], 1)
        # 安全字段由 intake 覆盖，不能被历史 artifact 的其他执行事实抬高。
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertEqual(summary["blocked_reasons"], [])

    def test_positive_summary_does_not_leak_raw_or_runtime_context(self):
        material = _material_module()

        summary = material.build_same_session_wheel_feedback_material_summary(
            _historical_artifact(), HISTORICAL_ARTIFACT
        )
        rendered = _render(summary)

        # 历史 artifact 内部有串口路径、baudrate 和 endpoint；摘要合同必须完全不回显。
        self.assertNotIn("/dev/tty", rendered)
        self.assertNotIn("115200", rendered)
        self.assertNotIn("/api/base", rendered)
        self.assertNotIn("compact_frames", rendered)
        self.assertNotIn("serial_motion_transaction", rendered)
        self.assertNotIn("vendor_frame", rendered)
        self.assertNotIn("/Users/", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("Traceback", rendered)

    def test_missing_motion_window_nonzero_blocks(self):
        material = _material_module()
        artifact = _historical_artifact()
        mutated = copy.deepcopy(artifact)
        # 把 motion window 的唯一非零反馈清零，验证 top-level nonzero summary 不能兜底。
        frame = mutated["serial_motion_transaction"]["feedback_during_motion"]["t1001_feedback_frames"][0]
        frame["L"] = 0
        frame["R"] = 0

        summary = material.build_same_session_wheel_feedback_material_summary(mutated, HISTORICAL_ARTIFACT)

        # 缺 motion-window nonzero 时必须 blocked，即使其他阶段仍完整。
        self.assertEqual(summary["status"], "blocked_invalid_same_session_wheel_feedback_material")
        self.assertFalse(summary["same_session_material_present"])
        self.assertFalse(summary["wheel_feedback_material_present"])
        self.assertIn("motion_window_nonzero_pair_missing", summary["blocked_reasons"])
        self.assertIsNone(summary["latest_nonzero_pair"])

    def test_missing_after_stop_zero_blocks(self):
        material = _material_module()
        artifact = _historical_artifact()
        mutated = copy.deepcopy(artifact)
        # stop 后如果不是 0/0，就不能证明停车回落已经被同会话材料覆盖。
        frame = mutated["serial_motion_transaction"]["feedback_after_stop"]["t1001_feedback_frames"][0]
        frame["L"] = 61
        frame["R"] = 61

        summary = material.build_same_session_wheel_feedback_material_summary(mutated, HISTORICAL_ARTIFACT)

        # motion-window 非零仍可被摘要记录，但整体 same-session material 不能 ready。
        self.assertEqual(summary["status"], "blocked_invalid_same_session_wheel_feedback_material")
        self.assertTrue(summary["wheel_feedback_material_present"])
        self.assertFalse(summary["stop_zero_readback_present"])
        self.assertIn("after_stop_zero_pair_missing", summary["blocked_reasons"])

    def test_unsafe_true_and_sensitive_text_fail_closed_without_leakage(self):
        material = _material_module()
        artifact = _historical_artifact()
        mutated = copy.deepcopy(artifact)
        # dangerous true 和敏感文本同时出现时，输出只能保留通用 reason。
        mutated["hil_pass"] = True
        mutated["debug_url"] = "https://example.invalid/raw"
        mutated["access_token"] = "should-not-leak"
        mutated["operator_note"] = "/Users/m1/private/raw.txt"

        summary = material.build_same_session_wheel_feedback_material_summary(mutated, HISTORICAL_ARTIFACT)
        rendered = _render(summary)

        self.assertEqual(summary["status"], "blocked_invalid_same_session_wheel_feedback_material")
        self.assertIn("dangerous_true_hil_pass", summary["blocked_reasons"])
        self.assertIn("unsafe_sensitive_key_present", summary["blocked_reasons"])
        self.assertIn("unsafe_text_present", summary["blocked_reasons"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn("should-not-leak", rendered)
        self.assertNotIn("example.invalid", rendered)
        self.assertNotIn("/Users/m1/private", rendered)
        self.assertNotIn("access_token", rendered)

    def test_bad_schema_and_bad_shape_block(self):
        material = _material_module()
        wrong_schema = copy.deepcopy(_historical_artifact())
        # schema 是来源门；shape 错则不能继续读取 serial_motion_transaction。
        wrong_schema["schema"] = "trashbot.other.v1"

        schema_summary = material.build_same_session_wheel_feedback_material_summary(
            wrong_schema, HISTORICAL_ARTIFACT
        )
        shape_summary = material.build_same_session_wheel_feedback_material_summary(
            ["not", "an", "object"], HISTORICAL_ARTIFACT
        )

        self.assertEqual(schema_summary["status"], "blocked_invalid_same_session_wheel_feedback_material")
        self.assertIn("schema_mismatch", schema_summary["blocked_reasons"])
        self.assertEqual(shape_summary["status"], "blocked_invalid_same_session_wheel_feedback_material")
        self.assertIn("artifact_root_not_object", shape_summary["blocked_reasons"])

    def test_nonzero_outside_motion_window_does_not_count(self):
        material = _material_module()
        artifact = _historical_artifact()
        mutated = copy.deepcopy(artifact)
        # 非零反馈移动到 after-stop 时不能被计算为 motion window material。
        during = mutated["serial_motion_transaction"]["feedback_during_motion"]["t1001_feedback_frames"][0]
        during["L"] = 0
        during["R"] = 0
        after_stop = mutated["serial_motion_transaction"]["feedback_after_stop"]["t1001_feedback_frames"][0]
        after_stop["L"] = 61
        after_stop["R"] = 61

        summary = material.build_same_session_wheel_feedback_material_summary(mutated, HISTORICAL_ARTIFACT)

        self.assertEqual(summary["status"], "blocked_invalid_same_session_wheel_feedback_material")
        self.assertFalse(summary["wheel_feedback_material_present"])
        self.assertFalse(summary["stop_zero_readback_present"])
        self.assertIn("motion_window_nonzero_pair_missing", summary["blocked_reasons"])
        self.assertIn("after_stop_zero_pair_missing", summary["blocked_reasons"])

    def test_cli_returns_zero_for_ready_and_nonzero_for_blocked(self):
        material = _material_module()

        # ready CLI exit 0 方便后续 smoke 把该 intake 当作可复验材料源。
        with redirect_stdout(io.StringIO()) as stdout:
            ready_code = material.main([str(HISTORICAL_ARTIFACT)])
        ready_payload = json.loads(stdout.getvalue())

        artifact = _historical_artifact()
        # dangerous true 必须让 CLI exit 4，避免 shell gate 误判 ready。
        artifact["safe_to_control"] = True
        with tempfile.TemporaryDirectory() as tmpdir:
            blocked_path = Path(tmpdir) / "unsafe.json"
            blocked_path.write_text(json.dumps(artifact), encoding="utf-8")
            with redirect_stdout(io.StringIO()) as blocked_stdout:
                blocked_code = material.main([str(blocked_path)])
            blocked_payload = json.loads(blocked_stdout.getvalue())

        self.assertEqual(ready_code, 0)
        self.assertEqual(ready_payload["status"], "same_session_wheel_feedback_material_ready_not_delivery_proof")
        self.assertEqual(blocked_code, 4)
        self.assertEqual(blocked_payload["status"], "blocked_invalid_same_session_wheel_feedback_material")
        self.assertFalse(blocked_payload["safe_to_control"])

    def test_cli_bad_json_blocks_without_traceback(self):
        material = _material_module()

        # 坏 JSON 也要输出 blocked 合同，不能把 Python traceback 暴露给上层消费者。
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "bad.json"
            artifact_path.write_text("{not-json", encoding="utf-8")
            with redirect_stdout(io.StringIO()) as stdout:
                result = material.main([str(artifact_path)])
            rendered = stdout.getvalue()

        self.assertEqual(result, 4)
        self.assertIn("artifact_json_unreadable_or_invalid", rendered)
        self.assertNotIn("Traceback", rendered)


if __name__ == "__main__":
    unittest.main()

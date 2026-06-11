"""motion_evidence_material_review 的 file-only 复核单测。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "motion_evidence_material_review.py"
SPEC = importlib.util.spec_from_file_location("motion_evidence_material_review", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)


class MotionEvidenceMaterialReviewTests(unittest.TestCase):
    """锁定 wheel/scan 材料草稿的保守判定和 fail-closed 输出。"""

    def write_json(self, root: Path, name: str, payload: object) -> Path:
        """测试夹具统一落盘，便于 CLI 和模块内函数复用同一输入。"""
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return path

    def write_jsonl(self, root: Path, name: str, payloads: list[object]) -> Path:
        """feedback 样本需要覆盖 JSONL 形式，避免只测 JSON 聚合结构。"""
        path = root / name
        path.write_text("".join(json.dumps(item, ensure_ascii=True) + "\n" for item in payloads), encoding="utf-8")
        return path

    def manual_response_fixture(self) -> dict[str, object]:
        """夹具只保留本轮脚本要求的关键字段，不引入真实 API 副作用。"""
        return {
            "schema": "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
            "before_readback": {
                "base_feedback_samples_latest": {"artifact": {"path": "runtime/base_feedback_samples_latest.json"}},
                "radar_scan_proof_latest": {"artifact": {"path": "runtime/scan_before_latest.json"}},
            },
            "after_readback": {
                "base_feedback_samples_latest": {"artifact": {"path": "runtime/base_feedback_samples_latest.json"}},
                "radar_scan_proof_latest": {"artifact": {"path": "runtime/scan_after_latest.json"}},
            },
            "evidence_capture_endpoints": [
                {"phase": "before", "id": "base_feedback_samples_latest", "endpoint": "/api/base/feedback-samples/latest"},
                {"phase": "after", "id": "radar_scan_proof_latest", "endpoint": "/api/radar/scan-proof/latest"},
            ],
            "motion_evidence_summary": "manual command before/after fixed GET evidence snapshot captured; this is not HIL pass.",
        }

    def test_help_is_file_only(self) -> None:
        """`--help` 只暴露文件参数，不应出现串口、HTTP 或 ROS 运行提示。"""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            text=True,
            capture_output=True,
            timeout=5,
        )

        self.assertEqual(0, result.returncode)
        for required in ("--manual-response", "--base-feedback", "--scan-before", "--scan-after", "--output"):
            self.assertIn(required, result.stdout)
        for forbidden in ("/api/base/manual", "/cmd_vel", "serial", "ROS"):
            self.assertNotIn(forbidden, result.stdout)

    def test_ready_review_requires_both_wheels_nonzero_and_scan_delta(self) -> None:
        """pass 只在双轮同帧非零且 scan delta 达阈值时成立。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manual_path = self.write_json(root, "manual.json", self.manual_response_fixture())
            feedback_path = self.write_jsonl(
                root,
                "feedback.jsonl",
                [
                    {"T": 1001, "L": 0.0, "R": 0.0, "v": 11.9},
                    {"T": 1001, "L": 0.06, "R": 0.05, "v": 11.8},
                ],
            )
            scan_before = self.write_json(root, "scan_before.json", {"ranges": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]})
            scan_after = self.write_json(root, "scan_after.json", {"ranges": [1.10, 1.12, 1.09, 1.08, 1.11, 1.15, 1.10, 1.09]})
            output_path = root / "review.json"

            rc = REVIEW.main(
                [
                    "--manual-response",
                    str(manual_path),
                    "--base-feedback",
                    str(feedback_path),
                    "--scan-before",
                    str(scan_before),
                    "--scan-after",
                    str(scan_after),
                    "--output",
                    str(output_path),
                ]
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual(REVIEW.SCHEMA, payload["schema"])
        self.assertEqual("ready_for_operator_report_material", payload["review_status"])
        self.assertTrue(payload["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(payload["physical_motion_lidar_delta_proven"])
        self.assertEqual(str(feedback_path), payload["wheel_feedback_ref"])
        self.assertEqual(f"{scan_before} -> {scan_after}", payload["scan_delta_ref"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["sends_motion_commands"])
        self.assertTrue(payload["operator_report_claims"]["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(payload["operator_report_claims"]["physical_motion_lidar_delta_proven"])
        self.assertEqual("raw_ranges", payload["details"]["scan_review"]["source"])

    def test_insufficient_when_only_single_side_nonzero_and_scan_missing(self) -> None:
        """单侧轮速或缺 scan 输入时必须保持 insufficient。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manual_path = self.write_json(root, "manual.json", self.manual_response_fixture())
            feedback_path = self.write_json(
                root,
                "feedback.json",
                {"samples": [{"T": 1001, "left_speed": 0.08, "right_speed": 0.0}]},
            )
            output_path = root / "review.json"

            rc = REVIEW.main(
                [
                    "--manual-response",
                    str(manual_path),
                    "--base-feedback",
                    str(feedback_path),
                    "--output",
                    str(output_path),
                ]
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual("insufficient_material", payload["review_status"])
        self.assertFalse(payload["wheel_feedback_lr_nonzero_proven"])
        self.assertFalse(payload["physical_motion_lidar_delta_proven"])
        self.assertIn("wheel_feedback_single_side_nonzero_only", payload["failure_reasons"])
        self.assertIn("scan_before_or_after_file_not_provided", payload["failure_reasons"])
        self.assertEqual(str(feedback_path), payload["wheel_feedback_ref"])

    def test_invalid_when_manual_response_missing_required_shape(self) -> None:
        """manual response 缺关键字段时必须输出 invalid_input，而不是猜测补齐。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manual_path = self.write_json(root, "manual_invalid.json", {"schema": "x"})
            output_path = root / "review.json"

            rc = REVIEW.main(
                [
                    "--manual-response",
                    str(manual_path),
                    "--output",
                    str(output_path),
                ]
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual("invalid_input", payload["review_status"])
        self.assertIn("manual_response_missing_before_readback", payload["failure_reasons"])
        self.assertIn("manual_response_before_readback_not_object", payload["failure_reasons"])
        self.assertFalse(payload["wheel_feedback_lr_nonzero_proven"])
        self.assertFalse(payload["physical_motion_lidar_delta_proven"])

    def test_summary_scan_mode_is_supported_without_raw_ranges(self) -> None:
        """当 scan proof 已经给出 delta summary 时，脚本应复用 summary 判定。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manual_path = self.write_json(root, "manual.json", self.manual_response_fixture())
            feedback_path = self.write_jsonl(root, "feedback.jsonl", [{"T": 1001, "L": 0.03, "R": 0.04}])
            scan_before = self.write_json(root, "scan_before.json", {"valid_beam_count": 12, "average_abs_delta_m": 0.0, "max_abs_delta_m": 0.0})
            scan_after = self.write_json(root, "scan_after.json", {"valid_beam_count": 12, "average_abs_delta_m": 0.05, "max_abs_delta_m": 0.12})
            output_path = root / "review.json"

            rc = REVIEW.main(
                [
                    "--manual-response",
                    str(manual_path),
                    "--base-feedback",
                    str(feedback_path),
                    "--scan-before",
                    str(scan_before),
                    "--scan-after",
                    str(scan_after),
                    "--output",
                    str(output_path),
                ]
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual("ready_for_operator_report_material", payload["review_status"])
        self.assertEqual("summary_fields", payload["details"]["scan_review"]["source"])


if __name__ == "__main__":
    unittest.main()

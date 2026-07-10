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
ARTIFACT_DIR = REPO_ROOT / "sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts"
MANUAL_HIL_GATE_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts"
)
STRUCTURED_HIL_REPORT_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts"
)
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def _module():
    return importlib.import_module("ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle")


def _load_json(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _load_yaml_text(name: str) -> str:
    return (ARTIFACT_DIR / name).read_text(encoding="utf-8")


def _load_json_path(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _default_paths() -> dict[str, Path]:
    return {name: Path(path) for name, path in _module().DEFAULT_PATHS.items()}


def _render(payload: dict) -> str:
    # 泄露检查统一看最终 JSON 文本，因为 CLI/上层 readback 看到的就是这层合同。
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


class WaveRoverMotionMapHilMaterialBundleTest(unittest.TestCase):
    def test_positive_historical_run_outputs_ready_safe_bundle(self):
        material = _module()

        summary = material.build_motion_map_hil_material_bundle_from_files(_default_paths())

        # 正例必须是 ready，但边界仍锁在 not_hil_pass。
        self.assertEqual(summary["schema"], "trashbot.wave_rover_motion_map_hil_material_bundle.v1")
        self.assertEqual(summary["status"], "motion_map_hil_material_bundle_ready_not_hil_pass")
        self.assertEqual(
            summary["proof_scope"],
            "software_proof_o1_motion_map_hil_material_bundle_only",
        )
        self.assertTrue(summary["same_run_material_present"])
        self.assertEqual(summary["run_token"], "20260622_0135")
        # first jog / feedback / scan delta / operator / map 三条链都必须被安全提炼出来。
        self.assertTrue(summary["first_jog_command_present"])
        self.assertEqual(summary["first_jog_command_summary"]["applied_direction"], "forward")
        self.assertEqual(summary["first_jog_command_summary"]["clamped_speed_mps"], 0.08)
        self.assertTrue(summary["feedback_sample_present"])
        self.assertEqual(summary["feedback_sample_summary"]["t1001_observed_count"], 3)
        self.assertEqual(summary["feedback_sample_summary"]["observed_feedback_types"], [130, 1001])
        self.assertTrue(summary["scan_delta_present"])
        self.assertAlmostEqual(summary["scan_delta_summary"]["median_abs_diff_m"], 1.7350000441074371)
        self.assertEqual(summary["scan_delta_summary"]["changed_bin_ratio"], 1.0)
        self.assertTrue(summary["operator_report_present"])
        self.assertTrue(summary["operator_claim_summary"]["physical_motion_lidar_delta_proven"])
        self.assertFalse(summary["operator_claim_summary"]["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(summary["field_first_jog_map_present"])
        self.assertTrue(summary["manual_motion_map_present"])
        self.assertTrue(summary["map_output_present"])
        # 老 map artifacts 没有 free cells；新增 material readiness 不能改变旧字段语义。
        self.assertFalse(summary["map_navigation_ready"])
        self.assertFalse(summary["pixel_review_summary"]["field_first_jog_map"]["has_free_cells"])
        self.assertFalse(summary["pixel_review_summary"]["manual_motion_map"]["has_free_cells"])
        self.assertTrue(summary["free_cell_map_material_present"])
        self.assertTrue(summary["free_cell_map_lifecycle_present"])
        self.assertTrue(summary["free_cell_map_list_present"])
        self.assertTrue(summary["free_cell_map_yaml_present"])
        self.assertTrue(summary["free_cell_map_pgm_present"])
        self.assertTrue(summary["free_cell_pixel_review_present"])
        self.assertTrue(summary["free_cell_has_free_cells"])
        self.assertEqual(summary["free_cell_pixel_count"], 394)
        self.assertEqual(summary["free_cell_usable_map_count"], 1)
        self.assertTrue(summary["map_navigation_material_ready"])
        self.assertTrue(summary["localization_path_material_bridge_present"])
        self.assertTrue(summary["same_run_localization_material_present"])
        self.assertTrue(summary["same_run_map_once_observed"])
        self.assertTrue(summary["same_run_amcl_pose_observed"])
        self.assertTrue(summary["same_run_localization_tf_map_to_odom"])
        self.assertTrue(summary["same_run_localization_tf_map_to_base_link"])
        self.assertTrue(summary["same_run_planner_server_active"])
        self.assertTrue(summary["same_run_path_generation_requested"])
        self.assertFalse(summary["same_run_path_generation_succeeded"])
        self.assertFalse(summary["same_run_path_generated"])
        self.assertEqual(summary["same_run_path_point_count"], 0)
        self.assertFalse(summary["same_run_path_proven"])
        self.assertFalse(summary["nav2_route_execution_success"])
        self.assertFalse(summary["robot_control_executed"])
        self.assertTrue(summary["localization_path_bridge_ready_not_route_execution_proof"])
        # June 11 只能作为 cross-run comparator，不能覆盖 same-run path=false。
        self.assertTrue(summary["cross_run_clean_baseline_path_comparator_present"])
        self.assertEqual(summary["cross_run_clean_baseline_path_summary"]["path_point_count"], 31)
        self.assertTrue(summary["cross_run_clean_baseline_path_summary"]["path_generation_succeeded"])
        self.assertTrue(summary["bounded_motion_feedback_material_present"])
        self.assertTrue(summary["bounded_motion_feedback_present"])
        self.assertTrue(summary["feedback_motion_summary_present"])
        self.assertTrue(summary["base_feedback_samples_latest_present"])
        self.assertTrue(summary["bounded_motion_command_observed"])
        self.assertTrue(summary["bounded_motion_duration_lte_0_3s"])
        self.assertTrue(summary["bounded_motion_stop_observed"])
        self.assertTrue(summary["t1001_feedback_before_after_observed"])
        self.assertEqual(summary["t1001_feedback_sample_count"], 2)
        self.assertEqual(summary["t1001_observed_count"], 2)
        self.assertTrue(summary["odom_readback_sample_present"])
        self.assertEqual(summary["odom_readback_frame_id"], "odom")
        self.assertEqual(summary["odom_readback_child_frame_id"], "base_link")
        self.assertTrue(summary["imu_sample_present"])
        self.assertEqual(summary["imu_frame_id"], "imu_link")
        self.assertTrue(summary["battery_sample_present"])
        self.assertFalse(summary["bounded_motion_lr_nonzero_proven"])
        self.assertFalse(summary["wheel_direction_proven"])
        self.assertFalse(summary["imu_battery_calibration_proven"])
        self.assertTrue(summary["bounded_motion_feedback_ready_not_hil_pass"])
        self.assertTrue(summary["feedback_request_observed"])
        self.assertTrue(summary["feedback_request_t130_observed"])
        self.assertFalse(summary["sends_motion_commands"])
        self.assertTrue(summary["wheel_feedback_diagnostic_context_present"])
        self.assertTrue(summary["wheel_feedback_sweep_all_nonzero_lr_count_zero"])
        self.assertEqual(summary["blocked_reasons"], [])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_positive_bundle_does_not_leak_runtime_context(self):
        material = _module()

        summary = material.build_motion_map_hil_material_bundle_from_files(_default_paths())
        rendered = _render(summary)

        # 正例原始材料带有 source_base_url、endpoint、/root/... 等上下文，但最终合同必须干净。
        self.assertNotIn("source_base_url", rendered)
        self.assertNotIn("remote_endpoint", rendered)
        self.assertNotIn("normalized_base_url", rendered)
        self.assertNotIn("source_endpoint_id", rendered)
        self.assertNotIn("/root/", rendered)
        self.assertNotIn("/Users/", rendered)
        self.assertNotIn("/dev/tty", rendered)
        self.assertNotIn("115200", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("/api/status", rendered)
        self.assertNotIn("/api/nav2/proof/latest", rendered)
        self.assertNotIn("Traceback", rendered)
        self.assertNotIn("camera_artifacts_ref", rendered)
        self.assertNotIn("camera_visible", rendered)
        self.assertNotIn("safe_command_boundary", rendered)
        self.assertNotIn("scan_delta_ref", rendered)
        self.assertNotIn("token-secret", rendered.lower())
        self.assertNotIn("secret", rendered.lower())
        self.assertNotIn("baudrate", rendered.lower())

    def test_bounded_motion_duration_over_limit_blocks(self):
        material = _module()
        bounded_summary = json.loads(Path(material.DEFAULT_PATHS["bounded_motion_feedback_summary_json"]).read_text())
        # bounded pulse 必须保持 <=0.3s；超界不能继续 ready。
        bounded_summary["observed"]["nonzero_duration_s"] = 0.31
        bounded_summary["observed"]["nonzero_duration_lte_0_3s"] = False

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "feedback_motion_summary.json"
            broken_path.write_text(json.dumps(bounded_summary), encoding="utf-8")
            paths = _default_paths()
            paths["bounded_motion_feedback_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("bounded_motion_duration_over_0_3s", summary["blocked_reasons"])
        self.assertIn("bounded_motion_duration_lte_not_true", summary["blocked_reasons"])
        self.assertFalse(summary["bounded_motion_feedback_ready_not_hil_pass"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["safe_to_control"])

    def test_base_feedback_sends_commands_is_t130_request_only(self):
        material = _module()

        summary = material.build_motion_map_hil_material_bundle_from_files(_default_paths())

        self.assertTrue(summary["base_feedback_samples_latest_present"])
        self.assertTrue(summary["feedback_request_observed"])
        self.assertTrue(summary["feedback_request_t130_observed"])
        self.assertFalse(summary["sends_motion_commands"])
        self.assertFalse(summary["robot_control_executed"])
        self.assertFalse(summary["base_feedback_samples_latest_summary"]["sends_motion_commands"])

    def test_base_feedback_motion_command_true_blocks(self):
        material = _module()
        base_feedback = json.loads(Path(material.DEFAULT_PATHS["base_feedback_samples_latest_json"]).read_text())
        # latest_result.sends_commands=true 是 T130 request；sends_motion_commands=true 则必须阻塞。
        base_feedback["latest_result"]["sends_motion_commands"] = True

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "base_feedback_samples_latest.json"
            broken_path.write_text(json.dumps(base_feedback), encoding="utf-8")
            paths = _default_paths()
            paths["base_feedback_samples_latest_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("base_feedback_sends_motion_commands_not_false", summary["blocked_reasons"])
        self.assertFalse(summary["robot_control_executed"])
        self.assertFalse(summary["safe_to_control"])

    def test_bounded_motion_unsafe_text_blocks_without_leakage(self):
        material = _module()
        pulse_log = Path(material.DEFAULT_PATHS["bounded_motion_pulse_and_stop_log"]).read_text(encoding="utf-8")
        pulse_log += "\noperator_note=https://example.invalid/token-secret\n"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pulse_and_stop.log"
            broken_path.write_text(pulse_log, encoding="utf-8")
            paths = _default_paths()
            paths["bounded_motion_pulse_and_stop_log"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)
        rendered = _render(summary)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("bounded_motion_pulse_log_invalid", summary["blocked_reasons"])
        self.assertNotIn("example.invalid", rendered)
        self.assertNotIn("token-secret", rendered)

    def test_wheel_feedback_diagnostic_nonzero_blocks(self):
        material = _module()
        diagnostic = json.loads(Path(material.DEFAULT_PATHS["wheel_feedback_diagnostic_sweep_summary_json"]).read_text())
        diagnostic["segments"][0]["nonzero_lr_count"] = 1

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "wheel_feedback_sweep_summary.json"
            broken_path.write_text(json.dumps(diagnostic), encoding="utf-8")
            paths = _default_paths()
            paths["wheel_feedback_diagnostic_sweep_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("wheel_feedback_diagnostic_nonzero_lr_unexpected", summary["blocked_reasons"])
        self.assertFalse(summary["wheel_direction_proven"])
        self.assertFalse(summary["bounded_motion_lr_nonzero_proven"])

    def test_free_cell_pixel_review_missing_blocks(self):
        material = _module()
        paths = _default_paths()
        # 新增 33-38 中任一核心 artifact 缺失，都不能沿用旧 map bundle 正例。
        paths["free_cell_pixel_review_json"] = ARTIFACT_DIR / "missing_free_cell_review.json"

        summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("artifact_bundle_unreadable_or_invalid", summary["blocked_reasons"])
        self.assertFalse(summary["free_cell_pixel_review_present"])
        self.assertFalse(summary["map_navigation_material_ready"])

    def test_free_cell_map_list_not_usable_blocks(self):
        material = _module()
        map_list = _load_json("34_pc_map_list_after_free_pixel_fix.json")
        # usable map 不是唯一可用地图时，不能输出 material ready。
        map_list["map_quality_summary"]["status"] = "no_usable_map"
        map_list["map_quality_summary"]["usable_map_count"] = 0
        map_list["map_usable_for_navigation"] = False

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "map_list.json"
            broken_path.write_text(json.dumps(map_list), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_map_list_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("free_cell_map_list_not_has_usable_map", summary["blocked_reasons"])
        self.assertIn("free_cell_usable_map_count_not_one", summary["blocked_reasons"])
        self.assertIn("free_cell_map_not_usable_for_navigation", summary["blocked_reasons"])
        self.assertFalse(summary["free_cell_map_list_present"])
        self.assertFalse(summary["map_navigation_material_ready"])

    def test_free_cell_pixel_count_mismatch_blocks(self):
        material = _module()
        pixel_review = _load_json("37_fixed_free_cells_map_pixel_review.json")
        # free cell count 是本轮核心事实，不能被其他 PGM 统计兜底。
        pixel_review["free_pixel_count"] = 393
        pixel_review["counts"]["254"] = 393

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "free_cell_review.json"
            broken_path.write_text(json.dumps(pixel_review), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pixel_review_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("free_cell_pixel_count_not_394", summary["blocked_reasons"])
        self.assertIn("free_cell_pixel_review_counts_free_not_394", summary["blocked_reasons"])
        self.assertFalse(summary["free_cell_pixel_review_present"])

    def test_free_cell_yaml_pgm_basename_mismatch_blocks(self):
        material = _module()
        yaml_text = _load_yaml_text("35_fixed_free_cells_map.yaml").replace(
            "image: fixed_free_cells_20260622_0112.pgm",
            "image: wrong_free_cells_map.pgm",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "map.yaml"
            broken_path.write_text(yaml_text, encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_map_yaml"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("free_cell_yaml_pgm_basename_mismatch", summary["blocked_reasons"])
        self.assertFalse(summary["free_cell_map_yaml_present"])
        self.assertFalse(summary["map_navigation_material_ready"])

    def test_free_cell_unsafe_consumed_value_blocks_without_leakage(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        # 只污染 allowlisted 字段；输出必须 blocked 且不能把 URL/token 反射出来。
        pc_summary["first_jog_readiness_summary"]["next_action"] = "https://example.invalid/token-secret"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)
        rendered = _render(summary)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("free_cell_pc_next_action_invalid", summary["blocked_reasons"])
        self.assertNotIn("example.invalid", rendered)
        self.assertNotIn("token-secret", rendered)
        self.assertFalse(summary["free_cell_pc_summary_present"])

    def test_localization_required_endpoint_missing_blocks(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        # localize endpoint 缺失时不能只靠 status/nav2 proof 兜底。
        pc_summary["read_endpoints"] = [
            item for item in pc_summary["read_endpoints"] if item.get("id") != "localize_proof_latest"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn(
            "localization_path_required_endpoint_missing_localize_proof_latest",
            summary["blocked_reasons"],
        )
        self.assertFalse(summary["localization_path_material_bridge_present"])

    def test_localization_tf_json_parse_failure_blocks(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        for endpoint in pc_summary["read_endpoints"]:
            if endpoint.get("id") == "localize_proof_latest":
                endpoint["key_values"]["localization_tf_observed"] = "{not-json"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("same_run_localize_tf_json_invalid", summary["blocked_reasons"])
        self.assertFalse(summary["same_run_localization_tf_map_to_base_link"])

    def test_localization_tf_incomplete_blocks(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        for endpoint in pc_summary["read_endpoints"]:
            if endpoint.get("id") == "nav2_proof_latest":
                endpoint["key_values"]["localization_tf_observed"] = json.dumps(
                    {"map_to_odom": True, "map_to_base_link": False}
                )

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("same_run_nav2_proof_tf_map_to_base_link_not_true", summary["blocked_reasons"])
        self.assertFalse(summary["same_run_localization_tf_map_to_base_link"])

    def test_same_run_path_success_tamper_blocks(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        for endpoint in pc_summary["read_endpoints"]:
            if endpoint.get("id") == "nav2_proof_latest":
                endpoint["key_values"]["path_generation_succeeded"] = "true"
                endpoint["key_values"]["path_generated"] = "true"
                endpoint["key_values"]["path_point_count"] = "7"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("same_run_nav2_proof_latest_path_generation_succeeded_unexpected_true", summary["blocked_reasons"])
        self.assertIn("same_run_nav2_proof_latest_path_generated_unexpected_true", summary["blocked_reasons"])
        self.assertIn("same_run_nav2_proof_latest_path_point_count_unexpected_positive", summary["blocked_reasons"])
        self.assertFalse(summary["same_run_path_proven"])
        self.assertFalse(summary["nav2_route_execution_success"])

    def test_localization_consumed_unsafe_value_blocks_without_leakage(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        for endpoint in pc_summary["read_endpoints"]:
            if endpoint.get("id") == "status":
                endpoint["key_values"]["map_once_observed"] = "https://example.invalid/token-secret"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)
        rendered = _render(summary)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("same_run_status_map_once_invalid", summary["blocked_reasons"])
        self.assertNotIn("example.invalid", rendered)
        self.assertNotIn("token-secret", rendered)

    def test_localization_dangerous_true_blocks(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        for endpoint in pc_summary["read_endpoints"]:
            if endpoint.get("id") == "nav2_proof_latest":
                endpoint["key_values"]["safe_to_control"] = "true"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn(
            "localization_path_nav2_proof_latest_dangerous_true_safe_to_control",
            summary["blocked_reasons"],
        )
        self.assertFalse(summary["safe_to_control"])

    def test_localization_optional_dangerous_key_values_block(self):
        material = _module()
        pc_summary = _load_json("38_pc_summary_after_map_fix.json")
        for endpoint in pc_summary["read_endpoints"]:
            if endpoint.get("id") == "nav2_proof_latest":
                endpoint["key_values"]["robot_control_executed"] = "true"
                endpoint["key_values"]["nav2_route_execution_success"] = "true"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "pc_summary.json"
            broken_path.write_text(json.dumps(pc_summary), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_pc_summary_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn(
            "localization_path_nav2_proof_latest_dangerous_true_robot_control_executed",
            summary["blocked_reasons"],
        )
        self.assertIn(
            "localization_path_nav2_proof_latest_dangerous_true_nav2_route_execution_success",
            summary["blocked_reasons"],
        )
        self.assertFalse(summary["robot_control_executed"])
        self.assertFalse(summary["nav2_route_execution_success"])

    def test_cross_run_comparator_latest_result_primary_actions_true_blocks_comparator(self):
        material = _module()
        latest_path = Path(material.DEFAULT_PATHS["clean_baseline_nav2_path_latest_json"])
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
        # Comparator 是 cross-run 参考；若它试图打开主动作，只禁用 comparator，不覆盖 same-run false 结论。
        latest["latest_result"]["primary_actions_enabled"] = True

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "nav2_latest.json"
            broken_path.write_text(json.dumps(latest), encoding="utf-8")
            paths = _default_paths()
            paths["clean_baseline_nav2_path_latest_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "motion_map_hil_material_bundle_ready_not_hil_pass")
        self.assertFalse(summary["cross_run_clean_baseline_path_comparator_present"])
        self.assertIn(
            "cross_run_clean_baseline_latest_result_primary_actions_enabled_not_false",
            summary["cross_run_clean_baseline_path_comparator_blocked_reasons"],
        )
        self.assertTrue(summary["localization_path_material_bridge_present"])
        self.assertFalse(summary["same_run_path_proven"])

    def test_free_cell_dangerous_true_blocks(self):
        material = _module()
        map_list = _load_json("34_pc_map_list_after_free_pixel_fix.json")
        # 输入试图提升安全控制字段时，必须 fail-closed。
        map_list["safe_to_control"] = True

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "map_list.json"
            broken_path.write_text(json.dumps(map_list), encoding="utf-8")
            paths = _default_paths()
            paths["free_cell_map_list_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("free_cell_map_list_dangerous_true_safe_to_control", summary["blocked_reasons"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["map_navigation_material_ready"])

    def test_missing_feedback_sample_blocks(self):
        material = _module()
        paths = _default_paths()
        # 核心 artifact 缺失时必须 blocked，而不是用其他 summary 兜底。
        paths["feedback_samples_json"] = ARTIFACT_DIR / "missing_feedback_samples.json"

        summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("artifact_bundle_unreadable_or_invalid", summary["blocked_reasons"])
        self.assertFalse(summary["feedback_sample_present"])

    def test_feedback_all_samples_not_t1001_blocks(self):
        material = _module()
        feedback_samples = _load_json("12_pc_feedback_samples_after_scan_delta_jog.json")
        # required true 变成 false 时必须显式进入 blocked_reasons，不能只让 present 掉成 false。
        feedback_samples["sample_key_values"]["all_samples_observed_t1001"] = "false"

        summary = material.build_motion_map_hil_material_bundle(
            _load_json("10_pc_first_jog_for_scan_delta.json"),
            feedback_samples,
            _load_json("14_scan_delta_metrics.json"),
            _load_json("18_operator_report_lidar_delta_response.json"),
            material._load_map_yaml(ARTIFACT_DIR / "22_field_first_jog_map.yaml"),
            ARTIFACT_DIR / "23_field_first_jog_map.pgm",
            _load_json("24_field_first_jog_map_pixel_review.json"),
            material._load_map_yaml(ARTIFACT_DIR / "30_manual_motion_map.yaml"),
            ARTIFACT_DIR / "31_manual_motion_map.pgm",
            _load_json("32_manual_motion_map_pixel_review.json"),
            {name: material._path_ref(path) for name, path in _default_paths().items()},
        )

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("feedback_all_samples_not_t1001", summary["blocked_reasons"])
        self.assertFalse(summary["feedback_sample_present"])

    def test_scan_delta_and_operator_claim_mismatch_blocks(self):
        material = _module()
        operator_report = _load_json("18_operator_report_lidar_delta_response.json")
        # operator 把 lidar delta claim 改成 false，必须与 scan_delta true 形成 mismatch blocked。
        operator_report["structured_hil_claims"]["physical_motion_lidar_delta_proven"] = False

        summary = material.build_motion_map_hil_material_bundle(
            _load_json("10_pc_first_jog_for_scan_delta.json"),
            _load_json("12_pc_feedback_samples_after_scan_delta_jog.json"),
            _load_json("14_scan_delta_metrics.json"),
            operator_report,
            material._load_map_yaml(ARTIFACT_DIR / "22_field_first_jog_map.yaml"),
            ARTIFACT_DIR / "23_field_first_jog_map.pgm",
            _load_json("24_field_first_jog_map_pixel_review.json"),
            material._load_map_yaml(ARTIFACT_DIR / "30_manual_motion_map.yaml"),
            ARTIFACT_DIR / "31_manual_motion_map.pgm",
            _load_json("32_manual_motion_map_pixel_review.json"),
            {name: material._path_ref(path) for name, path in _default_paths().items()},
        )

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("operator_scan_delta_claim_missing", summary["blocked_reasons"])
        self.assertFalse(summary["same_run_material_present"])

    def test_map_pixel_review_mismatch_blocks(self):
        material = _module()
        pixel_review = _load_json("24_field_first_jog_map_pixel_review.json")
        # 尺寸一旦和 PGM header 对不上，就不能把 map artifact 视为可信配对。
        pixel_review["width"] = 999

        summary = material.build_motion_map_hil_material_bundle(
            _load_json("10_pc_first_jog_for_scan_delta.json"),
            _load_json("12_pc_feedback_samples_after_scan_delta_jog.json"),
            _load_json("14_scan_delta_metrics.json"),
            _load_json("18_operator_report_lidar_delta_response.json"),
            material._load_map_yaml(ARTIFACT_DIR / "22_field_first_jog_map.yaml"),
            ARTIFACT_DIR / "23_field_first_jog_map.pgm",
            pixel_review,
            material._load_map_yaml(ARTIFACT_DIR / "30_manual_motion_map.yaml"),
            ARTIFACT_DIR / "31_manual_motion_map.pgm",
            _load_json("32_manual_motion_map_pixel_review.json"),
            {name: material._path_ref(path) for name, path in _default_paths().items()},
        )

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("field_first_jog_pixel_review_width_mismatch", summary["blocked_reasons"])
        self.assertFalse(summary["field_first_jog_map_present"])

    def test_operator_required_true_false_and_external_video_true_block(self):
        material = _module()
        operator_report = _load_json("18_operator_report_lidar_delta_response.json")
        # required true / required false 条件都必须顶层 blocked。
        operator_report["request_body"]["operator_present"] = False
        operator_report["structured_hil_claims"]["external_video_recorded"] = True

        summary = material.build_motion_map_hil_material_bundle(
            _load_json("10_pc_first_jog_for_scan_delta.json"),
            _load_json("12_pc_feedback_samples_after_scan_delta_jog.json"),
            _load_json("14_scan_delta_metrics.json"),
            operator_report,
            material._load_map_yaml(ARTIFACT_DIR / "22_field_first_jog_map.yaml"),
            ARTIFACT_DIR / "23_field_first_jog_map.pgm",
            _load_json("24_field_first_jog_map_pixel_review.json"),
            material._load_map_yaml(ARTIFACT_DIR / "30_manual_motion_map.yaml"),
            ARTIFACT_DIR / "31_manual_motion_map.pgm",
            _load_json("32_manual_motion_map_pixel_review.json"),
            {name: material._path_ref(path) for name, path in _default_paths().items()},
        )

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("operator_present_false", summary["blocked_reasons"])
        self.assertIn("operator_external_video_recorded_true", summary["blocked_reasons"])
        self.assertFalse(summary["operator_report_present"])

    def test_unsafe_consumed_value_and_dangerous_true_fail_closed_without_leakage(self):
        material = _module()
        first_jog = _load_json("10_pc_first_jog_for_scan_delta.json")
        operator_report = _load_json("18_operator_report_lidar_delta_response.json")
        field_yaml = material._load_map_yaml(ARTIFACT_DIR / "22_field_first_jog_map.yaml")

        # 只在真正被消费的字段里塞危险内容；bundle 必须 blocked 且不回显原值。
        first_jog["safe_to_control"] = True
        first_jog["applied_direction"] = "https://example.invalid/forward"
        operator_report["structured_hil_claims"]["site_state"] = "/Users/m1/private.txt"
        field_yaml["image"] = "/root/private/field_map.pgm"

        summary = material.build_motion_map_hil_material_bundle(
            first_jog,
            _load_json("12_pc_feedback_samples_after_scan_delta_jog.json"),
            _load_json("14_scan_delta_metrics.json"),
            operator_report,
            field_yaml,
            ARTIFACT_DIR / "23_field_first_jog_map.pgm",
            _load_json("24_field_first_jog_map_pixel_review.json"),
            material._load_map_yaml(ARTIFACT_DIR / "30_manual_motion_map.yaml"),
            ARTIFACT_DIR / "31_manual_motion_map.pgm",
            _load_json("32_manual_motion_map_pixel_review.json"),
            {name: material._path_ref(path) for name, path in _default_paths().items()},
        )
        rendered = _render(summary)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("dangerous_true_safe_to_control", summary["blocked_reasons"])
        self.assertIn("first_jog_applied_direction_invalid", summary["blocked_reasons"])
        self.assertIn("operator_site_state_invalid", summary["blocked_reasons"])
        self.assertIn("field_first_jog_map_image_invalid", summary["blocked_reasons"])
        self.assertNotIn("example.invalid", rendered)
        self.assertNotIn("/Users/m1/private", rendered)
        self.assertNotIn("/root/private", rendered)

    def test_first_jog_confirm_hil_checklist_false_blocks(self):
        material = _module()
        first_jog = _load_json("10_pc_first_jog_for_scan_delta.json")
        # confirm_hil_checklist 是 first jog 的 required true，不能只让 present=false。
        first_jog["confirm_hil_checklist"] = False

        summary = material.build_motion_map_hil_material_bundle(
            first_jog,
            _load_json("12_pc_feedback_samples_after_scan_delta_jog.json"),
            _load_json("14_scan_delta_metrics.json"),
            _load_json("18_operator_report_lidar_delta_response.json"),
            material._load_map_yaml(ARTIFACT_DIR / "22_field_first_jog_map.yaml"),
            ARTIFACT_DIR / "23_field_first_jog_map.pgm",
            _load_json("24_field_first_jog_map_pixel_review.json"),
            material._load_map_yaml(ARTIFACT_DIR / "30_manual_motion_map.yaml"),
            ARTIFACT_DIR / "31_manual_motion_map.pgm",
            _load_json("32_manual_motion_map_pixel_review.json"),
            {name: material._path_ref(path) for name, path in _default_paths().items()},
        )

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("first_jog_confirm_hil_checklist_false", summary["blocked_reasons"])
        self.assertFalse(summary["first_jog_command_present"])

    def test_cli_default_ready_and_negative_override_nonzero_exit(self):
        material = _module()

        # 默认 CLI 直接消费历史材料，便于 smoke 不显式传十个路径。
        with redirect_stdout(io.StringIO()) as stdout:
            ready_code = material.main([])
        ready_payload = json.loads(stdout.getvalue())

        feedback_samples = _load_json("12_pc_feedback_samples_after_scan_delta_jog.json")
        feedback_samples["sample_key_values"]["t1001_observed_count"] = "0"
        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "feedback.json"
            broken_path.write_text(json.dumps(feedback_samples), encoding="utf-8")
            with redirect_stdout(io.StringIO()) as blocked_stdout:
                blocked_code = material.main(["--feedback-samples-json", str(broken_path)])
            blocked_payload = json.loads(blocked_stdout.getvalue())

        self.assertEqual(ready_code, 0)
        self.assertEqual(ready_payload["status"], "motion_map_hil_material_bundle_ready_not_hil_pass")
        self.assertEqual(blocked_code, 4)
        self.assertEqual(blocked_payload["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("feedback_t1001_missing", blocked_payload["blocked_reasons"])

    def test_manual_hil_gate_positive_summary_ready_not_hil_pass(self):
        material = _module()

        summary = material.build_motion_map_hil_material_bundle_from_files(_default_paths())

        self.assertTrue(summary["manual_hil_gate_current_evidence_material_present"])
        self.assertEqual(
            summary["manual_hil_gate_current_evidence_material_status"],
            "manual_hil_gate_current_evidence_material_ready_not_hil_pass",
        )
        self.assertEqual(summary["manual_hil_gate_status"], "blocked")
        self.assertEqual(
            summary["manual_hil_gate_missing_fields"],
            [
                "external_video_recorded",
                "visible_content_proven",
                "wheel_feedback_lr_nonzero_proven",
                "physical_motion_lidar_delta_proven",
            ],
        )
        self.assertTrue(summary["visible_content_proven_blocks_motion"])
        self.assertEqual(
            summary["manual_nonzero_policy"],
            "do_not_send_nonzero_expect_pc_local_reject",
        )
        self.assertTrue(summary["stop_safety_smoke_forwarded"])
        self.assertEqual(summary["stop_remote_http_status"], 200)
        self.assertTrue(summary["manual_nonstop_local_reject_present"])
        self.assertFalse(summary["manual_nonstop_remote_base_manual_called"])
        self.assertEqual(summary["manual_nonstop_failure_reason"], "operator_report_preflight_required")
        self.assertTrue(summary["proxy_remote_base_manual_not_called_by_local_reject"])
        self.assertEqual(summary["manual_gate_t1001_observed_count"], 2)
        self.assertTrue(summary["manual_gate_all_samples_observed_t1001"])
        self.assertTrue(summary["manual_gate_feedback_request_t130_observed"])
        self.assertTrue(summary["operator_structured_report_material_only"])
        self.assertEqual(summary["operator_structured_report_status"], "ready_for_execution")
        self.assertTrue(summary["operator_structured_delivery_claim_material_only"])
        self.assertTrue(summary["manual_hil_gate_ready_not_hil_pass"])

    def test_manual_hil_gate_remote_base_manual_called_blocks(self):
        material = _module()
        proxy_smoke = _load_json_path(MANUAL_HIL_GATE_ARTIFACT_DIR / "pc_proxy/proxy_smoke_result.json")
        proxy_smoke["manual"]["remote_base_manual_not_called_by_local_reject"] = False

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "proxy_smoke_result.json"
            broken_path.write_text(json.dumps(proxy_smoke), encoding="utf-8")
            paths = _default_paths()
            paths["manual_hil_gate_proxy_smoke_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("manual_hil_gate_remote_base_manual_called", summary["blocked_reasons"])
        self.assertFalse(summary["manual_hil_gate_current_evidence_material_present"])
        self.assertFalse(summary["proxy_remote_base_manual_not_called_by_local_reject"])

    def test_manual_hil_gate_missing_core_artifact_blocks(self):
        material = _module()
        paths = _default_paths()
        paths["manual_hil_gate_decision_json"] = MANUAL_HIL_GATE_ARTIFACT_DIR / "pc_proxy/missing_gate_decision.json"

        summary = material.build_motion_map_hil_material_bundle_from_files(paths)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn("artifact_bundle_unreadable_or_invalid", summary["blocked_reasons"])
        self.assertFalse(summary["manual_hil_gate_current_evidence_material_present"])

    def test_manual_hil_gate_operator_delivery_leak_blocks_without_leakage(self):
        material = _module()
        operator_report = _load_json_path(
            STRUCTURED_HIL_REPORT_ARTIFACT_DIR / "real_board_operator_report_direct_192_168_1_11_8787.json"
        )
        operator_report["delivery_success"] = True
        operator_report["structured_hil_claims"]["normalization"]["source"] = "https://example.invalid/token-secret"

        with tempfile.TemporaryDirectory() as tmpdir:
            broken_path = Path(tmpdir) / "operator_report.json"
            broken_path.write_text(json.dumps(operator_report), encoding="utf-8")
            paths = _default_paths()
            paths["manual_hil_gate_operator_report_latest_json"] = broken_path
            summary = material.build_motion_map_hil_material_bundle_from_files(paths)
        rendered = _render(summary)

        self.assertEqual(summary["status"], "blocked_invalid_motion_map_hil_material_bundle")
        self.assertIn(
            "manual_hil_gate_operator_top_level_delivery_success_not_false",
            summary["blocked_reasons"],
        )
        self.assertNotIn("example.invalid", rendered)
        self.assertNotIn("token-secret", rendered)


if __name__ == "__main__":
    unittest.main()

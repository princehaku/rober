import ast
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
GATEWAY = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "operator_gateway.py"
DIAGNOSTICS = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "operator_gateway_diagnostics.py"
HTTP = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "operator_gateway_http.py"
SETUP = REPO_ROOT / "ros2_trashbot_behavior" / "setup.py"


class OperatorGatewayStaticTest(unittest.TestCase):
    def test_gateway_exposes_minimum_http_contract(self):
        source = GATEWAY.read_text(encoding="utf-8")
        http_source = HTTP.read_text(encoding="utf-8")
        ast.parse(source)
        ast.parse(http_source)

        for route in (
            '"/api/status"',
            '"/api/diagnostics"',
            '"/api/vision/review-queue"',
            '"/api/vision/review-decisions"',
            '"/api/collect"',
            '"/api/dropoff/confirm"',
            '"/api/cancel"',
            '"robots"',
            '"commands"',
            '"commands_next"',
            '"status"',
            '"ack"',
        ):
            self.assertIn(route, http_source)

        self.assertIn("default_target", source)
        self.assertIn("collect_action_name", source)
        self.assertIn("dropoff_service_name", source)
        self.assertIn("pose_topic", source)
        self.assertIn("software_version", source)
        self.assertIn("map_version", source)
        self.assertIn("route_version", source)
        self.assertIn("log_refs", source)
        self.assertIn("vision_sample_manifest_ref", source)
        self.assertIn("review_decision_log_ref", source)
        self.assertIn('self.declare_parameter("hardware_proof_ref", "")', source)
        self.assertIn('self.declare_parameter("mock_cloud_state_path", "")', source)
        self.assertIn('self.hardware_proof_ref = os.path.expanduser(', source)
        self.assertIn('self.mock_cloud_state_path = os.path.expanduser(', source)
        self.assertIn("def diagnostics", source)
        self.assertIn("build_diagnostics_payload", source)
        self.assertIn("def vision_review_queue", source)
        self.assertIn("def submit_review_decision", source)
        self.assertIn("PoseWithCovarianceStamped", source)
        self.assertIn("robot_pose", source)
        self.assertIn("robot_path", source)
        self.assertIn("ActionClient(self, TrashCollection, self.collect_action_name)", source)
        self.assertIn("create_client(SetBool, self.dropoff_service_name)", source)
        self.assertIn("make_handler(self)", source)
        self.assertIn("status_payload", source)
        self.assertIn("OPERATOR_PROMPTS", http_source)
        self.assertIn("ELEVATOR_ASSIST_SPEAKER_PROMPT", http_source)
        self.assertIn("normalize_elevator_assist", http_source)
        self.assertIn("operator_prompt_for_state", http_source)
        self.assertIn("REMOTE_PROTOCOL_VERSION", http_source)
        self.assertIn("trashbot.remote.v1", http_source)
        self.assertIn("MockCloudStore", http_source)
        self.assertIn("REMOTE_PERSISTENCE_SCHEMA", http_source)
        self.assertIn("REMOTE_STATUS_STALE_AFTER_SEC", http_source)
        self.assertIn("_remote_safe_value", http_source)
        self.assertIn("state_path=state_path", http_source)
        self.assertIn("normalize_remote_command", http_source)
        self.assertIn("normalize_remote_status", http_source)
        self.assertIn("normalize_remote_ack", http_source)
        self.assertIn("mock_cloud.next_command", http_source)
        self.assertIn("mock_cloud.submit_command", http_source)
        self.assertIn("mock_cloud.post_status", http_source)
        self.assertIn("mock_cloud.post_ack", http_source)
        self.assertIn("mock_cloud.get_ack", http_source)
        self.assertIn('"remote_ready"', http_source)
        self.assertIn('"cloud_reachable"', http_source)
        self.assertIn('"last_command_ack"', http_source)
        self.assertIn('"status_stale"', http_source)
        self.assertIn('"retry_hint"', http_source)
        self.assertIn('"auth_state"', http_source)
        self.assertIn('"degradation_state"', http_source)
        self.assertIn('"safe_phone_copy"', http_source)
        self.assertIn("REMOTE_DEGRADATION_COPY", http_source)
        self.assertIn("mock_cloud_bearer_token", http_source)
        self.assertIn('"phone_copy": prompt["phone_copy"]', http_source)
        self.assertIn('"speaker_prompt": prompt["speaker_prompt"]', http_source)
        self.assertIn('"elevator_assist": elevator_assist', http_source)
        self.assertIn("gateway.diagnostics()", http_source)
        self.assertNotIn("flask", source.lower())
        self.assertNotIn("aiohttp", source.lower())

        remote_source = http_source[
            http_source.index("def normalize_remote_command"):
            http_source.index("SENSITIVE_REMOTE_KEYS")
        ]
        self.assertIn("REMOTE_COMMAND_TYPES", remote_source)
        self.assertIn('"collect"', http_source)
        self.assertIn('"confirm_dropoff"', http_source)
        self.assertIn('"cancel"', http_source)
        self.assertNotIn("/cmd_vel", remote_source)
        self.assertNotIn("serial_port", remote_source)
        self.assertNotIn("baudrate", remote_source)

    def test_gateway_diagnostics_exposes_minimum_remote_support_package(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)
        diagnostics_source = DIAGNOSTICS.read_text(encoding="utf-8")
        ast.parse(diagnostics_source)
        diagnostics_block = diagnostics_source[
            diagnostics_source.index("def build_diagnostics_payload"):
        ]
        gateway_diagnostics_block = source[
            source.index("def diagnostics"):
            source.index("def start_collection")
        ]

        for field in (
            "software_version=self.software_version",
            "map_version=self.map_version",
            "route_version=self.route_version",
            "log_refs=self.log_refs",
            "vision_sample_manifest_ref=self.vision_sample_manifest_ref",
            "review_decision_log_ref=self.review_decision_log_ref",
            "hardware_proof_ref=self.hardware_proof_ref",
            "operator_status_file=self.status_file",
        ):
            self.assertIn(field, gateway_diagnostics_block)

        self.assertIn('latest_status.get("error_code") or last_task.get("error_code", "")', diagnostics_block)
        self.assertIn('latest_status.get("final_state") or last_task.get("final_state", "")', diagnostics_block)
        self.assertIn("normalize_evidence_source", diagnostics_block)
        self.assertIn("summarize_vision_manifest", diagnostics_source)
        self.assertIn("load_review_decision_log", diagnostics_source)
        self.assertIn("summarize_hardware_proof", diagnostics_source)
        self.assertIn("summarize_review_progress", diagnostics_source)
        self.assertIn("vision_samples=summarize_vision_manifest(", diagnostics_block)
        self.assertIn("decision_index=decision_index", diagnostics_block)
        self.assertIn("route_proof_summary, route_proof_source = _extract_route_proof_summary", diagnostics_block)
        self.assertIn("route_proof_status=route_proof_status", diagnostics_block)
        self.assertIn('"progress_summary"', diagnostics_source)
        self.assertIn('"decision_distribution"', diagnostics_source)
        self.assertIn('"next_pending_sample"', diagnostics_source)
        self.assertIn("hardware_proof=summarize_hardware_proof(hardware_proof_ref)", diagnostics_block)
        self.assertIn("extract_elevator_assist", diagnostics_source)
        self.assertIn("classify_elevator_assist", diagnostics_source)
        self.assertIn("elevator_assist=elevator_assist", diagnostics_block)
        self.assertIn("elevator_assist_status=elevator_assist_status", diagnostics_block)
        self.assertIn("source=", diagnostics_block)
        self.assertIn("evidence_ref=", diagnostics_block)
        self.assertIn("failure_code=", diagnostics_block)
        self.assertIn("human_intervention_required=", diagnostics_block)
        self.assertIn("state_transition_history=", diagnostics_block)
        self.assertIn(
            'latest_status.get("task_record_path") or last_task.get("task_record_path", "")',
            diagnostics_block,
        )

    def test_operator_page_exposes_hardware_proof_diagnostics_card(self):
        http_source = HTTP.read_text(encoding="utf-8")
        ast.parse(http_source)

        for text in (
            "diagHardwareProof",
            "diagHardwareProofBadge",
            "diagHardwareProofSummary",
            "diagHardwareProofNextStep",
            "diagHardwareProofReasons",
            "diagSource",
            "diagFailureCode",
            "diagEvidenceRef",
            "diagHumanIntervention",
            "diagStateTransitionHistory",
            "diagStateTransitionHistoryList",
            "diagRecoveryHint",
            "hardwareProofView",
            "renderHardwareProof",
            "hardware_proof",
            "software_proof",
            "needs_hil",
            "invalid_config",
            "read_error",
            "Software proof exists, hardware-in-loop still required",
            "reviewProgressSummary",
            "reviewDecisionDistribution",
            "reviewNextPending",
            "diagRouteProofState",
            "diagRouteProofReason",
            "diagRouteProofSource",
            "route_proof_summary",
            "route_proof_status",
            "diagElevatorAssistState",
            "diagElevatorAssistPrompt",
            "diagElevatorAssistEvidence",
            "diagElevatorAssistNextStep",
            "elevator_assist",
            "elevator_assist_status",
            "requesting_floor_help",
            "waiting_target_floor",
            "target_floor_unconfirmed",
            "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,",
            "reviewJumpPendingButton",
            "jumpToNextPending",
            "applyReviewProgress",
            "progress_summary",
            "decision_distribution",
            "next_pending_sample",
        ):
            self.assertIn(text, http_source)

        self.assertNotIn("hardware passed", http_source.lower())
        self.assertNotIn("hil passed", http_source.lower())

    def test_gateway_has_console_entry_point(self):
        source = SETUP.read_text(encoding="utf-8")

        self.assertIn(
            "operator_gateway = ros2_trashbot_behavior.operator_gateway:main",
            source,
        )

    def test_gateway_blocks_duplicate_collect_while_goal_response_is_pending(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)

        self.assertIn("self._collect_pending = False", source)
        self.assertIn("self._collect_pending = True", source)
        self.assertIn("task_active = self._collect_pending", source)
        goal_response_block = source[source.index("def _on_goal_response"):]
        self.assertIn("self._collect_pending = False", goal_response_block)

    def test_gateway_cancel_does_not_claim_canceled_before_goal_handle_exists(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)

        cancel_block = source[
            source.index("def cancel_collection"):
            source.index("def _on_goal_response")
        ]
        self.assertIn("collect goal is still pending", cancel_block)
        self.assertIn('status_payload("busy"', cancel_block)

    def test_gateway_handles_async_action_result_and_dropoff_service_errors(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)

        result_block = source[
            source.index("def _on_collect_result"):
            source.index("def _set_status")
        ]
        confirm_block = source[
            source.index("def confirm_dropoff"):
            source.index("def cancel_collection")
        ]
        self.assertIn("except Exception as exc", result_block)
        self.assertIn("finally:", result_block)
        self.assertIn("self._goal_handle = None", result_block)
        self.assertIn("self._collect_pending = False", result_block)
        self.assertIn('holder["error"]', confirm_block)
        self.assertIn("finally:", confirm_block)
        self.assertIn("confirm_dropoff service failed", confirm_block)

    def test_gateway_final_status_exposes_machine_terminal_diagnostics(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)
        result_block = source[
            source.index("def _on_collect_result"):
            source.index("def _set_status")
        ]

        self.assertIn("error_code=result.error_code", result_block)
        self.assertIn("final_state=result.final_state", result_block)
        self.assertIn('"error_code": result.error_code', result_block)
        self.assertIn('"final_state": result.final_state', result_block)
        self.assertIn("extract_elevator_assist", result_block)
        self.assertIn('"elevator_assist": elevator_assist', result_block)


if __name__ == "__main__":
    unittest.main()

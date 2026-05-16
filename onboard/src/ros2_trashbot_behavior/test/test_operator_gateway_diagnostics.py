import unittest
import json
import os
import sys
import tempfile
from pathlib import Path


BEHAVIOR_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
VISION_PACKAGE_ROOT = BEHAVIOR_PACKAGE_ROOT.parent / "ros2_trashbot_vision"
sys.path.insert(0, str(BEHAVIOR_PACKAGE_ROOT))
sys.path.insert(0, str(VISION_PACKAGE_ROOT))

from ros2_trashbot_behavior.operator_gateway_diagnostics import (
    build_diagnostics_payload,
    classify_elevator_assist,
    extract_elevator_assist,
    normalize_log_refs,
    summarize_pc_route_debug_console,
    summarize_hardware_proof,
    summarize_route_task_rehearsal_artifact,
    summarize_route_task_rehearsal_execution_bundle,
    summarize_route_task_rehearsal_operator_review,
    summarize_route_task_field_run_execution_pack,
    summarize_route_task_field_retest_execution_pack,
    summarize_route_task_field_retest_session_handoff,
    summarize_route_task_field_retest_result_intake,
    summarize_route_task_field_retest_result_reconciliation,
    summarize_route_task_field_retest_material_pack,
    summarize_route_task_field_retest_operator_drill,
    summarize_route_task_field_run_intake,
    summarize_route_task_field_run_reconciliation,
    summarize_route_task_field_run_readiness,
    summarize_route_task_field_run_review,
    summarize_route_task_completion_signal,
    summarize_route_task_terminal_completion_rehearsal,
    summarize_route_task_terminal_review_decision,
    summarize_route_task_field_run_console,
    summarize_route_task_field_run_evidence_kit,
    summarize_route_task_field_run_material_bundle,
    summarize_route_task_field_run_material_validation,
    summarize_elevator_field_run_material_validation,
    summarize_elevator_field_run_review,
    summarize_elevator_field_run_execution_pack,
    summarize_elevator_route_evidence_reconciliation,
    summarize_mobile_field_material_intake,
    summarize_mobile_field_material_review_decision,
    summarize_mobile_field_material_retest_request,
    summarize_hardware_baseline_review,
    summarize_hardware_baseline_source_alignment,
    summarize_hardware_sensor_procurement_intake,
    summarize_hardware_sensor_procurement_review_decision,
    summarize_hardware_sensor_procurement_execution_pack,
    summarize_hardware_sensor_procurement_receipt_intake,
    summarize_hardware_sensor_hil_entry_config_precheck,
    summarize_mobile_route_elevator_field_device_precheck,
    summarize_route_elevator_field_session_handoff,
    summarize_vision_manifest,
)
from ros2_trashbot_behavior.operator_gateway_http import (
    ELEVATOR_ASSIST_SPEAKER_PROMPT,
    MockCloudStore,
    _diagnostics_with_phone_task_flow,
)
from ros2_trashbot_behavior.remote_cloud_relay import (
    create_credential_rotation_artifact,
    create_network_recovery_artifact,
    create_oss_cdn_manifest_artifact,
    create_production_store_queue_artifact,
    create_production_recovery_artifact,
    create_provisioning_audit_artifact,
    create_queue_ordering_drill_artifact,
    create_transaction_isolation_artifact,
)


class OperatorGatewayDiagnosticsTest(unittest.TestCase):
    def _base_build_payload(self, latest_status):
        return build_diagnostics_payload(
            latest_status,
            software_version="",
            map_version="",
            route_version="",
            log_refs=[],
            vision_sample_manifest_ref="",
            review_decision_log_ref="",
            operator_status_file="/tmp/status.json",
        )

    def test_route_proof_summary_passthrough_and_ready_state(self):
        route_proof_summary = {
            "coverage_rate": 1.0,
            "covered_checkpoints": 3,
            "total_checkpoints": 3,
            "missing_checkpoints": [],
            "gate_status": "passed",
            "last_block_reason": "",
        }
        payload = self._base_build_payload(
            {
                "state": "waiting_for_trash",
                "route_proof_summary": route_proof_summary,
            }
        )

        self.assertEqual(payload["route_proof_summary"], route_proof_summary)
        self.assertEqual(payload["route_proof_status"]["state"], "ready")
        self.assertEqual(payload["route_proof_status"]["source"], "latest_status.route_proof_summary")
        self.assertEqual(payload["route_proof_status"]["blocking_reason"], "")

    def test_elevator_assist_passthrough_and_request_floor_help_prompt(self):
        payload = self._base_build_payload(
            {
                "state": "requesting_floor_help",
                "elevator_assist": {
                    "enabled": True,
                    "mode": "dry_run",
                    "phase": "requesting_floor_help",
                    "requires_human_help": True,
                    "target_floor": "1",
                    "evidence": {"inside_elevator": True},
                    "events": [{"phase": "entering_elevator"}, {"phase": "requesting_floor_help"}],
                },
            }
        )

        self.assertEqual(payload["elevator_assist"]["phase"], "requesting_floor_help")
        self.assertEqual(payload["elevator_assist"]["target_floor"], "1")
        self.assertEqual(payload["elevator_assist"]["speaker_prompt"], ELEVATOR_ASSIST_SPEAKER_PROMPT)
        self.assertEqual(payload["elevator_assist_status"]["state"], "needs_human_help")
        self.assertEqual(payload["elevator_assist_status"]["source"], "latest_status.elevator_assist")

    def test_elevator_assist_diagnostics_explains_unreliable_target_floor(self):
        summary = classify_elevator_assist(
            {
                "enabled": True,
                "mode": "dry_run",
                "state": "target_floor_evidence_unreliable",
                "phase": "waiting_target_floor",
                "requires_human_help": True,
                "reason": "target_floor_unconfirmed",
                "evidence": {"target_floor_unconfirmed": True},
            },
            source="last_task.elevator_assist",
        )

        self.assertEqual(summary["state"], "needs_human_help")
        self.assertIn("target_floor_unconfirmed", summary["reason"])
        self.assertIn("operator", summary["next_step"])
        self.assertEqual(summary["source"], "last_task.elevator_assist")

    def test_elevator_assist_can_be_read_from_task_record_events(self):
        with tempfile.TemporaryDirectory() as td:
            task_record_path = Path(td) / "task.json"
            task_record_path.write_text(
                json.dumps(
                    {
                        "task_id": "delivery-elevator-1",
                        "elevator_assist_events": [
                            {
                                "phase": "waiting_elevator_open",
                                "reason": "door_closed_or_unknown",
                                "evidence": {"door_closed_or_unknown": True},
                            },
                            {
                                "phase": "waiting_target_floor",
                                "state": "target_floor_unconfirmed",
                                "requires_human_help": True,
                                "target_floor": "1",
                                "reason": "target_floor_unconfirmed",
                                "evidence": {"target_floor_unconfirmed": True},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            elevator_assist, source = extract_elevator_assist(
                {"task_record_path": str(task_record_path)},
                {},
            )

        self.assertEqual(source, "task_record.elevator_assist_events")
        self.assertEqual(elevator_assist["phase"], "waiting_target_floor")
        self.assertEqual(elevator_assist["state"], "target_floor_unconfirmed")
        self.assertTrue(elevator_assist["requires_human_help"])
        self.assertEqual(elevator_assist["target_floor"], "1")
        self.assertEqual(elevator_assist["evidence"]["target_floor_unconfirmed"], True)

    def test_route_proof_summary_missing_fields_downgrades_to_unknown(self):
        payload = self._base_build_payload(
            {
                "state": "failed",
                "route_proof_summary": {
                    "coverage_rate": 0.5,
                    "covered_checkpoints": 1,
                    "total_checkpoints": 2,
                    "gate_status": "passed",
                },
            }
        )

        self.assertEqual(payload["route_proof_status"]["state"], "unknown")
        self.assertIn("missing required fields", payload["route_proof_status"]["reason"])
        self.assertIn("missing_checkpoints", payload["route_proof_status"]["missing_fields"])
        self.assertIn("last_block_reason", payload["route_proof_status"]["missing_fields"])

    def test_route_proof_summary_blocked_surfaces_reason(self):
        payload = self._base_build_payload(
            {
                "state": "failed",
                "route_proof_summary": {
                    "coverage_rate": 0.66,
                    "covered_checkpoints": 2,
                    "total_checkpoints": 3,
                    "missing_checkpoints": ["checkpoint_3"],
                    "gate_status": "passed",
                    "last_block_reason": "corridor blocked by obstacle",
                },
            }
        )

        self.assertEqual(payload["route_proof_status"]["state"], "blocked")
        self.assertEqual(payload["route_proof_status"]["blocking_reason"], "corridor blocked by obstacle")
        self.assertIn("corridor blocked by obstacle", payload["route_proof_status"]["reason"])

    def test_route_proof_summary_waiting_gate_status_wins_over_block_reason(self):
        payload = self._base_build_payload(
            {
                "state": "failed",
                "route_proof_summary": {
                    "coverage_rate": 0.25,
                    "covered_checkpoints": 1,
                    "total_checkpoints": 4,
                    "missing_checkpoints": ["checkpoint_2", "checkpoint_3", "checkpoint_4"],
                    "gate_status": "waiting_camera_frame",
                    "last_block_reason": "visual gate waiting for camera frame at checkpoint 2",
                },
            }
        )

        self.assertEqual(payload["route_proof_status"]["state"], "waiting_visual_gate")
        self.assertEqual(payload["route_proof_status"]["blocking_reason"], "")
        self.assertIn("waiting for visual gate", payload["route_proof_status"]["reason"])

    def test_route_proof_summary_empty_maps_to_unknown(self):
        payload = self._base_build_payload(
            {
                "state": "failed",
                "route_proof_summary": {},
            }
        )

        self.assertEqual(payload["route_proof_summary"], {})
        self.assertEqual(payload["route_proof_status"]["state"], "unknown")
        self.assertIn("route_proof_summary is missing", payload["route_proof_status"]["reason"])

    def test_route_proof_summary_can_be_read_from_task_record_nav_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            task_record_path = Path(td) / "task.json"
            task_record_path.write_text(
                json.dumps(
                    {
                        "task_id": "delivery-1",
                        "nav_results": [
                            {
                                "success": False,
                                "result_code": "fixed_route_failed",
                                "evidence": {
                                    "route_proof_summary": {
                                        "coverage_rate": 0.5,
                                        "covered_checkpoints": 1,
                                        "total_checkpoints": 2,
                                        "missing_checkpoints": ["checkpoint_2"],
                                        "gate_status": "passed",
                                        "last_block_reason": "",
                                    }
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            payload = self._base_build_payload(
                {
                    "state": "failed",
                    "task_record_path": str(task_record_path),
                    "last_task": {"task_record_path": str(task_record_path)},
                }
            )

        self.assertEqual(payload["route_proof_status"]["state"], "insufficient_coverage")
        self.assertEqual(
            payload["route_proof_status"]["source"],
            "task_record.nav_results.evidence.route_proof_summary",
        )
        self.assertEqual(payload["route_proof_summary"]["missing_checkpoints"], ["checkpoint_2"])

    def test_diagnostics_includes_traceability_fields_from_task_record(self):
        with tempfile.TemporaryDirectory() as td:
            task_record_path = Path(td) / "task.json"
            task_record_path.write_text(
                json.dumps(
                    {
                        "task_id": "delivery-123",
                        "source": "hil_pass",
                        "result_path": "/tmp/task_records/task-123.bin",
                        "evidence_ref": "/tmp/evidence_refs/task-123.ref.json",
                        "failure_code": "NAV_TIMEOUT",
                        "human_intervention_required": True,
                        "route_progress": {
                            "checkpoint": "cp-timeout",
                            "current_index": 2,
                            "target": {"name": "trash_station"},
                            "failure_code": "NAV_TIMEOUT",
                            "evidence_ref": "/tmp/evidence_refs/task-123.ref.json",
                            "source": "hil_pass",
                        },
                        "state_transition_history": [
                            {
                                "timestamp": 1710000000.0,
                                "event": "nav_timeout",
                                "from_state": "navigating",
                                "to_state": "error",
                                "message": "timeout waiting for gate",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            payload = self._base_build_payload(
                {
                    "state": "failed",
                    "task_record_path": str(task_record_path),
                    "error_code": "old_error",
                }
            )

        self.assertEqual(payload["source"], "hil_pass")
        self.assertEqual(payload["result_path"], "/tmp/task_records/task-123.bin")
        self.assertEqual(payload["evidence_ref"], "/tmp/evidence_refs/task-123.ref.json")
        self.assertEqual(payload["failure_code"], "NAV_TIMEOUT")
        self.assertTrue(payload["human_intervention_required"])
        self.assertEqual(payload["failure"]["result_path"], "/tmp/task_records/task-123.bin")
        self.assertEqual(payload["failure"]["evidence_ref"], "/tmp/evidence_refs/task-123.ref.json")
        self.assertEqual(payload["failure"]["failure_code"], "NAV_TIMEOUT")
        self.assertTrue(payload["failure"]["human_intervention_required"])
        self.assertEqual(payload["route_progress"]["checkpoint"], "cp-timeout")
        self.assertEqual(payload["failure"]["route_progress"]["current_index"], 2)
        self.assertEqual(payload["last_task"]["route_progress"]["target"], {"name": "trash_station"})
        self.assertEqual(payload["failure"]["source"], "hil_pass")
        self.assertEqual(payload["last_task"]["source"], "hil_pass")
        self.assertEqual(payload["last_task"]["evidence_ref"], "/tmp/task_records/task-123.bin")
        self.assertEqual(payload["last_task"]["failure_code"], "NAV_TIMEOUT")
        self.assertTrue(payload["last_task"]["human_intervention_required"])
        self.assertEqual(len(payload["failure"]["state_transition_history"]), 1)
        self.assertEqual(payload["failure"]["state_transition_history"][0]["event"], "nav_timeout")
        self.assertEqual(payload["last_task"]["state_transition_history"], payload["failure"]["state_transition_history"])

    def test_diagnostics_uses_nav_route_progress_when_top_level_empty(self):
        route_progress = {
            "checkpoint": "cp-nav",
            "current_index": 5,
            "target": {"name": "trash_station"},
            "failure_code": "",
            "evidence_ref": "/tmp/nav-route-progress.ref",
        }
        payload = self._base_build_payload(
            {
                "state": "failed",
                "route_progress": {},
                "nav_results": [
                    {
                        "evidence": {
                            "route_progress": route_progress,
                        }
                    }
                ],
            }
        )

        self.assertEqual(payload["route_progress"], route_progress)
        self.assertEqual(payload["failure"]["route_progress"], route_progress)
        self.assertEqual(payload["last_task"]["route_progress"], route_progress)

    def test_diagnostics_prefers_latest_status_terminal_fields(self):
        payload = build_diagnostics_payload(
            {
                "state": "failed",
                "message": "navigation failed",
                "error_code": "nav_failed",
                "final_state": "error",
                "task_record_path": "/tmp/current.json",
                "last_task": {
                    "error_code": "old_error",
                    "final_state": "old_state",
                    "task_record_path": "/tmp/old.json",
                },
            },
            software_version="1.2.3",
            map_version="",
            route_version="",
            log_refs=" /tmp/a.log, /tmp/b.log ",
            vision_sample_manifest_ref="/tmp/vision/manifest.json",
            review_decision_log_ref="",
            operator_status_file="/tmp/status.json",
        )

        self.assertEqual(payload["state"], "diagnostics_ready")
        self.assertIn("Diagnostics are ready", payload["phone_copy"])
        self.assertEqual(payload["speaker_prompt"], "Diagnostics are ready.")
        self.assertEqual(payload["software_version"], "1.2.3")
        self.assertEqual(payload["map_version"], "")
        self.assertEqual(payload["route_version"], "")
        self.assertEqual(payload["failure"]["error_code"], "nav_failed")
        self.assertEqual(payload["failure"]["final_state"], "error")
        self.assertEqual(payload["failure"]["task_record_path"], "/tmp/current.json")
        self.assertEqual(payload["log_refs"], ["/tmp/a.log", "/tmp/b.log"])
        self.assertEqual(payload["vision_sample_manifest_ref"], "/tmp/vision/manifest.json")
        self.assertFalse(payload["vision_samples"]["exists"])
        self.assertIn("not found", payload["vision_samples"]["read_error"])
        self.assertEqual(payload["hardware_proof"]["status"], "read_error")
        self.assertIn("not configured", payload["hardware_proof"]["read_error"])
        self.assertEqual(payload["review_decision_log"]["status"], "not_configured")
        self.assertEqual(payload["operator_status_file"], "/tmp/status.json")

    def test_diagnostics_falls_back_to_last_task_terminal_fields(self):
        payload = build_diagnostics_payload(
            {
                "state": "failed",
                "message": "delivery failed",
                "last_task": {
                    "error_code": "timed_out",
                    "final_state": "dropoff",
                    "task_record_path": "/tmp/task.json",
                    "source": "task_orchestrator",
                    "failure_code": "TASK_CANCEL",
                    "human_intervention_required": True,
                    "state_transition_history": [
                        {
                            "timestamp": 1710000000.0,
                            "event": "user_cancel",
                            "from_state": "navigating",
                            "to_state": "canceled",
                        }
                    ],
                },
            },
            software_version="",
            map_version="map-a",
            route_version="route-a",
            log_refs=["/tmp/robot.log", ""],
            vision_sample_manifest_ref="",
            review_decision_log_ref="",
            operator_status_file="/tmp/status.json",
        )

        self.assertEqual(payload["failure"]["error_code"], "timed_out")
        self.assertEqual(payload["failure"]["final_state"], "dropoff")
        self.assertEqual(payload["failure"]["task_record_path"], "/tmp/task.json")
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["evidence_ref"], "/tmp/task.json")
        self.assertEqual(payload["failure_code"], "TASK_CANCEL")
        self.assertEqual(payload["human_intervention_required"], True)
        self.assertEqual(payload["failure"]["source"], "software_proof")
        self.assertEqual(payload["failure"]["failure_code"], "TASK_CANCEL")
        self.assertEqual(payload["failure"]["human_intervention_required"], True)
        self.assertEqual(payload["map_version"], "map-a")
        self.assertEqual(payload["route_version"], "route-a")
        self.assertEqual(payload["log_refs"], ["/tmp/robot.log"])
        self.assertEqual(payload["vision_samples"]["integrity_summary"]["status"], "not_configured")
        self.assertEqual(payload["vision_samples"]["integrity_error_count"], 1)
        self.assertEqual(payload["hardware_proof"]["status"], "read_error")
        self.assertEqual(payload["review_decision_log"]["status"], "not_configured")

    def test_diagnostics_prefers_task_record_fields_over_last_task_evidence_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            task_record_path = Path(td) / "task_record.json"
            task_record_path.write_text(
                json.dumps(
                    {
                        "task_id": "delivery-456",
                        "result_path": "/tmp/task_record_result.bin",
                        "evidence_ref": "/tmp/task_record_evidence.ref.json",
                        "source": "hil_pass",
                        "failure_code": "NAV_FAIL",
                        "human_intervention_required": True,
                        "state_transition_history": [
                            {
                                "timestamp": 1710000001.0,
                                "event": "navigation_failed",
                                "from_state": "navigating",
                                "to_state": "error",
                                "message": "navigation failed from task record",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            payload = self._base_build_payload(
                {
                    "state": "failed",
                    "task_record_path": str(task_record_path),
                    "last_task": {
                        "task_record_path": str(task_record_path),
                        "result_path": "/tmp/legacy_result.bin",
                        "evidence_ref": "/tmp/legacy_evidence.ref.json",
                        "failure_code": "LEGACY_FAIL",
                        "human_intervention_required": False,
                    },
                }
            )

        self.assertEqual(payload["result_path"], "/tmp/task_record_result.bin")
        self.assertEqual(payload["evidence_ref"], "/tmp/task_record_evidence.ref.json")
        self.assertEqual(payload["source"], "hil_pass")
        self.assertEqual(payload["failure_code"], "NAV_FAIL")
        self.assertTrue(payload["human_intervention_required"])
        self.assertEqual(payload["failure"]["result_path"], "/tmp/task_record_result.bin")
        self.assertEqual(payload["failure"]["evidence_ref"], "/tmp/task_record_evidence.ref.json")
        self.assertEqual(payload["last_task"]["result_path"], "/tmp/task_record_result.bin")
        self.assertEqual(payload["last_task"]["evidence_ref"], "/tmp/task_record_evidence.ref.json")

    def test_diagnostics_prefers_task_record_trace_fields(self):
        with tempfile.TemporaryDirectory() as td:
            task_record_path = Path(td) / "task.json"
            task_record_path.write_text(
                json.dumps(
                    {
                        "task_id": "delivery-999",
                        "result_path": "/tmp/task_record_result.bin",
                        "evidence_ref": "/tmp/task_record_evidence.ref",
                        "source": "hil_pass",
                        "failure_code": "NAV_FAIL",
                        "human_intervention_required": True,
                        "state_transition_history": [
                            {
                                "timestamp": 1710000003.0,
                                "event": "navigation_failed",
                                "from_state": "navigating",
                                "to_state": "error",
                                "message": "task record history",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            payload = self._base_build_payload(
                {
                    "state": "failed",
                    "task_record_path": str(task_record_path),
                    "result_path": "/tmp/latest-result.bin",
                    "evidence_ref": "/tmp/outer-evidence.bin",
                    "source": "software_proof",
                    "failure_code": "TASK_CANCEL",
                    "human_intervention_required": False,
                    "state_transition_history": [
                        {
                            "timestamp": 1710000000.0,
                            "event": "latest_status",
                            "from_state": "loaded",
                            "to_state": "error",
                        }
                    ],
                }
            )

        self.assertEqual(payload["source"], "hil_pass")
        self.assertEqual(payload["result_path"], "/tmp/task_record_result.bin")
        self.assertEqual(payload["evidence_ref"], "/tmp/task_record_evidence.ref")
        self.assertEqual(payload["failure_code"], "NAV_FAIL")
        self.assertTrue(payload["human_intervention_required"])
        self.assertEqual(
            payload["failure"]["state_transition_history"][0]["event"],
            "navigation_failed",
        )
        self.assertEqual(
            payload["last_task"]["state_transition_history"][0]["event"],
            "navigation_failed",
        )

    def test_diagnostics_reuses_last_task_state_transition_when_task_record_unreadable(self):
        with tempfile.TemporaryDirectory() as td:
            task_record_path = Path(td) / "corrupt_task.json"
            task_record_path.write_text("{bad json", encoding="utf-8")
            payload = build_diagnostics_payload(
                {
                    "state": "failed",
                    "task_record_path": str(task_record_path),
                    "result_path": "/tmp/latest-result.bin",
                    "evidence_ref": "/tmp/outer-evidence.bin",
                    "source": "software_proof",
                    "failure_code": "TASK_CANCEL",
                    "human_intervention_required": True,
                    "state_transition_history": [
                        {
                            "timestamp": 1710000001.0,
                            "event": "latest_state_transition",
                            "from_state": "navigating",
                            "to_state": "error",
                        }
                    ],
                    "last_task": {
                        "result_path": "/tmp/legacy.bin",
                        "evidence_ref": "/tmp/legacy-evidence.bin",
                        "failure_code": "NAV_TIMEOUT",
                        "human_intervention_required": False,
                        "state_transition_history": [
                            {
                                "timestamp": 1710000002.0,
                                "event": "legacy_history",
                                "from_state": "delivering",
                                "to_state": "error",
                            }
                        ],
                    },
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
            )

        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["result_path"], "/tmp/latest-result.bin")
        self.assertEqual(payload["evidence_ref"], "/tmp/outer-evidence.bin")
        self.assertEqual(payload["failure_code"], "TASK_CANCEL")
        self.assertTrue(payload["human_intervention_required"])
        self.assertEqual(payload["failure"]["state_transition_history"][0]["event"], "legacy_history")
        self.assertEqual(payload["last_task"]["state_transition_history"][0]["event"], "legacy_history")

    def test_hardware_proof_ready_with_hil_risk_maps_to_needs_hil(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "software_proof_ready",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "risk_flags": [
                            {
                                "id": "hil_required",
                                "severity": "high",
                                "detail": "Offline proof still needs hardware-in-loop.",
                            }
                        ],
                        "hil_recipe": {"no_motion": "python3 onboard/scripts/hardware_smoke_wave_rover.py"},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "needs_hil")
        self.assertEqual(summary["source_status"], "software_proof_ready")
        self.assertTrue(summary["exists"])
        self.assertEqual(summary["vendor_sources"], ["docs/vendor/VENDOR_INDEX.md"])
        self.assertEqual(summary["risk_flags"][0]["id"], "hil_required")
        self.assertIn("hardware-in-loop still required", summary["summary"])
        self.assertNotIn("hardware passed", summary["summary"].lower())
        self.assertNotIn("hil passed", summary["summary"].lower())

    def test_hardware_proof_ready_without_hil_risk_maps_to_software_proof(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "software_proof_ready",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "risk_flags": [
                            {
                                "id": "doc_review",
                                "severity": "medium",
                                "detail": "Keep vendor references with the support package.",
                            }
                        ],
                        "hil_recipe": {},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "software_proof")
        self.assertIn("Software proof is ready only", summary["summary"])
        self.assertIn("does not validate real UART", summary["summary"])

    def test_hardware_proof_invalid_config_maps_to_invalid_config(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "invalid_config",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "config_validation": {"error": "track_width_m must be positive"},
                        "risk_flags": [],
                        "hil_recipe": {},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "invalid_config")
        self.assertEqual(summary["read_error"], "track_width_m must be positive")
        self.assertIn("Fix the reported bridge configuration", summary["next_step"])

    def test_hardware_proof_feedback_parse_failed_stays_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "feedback_parse_failed",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "risk_flags": [],
                        "hil_recipe": {},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "needs_hil")
        self.assertIn("feedback parsing failed", summary["summary"])

    def test_hardware_proof_read_errors_are_structured(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "missing.json"
            corrupt = root / "corrupt.json"
            non_dict = root / "non-dict.json"
            missing_status = root / "missing-status.json"
            corrupt.write_text("{bad json", encoding="utf-8")
            non_dict.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            missing_status.write_text(json.dumps({"risk_flags": []}), encoding="utf-8")

            missing_summary = summarize_hardware_proof(str(missing))
            corrupt_summary = summarize_hardware_proof(str(corrupt))
            non_dict_summary = summarize_hardware_proof(str(non_dict))
            missing_status_summary = summarize_hardware_proof(str(missing_status))

        self.assertEqual(missing_summary["status"], "read_error")
        self.assertFalse(missing_summary["exists"])
        self.assertIn("not found", missing_summary["read_error"])
        self.assertEqual(corrupt_summary["status"], "read_error")
        self.assertTrue(corrupt_summary["exists"])
        self.assertIn("failed reading", corrupt_summary["read_error"])
        self.assertEqual(non_dict_summary["status"], "read_error")
        self.assertIn("must be an object", non_dict_summary["read_error"])
        self.assertEqual(missing_status_summary["status"], "read_error")
        self.assertIn("missing status", missing_status_summary["read_error"])

    def test_diagnostics_payload_includes_configured_hardware_proof(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps({"status": "software_proof_ready", "risk_flags": [], "vendor_sources": []}),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_proof_ref=str(proof_path),
            )

        self.assertEqual(payload["hardware_proof"]["status"], "software_proof")
        self.assertEqual(payload["hardware_proof"]["artifact_ref"], str(proof_path))

    def test_diagnostics_payload_includes_phone_safe_route_task_rehearsal_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "route_task_rehearsal_artifact.json"
            artifact_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_artifact",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_route_task_rehearsal_artifact_gate",
                        "evidence_ref": str(Path(td) / "route_replay_evidence.json"),
                        "crosscheck_status": {
                            "status": "pass",
                            "scope": "status/replay/task_record software alignment only",
                            "software_mismatches": [],
                        },
                        "hil_alignment_status": {
                            "status": "software_proof",
                            "alignment_status": "not_proven",
                            "evidence_ref_match": False,
                            "detail": (
                                "not real HIL; Authorization: Bearer secret-token "
                                "postgres://robot:secret@db.local/queue /dev/ttyUSB0 baudrate=115200"
                            ),
                            "mismatches": [],
                            "not_real_hil_when_status_is_missing_blocked_or_software_proof": True,
                        },
                        "not_proven": ["real_hil_pass", "delivery_success"],
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_rehearsal_artifact_ref=str(artifact_path),
            )
            summary = payload["route_task_rehearsal"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["state"], "crosscheck_pass")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_rehearsal_diagnostics_gate",
        )
        self.assertEqual(
            summary["source_evidence_boundary"],
            "software_proof_docker_route_task_rehearsal_artifact_gate",
        )
        self.assertEqual(summary["crosscheck_status"]["status"], "pass")
        self.assertEqual(summary["hil_alignment_status"]["alignment_status"], "not_proven")
        self.assertIn("local_path_redacted:route_replay_evidence.json", summary["evidence_ref"])
        self.assertIn("not delivery success", summary["safe_phone_copy"])
        self.assertIn("real_hil_pass", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        for forbidden in (
            str(artifact_path),
            str(Path(td)),
            "secret-token",
            "Authorization:",
            "postgres://",
            "/dev/ttyUSB0",
            "baudrate=115200",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_route_task_rehearsal_missing_and_sensitive_path_stays_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            missing_path = Path(td) / "Bearer-secret-token" / "missing.json"
            summary = summarize_route_task_rehearsal_artifact(str(missing_path))
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["state"], "missing")
        self.assertFalse(summary["exists"])
        self.assertIn("software_proof_docker_route_task_rehearsal_diagnostics_gate", encoded)
        self.assertIn("not delivery success", summary["safe_phone_copy"])
        self.assertIn("not_proven", summary)
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_route_task_rehearsal_crosscheck_fail_stays_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "route_task_rehearsal_fail.json"
            artifact_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_artifact",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_route_task_rehearsal_artifact_gate",
                        "evidence_ref": "evidence://route-task-1",
                        "crosscheck_status": {
                            "status": "fail",
                            "software_mismatches": ["task_record evidence_ref mismatch at /tmp/raw.json"],
                        },
                        "hil_alignment_status": {"alignment_status": "not_proven"},
                        "not_proven": ["delivery_success"],
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_route_task_rehearsal_artifact(str(artifact_path))
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["state"], "crosscheck_fail")
        self.assertEqual(summary["crosscheck_status"]["software_mismatch_count"], 1)
        self.assertIn("not_proven", summary["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertNotIn("/tmp/raw.json", encoded)

    def test_diagnostics_payload_includes_route_task_rehearsal_execution_bundle_summary(self):
        with tempfile.TemporaryDirectory() as td:
            bundle_path = Path(td) / "route_task_rehearsal_execution_bundle.json"
            bundle_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_execution_bundle",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_rehearsal_execution_bundle_gate"
                        ),
                        "evidence_ref": str(Path(td) / "route_task_execution.ref.json"),
                        "artifact_ref": str(Path(td) / "route_task_rehearsal_artifact.json"),
                        "crosscheck_status": {
                            "status": "pass",
                            "scope": "status/replay/task_record software alignment only",
                            "software_mismatches": [],
                        },
                        "hil_alignment_status": {
                            "status": "software_proof",
                            "alignment_status": "not_proven",
                            "detail": "not real HIL; Bearer secret-token /dev/ttyUSB0 baudrate=115200",
                            "mismatches": [],
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_rehearsal_bundle_ref=str(bundle_path),
            )
            summary = payload["route_task_rehearsal_execution_bundle"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["state"], "crosscheck_pass")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_rehearsal_execution_bundle_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_rehearsal_execution_bundle")
        self.assertEqual(summary["crosscheck_status"]["status"], "pass")
        self.assertEqual(summary["hil_alignment_status"]["alignment_status"], "not_proven")
        self.assertIn("local_path_redacted:route_task_execution.ref.json", summary["evidence_ref"])
        self.assertIn("local_path_redacted:route_task_rehearsal_artifact.json", summary["artifact_ref"])
        self.assertIn("not delivery success", summary["safe_phone_copy"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        for forbidden in (
            str(bundle_path),
            str(Path(td)),
            "secret-token",
            "/dev/ttyUSB0",
            "baudrate=115200",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_route_task_rehearsal_execution_bundle_env_and_fail_stay_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            bundle_path = Path(td) / "route_task_rehearsal_execution_bundle_fail.json"
            bundle_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_execution_bundle",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_rehearsal_execution_bundle_gate"
                        ),
                        "evidence_ref": "evidence://route-task-execution-1",
                        "diagnostics_summary": {
                            "crosscheck_status": {
                                "status": "fail",
                                "software_mismatches": ["task_record mismatch at /tmp/raw.json"],
                            },
                            "hil_alignment_status": {"alignment_status": "not_proven"},
                        },
                        "not_proven": ["delivery_success"],
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE")
            os.environ["TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE"] = str(bundle_path)
            try:
                payload = self._base_build_payload({"state": "waiting_for_trash"})
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE"] = previous
            summary = payload["route_task_rehearsal_execution_bundle"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["state"], "crosscheck_fail")
        self.assertEqual(summary["crosscheck_status"]["software_mismatch_count"], 1)
        self.assertIn("not_proven", summary["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertNotIn("/tmp/raw.json", encoded)

    def test_route_task_rehearsal_execution_bundle_missing_or_invalid_is_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            missing_path = Path(td) / "Bearer-secret-token" / "missing.json"
            missing_summary = summarize_route_task_rehearsal_execution_bundle(str(missing_path))
            invalid_path = Path(td) / "invalid_bundle.json"
            invalid_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_artifact",
                        "evidence_boundary": "software_proof_docker_route_task_rehearsal_artifact_gate",
                    }
                ),
                encoding="utf-8",
            )
            invalid_summary = summarize_route_task_rehearsal_execution_bundle(str(invalid_path))
            encoded = json.dumps([missing_summary, invalid_summary], ensure_ascii=False)

        self.assertEqual(missing_summary["state"], "missing")
        self.assertEqual(invalid_summary["state"], "unsupported_schema")
        self.assertIn("software_proof_docker_route_task_rehearsal_execution_bundle_gate", encoded)
        self.assertIn("not delivery success", missing_summary["safe_phone_copy"])
        self.assertFalse(missing_summary["primary_actions_enabled"])
        self.assertFalse(invalid_summary["delivery_success"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_rehearsal_operator_review_summary(self):
        with tempfile.TemporaryDirectory() as td:
            review_path = Path(td) / "route_task_rehearsal_operator_review.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_operator_review.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_rehearsal_operator_review_gate"
                        ),
                        "evidence_ref": str(Path(td) / "route_task_review.ref.json"),
                        "crosscheck_status": {
                            "status": "pass",
                            "scope": "status/replay/task_record software alignment only",
                            "software_mismatches": [],
                        },
                        "hil_alignment_status": {
                            "status": "software_proof",
                            "alignment_status": "not_proven",
                            "evidence_ref_match": False,
                            "detail": "not real HIL; /dev/ttyUSB0 baudrate=115200",
                            "mismatches": [],
                        },
                        "mismatch_summary": {
                            "software_mismatch_count": 0,
                            "hil_mismatch_count": 0,
                            "items": [],
                        },
                        "next_rehearsal_decision": "keep review read-only and collect real HIL later",
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "safe_copy": "Operator review is software proof only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_rehearsal_operator_review_ref=str(review_path),
            )
            summary = payload["route_task_rehearsal_operator_review"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["overall_status"], "degraded")
        self.assertEqual(summary["state"], "crosscheck_pass")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_rehearsal_operator_review_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_rehearsal_operator_review.v1")
        self.assertEqual(summary["crosscheck_status"]["status"], "pass")
        self.assertEqual(summary["hil_alignment_status"]["alignment_status"], "not_proven")
        self.assertIn("local_path_redacted:route_task_review.ref.json", summary["evidence_ref"])
        self.assertEqual(summary["next_rehearsal_decision"], "keep review read-only and collect real HIL later")
        self.assertIn("not delivery success", summary["safe_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        for forbidden in (
            str(review_path),
            str(Path(td)),
            "/dev/ttyUSB0",
            "baudrate=115200",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_route_task_rehearsal_operator_review_env_fail_and_unsafe_copy_block(self):
        with tempfile.TemporaryDirectory() as td:
            fail_path = Path(td) / "route_task_rehearsal_operator_review_fail.json"
            fail_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_operator_review.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_rehearsal_operator_review_gate"
                        ),
                        "evidence_ref": "evidence://route-task-review-1",
                        "crosscheck_status": {
                            "status": "fail",
                            "software_mismatches": ["task_record mismatch at /tmp/raw.json"],
                        },
                        "hil_alignment_status": {
                            "alignment_status": "not_proven",
                            "mismatches": ["HIL missing at /tmp/hil.json"],
                        },
                        "not_proven": ["delivery_success"],
                        "safe_copy": "Operator review is software proof only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW")
            os.environ["TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW"] = str(fail_path)
            try:
                payload = self._base_build_payload({"state": "waiting_for_trash"})
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW"] = previous
            fail_summary = payload["route_task_rehearsal_operator_review"]

            unsafe_path = Path(td) / "unsafe_review.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_operator_review.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_rehearsal_operator_review_gate"
                        ),
                        "crosscheck_status": {"status": "pass"},
                        "safe_copy": "Operator review confirms delivery success and ACK posted.",
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_rehearsal_operator_review(str(unsafe_path))
            encoded = json.dumps([fail_summary, unsafe_summary], ensure_ascii=False)

        self.assertEqual(fail_summary["overall_status"], "blocked")
        self.assertEqual(fail_summary["state"], "crosscheck_fail")
        self.assertEqual(fail_summary["mismatch_summary"]["software_mismatch_count"], 1)
        self.assertEqual(fail_summary["mismatch_summary"]["hil_mismatch_count"], 1)
        self.assertIn("not_proven", fail_summary["safe_copy"])
        self.assertFalse(fail_summary["primary_actions_enabled"])
        self.assertEqual(unsafe_summary["state"], "unsafe_copy")
        self.assertEqual(unsafe_summary["overall_status"], "blocked")
        self.assertIn("safe_copy is missing or unsafe", unsafe_summary["read_error"])
        self.assertFalse(unsafe_summary["ack_post_allowed"])
        self.assertNotIn("/tmp/raw.json", encoded)
        self.assertNotIn("/tmp/hil.json", encoded)

    def test_route_task_rehearsal_operator_review_missing_and_unsupported_are_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            missing_path = Path(td) / "Bearer-secret-token" / "missing_review.json"
            missing_summary = summarize_route_task_rehearsal_operator_review(str(missing_path))
            invalid_path = Path(td) / "invalid_review.json"
            invalid_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_execution_bundle",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_rehearsal_execution_bundle_gate"
                        ),
                    }
                ),
                encoding="utf-8",
            )
            invalid_summary = summarize_route_task_rehearsal_operator_review(str(invalid_path))
            encoded = json.dumps([missing_summary, invalid_summary], ensure_ascii=False)

        self.assertEqual(missing_summary["state"], "missing")
        self.assertEqual(invalid_summary["state"], "unsupported_schema")
        self.assertEqual(missing_summary["overall_status"], "blocked")
        self.assertEqual(invalid_summary["overall_status"], "blocked")
        self.assertIn("software_proof_docker_route_task_rehearsal_operator_review_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(missing_summary["delivery_success"])
        self.assertFalse(invalid_summary["primary_actions_enabled"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_pc_route_debug_console_metadata_only_summary(self):
        with tempfile.TemporaryDirectory() as td:
            console_path = Path(td) / "pc_route_debug_console.json"
            console_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.pc_route_debug_console.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_pc_route_debug_console_gate"
                        ),
                        "availability": {
                            "status": "available",
                            "reason": "route debug console rendered from local JSON only",
                        },
                        "route_debug_status": {
                            "status": "available",
                            "current_checkpoint": "cp-02",
                            "target": "trash_station",
                            "matching_status": "matched",
                            "failure_reason": "",
                        },
                        "route_progress": {
                            "checkpoint": "cp-02",
                            "current_index": 2,
                            "target": {"name": "trash_station"},
                            "raw_path": str(Path(td) / "raw_status.json"),
                        },
                        "keyframe_preflight": {
                            "status": "passed",
                            "detail": "Bearer secret-token /dev/ttyUSB0 baudrate=115200",
                        },
                        "recent_task_summary": {
                            "task_id": "task-1",
                            "final_status": "software_rehearsal_only",
                        },
                        "route_elevator_reconciliation": {
                            "evidence_boundary": (
                                "software_proof_docker_pc_route_elevator_console_integration_gate"
                            ),
                            "availability": {
                                "status": "available",
                                "reason": "same evidence_ref route and elevator summaries visible",
                            },
                            "reconciliation_status": {
                                "status": "available",
                                "verdict": "metadata_only_reconciled_not_proven",
                            },
                            "elevator_assist_status": {
                                "state": "needs_human_help",
                                "phase": "waiting_target_floor",
                            },
                            "route_completion_status": {
                                "state": "metadata_only",
                                "dropoff_completion": False,
                            },
                            "operator_next_steps": [
                                "Review same evidence_ref before field-run claims.",
                            ],
                            "not_proven": ["delivery_success", "real_elevator_operation"],
                            "safe_copy": (
                                "Route elevator reconciliation is metadata-only; "
                                "not delivery success."
                            ),
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "safe_copy": "PC route debug console is metadata-only software proof; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                pc_route_debug_console_ref=str(console_path),
            )
            summary = payload["pc_route_debug_console"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary["overall_status"], "degraded")
        self.assertEqual(summary["state"], "available")
        self.assertEqual(summary["schema"], "trashbot.pc_route_debug_console_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_pc_route_debug_console_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.pc_route_debug_console.v1")
        self.assertEqual(summary["availability"]["status"], "available")
        self.assertEqual(summary["route_debug_status"]["current_checkpoint"], "cp-02")
        self.assertEqual(summary["route_progress"]["target"]["name"], "trash_station")
        self.assertEqual(summary["keyframe_preflight"]["status"], "passed")
        nested = summary["route_elevator_reconciliation"]
        self.assertEqual(nested["overall_status"], "degraded")
        self.assertEqual(nested["state"], "available")
        self.assertEqual(
            nested["evidence_boundary"],
            "software_proof_docker_pc_route_elevator_console_integration_gate",
        )
        self.assertEqual(
            nested["source_evidence_boundary"],
            "software_proof_docker_pc_route_debug_console_gate",
        )
        self.assertEqual(nested["reconciliation_status"]["status"], "available")
        self.assertEqual(nested["elevator_assist_status"]["phase"], "waiting_target_floor")
        self.assertIn("same evidence_ref", nested["operator_next_steps"][0])
        self.assertIn("delivery_success", nested["not_proven"])
        self.assertIn("remote_ack", nested["not_proven"])
        self.assertIn("terminal_ack", nested["not_proven"])
        self.assertFalse(nested["primary_actions_enabled"])
        self.assertFalse(nested["ack_post_allowed"])
        self.assertFalse(nested["remote_ack_allowed"])
        self.assertFalse(nested["cursor_updates_allowed"])
        self.assertFalse(nested["persistence_updates_allowed"])
        self.assertFalse(nested["terminal_ack_allowed"])
        self.assertFalse(nested["nav2_triggered"])
        self.assertFalse(nested["hil_pass"])
        self.assertFalse(nested["dropoff_completion"])
        self.assertFalse(nested["cancel_completion"])
        self.assertFalse(nested["delivery_success"])
        self.assertIn("not delivery success", summary["safe_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        for forbidden in (
            str(console_path),
            str(Path(td)),
            "secret-token",
            "/dev/ttyUSB0",
            "baudrate=115200",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_pc_route_debug_console_env_missing_unsupported_and_unsafe_stay_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            blocked_path = Path(td) / "pc_route_debug_console_blocked.json"
            blocked_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.pc_route_debug_console.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_pc_route_debug_console_gate"
                        ),
                        "availability": {
                            "status": "blocked",
                            "reason": "missing fixed_route status JSON",
                        },
                        "route_debug_status": {
                            "status": "not_proven",
                            "failure_reason": "input missing",
                        },
                        "not_proven": ["delivery_success"],
                        "safe_copy": "PC route debug console is metadata-only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_PC_ROUTE_DEBUG_CONSOLE")
            os.environ["TRASHBOT_PC_ROUTE_DEBUG_CONSOLE"] = str(blocked_path)
            try:
                payload = self._base_build_payload({"state": "waiting_for_trash"})
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_PC_ROUTE_DEBUG_CONSOLE", None)
                else:
                    os.environ["TRASHBOT_PC_ROUTE_DEBUG_CONSOLE"] = previous
            blocked_summary = payload["pc_route_debug_console"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_console.json"
            missing_summary = summarize_pc_route_debug_console(str(missing_path))
            unsupported_path = Path(td) / "unsupported_console.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_rehearsal_operator_review.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_rehearsal_operator_review_gate"
                        ),
                        "safe_copy": "Unsupported summary is not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_pc_route_debug_console(str(unsupported_path))
            unsafe_path = Path(td) / "unsafe_console.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.pc_route_debug_console.v1",
                        "evidence_boundary": (
                            "software_proof_docker_pc_route_debug_console_gate"
                        ),
                        "availability": {"status": "available"},
                        "safe_copy": "PC console confirms delivery success and ACK posted.",
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_pc_route_debug_console(str(unsafe_path))
            unsafe_nested_path = Path(td) / "unsafe_nested_console.json"
            unsafe_nested_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.pc_route_debug_console.v1",
                        "evidence_boundary": (
                            "software_proof_docker_pc_route_debug_console_gate"
                        ),
                        "availability": {"status": "available"},
                        "route_elevator_reconciliation": {
                            "evidence_boundary": (
                                "software_proof_docker_pc_route_elevator_console_integration_gate"
                            ),
                            "availability": {"status": "available"},
                            "reconciliation_status": {"status": "available"},
                            "safe_copy": (
                                "Route elevator reconciliation confirms delivery success "
                                "and ACK posted."
                            ),
                            "delivery_success": True,
                            "primary_actions_enabled": True,
                            "ack_post_allowed": True,
                            "nav2_triggered": True,
                            "hil_pass": True,
                        },
                        "safe_copy": "PC route debug console is metadata-only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            unsafe_nested_summary = summarize_pc_route_debug_console(str(unsafe_nested_path))
            encoded = json.dumps(
                [
                    blocked_summary,
                    missing_summary,
                    unsupported_summary,
                    unsafe_summary,
                    unsafe_nested_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(blocked_summary["overall_status"], "blocked")
        self.assertEqual(blocked_summary["state"], "blocked")
        self.assertEqual(missing_summary["state"], "missing")
        self.assertEqual(unsupported_summary["state"], "unsupported_schema")
        self.assertEqual(unsafe_summary["state"], "unsafe_copy")
        self.assertEqual(
            blocked_summary["route_elevator_reconciliation"]["state"],
            "not_configured",
        )
        self.assertEqual(
            unsafe_nested_summary["route_elevator_reconciliation"]["state"],
            "unsafe_fields",
        )
        self.assertIn("software_proof_docker_pc_route_debug_console_gate", encoded)
        self.assertIn("software_proof_docker_pc_route_elevator_console_integration_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertIn(
            "delivery_success",
            unsafe_nested_summary["route_elevator_reconciliation"]["not_proven"],
        )
        self.assertFalse(blocked_summary["primary_actions_enabled"])
        self.assertFalse(missing_summary["delivery_success"])
        self.assertFalse(unsupported_summary["ack_post_allowed"])
        self.assertFalse(unsafe_summary["cursor_updates_allowed"])
        self.assertFalse(unsafe_nested_summary["primary_actions_enabled"])
        self.assertFalse(unsafe_nested_summary["route_elevator_reconciliation"]["delivery_success"])
        self.assertFalse(unsafe_nested_summary["route_elevator_reconciliation"]["ack_post_allowed"])
        self.assertFalse(unsafe_nested_summary["route_elevator_reconciliation"]["nav2_triggered"])
        self.assertFalse(unsafe_nested_summary["route_elevator_reconciliation"]["hil_pass"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_readiness_summary(self):
        with tempfile.TemporaryDirectory() as td:
            readiness_path = Path(td) / "route_task_field_run_readiness.json"
            readiness_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_readiness.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_readiness_gate"
                        ),
                        "overall_status": "ready_for_field_run_materials",
                        "evidence_ref": "evidence://route-task-field-run-1",
                        "same_evidence_ref_required": True,
                        "required_field_run_materials": [
                            "route status",
                            "task record",
                            "Nav2/fixed-route runtime log",
                        ],
                        "missing_materials": ["real HIL packet", "support-safe mobile summary"],
                        "commands_to_run": [
                            "python3 pc-tools/evidence/route_task_field_run_readiness.py --once-json"
                        ],
                        "phone_support_safe_summary": {
                            "availability": {
                                "status": "available",
                                "reason": "handoff metadata ready for the next Docker-local review",
                            },
                            "next_evidence_summary": (
                                "Collect the missing field-run materials with the same evidence_ref."
                            ),
                            "safe_copy": (
                                "Route-task field-run readiness is metadata-only; not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_readiness_ref=str(readiness_path),
            )
            summary = payload["route_task_field_run_readiness"]
            summary_alias = payload["route_task_field_run_readiness_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["overall_status"], "ready_for_field_run_materials")
        self.assertEqual(summary["state"], "available")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_readiness_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_readiness_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_readiness.v1")
        self.assertEqual(summary["availability"]["status"], "available")
        self.assertEqual(summary["evidence_ref"], "evidence://route-task-field-run-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertIn("support-safe mobile summary", summary["next_evidence"]["missing_materials"])
        self.assertIn("route status", summary["next_evidence"]["required_field_run_materials"])
        self.assertIn("route_task_field_run_readiness.py", summary["commands_summary"][0])
        self.assertIn("not delivery success", summary["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("objective_5_external_proof", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertNotIn(str(readiness_path), encoded)

    def test_route_task_field_run_readiness_env_missing_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "route_task_field_run_readiness_env.json"
            env_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_readiness.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_readiness_gate"
                        ),
                        "overall_status": "blocked_missing_material",
                        "evidence_ref": "evidence://route-task-field-run-2",
                        "same_evidence_ref_required": True,
                        "missing_materials": ["robot-side task evidence"],
                        "commands_to_run": ["collect support-safe mobile summary"],
                        "phone_support_safe_summary": {
                            "availability": {
                                "status": "blocked",
                                "reason": "missing robot-side task evidence",
                            },
                            "safe_copy": "Route-task field-run readiness is metadata-only; not_proven.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_READINESS")
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_READINESS"] = str(env_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_readiness"
                ]
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_READINESS", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_READINESS"] = previous

            missing_path = Path(td) / "Bearer-secret-token" / "missing_readiness.json"
            missing_summary = summarize_route_task_field_run_readiness(str(missing_path))

            unsupported_path = Path(td) / "unsupported_readiness.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.pc_route_debug_console.v1",
                        "evidence_boundary": "software_proof_docker_pc_route_debug_console_gate",
                        "safe_copy": "Unsupported readiness is metadata-only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_readiness(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_readiness.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_readiness.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_readiness_gate"
                        ),
                        "overall_status": "ready_for_field_run_materials",
                        "evidence_ref": "evidence://unsafe-readiness",
                        "primary_actions_enabled": True,
                        "phone_support_safe_summary": {
                            "safe_copy": "Readiness confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_readiness(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["overall_status"], "blocked_missing_material")
        self.assertEqual(env_summary["state"], "blocked")
        self.assertEqual(missing_summary["state"], "missing")
        self.assertEqual(unsupported_summary["state"], "unsupported_schema")
        self.assertEqual(unsafe_summary["state"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_run_readiness_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(missing_summary["delivery_success"])
        self.assertFalse(unsupported_summary["ack_post_allowed"])
        self.assertFalse(unsafe_summary["cursor_updates_allowed"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_intake_summary(self):
        with tempfile.TemporaryDirectory() as td:
            intake_path = Path(td) / "route_task_field_run_intake.json"
            intake_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_intake_crosscheck.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
                        ),
                        "overall_status": "crosscheck_pass",
                        "evidence_ref": "evidence://route-task-field-run-intake-1",
                        "same_evidence_ref_required": True,
                        "missing_materials": ["real HIL packet"],
                        "mismatch_reasons": ["mobile summary evidence_ref missing"],
                        "commands_to_rerun": [
                            "python3 pc-tools/evidence/route_task_field_run_intake.py --once-json"
                        ],
                        "phone_support_safe_summary": {
                            "availability": {
                                "status": "available",
                                "reason": "metadata-only intake summary ready for review",
                            },
                            "crosscheck_status": "crosscheck_pass",
                            "safe_copy": (
                                "Route-task field-run intake is metadata-only; "
                                "not delivery success and not HIL."
                            ),
                        },
                        "raw_artifacts": {
                            "route_status_json": f"{td}/raw-route-status.json",
                            "trace": "Authorization: Bearer secret-token /dev/ttyUSB0 baudrate=115200",
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_intake_ref=str(intake_path),
            )
            summary = payload["route_task_field_run_intake"]
            summary_alias = payload["route_task_field_run_intake_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["overall_status"], "crosscheck_pass")
        self.assertEqual(summary["state"], "available")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_intake_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_intake_crosscheck_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_intake_crosscheck.v1")
        self.assertEqual(summary["availability"]["status"], "available")
        self.assertEqual(summary["evidence_ref"], "evidence://route-task-field-run-intake-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertIn("real HIL packet", summary["crosscheck"]["missing_materials"])
        self.assertIn("mobile summary evidence_ref missing", summary["crosscheck"]["mismatch_reasons"])
        self.assertIn("route_task_field_run_intake.py", summary["crosscheck"]["commands_to_rerun"][0])
        self.assertIn("metadata-only", summary["safe_phone_copy"])
        self.assertIn("not delivery success", summary["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("ack_post", summary["not_proven"])
        self.assertIn("cursor_advance_or_persistence", summary["not_proven"])
        self.assertIn("objective_5_external_proof", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        for forbidden in (
            str(intake_path),
            str(Path(td)),
            "raw-route-status.json",
            "secret-token",
            "Authorization:",
            "/dev/ttyUSB0",
            "baudrate=115200",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_route_task_field_run_intake_env_missing_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "route_task_field_run_intake_env.json"
            env_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_intake_crosscheck.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
                        ),
                        "overall_status": "blocked_mismatch",
                        "evidence_ref": "evidence://route-task-field-run-intake-2",
                        "same_evidence_ref_required": True,
                        "mismatch_reasons": ["task_record evidence_ref mismatch"],
                        "commands_to_rerun": ["collect route status and task record with one evidence_ref"],
                        "phone_support_safe_summary": {
                            "availability": {
                                "status": "blocked",
                                "reason": "crosscheck mismatch",
                            },
                            "safe_copy": "Route-task field-run intake is metadata-only; not_proven.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE")
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE"] = str(env_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_intake"
                ]
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE"] = previous

            missing_path = Path(td) / "Bearer-secret-token" / "missing_intake.json"
            missing_summary = summarize_route_task_field_run_intake(str(missing_path))

            unsupported_path = Path(td) / "unsupported_intake.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_readiness.v1",
                        "evidence_boundary": "software_proof_docker_route_task_field_run_readiness_gate",
                        "safe_copy": "Unsupported intake is metadata-only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_intake(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_intake.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_intake_crosscheck.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
                        ),
                        "overall_status": "crosscheck_pass",
                        "evidence_ref": "evidence://unsafe-intake",
                        "ack_post_allowed": True,
                        "phone_support_safe_summary": {
                            "safe_copy": "Intake confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_intake(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["overall_status"], "blocked_mismatch")
        self.assertEqual(env_summary["state"], "blocked")
        self.assertIn("task_record evidence_ref mismatch", env_summary["crosscheck"]["mismatch_reasons"])
        self.assertEqual(missing_summary["state"], "missing")
        self.assertEqual(unsupported_summary["state"], "unsupported_schema")
        self.assertEqual(unsafe_summary["state"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_run_intake_crosscheck_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(missing_summary["delivery_success"])
        self.assertFalse(unsupported_summary["ack_post_allowed"])
        self.assertFalse(unsafe_summary["cursor_updates_allowed"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_review_summary(self):
        with tempfile.TemporaryDirectory() as td:
            review_path = Path(td) / "route_task_field_run_review.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_review_console.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_review_console_gate"
                        ),
                        "overall_status": "ready_for_operator_review",
                        "review_decision": "needs_operator_review",
                        "evidence_ref": "evidence://route-task-field-run-review-1",
                        "same_evidence_ref_required": True,
                        "missing_materials": ["real HIL packet"],
                        "mismatch_reasons": ["mobile summary still missing"],
                        "commands_to_rerun": [
                            "python3 pc-tools/evidence/route_task_field_run_review.py --once-json"
                        ],
                        "operator_next_steps": ["Review missing material list before a real field run."],
                        "phone_safe_summary": {
                            "availability": {
                                "status": "available",
                                "reason": "metadata-only review report ready for support",
                            },
                            "safe_copy": (
                                "Route-task field-run review is metadata-only; "
                                "not delivery success and not HIL."
                            ),
                        },
                        "raw_review_log": f"{td}/raw-review.json",
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_review_ref=str(review_path),
            )
            summary = payload["route_task_field_run_review"]
            summary_alias = payload["route_task_field_run_review_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["overall_status"], "ready_for_operator_review")
        self.assertEqual(summary["state"], "available")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_review_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_review_console_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_review_console.v1")
        self.assertEqual(summary["availability"]["status"], "available")
        self.assertEqual(summary["evidence_ref"], "evidence://route-task-field-run-review-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["review"]["decision"], "needs_operator_review")
        self.assertIn("real HIL packet", summary["review"]["missing_materials"])
        self.assertIn("mobile summary still missing", summary["review"]["mismatch_reasons"])
        self.assertIn("route_task_field_run_review.py", summary["review"]["commands_to_rerun"][0])
        self.assertIn("Review missing material list", summary["review"]["operator_next_steps"][0])
        self.assertIn("metadata-only", summary["safe_phone_copy"])
        self.assertIn("not delivery success", summary["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("ack_post", summary["not_proven"])
        self.assertIn("cursor_advance_or_persistence", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertIn("production_readiness", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        for forbidden in (
            str(review_path),
            str(Path(td)),
            "raw-review.json",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_route_task_field_run_review_env_missing_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "route_task_field_run_review_env.json"
            env_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_review_console.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_review_console_gate"
                        ),
                        "overall_status": "blocked_mismatch",
                        "review_decision": "rerun_required",
                        "evidence_ref": "evidence://route-task-field-run-review-2",
                        "mismatch_reasons": ["intake report mismatch"],
                        "commands_to_rerun": ["collect route status and review report again"],
                        "phone_safe_summary": {
                            "availability": {
                                "status": "blocked",
                                "reason": "review mismatch",
                            },
                            "safe_copy": "Route-task field-run review is metadata-only; not_proven.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_console = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE")
            previous_review = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW")
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE"] = str(env_path)
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW", None)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_review"
                ]
            finally:
                if previous_console is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE"] = previous_console
                if previous_review is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW"] = previous_review

            missing_path = Path(td) / "Bearer-secret-token" / "missing_review.json"
            missing_summary = summarize_route_task_field_run_review(str(missing_path))

            unsupported_path = Path(td) / "unsupported_review.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_intake_crosscheck.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
                        ),
                        "safe_copy": "Unsupported review is metadata-only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_review(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_review.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_review_console.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_review_console_gate"
                        ),
                        "overall_status": "ready_for_operator_review",
                        "review_decision": "approved",
                        "production_ready": True,
                        "phone_safe_summary": {
                            "safe_copy": "Review confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_review(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["overall_status"], "blocked_mismatch")
        self.assertEqual(env_summary["state"], "blocked")
        self.assertEqual(env_summary["review"]["decision"], "rerun_required")
        self.assertIn("intake report mismatch", env_summary["review"]["mismatch_reasons"])
        self.assertEqual(missing_summary["state"], "missing")
        self.assertEqual(unsupported_summary["state"], "unsupported_schema")
        self.assertEqual(unsafe_summary["state"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_run_review_console_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(missing_summary["delivery_success"])
        self.assertFalse(unsupported_summary["ack_post_allowed"])
        self.assertFalse(unsafe_summary["cursor_updates_allowed"])
        self.assertFalse(unsafe_summary["production_ready"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_execution_pack_summary(self):
        with tempfile.TemporaryDirectory() as td:
            pack_path = Path(td) / "route_task_field_run_execution_pack.json"
            pack_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_execution_pack.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_execution_pack_gate"
                        ),
                        "status": "ready_for_field_run_execution_pack",
                        "evidence_ref": "evidence://route-task-field-run-execution-pack-1",
                        "same_evidence_ref_required": True,
                        "materials_status": {
                            "status": "available",
                            "missing_materials": [],
                            "required_materials": [
                                "route status",
                                "task record",
                                "support-safe mobile summary",
                            ],
                        },
                        "command_summary": [
                            "python3 pc-tools/evidence/route_task_field_run_execution_pack.py --once-json"
                        ],
                        "phone_safe_summary": {
                            "safe_copy": (
                                "Route-task field-run execution pack is metadata-only; "
                                "not delivery success and not HIL."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_execution_pack_ref=str(pack_path),
            )
            summary = payload["route_task_field_run_execution_pack"]
            summary_alias = payload["route_task_field_run_execution_pack_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["status"], "ready_for_field_run_execution_pack")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_execution_pack_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_execution_pack_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_execution_pack.v1")
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://route-task-field-run-execution-pack-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["materials_status"]["status"], "available")
        self.assertIn("support-safe mobile summary", summary["materials_status"]["required_materials"])
        self.assertIn("route_task_field_run_execution_pack.py", summary["command_summary"][0])
        self.assertIn("metadata-only", summary["safe_phone_copy"])
        self.assertIn("not delivery success", summary["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("cursor_advance_or_persistence", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertIn("production_readiness", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        for forbidden_key in (
            "delivery_success",
            "primary_actions_enabled",
            "collect_triggered",
            "dropoff_triggered",
            "cancel_triggered",
            "ack_post_allowed",
            "cursor_updates_allowed",
            "persistence_updates_allowed",
            "terminal_ack_allowed",
            "hil_pass",
            "production_ready",
            "dropoff_completion",
            "cancel_completion",
        ):
            self.assertNotIn(forbidden_key, summary)
        self.assertNotIn(str(pack_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_run_execution_pack_env_missing_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "route_task_field_run_execution_pack_env.json"
            env_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_execution_pack.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_execution_pack_gate"
                        ),
                        "status": "blocked_missing_material",
                        "evidence_ref": "evidence://route-task-field-run-execution-pack-2",
                        "same_evidence_ref_required": True,
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["field-run route log"],
                        },
                        "command_summary": ["collect route status and task record with one evidence_ref"],
                        "phone_safe_summary": {
                            "safe_copy": "Route-task field-run execution pack is metadata-only; not_proven.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK")
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK"] = str(env_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_execution_pack"
                ]
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK"] = previous

            missing_path = Path(td) / "Bearer-secret-token" / "missing_execution_pack.json"
            missing_summary = summarize_route_task_field_run_execution_pack(str(missing_path))

            unsupported_path = Path(td) / "unsupported_execution_pack.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_review_console.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_review_console_gate"
                        ),
                        "safe_copy": "Unsupported execution pack is metadata-only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_execution_pack(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_execution_pack.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_execution_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_execution_pack_gate"
                        ),
                        "status": "ready_for_field_run_execution_pack",
                        "production_ready": True,
                        "phone_safe_summary": {
                            "safe_copy": "Execution pack confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_execution_pack(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["status"], "blocked_missing_material")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("field-run route log", env_summary["materials_status"]["missing_materials"])
        self.assertEqual(missing_summary["status"], "missing")
        self.assertEqual(unsupported_summary["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["status"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_run_execution_pack_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_retest_execution_pack_summary(self):
        with tempfile.TemporaryDirectory() as td:
            pack_path = Path(td) / "route_task_field_retest_execution_pack.json"
            pack_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_execution_pack_gate"
                        ),
                        "execution_status": "ready_for_field_retest_execution_pack_not_proven",
                        "evidence_ref": "evidence://route-task-field-retest-execution-pack-1",
                        "same_evidence_ref_required": True,
                        "required_field_materials": {
                            "status": "ready_not_proven",
                            "items": [
                                "real Nav2/fixed-route runtime log",
                                "route completion signal",
                                "task record",
                            ],
                        },
                        "rerun_commands": ["python3 pc-tools/evidence/route_task_field_retest_execution_pack.py --once-json"],
                        "operator_handoff": {"owner": "Autonomy", "next_step": "run field retest"},
                        "field_retest_checklist": ["collect same evidence_ref materials"],
                        "phone_readiness": {
                            "safe_copy": (
                                "Route-task field retest execution pack is metadata-only; "
                                "delivery_success=false; primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["delivery_success"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_retest_execution_pack_ref=str(pack_path),
            )
            summary = payload["route_task_field_retest_execution_pack"]
            summary_alias = payload["route_task_field_retest_execution_pack_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_execution_pack_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_execution_pack_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_retest_execution_pack.v1")
        self.assertEqual(
            summary["execution_status"],
            "ready_for_field_retest_execution_pack_not_proven",
        )
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://route-task-field-retest-execution-pack-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertIn("route completion signal", summary["required_field_materials_summary"]["items"])
        self.assertIn("route_task_field_retest_execution_pack.py", summary["rerun_commands_summary"][0])
        self.assertEqual(summary["operator_handoff"]["owner"], "Autonomy")
        self.assertIn("collect same evidence_ref materials", summary["field_retest_checklist"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(pack_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_retest_execution_pack_env_nested_missing_mismatch_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_retest_execution_pack_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_execution_pack_summary.v1",
                        "source_schema": "trashbot.route_task_field_retest_execution_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_execution_pack_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_execution_pack_gate"
                        ),
                        "execution_status": "blocked_missing_field_retest_material",
                        "safe_evidence_ref": "evidence://route-task-field-retest-execution-pack-2",
                        "same_evidence_ref_required": True,
                        "required_field_materials_summary": {"status": "blocked", "items": ["field note"]},
                        "rerun_commands_summary": ["collect field note"],
                        "operator_handoff": {"owner": "Robot"},
                        "field_retest_checklist": ["same evidence_ref"],
                        "safe_phone_copy": "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_pack = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_retest_execution_pack"
                ]
            finally:
                if previous_pack is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK"] = previous_pack
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY"] = previous_summary

            nested_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "diagnostics_summary": {
                            "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                            "evidence_boundary": (
                                "software_proof_docker_route_task_field_retest_execution_pack_gate"
                            ),
                            "execution_status": "ready_nested_not_proven",
                            "evidence_ref": "evidence://route-task-field-retest-execution-pack-3",
                            "same_evidence_ref_required": True,
                            "required_field_materials_summary": {"status": "ready", "items": ["task record"]},
                            "rerun_commands_summary": ["rerun route task"],
                            "operator_handoff": {"owner": "Autonomy"},
                            "field_retest_checklist": ["capture route completion signal"],
                            "safe_copy": "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["route_task_field_retest_execution_pack"]
            missing_summary = summarize_route_task_field_retest_execution_pack(
                Path(td) / "Bearer-secret-token" / "missing_retest_pack.json"
            )
            unsupported_summary = summarize_route_task_field_retest_execution_pack(
                {
                    "schema": "trashbot.route_task_terminal_review_decision.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_terminal_review_decision_gate"
                    ),
                    "evidence_ref": "evidence://unsupported",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Unsupported route-task field retest execution pack is metadata-only; delivery_success=false.",
                }
            )
            missing_ref_summary = summarize_route_task_field_retest_execution_pack(
                {
                    "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_execution_pack_gate"
                    ),
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            mismatch_summary = summarize_route_task_field_retest_execution_pack(
                {
                    "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_execution_pack_gate"
                    ),
                    "evidence_ref": "evidence://source-ref",
                    "route_task_field_retest_execution_pack_summary": {
                        "safe_evidence_ref": "evidence://summary-ref",
                    },
                    "same_evidence_ref_required": True,
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            unsafe_summary = summarize_route_task_field_retest_execution_pack(
                {
                    "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_execution_pack_gate"
                    ),
                    "evidence_ref": "evidence://unsafe",
                    "same_evidence_ref_required": True,
                    "delivery_success": True,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest execution pack confirms delivery success and ACK posted.",
                }
            )
            enabled_summary = summarize_route_task_field_retest_execution_pack(
                {
                    "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_execution_pack_gate"
                    ),
                    "evidence_ref": "evidence://enabled",
                    "same_evidence_ref_required": True,
                    "delivery_success": False,
                    "primary_actions_enabled": True,
                    "safe_copy": "Route-task field retest execution pack is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    nested_summary,
                    missing_summary,
                    unsupported_summary,
                    missing_ref_summary,
                    mismatch_summary,
                    unsafe_summary,
                    enabled_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["execution_status"], "blocked_missing_field_retest_material")
        self.assertEqual(nested_summary["execution_status"], "ready_nested_not_proven")
        self.assertEqual(missing_summary["execution_status"], "missing")
        self.assertEqual(unsupported_summary["execution_status"], "unsupported_schema")
        self.assertEqual(missing_ref_summary["execution_status"], "missing_evidence_ref")
        self.assertEqual(mismatch_summary["execution_status"], "evidence_ref_mismatch")
        self.assertEqual(unsafe_summary["execution_status"], "unsafe_fields")
        self.assertEqual(enabled_summary["execution_status"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_retest_execution_pack_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(env_summary["ack_post_allowed"])
        self.assertFalse(env_summary["nav2_triggered"])
        self.assertFalse(env_summary["hil_pass"])
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_retest_session_handoff_summary(self):
        with tempfile.TemporaryDirectory() as td:
            handoff_path = Path(td) / "route_task_field_retest_session_handoff.json"
            handoff_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_session_handoff.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_session_handoff_gate"
                        ),
                        "handoff_status": {
                            "status": "ready_for_field_retest_session_handoff_not_proven",
                            "verdict": "not_proven",
                            "reason": "handoff is ready for field materials only",
                        },
                        "evidence_ref": "evidence://route-task-field-retest-session-handoff-1",
                        "same_evidence_ref_required": True,
                        "session_owner": "Autonomy",
                        "required_field_materials": {
                            "status": "blocked_until_real_field_materials",
                            "items": [
                                "real Nav2/fixed-route runtime log",
                                "route completion signal",
                                "task record",
                                "door state",
                            ],
                        },
                        "material_placeholders": ["Nav2 runtime log placeholder", "task record placeholder"],
                        "rerun_commands": ["python3 pc-tools/evidence/route_task_field_retest_session_handoff.py --once-json"],
                        "operator_next_steps": ["Collect same evidence_ref field materials."],
                        "field_callback_checklist": ["capture target floor confirmation"],
                        "robot_diagnostics_summary": {
                            "status": "metadata_only",
                            "reason": "Robot diagnostics only mirrors safe handoff metadata.",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field retest session handoff is metadata-only; "
                                "delivery_success=false; primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["delivery_success"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_retest_session_handoff_ref=str(handoff_path),
            )
            summary = payload["route_task_field_retest_session_handoff"]
            summary_alias = payload["route_task_field_retest_session_handoff_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_session_handoff_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_session_handoff_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_retest_session_handoff.v1")
        self.assertEqual(
            summary["handoff_status"]["status"],
            "ready_for_field_retest_session_handoff_not_proven",
        )
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://route-task-field-retest-session-handoff-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["session_owner"], "Autonomy")
        self.assertIn("door state", summary["required_field_materials_summary"]["items"])
        self.assertIn("route_task_field_retest_session_handoff.py", summary["rerun_commands_summary"][0])
        self.assertIn("capture target floor confirmation", summary["field_callback_checklist"])
        self.assertEqual(summary["robot_diagnostics_summary"]["status"], "metadata_only")
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(handoff_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_retest_session_handoff_env_nested_missing_mismatch_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_retest_session_handoff_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_session_handoff_summary.v1",
                        "source_schema": "trashbot.route_task_field_retest_session_handoff.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_session_handoff_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_session_handoff_gate"
                        ),
                        "handoff_status": {
                            "status": "blocked_missing_field_material",
                            "verdict": "not_proven",
                            "reason": "field materials are not attached",
                        },
                        "safe_evidence_ref": "evidence://route-task-field-retest-session-handoff-2",
                        "same_evidence_ref_required": True,
                        "session_owner": "Robot",
                        "required_field_materials_summary": {"status": "blocked", "items": ["field note"]},
                        "rerun_commands_summary": ["collect field note"],
                        "operator_next_steps": ["keep metadata-only"],
                        "field_callback_checklist": ["same evidence_ref"],
                        "safe_phone_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_handoff = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_retest_session_handoff"
                ]
            finally:
                if previous_handoff is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF"] = previous_handoff
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY"] = previous_summary

            nested_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "route_task_field_retest_session_handoff_summary": {
                            "schema": "trashbot.route_task_field_retest_session_handoff.v1",
                            "evidence_boundary": (
                                "software_proof_docker_route_task_field_retest_session_handoff_gate"
                            ),
                            "handoff_status": "ready_nested_not_proven",
                            "evidence_ref": "evidence://route-task-field-retest-session-handoff-3",
                            "same_evidence_ref_required": True,
                            "required_field_materials_summary": {"status": "ready", "items": ["task record"]},
                            "rerun_commands_summary": ["rerun route task"],
                            "session_owner": "Autonomy",
                            "field_callback_checklist": ["capture route completion signal"],
                            "safe_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["route_task_field_retest_session_handoff"]
            missing_summary = summarize_route_task_field_retest_session_handoff(
                Path(td) / "Bearer-secret-token" / "missing_session_handoff.json"
            )
            unsupported_summary = summarize_route_task_field_retest_session_handoff(
                {
                    "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_execution_pack_gate"
                    ),
                    "evidence_ref": "evidence://unsupported",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Unsupported route-task field retest session handoff is metadata-only; delivery_success=false.",
                }
            )
            missing_ref_summary = summarize_route_task_field_retest_session_handoff(
                {
                    "schema": "trashbot.route_task_field_retest_session_handoff.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_session_handoff_gate"
                    ),
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            mismatch_summary = summarize_route_task_field_retest_session_handoff(
                {
                    "schema": "trashbot.route_task_field_retest_session_handoff.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_session_handoff_gate"
                    ),
                    "evidence_ref": "evidence://source-ref",
                    "route_task_field_retest_session_handoff_summary": {
                        "safe_evidence_ref": "evidence://summary-ref",
                    },
                    "same_evidence_ref_required": True,
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            weak_same_ref_summary = summarize_route_task_field_retest_session_handoff(
                {
                    "schema": "trashbot.route_task_field_retest_session_handoff.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_session_handoff_gate"
                    ),
                    "evidence_ref": "evidence://weak-same-ref",
                    "same_evidence_ref_required": "true",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest session handoff is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            unsafe_summary = summarize_route_task_field_retest_session_handoff(
                {
                    "schema": "trashbot.route_task_field_retest_session_handoff.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_session_handoff_gate"
                    ),
                    "evidence_ref": "evidence://unsafe",
                    "same_evidence_ref_required": True,
                    "delivery_success": False,
                    "primary_actions_enabled": True,
                    "safe_copy": "Route-task field retest session handoff confirms delivery success and ACK posted.",
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    nested_summary,
                    missing_summary,
                    unsupported_summary,
                    missing_ref_summary,
                    mismatch_summary,
                    weak_same_ref_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["handoff_status"]["status"], "blocked_missing_field_material")
        self.assertEqual(nested_summary["handoff_status"]["status"], "ready_nested_not_proven")
        self.assertEqual(missing_summary["handoff_status"]["status"], "missing")
        self.assertEqual(unsupported_summary["handoff_status"]["status"], "unsupported_schema")
        self.assertEqual(missing_ref_summary["handoff_status"]["status"], "missing_evidence_ref")
        self.assertEqual(mismatch_summary["handoff_status"]["status"], "evidence_ref_mismatch")
        self.assertEqual(weak_same_ref_summary["handoff_status"]["status"], "unsafe_fields")
        self.assertEqual(unsafe_summary["handoff_status"]["status"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_retest_session_handoff_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(env_summary["ack_post_allowed"])
        self.assertFalse(env_summary["nav2_triggered"])
        self.assertFalse(env_summary["hil_pass"])
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_retest_result_intake_summary(self):
        with tempfile.TemporaryDirectory() as td:
            result_path = Path(td) / "route_task_field_retest_result_intake.json"
            result_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_result_intake.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_result_intake_gate"
                        ),
                        "result_status": {
                            "status": "ready_for_field_retest_result_intake_not_proven",
                            "verdict": "not_proven",
                            "reason": "field result metadata is ready for review only",
                        },
                        "evidence_ref": "evidence://route-task-field-retest-result-intake-1",
                        "same_evidence_ref_required": True,
                        "door_state": "observed_open_not_proven",
                        "target_floor_confirmation": "operator_confirmed_not_proven",
                        "human_assistance_note": "Operator observed elevator doorway; result remains not_proven.",
                        "result_materials": {
                            "status": "metadata_only",
                            "items": [
                                "door_state",
                                "target_floor_confirmation",
                                "human_assistance_note",
                            ],
                        },
                        "operator_next_steps": ["Review same evidence_ref field result metadata."],
                        "robot_diagnostics_summary": {
                            "status": "metadata_only",
                            "reason": "Robot diagnostics only mirrors safe result intake metadata.",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field retest result intake is metadata-only; "
                                "delivery_success=false; primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["delivery_success"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_retest_result_intake_ref=str(result_path),
            )
            summary = payload["route_task_field_retest_result_intake"]
            summary_alias = payload["route_task_field_retest_result_intake_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_intake_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_intake_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_retest_result_intake.v1")
        self.assertEqual(
            summary["result_status"]["status"],
            "ready_for_field_retest_result_intake_not_proven",
        )
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://route-task-field-retest-result-intake-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["door_state"], "observed_open_not_proven")
        self.assertEqual(summary["target_floor_confirmation"], "operator_confirmed_not_proven")
        self.assertIn("not_proven", summary["human_assistance_note"])
        self.assertIn("door_state", summary["result_materials_summary"]["items"])
        self.assertEqual(summary["robot_diagnostics_summary"]["status"], "metadata_only")
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("real_elevator_door_state", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(result_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_retest_result_intake_env_nested_missing_mismatch_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_retest_result_intake_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_result_intake_summary.v1",
                        "source_schema": "trashbot.route_task_field_retest_result_intake.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_result_intake_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_result_intake_gate"
                        ),
                        "result_status": {
                            "status": "blocked_missing_field_result_material",
                            "verdict": "not_proven",
                            "reason": "field result metadata is incomplete",
                        },
                        "safe_evidence_ref": "evidence://route-task-field-retest-result-intake-2",
                        "same_evidence_ref_required": True,
                        "door_state": "not_proven",
                        "target_floor_confirmation": "not_proven",
                        "human_assistance_note": "Waiting for operator result note; not_proven.",
                        "result_materials_summary": {"status": "blocked", "items": ["door_state"]},
                        "operator_next_steps": ["keep metadata-only"],
                        "safe_phone_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_result = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_retest_result_intake"
                ]
            finally:
                if previous_result is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE"] = previous_result
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY"] = previous_summary

            nested_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "diagnostics_summary": {
                            "schema": "trashbot.route_task_field_retest_result_intake.v1",
                            "evidence_boundary": (
                                "software_proof_docker_route_task_field_retest_result_intake_gate"
                            ),
                            "result_status": "ready_nested_not_proven",
                            "evidence_ref": "evidence://route-task-field-retest-result-intake-3",
                            "same_evidence_ref_required": True,
                            "door_state": "observed_closed_not_proven",
                            "target_floor_confirmation": "operator_pending_not_proven",
                            "human_assistance_note": "Operator note remains metadata-only.",
                            "result_materials_summary": {"status": "ready", "items": ["human_assistance_note"]},
                            "operator_next_steps": ["review field note"],
                            "safe_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["route_task_field_retest_result_intake"]
            missing_summary = summarize_route_task_field_retest_result_intake(
                Path(td) / "Bearer-secret-token" / "missing_result_intake.json"
            )
            unsupported_summary = summarize_route_task_field_retest_result_intake(
                {
                    "schema": "trashbot.route_task_field_retest_session_handoff.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_session_handoff_gate"
                    ),
                    "evidence_ref": "evidence://unsupported",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Unsupported route-task field retest result intake is metadata-only; delivery_success=false.",
                }
            )
            missing_ref_summary = summarize_route_task_field_retest_result_intake(
                {
                    "schema": "trashbot.route_task_field_retest_result_intake.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_intake_gate"
                    ),
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            mismatch_summary = summarize_route_task_field_retest_result_intake(
                {
                    "schema": "trashbot.route_task_field_retest_result_intake.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_intake_gate"
                    ),
                    "evidence_ref": "evidence://source-ref",
                    "route_task_field_retest_result_intake_summary": {
                        "safe_evidence_ref": "evidence://summary-ref",
                    },
                    "same_evidence_ref_required": True,
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            weak_same_ref_summary = summarize_route_task_field_retest_result_intake(
                {
                    "schema": "trashbot.route_task_field_retest_result_intake.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_intake_gate"
                    ),
                    "evidence_ref": "evidence://weak-same-ref",
                    "same_evidence_ref_required": "true",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result intake is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            unsafe_summary = summarize_route_task_field_retest_result_intake(
                {
                    "schema": "trashbot.route_task_field_retest_result_intake.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_intake_gate"
                    ),
                    "evidence_ref": "evidence://unsafe",
                    "same_evidence_ref_required": True,
                    "delivery_success": True,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result intake confirms delivery success and ACK posted.",
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    nested_summary,
                    missing_summary,
                    unsupported_summary,
                    missing_ref_summary,
                    mismatch_summary,
                    weak_same_ref_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["result_status"]["status"], "blocked_missing_field_result_material")
        self.assertEqual(nested_summary["result_status"]["status"], "ready_nested_not_proven")
        self.assertEqual(missing_summary["result_status"]["status"], "missing")
        self.assertEqual(unsupported_summary["result_status"]["status"], "unsupported_schema")
        self.assertEqual(missing_ref_summary["result_status"]["status"], "missing_evidence_ref")
        self.assertEqual(mismatch_summary["result_status"]["status"], "evidence_ref_mismatch")
        self.assertEqual(weak_same_ref_summary["result_status"]["status"], "unsafe_fields")
        self.assertEqual(unsafe_summary["result_status"]["status"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_retest_result_intake_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(env_summary["ack_post_allowed"])
        self.assertFalse(env_summary["nav2_triggered"])
        self.assertFalse(env_summary["hil_pass"])
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_retest_result_reconciliation_summary(self):
        with tempfile.TemporaryDirectory() as td:
            reconciliation_path = Path(td) / "route_task_field_retest_result_reconciliation.json"
            reconciliation_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                        ),
                        "reconciliation_status": {
                            "status": "ready_for_field_retest_result_reconciliation_not_proven",
                            "verdict": "not_proven",
                            "reason": "result intake metadata reconciles with same evidence_ref only",
                        },
                        "evidence_ref": "evidence://route-task-field-retest-result-reconciliation-1",
                        "same_evidence_ref_required": True,
                        "result_intake_summary": {
                            "status": "metadata_only",
                            "safe_evidence_ref": "evidence://route-task-field-retest-result-reconciliation-1",
                        },
                        "result_reconciliation_summary": {
                            "status": "metadata_only",
                            "checked": ["result_intake_summary", "same_evidence_ref_required"],
                        },
                        "operator_next_steps": ["Review same evidence_ref retest result metadata."],
                        "robot_diagnostics_summary": {
                            "status": "metadata_only",
                            "reason": "Robot diagnostics only mirrors safe result reconciliation metadata.",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field retest result reconciliation is metadata-only; "
                                "delivery_success=false; primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["delivery_success"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_retest_result_reconciliation_ref=str(reconciliation_path),
            )
            summary = payload["route_task_field_retest_result_reconciliation"]
            summary_alias = payload["route_task_field_retest_result_reconciliation_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(
            summary["schema"],
            "trashbot.route_task_field_retest_result_reconciliation_summary.v1",
        )
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_reconciliation_gate",
        )
        self.assertEqual(
            summary["source_schema"],
            "trashbot.route_task_field_retest_result_reconciliation.v1",
        )
        self.assertEqual(
            summary["reconciliation_status"]["status"],
            "ready_for_field_retest_result_reconciliation_not_proven",
        )
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://route-task-field-retest-result-reconciliation-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["result_intake_summary"]["status"], "metadata_only")
        self.assertIn("same_evidence_ref_required", summary["result_reconciliation_summary"]["checked"])
        self.assertEqual(summary["robot_diagnostics_summary"]["status"], "metadata_only")
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(reconciliation_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_retest_result_reconciliation_env_nested_missing_mismatch_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_retest_result_reconciliation_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_result_reconciliation_summary.v1",
                        "source_schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                        ),
                        "reconciliation_status": {
                            "status": "blocked_missing_retest_result_material",
                            "verdict": "not_proven",
                            "reason": "result reconciliation metadata is incomplete",
                        },
                        "safe_evidence_ref": "evidence://route-task-field-retest-result-reconciliation-2",
                        "same_evidence_ref_required": True,
                        "result_intake_summary": {"status": "blocked"},
                        "result_reconciliation_summary": {"status": "blocked"},
                        "operator_next_steps": ["keep metadata-only"],
                        "safe_phone_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_result = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_retest_result_reconciliation"
                ]
            finally:
                if previous_result is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION"] = previous_result
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY"] = previous_summary

            nested_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "route_task_field_retest_result_reconciliation_summary": {
                            "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
                            "evidence_boundary": (
                                "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                            ),
                            "reconciliation_status": "ready_nested_not_proven",
                            "evidence_ref": "evidence://route-task-field-retest-result-reconciliation-3",
                            "same_evidence_ref_required": True,
                            "result_intake_summary": {"status": "ready"},
                            "result_reconciliation_summary": {"status": "ready"},
                            "operator_next_steps": ["review result reconciliation"],
                            "safe_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["route_task_field_retest_result_reconciliation"]
            missing_summary = summarize_route_task_field_retest_result_reconciliation(
                Path(td) / "Bearer-secret-token" / "missing_result_reconciliation.json"
            )
            unsupported_summary = summarize_route_task_field_retest_result_reconciliation(
                {
                    "schema": "trashbot.route_task_field_retest_result_intake.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_intake_gate"
                    ),
                    "evidence_ref": "evidence://unsupported",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Unsupported route-task field retest result reconciliation is metadata-only; delivery_success=false.",
                }
            )
            missing_ref_summary = summarize_route_task_field_retest_result_reconciliation(
                {
                    "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                    ),
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            mismatch_summary = summarize_route_task_field_retest_result_reconciliation(
                {
                    "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                    ),
                    "evidence_ref": "evidence://source-ref",
                    "route_task_field_retest_result_reconciliation_summary": {
                        "safe_evidence_ref": "evidence://summary-ref",
                    },
                    "same_evidence_ref_required": True,
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            weak_same_ref_summary = summarize_route_task_field_retest_result_reconciliation(
                {
                    "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                    ),
                    "evidence_ref": "evidence://weak-same-ref",
                    "same_evidence_ref_required": "true",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result reconciliation is metadata-only; delivery_success=false; primary_actions_enabled=false.",
                }
            )
            unsafe_summary = summarize_route_task_field_retest_result_reconciliation(
                {
                    "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_field_retest_result_reconciliation_gate"
                    ),
                    "evidence_ref": "evidence://unsafe",
                    "same_evidence_ref_required": True,
                    "delivery_success": True,
                    "primary_actions_enabled": False,
                    "safe_copy": "Route-task field retest result reconciliation confirms delivery success and ACK posted.",
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    nested_summary,
                    missing_summary,
                    unsupported_summary,
                    missing_ref_summary,
                    mismatch_summary,
                    weak_same_ref_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["reconciliation_status"]["status"], "blocked_missing_retest_result_material")
        self.assertEqual(nested_summary["reconciliation_status"]["status"], "ready_nested_not_proven")
        self.assertEqual(missing_summary["reconciliation_status"]["status"], "missing")
        self.assertEqual(unsupported_summary["reconciliation_status"]["status"], "unsupported_schema")
        self.assertEqual(missing_ref_summary["reconciliation_status"]["status"], "missing_evidence_ref")
        self.assertEqual(mismatch_summary["reconciliation_status"]["status"], "evidence_ref_mismatch")
        self.assertEqual(weak_same_ref_summary["reconciliation_status"]["status"], "unsafe_fields")
        self.assertEqual(unsafe_summary["reconciliation_status"]["status"], "unsafe_fields")
        self.assertIn("software_proof_docker_route_task_field_retest_result_reconciliation_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(env_summary["ack_post_allowed"])
        self.assertFalse(env_summary["nav2_triggered"])
        self.assertFalse(env_summary["hil_pass"])
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_retest_material_pack_summary(self):
        with tempfile.TemporaryDirectory() as td:
            pack_path = Path(td) / "route_task_field_retest_material_pack.json"
            pack_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_material_pack.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_material_pack_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-retest-material-pack-1",
                        "route_task_field_retest_material_pack_summary": {
                            "schema": "trashbot.route_task_field_retest_material_pack_summary.v1",
                            "source_schema": "trashbot.route_task_field_retest_material_pack.v1",
                            "source_evidence_boundary": (
                                "software_proof_docker_route_task_field_retest_material_pack_gate"
                            ),
                            "safe_evidence_ref": "evidence://route-task-field-retest-material-pack-1",
                            "same_evidence_ref_required": True,
                            "material_status": {
                                "status": "ready_for_retest_review",
                                "verdict": "not_proven",
                                "reason": "all eight material categories have safe summaries",
                            },
                            "material_completeness": {
                                "status": "complete",
                                "accepted_count": 8,
                                "required_count": 8,
                            },
                            "missing_materials": [],
                            "rejected_materials": [],
                            "operator_next_steps": ["Review same evidence_ref before field retest."],
                            "robot_diagnostics_summary": {
                                "status": "ready_for_retest_review",
                                "reason": "metadata-only material pack summary available",
                            },
                            "safe_copy": (
                                "Route-task field retest material pack is metadata-only; "
                                "delivery_success=false; primary_actions_enabled=false."
                            ),
                            "not_proven": ["delivery_success", "real_hil_pass"],
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_retest_material_pack_ref=str(pack_path),
            )
            summary = payload["route_task_field_retest_material_pack"]
            summary_alias = payload["route_task_field_retest_material_pack_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_material_pack_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_material_pack_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_retest_material_pack.v1")
        self.assertEqual(summary["material_status"]["status"], "ready_for_retest_review")
        self.assertEqual(summary["material_status"]["verdict"], "not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-task-field-retest-material-pack-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["material_completeness"]["status"], "complete")
        self.assertEqual(summary["missing_materials"], [])
        self.assertEqual(summary["rejected_materials"], [])
        self.assertIn("Review same evidence_ref", summary["operator_next_steps"][0])
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn(str(pack_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_retest_material_pack_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_retest_material_pack_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_material_pack_summary.v1",
                        "source_schema": "trashbot.route_task_field_retest_material_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_material_pack_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_material_pack_gate"
                        ),
                        "safe_evidence_ref": "evidence://route-task-field-retest-material-pack-2",
                        "same_evidence_ref_required": True,
                        "material_status": {"status": "blocked_missing_material", "verdict": "not_proven"},
                        "material_completeness": {
                            "status": "blocked",
                            "missing_materials": ["door_state"],
                            "rejected_materials": ["delivery_result"],
                        },
                        "missing_materials": ["door_state"],
                        "rejected_materials": ["delivery_result"],
                        "operator_next_steps": ["Capture missing door_state under the same evidence_ref."],
                        "safe_copy": (
                            "Route-task field retest material pack is metadata-only; "
                            "delivery_success=false; primary_actions_enabled=false."
                        ),
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_pack = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_retest_material_pack"
                ]
            finally:
                if previous_pack is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK"] = previous_pack
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_material_pack.json"
            missing_summary = summarize_route_task_field_retest_material_pack(str(missing_path))
            no_summary = summarize_route_task_field_retest_material_pack(
                {
                    "schema": "trashbot.route_task_field_retest_material_pack.v1",
                    "evidence_boundary": "software_proof_docker_route_task_field_retest_material_pack_gate",
                    "evidence_ref": "evidence://route-task-field-retest-material-pack-3",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                }
            )
            unsupported_summary = summarize_route_task_field_retest_material_pack(
                {
                    "schema": "trashbot.route_task_field_retest_result_intake.v1",
                    "evidence_boundary": "software_proof_docker_route_task_field_retest_result_intake_gate",
                    "route_task_field_retest_material_pack_summary": {
                        "safe_copy": "Unsupported material pack is metadata-only; delivery_success=false.",
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    },
                }
            )
            unsafe_summary = summarize_route_task_field_retest_material_pack(
                {
                    "schema": "trashbot.route_task_field_retest_material_pack.v1",
                    "evidence_boundary": "software_proof_docker_route_task_field_retest_material_pack_gate",
                    "evidence_ref": "evidence://route-task-field-retest-material-pack-4",
                    "route_task_field_retest_material_pack_summary": {
                        "safe_evidence_ref": "evidence://route-task-field-retest-material-pack-4",
                        "same_evidence_ref_required": True,
                        "safe_copy": "Material pack confirms delivery success and ACK posted.",
                        "delivery_success": True,
                        "primary_actions_enabled": False,
                    },
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                }
            )
            encoded = json.dumps(
                [env_summary, missing_summary, no_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["material_status"]["status"], "blocked_missing_material")
        self.assertEqual(env_summary["material_completeness"]["status"], "blocked")
        self.assertIn("door_state", env_summary["missing_materials"])
        self.assertIn("delivery_result", env_summary["rejected_materials"])
        self.assertEqual(missing_summary["material_status"]["status"], "missing")
        self.assertEqual(no_summary["material_status"]["status"], "missing_summary")
        self.assertEqual(unsupported_summary["material_status"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["material_status"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_field_retest_material_pack_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_retest_operator_drill_summary(self):
        with tempfile.TemporaryDirectory() as td:
            drill_path = Path(td) / "route_task_field_retest_operator_drill.json"
            drill_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_operator_drill.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_operator_drill_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-retest-operator-drill-1",
                        "route_task_field_retest_operator_drill_summary": {
                            "schema": "trashbot.route_task_field_retest_operator_drill_summary.v1",
                            "source_schema": "trashbot.route_task_field_retest_operator_drill.v1",
                            "source_evidence_boundary": (
                                "software_proof_docker_route_task_field_retest_operator_drill_gate"
                            ),
                            "safe_evidence_ref": "evidence://route-task-field-retest-operator-drill-1",
                            "same_evidence_ref_required": True,
                            "drill_status": {
                                "status": "ready_for_operator_drill_not_proven",
                                "verdict": "not_proven",
                                "reason": "operator callback checklist is ready",
                            },
                            "next_command_labels": [
                                "Run material pack gate",
                                "Run result intake gate",
                                "Run result reconciliation gate",
                            ],
                            "missing_material_prompts": [
                                "Ask operator to capture door state under the same evidence_ref."
                            ],
                            "operator_callback_checklist": [
                                "Confirm field operator used the same evidence_ref."
                            ],
                            "robot_diagnostics_summary": {
                                "status": "metadata_only",
                                "reason": "Robot diagnostics mirrors safe operator drill labels only.",
                            },
                            "safe_copy": (
                                "Route-task field retest operator drill is metadata-only; "
                                "delivery_success=false; primary_actions_enabled=false."
                            ),
                            "not_proven": ["delivery_success", "real_hil_pass"],
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_retest_operator_drill_ref=str(drill_path),
            )
            summary = payload["route_task_field_retest_operator_drill"]
            summary_alias = payload["route_task_field_retest_operator_drill_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_operator_drill_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_operator_drill_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_retest_operator_drill.v1")
        self.assertEqual(summary["drill_status"]["status"], "ready_for_operator_drill_not_proven")
        self.assertEqual(summary["drill_status"]["verdict"], "not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-task-field-retest-operator-drill-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertIn("Run material pack gate", summary["next_command_labels"])
        self.assertIn("door state", summary["missing_material_prompts"][0])
        self.assertIn("same evidence_ref", summary["operator_callback_checklist"][0])
        self.assertEqual(summary["robot_diagnostics_summary"]["status"], "metadata_only")
        self.assertIn("delivery_success=false", summary["safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn(str(drill_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_retest_operator_drill_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_retest_operator_drill_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_retest_operator_drill_summary.v1",
                        "source_schema": "trashbot.route_task_field_retest_operator_drill.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_operator_drill_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_retest_operator_drill_gate"
                        ),
                        "safe_evidence_ref": "evidence://route-task-field-retest-operator-drill-2",
                        "same_evidence_ref_required": True,
                        "drill_status": {"status": "blocked_missing_material", "verdict": "not_proven"},
                        "next_command_labels": ["Run retest material pack"],
                        "missing_material_prompts": ["Capture missing door state."],
                        "operator_callback_checklist": ["Call support after upload."],
                        "safe_copy": (
                            "Route-task field retest operator drill is metadata-only; "
                            "delivery_success=false; primary_actions_enabled=false."
                        ),
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_drill = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_retest_operator_drill"
                ]
            finally:
                if previous_drill is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL"] = previous_drill
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_operator_drill.json"
            missing_summary = summarize_route_task_field_retest_operator_drill(str(missing_path))
            no_summary = summarize_route_task_field_retest_operator_drill(
                {
                    "schema": "trashbot.route_task_field_retest_operator_drill.v1",
                    "evidence_boundary": "software_proof_docker_route_task_field_retest_operator_drill_gate",
                    "evidence_ref": "evidence://route-task-field-retest-operator-drill-3",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                }
            )
            unsupported_summary = summarize_route_task_field_retest_operator_drill(
                {
                    "schema": "trashbot.route_task_field_retest_material_pack.v1",
                    "evidence_boundary": "software_proof_docker_route_task_field_retest_material_pack_gate",
                    "route_task_field_retest_operator_drill_summary": {
                        "safe_copy": "Unsupported operator drill is metadata-only; delivery_success=false.",
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    },
                }
            )
            unsafe_summary = summarize_route_task_field_retest_operator_drill(
                {
                    "schema": "trashbot.route_task_field_retest_operator_drill.v1",
                    "evidence_boundary": "software_proof_docker_route_task_field_retest_operator_drill_gate",
                    "evidence_ref": "evidence://route-task-field-retest-operator-drill-4",
                    "route_task_field_retest_operator_drill_summary": {
                        "safe_evidence_ref": "evidence://route-task-field-retest-operator-drill-4",
                        "same_evidence_ref_required": True,
                        "safe_copy": "Operator drill confirms delivery success and ACK posted.",
                        "delivery_success": True,
                        "primary_actions_enabled": False,
                    },
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                }
            )
            encoded = json.dumps(
                [env_summary, missing_summary, no_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["drill_status"]["status"], "blocked_missing_material")
        self.assertIn("Run retest material pack", env_summary["next_command_labels"])
        self.assertIn("door state", env_summary["missing_material_prompts"][0])
        self.assertIn("Call support", env_summary["operator_callback_checklist"][0])
        self.assertEqual(missing_summary["drill_status"]["status"], "missing")
        self.assertEqual(no_summary["drill_status"]["status"], "missing_summary")
        self.assertEqual(unsupported_summary["drill_status"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["drill_status"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_field_retest_operator_drill_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_reconciliation_summary(self):
        with tempfile.TemporaryDirectory() as td:
            reconciliation_path = Path(td) / "route_task_field_run_reconciliation.json"
            reconciliation_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_reconciliation.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_reconciliation_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-run-reconciliation-1",
                        "same_evidence_ref_required": True,
                        "reconciliation_verdict": {
                            "status": "ready",
                            "verdict": "same_evidence_ref_materials_reconciled",
                            "reason": "all support-safe materials use the same evidence_ref",
                        },
                        "materials_status": {
                            "status": "available",
                            "missing_materials": [],
                            "required_materials": [
                                "route status",
                                "task record",
                                "execution pack summary",
                            ],
                        },
                        "operator_next_steps": [
                            "Keep this as metadata-only support evidence before any real field run."
                        ],
                        "phone_safe_summary": {
                            "safe_copy": (
                                "Route-task field-run reconciliation is metadata-only; "
                                "not delivery success and not HIL."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_reconciliation_ref=str(reconciliation_path),
            )
            summary = payload["route_task_field_run_reconciliation"]
            summary_alias = payload["route_task_field_run_reconciliation_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_reconciliation_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_reconciliation_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_reconciliation.v1")
        self.assertEqual(summary["reconciliation_verdict"]["status"], "ready")
        self.assertEqual(
            summary["reconciliation_verdict"]["verdict"],
            "same_evidence_ref_materials_reconciled",
        )
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://route-task-field-run-reconciliation-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["materials_status"]["status"], "available")
        self.assertIn("execution pack summary", summary["materials_status"]["required_materials"])
        self.assertIn("metadata-only", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("not delivery success", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("cursor_advance_or_persistence", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertIn("production_readiness", summary["not_proven"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        for forbidden_key in (
            "collect_triggered",
            "dropoff_triggered",
            "cancel_triggered",
            "ack_post_allowed",
            "cursor_updates_allowed",
            "persistence_updates_allowed",
            "terminal_ack_allowed",
            "nav2_triggered",
            "hil_pass",
            "production_ready",
            "dropoff_completion",
            "cancel_completion",
        ):
            self.assertNotIn(forbidden_key, summary)
        self.assertNotIn(str(reconciliation_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_run_reconciliation_env_missing_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "route_task_field_run_reconciliation_env.json"
            env_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_reconciliation.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_reconciliation_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-run-reconciliation-2",
                        "same_evidence_ref_required": True,
                        "reconciliation_verdict": {
                            "status": "blocked_missing_material",
                            "verdict": "not_proven",
                            "reason": "missing execution pack summary",
                        },
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["execution pack summary"],
                        },
                        "operator_next_steps": ["Regenerate Task A reconciliation artifact."],
                        "phone_safe_summary": {
                            "safe_copy": "Route-task field-run reconciliation is metadata-only; not_proven.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION")
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION"] = str(env_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_reconciliation"
                ]
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION"] = previous

            missing_path = Path(td) / "Bearer-secret-token" / "missing_reconciliation.json"
            missing_summary = summarize_route_task_field_run_reconciliation(str(missing_path))

            unsupported_path = Path(td) / "unsupported_reconciliation.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_execution_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_execution_pack_gate"
                        ),
                        "safe_copy": "Unsupported reconciliation is metadata-only; not delivery success.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_reconciliation(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_reconciliation.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_reconciliation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_reconciliation_gate"
                        ),
                        "production_ready": True,
                        "phone_safe_summary": {
                            "safe_copy": "Reconciliation confirms delivery success and terminal ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_reconciliation(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["reconciliation_verdict"]["status"], "blocked_missing_material")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("execution pack summary", env_summary["materials_status"]["missing_materials"])
        self.assertEqual(missing_summary["reconciliation_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["reconciliation_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["reconciliation_verdict"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_field_run_reconciliation_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_completion_signal_summary(self):
        with tempfile.TemporaryDirectory() as td:
            signal_path = Path(td) / "route_task_completion_signal.json"
            signal_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_completion_signal.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_completion_signal_gate"
                        ),
                        "evidence_ref": "evidence://route-task-completion-signal-1",
                        "same_evidence_ref_required": True,
                        "completion_verdict": {
                            "status": "ready",
                            "verdict": "ready_for_route_task_completion_review",
                            "reason": "completion materials share the same evidence_ref",
                        },
                        "fixed_route_summary": {"status": "available", "route_id": "route-a"},
                        "task_record_summary": {"final_status": "failed", "task_id": "task-a"},
                        "state_transition_summary": {"terminal_state": "error"},
                        "dropoff_completion": {"status": "not_proven"},
                        "cancel_completion": {"status": "not_proven"},
                        "failure_reason": "navigation_failed",
                        "recovery_reason": "manual_recovery_required",
                        "materials_status": {
                            "status": "available",
                            "required_materials": [
                                "fixed-route status",
                                "task record",
                                "dropoff/cancel completion flags",
                            ],
                        },
                        "operator_next_steps": [
                            "Review completion signal before any real field claim."
                        ],
                        "phone_safe_summary": {
                            "safe_copy": (
                                "Route-task completion signal is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_completion_signal_ref=str(signal_path),
            )
            summary = payload["route_task_completion_signal"]
            summary_alias = payload["route_task_completion_signal_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_completion_signal_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_completion_signal_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_completion_signal.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["completion_verdict"]["status"], "ready")
        self.assertEqual(
            summary["completion_verdict"]["verdict"],
            "ready_for_route_task_completion_review",
        )
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-task-completion-signal-1")
        self.assertEqual(summary["fixed_route_summary"]["status"], "available")
        self.assertEqual(summary["task_record_summary"]["final_status"], "failed")
        self.assertEqual(summary["state_transition_summary"]["terminal_state"], "error")
        self.assertEqual(summary["dropoff_completion"]["status"], "not_proven")
        self.assertEqual(summary["cancel_completion"]["status"], "not_proven")
        self.assertEqual(summary["failure_reason"], "navigation_failed")
        self.assertEqual(summary["recovery_reason"], "manual_recovery_required")
        self.assertIn("dropoff/cancel completion flags", summary["materials_status"]["required_materials"])
        self.assertIn("metadata-only", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success=false", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertIn("real_dropoff_completion", summary["not_proven"])
        self.assertIn("real_cancel_completion", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertNotIn(str(signal_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_completion_signal_env_missing_bad_json_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "route_task_completion_signal_env.json"
            env_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_completion_signal.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_completion_signal_gate"
                        ),
                        "evidence_ref": "evidence://route-task-completion-signal-2",
                        "completion_verdict": {
                            "status": "blocked_missing_completion_materials",
                            "verdict": "not_proven",
                            "reason": "missing dropoff/cancel completion flags",
                        },
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["dropoff/cancel completion flags"],
                        },
                        "phone_safe_summary": {
                            "safe_copy": "Route-task completion signal is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_COMPLETION_SIGNAL")
            os.environ["TRASHBOT_ROUTE_TASK_COMPLETION_SIGNAL"] = str(env_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_completion_signal"
                ]
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_COMPLETION_SIGNAL", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_COMPLETION_SIGNAL"] = previous

            missing_path = Path(td) / "Bearer-secret-token" / "missing_completion_signal.json"
            missing_summary = summarize_route_task_completion_signal(str(missing_path))

            bad_json_path = Path(td) / "bad_completion_signal.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_route_task_completion_signal(str(bad_json_path))

            unsupported_path = Path(td) / "unsupported_completion_signal.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_reconciliation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_reconciliation_gate"
                        ),
                        "safe_copy": "Unsupported completion signal is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_completion_signal(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_completion_signal.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_completion_signal.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_completion_signal_gate"
                        ),
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "phone_safe_summary": {
                            "safe_copy": "Completion signal confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_completion_signal(str(unsafe_path))
            encoded = json.dumps(
                [
                    env_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["completion_verdict"]["status"], "blocked_missing_completion_materials")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("dropoff/cancel completion flags", env_summary["materials_status"]["missing_materials"])
        self.assertEqual(missing_summary["completion_verdict"]["status"], "missing")
        self.assertEqual(bad_json_summary["completion_verdict"]["status"], "read_error")
        self.assertEqual(unsupported_summary["completion_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["completion_verdict"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_completion_signal_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_terminal_completion_rehearsal_summary(self):
        with tempfile.TemporaryDirectory() as td:
            rehearsal_path = Path(td) / "terminal_completion_rehearsal.json"
            rehearsal_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_terminal_completion_rehearsal.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_terminal_completion_rehearsal_gate"
                        ),
                        "evidence_ref": "terminal-rehearsal-001",
                        "route_task_terminal_completion_rehearsal_summary": {
                            "terminal_verdict": {
                                "status": "route_task_terminal_completion_rehearsal",
                                "verdict": "not_proven",
                                "reason": "materials share the same evidence_ref",
                            },
                            "final_status": "failed",
                            "final_state": "error",
                            "dropoff_result": {
                                "status": "not_proven",
                                "result_code": "manual_confirm_timeout",
                            },
                            "cancel_reason": "",
                            "failure_reason": "dropoff confirmation timed out",
                            "recovery_reason": "manual_recovery_required",
                            "safe_evidence_ref": "terminal-rehearsal-001",
                            "same_evidence_ref_required": True,
                            "route_progress": {
                                "present": True,
                                "evidence_ref": "terminal-rehearsal-001",
                            },
                            "materials_status": {
                                "status": "not_proven",
                                "reason": "real dropoff/cancel completion is still missing",
                            },
                            "operator_next_steps": ["Attach field dropoff/cancel material."],
                            "phone_safe_summary": {
                                "safe_copy": (
                                    "Route/task terminal completion rehearsal is metadata-only; "
                                    "delivery_success=false; primary_actions_enabled=false."
                                )
                            },
                            "not_proven": ["real_dropoff_completion"],
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        },
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_terminal_completion_rehearsal_ref=str(rehearsal_path),
            )
            summary = payload["route_task_terminal_completion_rehearsal"]
            summary_alias = payload["route_task_terminal_completion_rehearsal_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(
            summary["schema"],
            "trashbot.route_task_terminal_completion_rehearsal_summary.v1",
        )
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_terminal_completion_rehearsal_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_terminal_completion_rehearsal.v1")
        self.assertEqual(summary["terminal_verdict"]["status"], "route_task_terminal_completion_rehearsal")
        self.assertEqual(summary["terminal_verdict"]["verdict"], "not_proven")
        self.assertEqual(summary["final_status"], "failed")
        self.assertEqual(summary["dropoff_result"]["result_code"], "manual_confirm_timeout")
        self.assertEqual(summary["failure_reason"], "dropoff confirmation timed out")
        self.assertEqual(summary["recovery_reason"], "manual_recovery_required")
        self.assertEqual(summary["safe_evidence_ref"], "terminal-rehearsal-001")
        self.assertTrue(summary["route_progress"]["present"])
        self.assertIn("real_dropoff_completion", summary["not_proven"])
        self.assertIn("real_cancel_completion", summary["not_proven"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertNotIn(str(rehearsal_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_terminal_completion_rehearsal_missing_mismatch_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            missing_path = Path(td) / "Bearer-secret-token" / "missing_terminal.json"
            missing_summary = summarize_route_task_terminal_completion_rehearsal(str(missing_path))

            unsupported_path = Path(td) / "unsupported_terminal.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_completion_signal.v1",
                        "evidence_boundary": "software_proof_docker_route_task_completion_signal_gate",
                        "safe_copy": "Unsupported terminal rehearsal is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_terminal_completion_rehearsal(str(unsupported_path))

            mismatch_path = Path(td) / "mismatch_terminal.json"
            mismatch_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_terminal_completion_rehearsal_summary.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_terminal_completion_rehearsal_gate"
                        ),
                        "safe_evidence_ref": "terminal-a",
                        "route_progress": {"present": True, "evidence_ref": "terminal-b"},
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            mismatch_summary = summarize_route_task_terminal_completion_rehearsal(str(mismatch_path))

            unsafe_path = Path(td) / "unsafe_terminal.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_terminal_completion_rehearsal.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_terminal_completion_rehearsal_gate"
                        ),
                        "evidence_ref": "terminal-unsafe",
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "route_task_terminal_completion_rehearsal_summary": {
                            "safe_evidence_ref": "terminal-unsafe",
                            "phone_safe_summary": {
                                "safe_copy": "Terminal rehearsal confirms delivery success and ACK posted.",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_terminal_completion_rehearsal(str(unsafe_path))
            encoded = json.dumps(
                [missing_summary, unsupported_summary, mismatch_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(
            missing_summary["terminal_verdict"]["status"],
            "blocked_missing_route_task_terminal_completion_rehearsal",
        )
        self.assertEqual(unsupported_summary["terminal_verdict"]["status"], "unsupported_schema")
        self.assertEqual(mismatch_summary["terminal_verdict"]["status"], "evidence_ref_mismatch")
        self.assertEqual(unsafe_summary["terminal_verdict"]["status"], "unsafe_fields")
        self.assertIn("blocked_missing_route_task_terminal_completion_rehearsal", encoded)
        self.assertIn("software_proof_docker_route_task_terminal_completion_rehearsal_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_terminal_review_decision_summary(self):
        with tempfile.TemporaryDirectory() as td:
            review_path = Path(td) / "route_task_terminal_review_decision.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_terminal_review_decision.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_terminal_review_decision_gate"
                        ),
                        "evidence_ref": "evidence://route-task-terminal-review-1",
                        "same_evidence_ref_required": True,
                        "review_decision": {
                            "status": "ready_for_field_retest_request_not_proven",
                            "decision": "request_field_retest_not_proven",
                            "reason": "terminal material review requires one field retest bundle",
                        },
                        "owner_handoff": "Autonomy",
                        "next_required_evidence": [
                            "same evidence_ref terminal review bundle",
                            "operator terminal note",
                        ],
                        "field_retest_request_guidance": {
                            "status": "requested_not_proven",
                            "reason": "capture terminal material before any retest",
                        },
                        "review_summary": {
                            "status": "ready",
                            "summary": "metadata-only terminal review decision is ready",
                        },
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only terminal review decision available",
                        },
                        "phone_safe_summary": {
                            "safe_copy": (
                                "Route-task terminal review decision is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_terminal_review_decision_ref=str(review_path),
            )
            summary = payload["route_task_terminal_review_decision"]
            summary_alias = payload["route_task_terminal_review_decision_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_terminal_review_decision_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_terminal_review_decision_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_terminal_review_decision.v1")
        self.assertEqual(summary["review_decision"]["status"], "ready_for_field_retest_request_not_proven")
        self.assertEqual(summary["review_decision"]["decision"], "request_field_retest_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-task-terminal-review-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["owner_handoff"], "Autonomy")
        self.assertIn("operator terminal note", summary["next_required_evidence"])
        self.assertEqual(summary["field_retest_request_guidance"]["status"], "requested_not_proven")
        self.assertEqual(summary["review_summary"]["status"], "ready")
        self.assertIn("delivery_success=false", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(review_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_terminal_review_decision_env_diagnostics_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_terminal_review_decision_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_terminal_review_decision_summary.v1",
                        "source_schema": "trashbot.route_task_terminal_review_decision.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_terminal_review_decision_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_terminal_review_decision_gate"
                        ),
                        "safe_evidence_ref": "evidence://route-task-terminal-review-2",
                        "same_evidence_ref_required": True,
                        "review_decision": {
                            "status": "blocked_missing_route_task_terminal_review_decision",
                            "decision": "not_proven",
                        },
                        "owner_handoff": "Robot",
                        "next_required_evidence": ["terminal review artifact"],
                        "field_retest_request_guidance": {"status": "blocked"},
                        "phone_safe_summary": {
                            "safe_copy": "Route-task terminal review decision is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_review = os.environ.get("TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION", None)
            os.environ["TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_terminal_review_decision"
                ]
            finally:
                if previous_review is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION"] = previous_review
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "route_task_terminal_review_decision_summary": {
                            "schema": "trashbot.route_task_terminal_review_decision_summary.v1",
                            "source_schema": "trashbot.route_task_terminal_review_decision.v1",
                            "evidence_boundary": (
                                "software_proof_docker_route_task_terminal_review_decision_gate"
                            ),
                            "source_evidence_boundary": (
                                "software_proof_docker_route_task_terminal_review_decision_gate"
                            ),
                            "safe_evidence_ref": "evidence://route-task-terminal-review-3",
                            "same_evidence_ref_required": True,
                            "review_decision": {
                                "status": "ready_for_field_retest_request_not_proven",
                                "decision": "request_field_retest_not_proven",
                            },
                            "owner_handoff": "Autonomy",
                            "field_retest_request_guidance": {"status": "requested_not_proven"},
                            "phone_safe_summary": {
                                "safe_copy": (
                                    "Route-task terminal review decision is metadata-only; "
                                    "delivery_success=false."
                                ),
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["route_task_terminal_review_decision"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_terminal_review.json"
            missing_summary = summarize_route_task_terminal_review_decision(str(missing_path))
            unsupported_summary = summarize_route_task_terminal_review_decision(
                {
                    "schema": "trashbot.route_task_terminal_completion_rehearsal.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_terminal_completion_rehearsal_gate"
                    ),
                    "safe_copy": "Unsupported terminal review is metadata-only; delivery_success=false.",
                }
            )
            mismatch_summary = summarize_route_task_terminal_review_decision(
                {
                    "schema": "trashbot.route_task_terminal_review_decision.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_terminal_review_decision_gate"
                    ),
                    "evidence_ref": "evidence://route-task-terminal-review-a",
                    "route_task_terminal_review_decision_summary": {
                        "safe_evidence_ref": "evidence://route-task-terminal-review-b",
                    },
                    "same_evidence_ref_required": True,
                    "safe_copy": "Route-task terminal review decision is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_route_task_terminal_review_decision(
                {
                    "schema": "trashbot.route_task_terminal_review_decision.v1",
                    "evidence_boundary": (
                        "software_proof_docker_route_task_terminal_review_decision_gate"
                    ),
                    "same_evidence_ref_required": True,
                    "delivery_success": True,
                    "phone_safe_summary": {
                        "safe_copy": "Terminal review confirms delivery success and ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [env_summary, diagnostics_summary, missing_summary, unsupported_summary, mismatch_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(
            env_summary["review_decision"]["status"],
            "blocked_missing_route_task_terminal_review_decision",
        )
        self.assertEqual(diagnostics_summary["owner_handoff"], "Autonomy")
        self.assertEqual(diagnostics_summary["field_retest_request_guidance"]["status"], "requested_not_proven")
        self.assertEqual(
            missing_summary["review_decision"]["status"],
            "blocked_missing_route_task_terminal_review_decision",
        )
        self.assertEqual(unsupported_summary["review_decision"]["status"], "unsupported_schema")
        self.assertEqual(mismatch_summary["review_decision"]["status"], "evidence_ref_mismatch")
        self.assertEqual(unsafe_summary["review_decision"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_terminal_review_decision_gate", encoded)
        self.assertIn("blocked_missing_route_task_terminal_review_decision", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_console_summary(self):
        with tempfile.TemporaryDirectory() as td:
            console_path = Path(td) / "route_task_field_run_console.json"
            console_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_console.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_console_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-run-console-1",
                        "same_evidence_ref_required": True,
                        "console_verdict": {
                            "status": "ready",
                            "verdict": "ready_for_operator_field_run",
                            "reason": "field-run console can guide metadata capture only",
                        },
                        "field_run_plan": {
                            "status": "ready",
                            "steps": ["Review route pack", "Capture checklist before claims"],
                        },
                        "capture_checklist": {
                            "status": "ready",
                            "items": ["route status", "task record", "dropoff/cancel material"],
                        },
                        "dropoff_completion": {"status": "not_proven"},
                        "cancel_completion": {"status": "not_proven"},
                        "operator_next_steps": [
                            "Run real field collection before claiming delivery."
                        ],
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only route-task field-run console",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field-run console is metadata-only; "
                                "delivery_success=false and not_proven."
                            ),
                            "operator_next_steps": ["Keep primary actions blocked."],
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_console_ref=str(console_path),
            )
            summary = payload["route_task_field_run_console"]
            summary_alias = payload["route_task_field_run_console_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_console_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_console_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_console.v1")
        self.assertEqual(summary["console_verdict"]["status"], "ready")
        self.assertEqual(summary["console_verdict"]["verdict"], "ready_for_operator_field_run")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-task-field-run-console-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["field_run_plan"]["status"], "ready")
        self.assertIn("route status", summary["capture_checklist"]["items"])
        self.assertEqual(summary["dropoff_completion"]["status"], "not_proven")
        self.assertEqual(summary["cancel_completion"]["status"], "not_proven")
        self.assertIn("Keep primary actions blocked.", summary["operator_next_steps"])
        self.assertEqual(summary["robot_diagnostics_summary"]["status"], "ready")
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertIn("real_dropoff_completion", summary["not_proven"])
        self.assertIn("real_cancel_completion", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertNotIn(str(console_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_run_console_env_missing_bad_json_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "route_task_field_run_console_env.json"
            env_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_console.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_console_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-run-console-2",
                        "console_verdict": {
                            "status": "blocked_missing_field_materials",
                            "verdict": "not_proven",
                            "reason": "missing field-run capture checklist",
                        },
                        "capture_checklist": {
                            "status": "blocked",
                            "missing_materials": ["field-run capture checklist"],
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": "Route-task field-run console is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE")
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE"] = str(env_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_console"
                ]
            finally:
                if previous is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE"] = previous

            missing_path = Path(td) / "Bearer-secret-token" / "missing_field_console.json"
            missing_summary = summarize_route_task_field_run_console(str(missing_path))

            bad_json_path = Path(td) / "bad_field_console.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_route_task_field_run_console(str(bad_json_path))

            unsupported_path = Path(td) / "unsupported_field_console.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_completion_signal.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_completion_signal_gate"
                        ),
                        "safe_copy": "Unsupported field-run console is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_console(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_field_console.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_console.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_console_gate"
                        ),
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Field-run console confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_console(str(unsafe_path))
            encoded = json.dumps(
                [
                    env_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["console_verdict"]["status"], "blocked_missing_field_materials")
        self.assertEqual(env_summary["capture_checklist"]["status"], "blocked")
        self.assertIn("field-run capture checklist", env_summary["capture_checklist"]["missing_materials"])
        self.assertEqual(missing_summary["console_verdict"]["status"], "missing")
        self.assertEqual(bad_json_summary["console_verdict"]["status"], "read_error")
        self.assertEqual(unsupported_summary["console_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["console_verdict"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_field_run_console_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_evidence_kit_summary(self):
        with tempfile.TemporaryDirectory() as td:
            kit_path = Path(td) / "route_task_field_run_evidence_kit.json"
            kit_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_evidence_kit.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_evidence_kit_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-run-evidence-kit-1",
                        "same_evidence_ref_required": True,
                        "kit_verdict": {
                            "status": "ready",
                            "verdict": "ready_for_field_run_material_review",
                            "reason": "kit materials use the same evidence_ref",
                        },
                        "materials_status": {
                            "status": "available",
                            "required_materials": ["console summary", "completion signal"],
                        },
                        "field_run_plan": {"status": "ready", "steps": ["review kit"]},
                        "capture_checklist": {"status": "ready", "items": ["route status"]},
                        "completion_signal_summary": {"status": "available"},
                        "reconciliation_summary": {"status": "available"},
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only kit available",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field-run evidence kit is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                            "operator_next_steps": ["Keep primary actions blocked."],
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_evidence_kit_ref=str(kit_path),
            )
            summary = payload["route_task_field_run_evidence_kit"]
            summary_alias = payload["route_task_field_run_evidence_kit_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_evidence_kit_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_evidence_kit_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_evidence_kit.v1")
        self.assertEqual(summary["kit_verdict"]["status"], "ready")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-task-field-run-evidence-kit-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["materials_status"]["status"], "available")
        self.assertIn("console summary", summary["materials_status"]["required_materials"])
        self.assertEqual(summary["field_run_plan"]["status"], "ready")
        self.assertEqual(summary["completion_signal_summary"]["status"], "available")
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn(str(kit_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_run_evidence_kit_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_run_evidence_kit_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_evidence_kit_summary.v1",
                        "source_schema": "trashbot.route_task_field_run_evidence_kit.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_evidence_kit_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_run_evidence_kit_gate"
                        ),
                        "safe_evidence_ref": "evidence://route-task-field-run-evidence-kit-2",
                        "same_evidence_ref_required": True,
                        "kit_verdict": {"status": "blocked_missing_material", "verdict": "not_proven"},
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["completion signal"],
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": "Route-task field-run evidence kit is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_kit = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_evidence_kit"
                ]
            finally:
                if previous_kit is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT"] = previous_kit
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_evidence_kit.json"
            missing_summary = summarize_route_task_field_run_evidence_kit(str(missing_path))

            unsupported_path = Path(td) / "unsupported_evidence_kit.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_console.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_console_gate"
                        ),
                        "safe_copy": "Unsupported evidence kit is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_evidence_kit(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_evidence_kit.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_evidence_kit.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_evidence_kit_gate"
                        ),
                        "same_evidence_ref_required": False,
                        "delivery_success": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Evidence kit confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_evidence_kit(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["kit_verdict"]["status"], "blocked_missing_material")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("completion signal", env_summary["materials_status"]["missing_materials"])
        self.assertEqual(missing_summary["kit_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["kit_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["kit_verdict"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_field_run_evidence_kit_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_material_bundle_summary(self):
        with tempfile.TemporaryDirectory() as td:
            bundle_path = Path(td) / "route_task_field_run_material_bundle.json"
            bundle_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_bundle.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_bundle_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-run-material-bundle-1",
                        "same_evidence_ref_required": True,
                        "bundle_verdict": {
                            "status": "ready",
                            "verdict": "ready_for_field_run_material_handoff",
                            "reason": "material bundle uses the same evidence_ref",
                        },
                        "materials_status": {
                            "status": "available",
                            "required_materials": ["route template", "operator notes"],
                        },
                        "material_directory_scaffold": {
                            "status": "generated",
                            "files": ["route.md", "task.md", "mobile_summary.md"],
                        },
                        "bundle_summary": {
                            "status": "ready",
                            "summary": "metadata-only material handoff is ready",
                        },
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only material bundle available",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field-run material bundle is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                            "operator_next_steps": ["Keep primary actions blocked."],
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_material_bundle_ref=str(bundle_path),
            )
            summary = payload["route_task_field_run_material_bundle"]
            summary_alias = payload["route_task_field_run_material_bundle_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_material_bundle_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_material_bundle_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_material_bundle.v1")
        self.assertEqual(summary["bundle_verdict"]["status"], "ready")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-task-field-run-material-bundle-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["materials_status"]["status"], "available")
        self.assertIn("operator notes", summary["materials_status"]["required_materials"])
        self.assertEqual(summary["material_directory_scaffold"]["status"], "generated")
        self.assertEqual(summary["bundle_summary"]["status"], "ready")
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn(str(bundle_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_run_material_bundle_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_run_material_bundle_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_bundle_summary.v1",
                        "source_schema": "trashbot.route_task_field_run_material_bundle.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_bundle_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_bundle_gate"
                        ),
                        "safe_evidence_ref": "evidence://route-task-field-run-material-bundle-2",
                        "same_evidence_ref_required": True,
                        "bundle_verdict": {"status": "blocked_missing_material", "verdict": "not_proven"},
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["operator notes"],
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": "Route-task field-run material bundle is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_bundle = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_material_bundle"
                ]
            finally:
                if previous_bundle is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE"] = previous_bundle
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_material_bundle.json"
            missing_summary = summarize_route_task_field_run_material_bundle(str(missing_path))

            unsupported_path = Path(td) / "unsupported_material_bundle.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_evidence_kit.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_evidence_kit_gate"
                        ),
                        "safe_copy": "Unsupported material bundle is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_material_bundle(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_material_bundle.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_bundle.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_bundle_gate"
                        ),
                        "same_evidence_ref_required": False,
                        "delivery_success": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Material bundle confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_material_bundle(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["bundle_verdict"]["status"], "blocked_missing_material")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("operator notes", env_summary["materials_status"]["missing_materials"])
        self.assertEqual(missing_summary["bundle_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["bundle_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["bundle_verdict"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_field_run_material_bundle_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_task_field_run_material_validation_summary(self):
        with tempfile.TemporaryDirectory() as td:
            validation_path = Path(td) / "route_task_field_run_material_validation.json"
            validation_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_validation.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_validation_gate"
                        ),
                        "evidence_ref": "evidence://route-task-field-run-material-validation-1",
                        "same_evidence_ref_required": True,
                        "validation_verdict": {
                            "status": "ready",
                            "verdict": "ready_for_material_handoff_review",
                            "reason": "all material validation checks passed",
                        },
                        "materials_status": {
                            "status": "available",
                            "required_materials": ["route template", "material bundle summary"],
                        },
                        "validation_summary": {
                            "status": "ready",
                            "summary": "metadata-only material validation is ready",
                        },
                        "material_validation_checks": [
                            {"name": "same_evidence_ref", "status": "pass"},
                            {"name": "safe_copy_present", "status": "pass"},
                        ],
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only validation available",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field-run material validation is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                            "operator_next_steps": ["Review validation checks before field run."],
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_task_field_run_material_validation_ref=str(validation_path),
            )
            summary = payload["route_task_field_run_material_validation"]
            summary_alias = payload["route_task_field_run_material_validation_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_task_field_run_material_validation_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_task_field_run_material_validation_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_run_material_validation.v1")
        self.assertEqual(summary["validation_verdict"]["status"], "ready")
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://route-task-field-run-material-validation-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["materials_status"]["status"], "available")
        self.assertIn("material bundle summary", summary["materials_status"]["required_materials"])
        self.assertEqual(summary["validation_summary"]["status"], "ready")
        self.assertEqual(summary["material_validation_checks"][0]["status"], "pass")
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn(str(validation_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_task_field_run_material_validation_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_task_field_run_material_validation_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_validation_summary.v1",
                        "source_schema": "trashbot.route_task_field_run_material_validation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_validation_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_validation_gate"
                        ),
                        "safe_evidence_ref": "evidence://route-task-field-run-material-validation-2",
                        "same_evidence_ref_required": True,
                        "validation_verdict": {"status": "blocked_missing_material", "verdict": "not_proven"},
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["material bundle summary"],
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route-task field-run material validation is metadata-only; "
                                "delivery_success=false."
                            ),
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_validation = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION", None)
            os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_task_field_run_material_validation"
                ]
            finally:
                if previous_validation is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION"] = previous_validation
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_material_validation.json"
            missing_summary = summarize_route_task_field_run_material_validation(str(missing_path))

            unsupported_path = Path(td) / "unsupported_material_validation.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_bundle.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_bundle_gate"
                        ),
                        "safe_copy": "Unsupported material validation is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_task_field_run_material_validation(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_material_validation.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_validation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_validation_gate"
                        ),
                        "same_evidence_ref_required": False,
                        "delivery_success": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Material validation confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_task_field_run_material_validation(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["validation_verdict"]["status"], "blocked_missing_material")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("material bundle summary", env_summary["materials_status"]["missing_materials"])
        self.assertEqual(missing_summary["validation_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["validation_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["validation_verdict"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_task_field_run_material_validation_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_elevator_field_run_material_validation_summary(self):
        with tempfile.TemporaryDirectory() as td:
            validation_path = Path(td) / "elevator_field_run_material_validation.json"
            validation_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_material_validation.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_material_validation_gate"
                        ),
                        "evidence_ref": "evidence://elevator-field-run-material-validation-1",
                        "same_evidence_ref_required": True,
                        "validation_verdict": {
                            "status": "ready",
                            "verdict": "ready_for_operator_review",
                            "reason": "all elevator material checks passed",
                        },
                        "materials_status": {
                            "status": "available",
                            "required_materials": ["door state notes", "floor confirmation"],
                        },
                        "validation_summary": {
                            "status": "ready",
                            "summary": "metadata-only elevator validation is ready",
                        },
                        "material_validation_checks": [
                            {"name": "same_evidence_ref", "status": "pass"},
                            {"name": "safe_copy_present", "status": "pass"},
                        ],
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only elevator validation available",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Elevator field-run material validation is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                            "operator_next_steps": ["Review elevator materials before field run."],
                        },
                        "not_proven": ["delivery_success", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                elevator_field_run_material_validation_ref=str(validation_path),
            )
            summary = payload["elevator_field_run_material_validation"]
            summary_alias = payload["elevator_field_run_material_validation_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.elevator_field_run_material_validation_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_elevator_field_material_validation_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.elevator_field_run_material_validation.v1")
        self.assertEqual(summary["validation_verdict"]["status"], "ready")
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://elevator-field-run-material-validation-1",
        )
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["materials_status"]["status"], "available")
        self.assertIn("floor confirmation", summary["materials_status"]["required_materials"])
        self.assertEqual(summary["validation_summary"]["status"], "ready")
        self.assertEqual(summary["material_validation_checks"][0]["status"], "pass")
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("real_elevator_operation", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn(str(validation_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_elevator_field_run_material_validation_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "elevator_field_run_material_validation_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_material_validation_summary.v1",
                        "source_schema": "trashbot.elevator_field_run_material_validation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_material_validation_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_elevator_field_material_validation_gate"
                        ),
                        "safe_evidence_ref": "evidence://elevator-field-run-material-validation-2",
                        "same_evidence_ref_required": True,
                        "validation_verdict": {"status": "blocked_missing_material", "verdict": "not_proven"},
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["door state notes"],
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Elevator field-run material validation is metadata-only; "
                                "delivery_success=false."
                            ),
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_validation = os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION")
            previous_summary = os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY")
            os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION", None)
            os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "elevator_field_run_material_validation"
                ]
            finally:
                if previous_validation is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION"] = previous_validation
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_elevator_validation.json"
            missing_summary = summarize_elevator_field_run_material_validation(str(missing_path))

            unsupported_path = Path(td) / "unsupported_elevator_validation.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_task_field_run_material_validation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_task_field_run_material_validation_gate"
                        ),
                        "safe_copy": "Unsupported elevator validation is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_elevator_field_run_material_validation(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_elevator_validation.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_material_validation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_material_validation_gate"
                        ),
                        "same_evidence_ref_required": False,
                        "delivery_success": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Elevator validation confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_elevator_field_run_material_validation(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["validation_verdict"]["status"], "blocked_missing_material")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("door state notes", env_summary["materials_status"]["missing_materials"])
        self.assertEqual(missing_summary["validation_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["validation_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["validation_verdict"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_elevator_field_material_validation_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_elevator_field_run_review_summary(self):
        with tempfile.TemporaryDirectory() as td:
            review_path = Path(td) / "elevator_field_run_review.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_review.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_review_decision_gate"
                        ),
                        "evidence_ref": "evidence://elevator-field-run-review-1",
                        "same_evidence_ref_required": True,
                        "review_decision": {
                            "status": "ready",
                            "decision": "ready_for_controlled_elevator_field_rehearsal_not_proven",
                            "reason": "review decision is ready for a controlled rehearsal checklist",
                        },
                        "blocked_categories": ["blocked_missing_materials"],
                        "operator_next_steps": ["Re-capture door state notes before the next rehearsal."],
                        "commands_to_rerun": ["python3 pc-tools/evidence/elevator_field_run_review.py --validation-json validation.json"],
                        "capture_checklist": ["door state note", "target floor confirmation"],
                        "review_summary": {
                            "status": "ready",
                            "summary": "metadata-only elevator review decision is ready",
                        },
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only elevator review available",
                        },
                        "phone_safe_summary": {
                            "safe_copy": (
                                "Elevator field-run review is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_elevator_operation"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                elevator_field_run_review_ref=str(review_path),
            )
            summary = payload["elevator_field_run_review"]
            summary_alias = payload["elevator_field_run_review_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.elevator_field_run_review_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_elevator_field_review_decision_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.elevator_field_run_review.v1")
        self.assertEqual(summary["review_decision"]["status"], "ready")
        self.assertEqual(
            summary["review_decision"]["decision"],
            "ready_for_controlled_elevator_field_rehearsal_not_proven",
        )
        self.assertEqual(summary["safe_evidence_ref"], "evidence://elevator-field-run-review-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertIn("blocked_missing_materials", summary["blocked_categories"])
        self.assertIn("door state notes", summary["operator_next_steps"][0])
        self.assertIn("elevator_field_run_review.py", summary["commands_to_rerun"][0])
        self.assertIn("target floor confirmation", summary["capture_checklist"])
        self.assertEqual(summary["review_summary"]["status"], "ready")
        self.assertIn("delivery_success=false", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("real_elevator_operation", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertNotIn(str(review_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_elevator_field_run_review_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "elevator_field_run_review_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_review_summary.v1",
                        "source_schema": "trashbot.elevator_field_run_review.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_review_decision_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_elevator_field_review_decision_gate"
                        ),
                        "safe_evidence_ref": "evidence://elevator-field-run-review-2",
                        "same_evidence_ref_required": True,
                        "review_decision": {
                            "status": "blocked_missing_materials",
                            "decision": "blocked_missing_materials",
                        },
                        "blocked_categories": ["blocked_missing_materials"],
                        "phone_safe_summary": {
                            "safe_copy": "Elevator field-run review is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_review = os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW")
            previous_summary = os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY")
            os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW", None)
            os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "elevator_field_run_review"
                ]
            finally:
                if previous_review is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW"] = previous_review
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_elevator_review.json"
            missing_summary = summarize_elevator_field_run_review(str(missing_path))

            unsupported_path = Path(td) / "unsupported_elevator_review.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_material_validation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_material_validation_gate"
                        ),
                        "safe_copy": "Unsupported elevator review is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_elevator_field_run_review(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_elevator_review.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_review.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_review_decision_gate"
                        ),
                        "same_evidence_ref_required": False,
                        "delivery_success": True,
                        "phone_safe_summary": {
                            "safe_copy": "Elevator review confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_elevator_field_run_review(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["review_decision"]["status"], "blocked_missing_materials")
        self.assertIn("blocked_missing_materials", env_summary["blocked_categories"])
        self.assertEqual(missing_summary["review_decision"]["status"], "missing")
        self.assertEqual(unsupported_summary["review_decision"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["review_decision"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_elevator_field_review_decision_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_elevator_field_run_execution_pack_summary(self):
        with tempfile.TemporaryDirectory() as td:
            pack_path = Path(td) / "elevator_field_run_execution_pack.json"
            pack_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_execution_pack.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"
                        ),
                        "evidence_ref": "evidence://elevator-field-run-execution-pack-1",
                        "same_evidence_ref_required": True,
                        "execution_pack_verdict": {
                            "status": "ready_for_controlled_rehearsal_not_proven",
                            "verdict": "ready_for_controlled_rehearsal_not_proven",
                            "reason": "operator can rehearse with metadata-only checklist",
                        },
                        "controlled_rehearsal_manifest": {
                            "status": "ready",
                            "boundary": "software_proof_docker_elevator_field_rehearsal_execution_pack_gate",
                        },
                        "required_material_templates": ["door state note", "target floor confirmation"],
                        "first_run_commands": ["python3 pc-tools/evidence/elevator_field_run_execution_pack.py --once-json"],
                        "rerun_commands": ["python3 pc-tools/evidence/elevator_field_run_review.py --once-json"],
                        "operator_handoff": {
                            "next_step": "Run controlled rehearsal and capture same evidence_ref.",
                        },
                        "robot_diagnostics_summary": {
                            "status": "ready",
                            "reason": "metadata-only elevator execution pack available",
                        },
                        "phone_safe_summary": {
                            "safe_copy": (
                                "Elevator execution pack is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_elevator_operation"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                elevator_field_run_execution_pack_ref=str(pack_path),
            )
            summary = payload["elevator_field_run_execution_pack"]
            summary_alias = payload["elevator_field_run_execution_pack_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.elevator_field_run_execution_pack_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.elevator_field_run_execution_pack.v1")
        self.assertEqual(
            summary["execution_pack_verdict"]["status"],
            "ready_for_controlled_rehearsal_not_proven",
        )
        self.assertEqual(summary["safe_evidence_ref"], "evidence://elevator-field-run-execution-pack-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["controlled_rehearsal_manifest"]["status"], "ready")
        self.assertIn("door state note", summary["required_material_templates"])
        self.assertIn("elevator_field_run_execution_pack.py", summary["first_run_commands"][0])
        self.assertIn("elevator_field_run_review.py", summary["rerun_commands"][0])
        self.assertIn("same evidence_ref", summary["operator_handoff"]["next_step"])
        self.assertIn("delivery_success=false", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("real_elevator_operation", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertNotIn(str(pack_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_elevator_field_run_execution_pack_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "elevator_field_run_execution_pack_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_execution_pack_summary.v1",
                        "source_schema": "trashbot.elevator_field_run_execution_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"
                        ),
                        "safe_evidence_ref": "evidence://elevator-field-run-execution-pack-2",
                        "same_evidence_ref_required": True,
                        "execution_pack_verdict": "blocked_missing_materials",
                        "controlled_rehearsal_manifest": {"status": "blocked"},
                        "required_material_templates": ["door state note"],
                        "first_run_commands": ["python3 pc-tools/evidence/elevator_field_run_execution_pack.py --once-json"],
                        "rerun_commands": ["python3 pc-tools/evidence/elevator_field_run_review.py --once-json"],
                        "operator_handoff": {"next_step": "Recapture missing materials."},
                        "phone_safe_summary": {
                            "safe_copy": "Elevator execution pack is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_pack = os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK")
            previous_summary = os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY")
            os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK", None)
            os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "elevator_field_run_execution_pack"
                ]
            finally:
                if previous_pack is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK"] = previous_pack
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_elevator_execution_pack.json"
            missing_summary = summarize_elevator_field_run_execution_pack(str(missing_path))

            unsupported_path = Path(td) / "unsupported_elevator_execution_pack.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_review.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_review_decision_gate"
                        ),
                        "safe_copy": "Unsupported elevator execution pack is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_elevator_field_run_execution_pack(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_elevator_execution_pack.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_execution_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"
                        ),
                        "same_evidence_ref_required": False,
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "phone_safe_summary": {
                            "safe_copy": "Elevator execution pack confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_elevator_field_run_execution_pack(str(unsafe_path))
            weak_same_ref_path = Path(td) / "weak_same_ref_elevator_execution_pack.json"
            weak_same_ref_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_execution_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"
                        ),
                        "same_evidence_ref_required": "false",
                        "phone_safe_summary": {
                            "safe_copy": "Elevator execution pack is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            weak_same_ref_summary = summarize_elevator_field_run_execution_pack(str(weak_same_ref_path))
            encoded = json.dumps(
                [
                    env_summary,
                    missing_summary,
                    unsupported_summary,
                    unsafe_summary,
                    weak_same_ref_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["execution_pack_verdict"]["status"], "blocked_missing_materials")
        self.assertEqual(env_summary["controlled_rehearsal_manifest"]["status"], "blocked")
        self.assertEqual(missing_summary["execution_pack_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["execution_pack_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["execution_pack_verdict"]["status"], "unsafe_fields")
        self.assertEqual(weak_same_ref_summary["execution_pack_verdict"]["status"], "unsafe_fields")
        self.assertFalse(weak_same_ref_summary["same_evidence_ref_required"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_elevator_field_rehearsal_execution_pack_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_elevator_route_evidence_reconciliation_summary(self):
        with tempfile.TemporaryDirectory() as td:
            reconciliation_path = Path(td) / "elevator_route_evidence_reconciliation.json"
            reconciliation_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_route_evidence_reconciliation.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_elevator_route_evidence_reconciliation_gate"
                        ),
                        "evidence_ref": "evidence://elevator-route-reconcile-1",
                        "same_evidence_ref_required": True,
                        "reconciliation_verdict": {
                            "status": "ready_for_operator_review_not_proven",
                            "verdict": "same_evidence_ref_reconciled",
                            "reason": "elevator evidence and route completion share one evidence_ref",
                        },
                        "source_states": {
                            "elevator_rehearsal": "available",
                            "route_completion_signal": "available",
                        },
                        "materials_status": {"status": "available"},
                        "missing_materials": [],
                        "mismatch_reasons": [],
                        "operator_next_steps": [
                            "Review same evidence_ref before any field-run claim."
                        ],
                        "robot_diagnostics_summary": {
                            "status": "metadata_only",
                            "reason": "safe robot diagnostics summary only",
                        },
                        "phone_safe_summary": {
                            "safe_copy": (
                                "Elevator route evidence reconciliation is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_elevator_operation"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                elevator_route_evidence_reconciliation_ref=str(reconciliation_path),
            )
            summary = payload["elevator_route_evidence_reconciliation"]
            summary_alias = payload["elevator_route_evidence_reconciliation_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.elevator_route_evidence_reconciliation_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_elevator_route_evidence_reconciliation_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.elevator_route_evidence_reconciliation.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["reconciliation_verdict"]["status"], "ready_for_operator_review_not_proven")
        self.assertEqual(summary["reconciliation_verdict"]["verdict"], "same_evidence_ref_reconciled")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://elevator-route-reconcile-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["source_states"]["elevator_rehearsal"], "available")
        self.assertEqual(summary["source_states"]["route_completion_signal"], "available")
        self.assertEqual(summary["materials_status"]["status"], "available")
        self.assertIn("same evidence_ref", summary["operator_next_steps"][0])
        self.assertIn("delivery_success=false", summary["phone_safe_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("remote_ack", summary["not_proven"])
        self.assertIn("terminal_ack", summary["not_proven"])
        self.assertIn("real_elevator_operation", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertNotIn(str(reconciliation_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_elevator_route_evidence_reconciliation_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "elevator_route_evidence_reconciliation_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_route_evidence_reconciliation_summary.v1",
                        "source_schema": "trashbot.elevator_route_evidence_reconciliation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_route_evidence_reconciliation_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_elevator_route_evidence_reconciliation_gate"
                        ),
                        "safe_evidence_ref": "evidence://elevator-route-reconcile-2",
                        "same_evidence_ref_required": True,
                        "reconciliation_verdict": {
                            "status": "blocked_mismatch",
                            "verdict": "not_proven",
                            "reason": "route completion evidence_ref mismatch",
                        },
                        "source_states": {
                            "elevator_rehearsal": "available",
                            "route_completion_signal": "mismatch",
                        },
                        "materials_status": {
                            "status": "blocked",
                            "missing_materials": ["same evidence_ref route completion signal"],
                        },
                        "mismatch_reasons": ["route completion evidence_ref mismatch"],
                        "phone_safe_summary": {
                            "safe_copy": "Elevator route reconciliation is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION")
            previous_summary = os.environ.get("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY")
            os.environ.pop("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION", None)
            os.environ["TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "elevator_route_evidence_reconciliation"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_elevator_route_reconciliation.json"
            missing_summary = summarize_elevator_route_evidence_reconciliation(str(missing_path))

            unsupported_path = Path(td) / "unsupported_elevator_route_reconciliation.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_field_run_execution_pack.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"
                        ),
                        "safe_copy": "Unsupported elevator route reconciliation is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_elevator_route_evidence_reconciliation(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_elevator_route_reconciliation.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_route_evidence_reconciliation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_route_evidence_reconciliation_gate"
                        ),
                        "same_evidence_ref_required": "false",
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "phone_safe_summary": {
                            "safe_copy": "Elevator route reconciliation confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_elevator_route_evidence_reconciliation(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["reconciliation_verdict"]["status"], "blocked_mismatch")
        self.assertEqual(env_summary["materials_status"]["status"], "blocked")
        self.assertIn("route completion evidence_ref mismatch", env_summary["mismatch_reasons"])
        self.assertEqual(missing_summary["reconciliation_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["reconciliation_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["reconciliation_verdict"]["status"], "unsafe_fields")
        self.assertFalse(unsafe_summary["same_evidence_ref_required"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_elevator_route_evidence_reconciliation_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_route_elevator_field_session_handoff_summary(self):
        with tempfile.TemporaryDirectory() as td:
            handoff_path = Path(td) / "route_elevator_field_session_handoff.json"
            handoff_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_elevator_field_session_handoff.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_route_elevator_field_session_handoff_gate"
                        ),
                        "evidence_ref": "evidence://route-elevator-handoff-1",
                        "same_evidence_ref_required": True,
                        "handoff_verdict": {
                            "status": "ready_for_field_session_handoff_not_proven",
                            "verdict": "ready_for_field_session_handoff_not_proven",
                            "reason": "all local summaries are bundled for field session collection",
                        },
                        "source_summaries": {
                            "pc_route_debug_console": {"status": "available"},
                            "route_completion_signal": {"status": "available"},
                            "elevator_route_reconciliation": {"status": "available"},
                        },
                        "field_session_manifest": {
                            "session_id": "field-session-1",
                            "materials_count": 9,
                        },
                        "required_materials_summary": [
                            "nav2_fixed_route_runtime_log.json",
                            "door_state.json",
                            "delivery_result.json",
                        ],
                        "operator_next_steps": [
                            "Collect field materials under the same safe evidence_ref."
                        ],
                        "robot_diagnostics_summary": {
                            "status": "metadata_only",
                            "reason": "safe robot diagnostics summary only",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Route/elevator field session handoff is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_elevator_operation"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                route_elevator_field_session_handoff_ref=str(handoff_path),
            )
            summary = payload["route_elevator_field_session_handoff"]
            summary_alias = payload["route_elevator_field_session_handoff_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertEqual(summary["schema"], "trashbot.route_elevator_field_session_handoff_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_route_elevator_field_session_handoff_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.route_elevator_field_session_handoff.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["handoff_verdict"]["status"], "ready_for_field_session_handoff_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://route-elevator-handoff-1")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertEqual(summary["source_summaries"]["pc_route_debug_console"]["status"], "available")
        self.assertEqual(summary["field_session_manifest"]["session_id"], "field-session-1")
        self.assertIn("door_state.json", summary["required_materials_summary"])
        self.assertIn("same safe evidence_ref", summary["operator_next_steps"][0])
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertIn("collect_dropoff_cancel_control", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertIn("real_hil_pass", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # 现场交接摘要只能帮助 operator 收集材料；这些开关防止 metadata 被误当成控制授权。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertNotIn(str(handoff_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_route_elevator_field_session_handoff_env_summary_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "route_elevator_field_session_handoff_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_elevator_field_session_handoff_summary.v1",
                        "source_schema": "trashbot.route_elevator_field_session_handoff.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_elevator_field_session_handoff_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_route_elevator_field_session_handoff_gate"
                        ),
                        "safe_evidence_ref": "evidence://route-elevator-handoff-2",
                        "same_evidence_ref_required": True,
                        "handoff_verdict": {
                            "status": "blocked_missing_inputs",
                            "verdict": "not_proven",
                            "reason": "route completion signal is missing",
                        },
                        "required_materials_summary": ["route_completion_signal.json"],
                        "operator_next_steps": ["Regenerate the route completion signal."],
                        "mobile_readonly_summary": {
                            "safe_copy": "Route/elevator field session handoff is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF")
            previous_summary = os.environ.get("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY")
            os.environ.pop("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF", None)
            os.environ["TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "route_elevator_field_session_handoff"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF", None)
                else:
                    os.environ["TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_route_elevator_handoff.json"
            missing_summary = summarize_route_elevator_field_session_handoff(str(missing_path))

            unsupported_path = Path(td) / "unsupported_route_elevator_handoff.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_route_evidence_reconciliation.v1",
                        "evidence_boundary": (
                            "software_proof_docker_elevator_route_evidence_reconciliation_gate"
                        ),
                        "safe_copy": "Unsupported handoff is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_route_elevator_field_session_handoff(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_route_elevator_handoff.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_elevator_field_session_handoff.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_elevator_field_session_handoff_gate"
                        ),
                        "same_evidence_ref_required": "false",
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Route/elevator handoff confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_route_elevator_field_session_handoff(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["handoff_verdict"]["status"], "blocked_missing_inputs")
        self.assertIn("route_completion_signal.json", env_summary["required_materials_summary"])
        self.assertEqual(missing_summary["handoff_verdict"]["status"], "missing")
        self.assertEqual(unsupported_summary["handoff_verdict"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["handoff_verdict"]["status"], "unsafe_fields")
        self.assertFalse(unsafe_summary["same_evidence_ref_required"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_route_elevator_field_session_handoff_gate", encoded)
        self.assertIn("delivery_success", missing_summary["not_proven"])
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_mobile_route_elevator_field_device_precheck_summary(self):
        with tempfile.TemporaryDirectory() as td:
            precheck_path = Path(td) / "mobile_route_elevator_field_device_precheck.json"
            precheck_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_route_elevator_field_device_precheck.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"
                        ),
                        "evidence_ref": "evidence://mobile-route-elevator-precheck-1",
                        "precheck_status": {
                            "status": "blocked_not_proven",
                            "verdict": "not_proven",
                            "reason": "waiting for real phone, route, elevator, and HIL evidence",
                        },
                        "device_precheck_summary": {"phone_surface": "metadata_only"},
                        "route_elevator_precheck_summary": {"route_elevator_status": "not_proven"},
                        "operator_next_steps": ["Collect real-device field evidence before enabling control."],
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Mobile route/elevator field device precheck is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_device_observed"],
                        "real_device_observed": False,
                        "pwa_install_prompt_observed": False,
                        "route_elevator_field_pass": False,
                        "dropoff_completion": False,
                        "cancel_completion": False,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "mobile_route_elevator_field_device_precheck": {
                        "delivery_success": True,
                    },
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                mobile_route_elevator_field_device_precheck_ref=str(precheck_path),
            )
            summary = payload["mobile_route_elevator_field_device_precheck"]
            summary_alias = payload["mobile_route_elevator_field_device_precheck_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("mobile_route_elevator_field_device_precheck", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.mobile_route_elevator_field_device_precheck_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_mobile_route_elevator_field_device_precheck_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.mobile_route_elevator_field_device_precheck.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["precheck_status"]["status"], "blocked_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://mobile-route-elevator-precheck-1")
        self.assertEqual(summary["device_precheck_summary"]["phone_surface"], "metadata_only")
        self.assertEqual(
            summary["route_elevator_precheck_summary"]["route_elevator_status"],
            "not_proven",
        )
        self.assertIn("real-device field evidence", summary["operator_next_steps"][0])
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("real_device_observed", summary["not_proven"])
        self.assertIn("pwa_install_prompt_observed", summary["not_proven"])
        self.assertIn("route_elevator_field_pass", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["real_device_observed"])
        self.assertFalse(summary["pwa_install_prompt_observed"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # 预检 metadata 只能进 diagnostics，不能触发 command、ACK、cursor、Nav2、HIL 或完成态。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(precheck_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_mobile_route_elevator_field_device_precheck_env_missing_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "mobile_route_elevator_field_device_precheck_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_route_elevator_field_device_precheck_summary.v1",
                        "source_schema": "trashbot.mobile_route_elevator_field_device_precheck.v1",
                        "evidence_boundary": (
                            "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"
                        ),
                        "safe_evidence_ref": "evidence://mobile-route-elevator-precheck-2",
                        "precheck_status": {
                            "status": "not_proven",
                            "verdict": "not_proven",
                            "reason": "real device field materials are missing",
                        },
                        "operator_next_steps": ["Run real-device route/elevator precheck later."],
                        "mobile_readonly_summary": {
                            "safe_copy": "Mobile route/elevator field device precheck is metadata-only; delivery_success=false.",
                        },
                        "real_device_observed": False,
                        "pwa_install_prompt_observed": False,
                        "route_elevator_field_pass": False,
                        "dropoff_completion": False,
                        "cancel_completion": False,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK")
            previous_summary = os.environ.get("TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY")
            os.environ.pop("TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK", None)
            os.environ["TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "mobile_route_elevator_field_device_precheck"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK", None)
                else:
                    os.environ["TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_precheck.json"
            missing_summary = summarize_mobile_route_elevator_field_device_precheck(str(missing_path))

            unsupported_path = Path(td) / "unsupported_precheck.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.route_elevator_field_session_handoff.v1",
                        "evidence_boundary": (
                            "software_proof_docker_route_elevator_field_session_handoff_gate"
                        ),
                        "safe_copy": "Unsupported precheck is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_mobile_route_elevator_field_device_precheck(str(unsupported_path))

            unsafe_path = Path(td) / "unsafe_precheck.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_route_elevator_field_device_precheck.v1",
                        "evidence_boundary": (
                            "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"
                        ),
                        "real_device_observed": True,
                        "pwa_install_prompt_observed": True,
                        "route_elevator_field_pass": True,
                        "dropoff_completion": True,
                        "cancel_completion": True,
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Mobile precheck confirms delivery success and ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_mobile_route_elevator_field_device_precheck(str(unsafe_path))
            encoded = json.dumps(
                [env_summary, missing_summary, unsupported_summary, unsafe_summary],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["precheck_status"]["status"], "not_proven")
        self.assertEqual(missing_summary["precheck_status"]["status"], "missing")
        self.assertEqual(unsupported_summary["precheck_status"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["precheck_status"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["real_device_observed"])
        self.assertFalse(env_summary["pwa_install_prompt_observed"])
        self.assertFalse(env_summary["route_elevator_field_pass"])
        self.assertFalse(env_summary["dropoff_completion"])
        self.assertFalse(env_summary["cancel_completion"])
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_mobile_route_elevator_field_device_precheck_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_mobile_field_material_intake_summary(self):
        with tempfile.TemporaryDirectory() as td:
            intake_path = Path(td) / "mobile_field_material_intake.json"
            intake_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_intake.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
                        "evidence_ref": "evidence://mobile-field-material-intake-1",
                        "same_evidence_ref_required": True,
                        "intake_status": {
                            "status": "blocked_not_proven",
                            "verdict": "not_proven",
                            "reason": "waiting for real phone, route/elevator, Nav2, and completion materials",
                        },
                        "device_observation_summary": {"phone_surface": "metadata_only"},
                        "route_elevator_materials_summary": {"route_elevator_status": "not_proven"},
                        "nav2_fixed_route_materials_summary": {"nav2_status": "not_proven"},
                        "task_record_materials_summary": {"task_record_status": "not_proven"},
                        "completion_signal_summary": {"completion_signal_status": "not_proven"},
                        "dropoff_cancel_materials_summary": {"terminal_status": "not_proven"},
                        "operator_next_steps": ["Collect same-evidence-ref field materials before control."],
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Mobile field material intake is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_route_elevator_field_pass"],
                        "real_device_observed": False,
                        "route_elevator_field_pass": False,
                        "nav2_fixed_route_run": False,
                        "task_record_completion": False,
                        "completion_signal_received": False,
                        "dropoff_completion": False,
                        "cancel_completion": False,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "mobile_field_material_intake": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                mobile_field_material_intake_ref=str(intake_path),
            )
            summary = payload["mobile_field_material_intake"]
            summary_alias = payload["mobile_field_material_intake_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("mobile_field_material_intake", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.mobile_field_material_intake_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_mobile_field_material_intake_gate")
        self.assertEqual(summary["source_schema"], "trashbot.mobile_field_material_intake.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["intake_status"]["status"], "blocked_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://mobile-field-material-intake-1")
        self.assertEqual(summary["device_observation_summary"]["phone_surface"], "metadata_only")
        self.assertEqual(summary["route_elevator_materials_summary"]["route_elevator_status"], "not_proven")
        self.assertEqual(summary["nav2_fixed_route_materials_summary"]["nav2_status"], "not_proven")
        self.assertEqual(summary["task_record_materials_summary"]["task_record_status"], "not_proven")
        self.assertEqual(summary["completion_signal_summary"]["completion_signal_status"], "not_proven")
        self.assertEqual(summary["dropoff_cancel_materials_summary"]["terminal_status"], "not_proven")
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertIn("dropoff_completion", summary["not_proven"])
        self.assertIn("cancel_completion", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["real_device_observed"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["task_record_completion"])
        self.assertFalse(summary["completion_signal_received"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # intake metadata 只能进 diagnostics，不能触发 command、ACK、control、cursor、Nav2、HIL 或完成态。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(intake_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_mobile_field_material_intake_env_bad_json_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "mobile_field_material_intake_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_intake_summary.v1",
                        "source_schema": "trashbot.mobile_field_material_intake.v1",
                        "evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
                        "source_evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
                        "safe_evidence_ref": "evidence://mobile-field-material-intake-2",
                        "same_evidence_ref_required": True,
                        "intake_status": {
                            "status": "not_proven",
                            "verdict": "not_proven",
                            "reason": "real field materials are missing",
                        },
                        "mobile_readonly_summary": {
                            "safe_copy": "Mobile field material intake is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE")
            previous_summary = os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY")
            os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE", None)
            os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "mobile_field_material_intake"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE", None)
                else:
                    os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY"] = previous_summary

            missing_path = Path(td) / "Bearer-secret-token" / "missing_intake.json"
            missing_summary = summarize_mobile_field_material_intake(str(missing_path))

            bad_json_path = Path(td) / "bad_intake.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_mobile_field_material_intake(str(bad_json_path))

            unsupported_path = Path(td) / "unsupported_intake.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_route_elevator_field_device_precheck.v1",
                        "evidence_boundary": (
                            "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"
                        ),
                        "safe_copy": "Unsupported intake is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_mobile_field_material_intake(str(unsupported_path))

            weak_ref_path = Path(td) / "weak_ref_intake.json"
            weak_ref_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_intake.v1",
                        "evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
                        "same_evidence_ref_required": "true",
                        "mobile_readonly_summary": {
                            "safe_copy": "Mobile field material intake is metadata-only; delivery_success=false.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            weak_ref_summary = summarize_mobile_field_material_intake(str(weak_ref_path))

            unsafe_path = Path(td) / "unsafe_intake.json"
            unsafe_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_intake.v1",
                        "evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
                        "same_evidence_ref_required": True,
                        "delivery_success": True,
                        "primary_actions_enabled": True,
                        "nav2_triggered": True,
                        "hil_pass": True,
                        "mobile_readonly_summary": {
                            "safe_copy": "Mobile intake confirms delivery success and terminal ACK posted.",
                        },
                    }
                ),
                encoding="utf-8",
            )
            unsafe_summary = summarize_mobile_field_material_intake(str(unsafe_path))
            encoded = json.dumps(
                [
                    env_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    weak_ref_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["intake_status"]["status"], "not_proven")
        self.assertEqual(missing_summary["intake_status"]["status"], "missing")
        self.assertEqual(bad_json_summary["intake_status"]["status"], "read_error")
        self.assertEqual(unsupported_summary["intake_status"]["status"], "unsupported_schema")
        self.assertEqual(weak_ref_summary["intake_status"]["status"], "unsafe_fields")
        self.assertEqual(unsafe_summary["intake_status"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_mobile_field_material_intake_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_mobile_field_material_review_decision_summary(self):
        with tempfile.TemporaryDirectory() as td:
            review_path = Path(td) / "mobile_field_material_review_decision.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_review_decision.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_mobile_field_material_review_decision_gate",
                        "evidence_ref": "evidence://mobile-field-material-review-1",
                        "same_evidence_ref_required": True,
                        "review_status": {
                            "status": "blocked_not_proven",
                            "verdict": "not_proven",
                            "reason": "waiting for same-evidence-ref route/elevator runtime materials",
                        },
                        "review_decision": "blocked_missing_route_elevator_field_materials",
                        "blocker_classification": "blocked_missing_route_elevator_field_materials",
                        "next_required_evidence": ["real phone/PWA observation", "Nav2 or fixed-route runtime log"],
                        "owner_handoff": "Autonomy",
                        "same_evidence_ref_status": "matched",
                        "operator_next_steps": ["Collect same-evidence-ref field materials before enabling control."],
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Mobile field material review decision is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_route_elevator_field_pass"],
                        "real_device_observed": False,
                        "route_elevator_field_pass": False,
                        "nav2_fixed_route_run": False,
                        "task_record_completion": False,
                        "completion_signal_received": False,
                        "dropoff_completion": False,
                        "cancel_completion": False,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "mobile_field_material_review_decision": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                mobile_field_material_review_decision_ref=str(review_path),
            )
            summary = payload["mobile_field_material_review_decision"]
            summary_alias = payload["mobile_field_material_review_decision_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("mobile_field_material_review_decision", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.mobile_field_material_review_decision_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_mobile_field_material_review_decision_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.mobile_field_material_review_decision.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["review_status"]["status"], "blocked_not_proven")
        self.assertEqual(summary["review_decision"], "blocked_missing_route_elevator_field_materials")
        self.assertEqual(summary["blocker_classification"], "blocked_missing_route_elevator_field_materials")
        self.assertEqual(summary["owner_handoff"], "Autonomy")
        self.assertEqual(summary["same_evidence_ref_status"], "matched")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://mobile-field-material-review-1")
        self.assertIn("Nav2 or fixed-route runtime log", summary["next_required_evidence"])
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertIn("dropoff_completion", summary["not_proven"])
        self.assertIn("cancel_completion", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertFalse(summary["real_device_observed"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["task_record_completion"])
        self.assertFalse(summary["completion_signal_received"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # review decision metadata 只能进 diagnostics，不能触发 command、ACK、cursor、Nav2、HIL 或完成态。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(review_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_mobile_field_material_review_decision_env_diagnostics_bad_json_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "mobile_field_material_review_decision_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_review_decision_summary.v1",
                        "source_schema": "trashbot.mobile_field_material_review_decision.v1",
                        "evidence_boundary": "software_proof_docker_mobile_field_material_review_decision_gate",
                        "source_evidence_boundary": (
                            "software_proof_docker_mobile_field_material_review_decision_gate"
                        ),
                        "safe_evidence_ref": "evidence://mobile-field-material-review-2",
                        "same_evidence_ref_required": True,
                        "review_status": {
                            "status": "not_proven",
                            "verdict": "not_proven",
                            "reason": "real field materials are missing",
                        },
                        "review_decision": "blocked_missing_real_phone_or_pwa_observation",
                        "blocker_classification": "blocked_missing_real_phone_or_pwa_observation",
                        "next_required_evidence": ["real phone/PWA observation"],
                        "owner_handoff": "Full-stack",
                        "mobile_readonly_summary": {
                            "safe_copy": "Mobile field material review decision is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION")
            previous_summary = os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY")
            os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION", None)
            os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "mobile_field_material_review_decision"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION", None)
                else:
                    os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "mobile_field_material_review_decision_summary": {
                            "schema": "trashbot.mobile_field_material_review_decision_summary.v1",
                            "source_schema": "trashbot.mobile_field_material_review_decision.v1",
                            "evidence_boundary": (
                                "software_proof_docker_mobile_field_material_review_decision_gate"
                            ),
                            "source_evidence_boundary": (
                                "software_proof_docker_mobile_field_material_review_decision_gate"
                            ),
                            "same_evidence_ref_required": True,
                            "review_decision": "ready_for_owner_handoff_not_proven",
                            "mobile_readonly_summary": {
                                "safe_copy": (
                                    "Mobile field material review decision is metadata-only; "
                                    "delivery_success=false."
                                ),
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["mobile_field_material_review_decision"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_review.json"
            missing_summary = summarize_mobile_field_material_review_decision(str(missing_path))

            bad_json_path = Path(td) / "bad_review.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_mobile_field_material_review_decision(str(bad_json_path))

            unsupported_path = Path(td) / "unsupported_review.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_intake.v1",
                        "evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
                        "safe_copy": "Unsupported review decision is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_mobile_field_material_review_decision(str(unsupported_path))

            weak_ref_summary = summarize_mobile_field_material_review_decision(
                {
                    "schema": "trashbot.mobile_field_material_review_decision.v1",
                    "evidence_boundary": "software_proof_docker_mobile_field_material_review_decision_gate",
                    "same_evidence_ref_required": "true",
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile field material review decision is metadata-only; delivery_success=false.",
                    },
                }
            )

            unsafe_summary = summarize_mobile_field_material_review_decision(
                {
                    "schema": "trashbot.mobile_field_material_review_decision.v1",
                    "evidence_boundary": "software_proof_docker_mobile_field_material_review_decision_gate",
                    "same_evidence_ref_required": True,
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "nav2_triggered": True,
                    "hil_pass": True,
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile review decision confirms delivery success and terminal ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    weak_ref_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )
        self.assertEqual(env_summary["review_status"]["status"], "not_proven")
        self.assertEqual(diagnostics_summary["review_decision"], "ready_for_owner_handoff_not_proven")
        self.assertEqual(missing_summary["review_status"]["status"], "missing")
        self.assertEqual(bad_json_summary["review_status"]["status"], "read_error")
        self.assertEqual(unsupported_summary["review_status"]["status"], "unsupported_schema")
        self.assertEqual(weak_ref_summary["review_status"]["status"], "unsafe_fields")
        self.assertEqual(unsafe_summary["review_status"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_mobile_field_material_review_decision_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_mobile_field_material_retest_request_summary(self):
        with tempfile.TemporaryDirectory() as td:
            request_path = Path(td) / "mobile_field_material_retest_request.json"
            request_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_retest_request.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_mobile_field_material_retest_request_gate"
                        ),
                        "evidence_ref": "evidence://mobile-field-material-retest-1",
                        "same_evidence_ref_required": True,
                        "retest_request_status": {
                            "status": "blocked_not_proven",
                            "verdict": "not_proven",
                            "reason": "waiting for same-evidence-ref retest materials",
                        },
                        "source_review_decision": "blocked_missing_route_elevator_field_materials",
                        "blockers": ["blocked_missing_route_elevator_field_materials"],
                        "next_required_evidence": [
                            "real phone/PWA observation",
                            "Nav2 or fixed-route runtime log",
                        ],
                        "retest_request": {
                            "status": "requested_not_proven",
                            "owner": "Autonomy",
                            "next_action": "Collect route/elevator material checklist.",
                        },
                        "route_elevator_material_checklist": [
                            "door state material",
                            "target floor confirmation",
                            "human assistance note",
                            "Nav2 or fixed-route runtime log",
                            "task record",
                            "completion signal",
                            "dropoff/cancel completion material",
                            "mobile/diagnostics safe summary",
                        ],
                        "owner_handoff": "Autonomy",
                        "same_evidence_ref_status": "required",
                        "operator_next_steps": ["Retest only after collecting the same evidence_ref materials."],
                        "mobile_readonly_summary": {
                            "safe_copy": (
                                "Mobile field material retest request is metadata-only; "
                                "delivery_success=false and not delivery success."
                            ),
                        },
                        "not_proven": ["delivery_success", "real_route_elevator_field_pass"],
                        "real_device_observed": False,
                        "route_elevator_field_pass": False,
                        "nav2_fixed_route_run": False,
                        "task_record_completion": False,
                        "completion_signal_received": False,
                        "dropoff_completion": False,
                        "cancel_completion": False,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "mobile_field_material_retest_request": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                mobile_field_material_retest_request_ref=str(request_path),
            )
            summary = payload["mobile_field_material_retest_request"]
            summary_alias = payload["mobile_field_material_retest_request_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("mobile_field_material_retest_request", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.mobile_field_material_retest_request_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_mobile_field_material_retest_request_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.mobile_field_material_retest_request.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["retest_request_status"]["status"], "blocked_not_proven")
        self.assertEqual(summary["source_review_decision"], "blocked_missing_route_elevator_field_materials")
        self.assertIn("blocked_missing_route_elevator_field_materials", summary["blockers"])
        self.assertEqual(summary["owner_handoff"], "Autonomy")
        self.assertEqual(summary["same_evidence_ref_status"], "required")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://mobile-field-material-retest-1")
        self.assertIn("Nav2 or fixed-route runtime log", summary["next_required_evidence"])
        self.assertEqual(summary["retest_request"]["status"], "requested_not_proven")
        self.assertIn("target floor confirmation", summary["route_elevator_material_checklist"])
        self.assertIn("delivery_success=false", summary["mobile_readonly_summary"]["safe_phone_copy"])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", summary["not_proven"])
        self.assertIn("dropoff_completion", summary["not_proven"])
        self.assertIn("cancel_completion", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["same_evidence_ref_required"])
        self.assertFalse(summary["real_device_observed"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["task_record_completion"])
        self.assertFalse(summary["completion_signal_received"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # retest request metadata 只能进 diagnostics，不能触发 command、ACK、cursor、Nav2、HIL 或完成态。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertNotIn(str(request_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_mobile_field_material_retest_request_env_diagnostics_bad_json_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "mobile_field_material_retest_request_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_retest_request_summary.v1",
                        "source_schema": "trashbot.mobile_field_material_retest_request.v1",
                        "evidence_boundary": (
                            "software_proof_docker_mobile_field_material_retest_request_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_mobile_field_material_retest_request_gate"
                        ),
                        "safe_evidence_ref": "evidence://mobile-field-material-retest-2",
                        "same_evidence_ref_required": True,
                        "retest_request_status": {
                            "status": "not_proven",
                            "verdict": "not_proven",
                            "reason": "real retest materials are missing",
                        },
                        "source_review_decision": "blocked_missing_real_phone_or_pwa_observation",
                        "blockers": ["blocked_missing_real_phone_or_pwa_observation"],
                        "next_required_evidence": ["real phone/PWA observation"],
                        "retest_request": {"status": "requested_not_proven"},
                        "route_elevator_material_checklist": ["door state material"],
                        "owner_handoff": "Full-stack",
                        "mobile_readonly_summary": {
                            "safe_copy": "Mobile field material retest request is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST")
            previous_summary = os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY")
            os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST", None)
            os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "mobile_field_material_retest_request"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST", None)
                else:
                    os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "mobile_field_material_retest_request_summary": {
                            "schema": "trashbot.mobile_field_material_retest_request_summary.v1",
                            "source_schema": "trashbot.mobile_field_material_retest_request.v1",
                            "evidence_boundary": (
                                "software_proof_docker_mobile_field_material_retest_request_gate"
                            ),
                            "source_evidence_boundary": (
                                "software_proof_docker_mobile_field_material_retest_request_gate"
                            ),
                            "same_evidence_ref_required": True,
                            "source_review_decision": "ready_for_retest_request_not_proven",
                            "retest_request": {"status": "requested_not_proven"},
                            "mobile_readonly_summary": {
                                "safe_copy": (
                                    "Mobile field material retest request is metadata-only; "
                                    "delivery_success=false."
                                ),
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["mobile_field_material_retest_request"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_retest_request.json"
            missing_summary = summarize_mobile_field_material_retest_request(str(missing_path))

            bad_json_path = Path(td) / "bad_retest_request.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_mobile_field_material_retest_request(str(bad_json_path))

            unsupported_path = Path(td) / "unsupported_retest_request.json"
            unsupported_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.mobile_field_material_review_decision.v1",
                        "evidence_boundary": "software_proof_docker_mobile_field_material_review_decision_gate",
                        "safe_copy": "Unsupported retest request is metadata-only; delivery_success=false.",
                    }
                ),
                encoding="utf-8",
            )
            unsupported_summary = summarize_mobile_field_material_retest_request(str(unsupported_path))

            weak_ref_summary = summarize_mobile_field_material_retest_request(
                {
                    "schema": "trashbot.mobile_field_material_retest_request.v1",
                    "evidence_boundary": "software_proof_docker_mobile_field_material_retest_request_gate",
                    "same_evidence_ref_required": "true",
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile field material retest request is metadata-only; delivery_success=false.",
                    },
                }
            )

            unsafe_summary = summarize_mobile_field_material_retest_request(
                {
                    "schema": "trashbot.mobile_field_material_retest_request.v1",
                    "evidence_boundary": "software_proof_docker_mobile_field_material_retest_request_gate",
                    "same_evidence_ref_required": True,
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "nav2_triggered": True,
                    "hil_pass": True,
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile retest request confirms delivery success and terminal ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    weak_ref_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["retest_request_status"]["status"], "not_proven")
        self.assertEqual(diagnostics_summary["source_review_decision"], "ready_for_retest_request_not_proven")
        self.assertEqual(missing_summary["retest_request_status"]["status"], "missing")
        self.assertEqual(bad_json_summary["retest_request_status"]["status"], "read_error")
        self.assertEqual(unsupported_summary["retest_request_status"]["status"], "unsupported_schema")
        self.assertEqual(weak_ref_summary["retest_request_status"]["status"], "unsafe_fields")
        self.assertEqual(unsafe_summary["retest_request_status"]["status"], "unsafe_fields")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_mobile_field_material_retest_request_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_diagnostics_payload_includes_hardware_baseline_review_summary(self):
        with tempfile.TemporaryDirectory() as td:
            review_path = Path(td) / "hardware_baseline_review.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_baseline_review_gate.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                        "evidence_ref": "evidence://hardware-baseline-review-1",
                        "review_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "waiting for reviewed hardware baseline materials",
                        },
                        "blockers": ["hardware_material_pending"],
                        "next_required_evidence": ["vendor-backed hardware baseline packet"],
                        "review_summary": {
                            "status": "hardware_material_pending",
                            "owner": "Hardware",
                        },
                        "operator_next_steps": ["Attach reviewed baseline materials before any robot action."],
                        "robot_diagnostics_summary": {
                            "safe_copy": (
                                "Hardware baseline review is metadata-only; software_proof only, "
                                "delivery_success=false and primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["hardware_material_pending", "delivery_success"],
                        "real_hardware_observed": False,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "hardware_baseline_review": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_baseline_review_ref=str(review_path),
            )
            summary = payload["hardware_baseline_review"]
            summary_alias = payload["hardware_baseline_review_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("hardware_baseline_review", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.hardware_baseline_review_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_hardware_baseline_review_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.hardware_baseline_review_gate.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["review_status"]["status"], "hardware_material_pending")
        self.assertEqual(summary["review_status"]["verdict"], "not_proven")
        self.assertEqual(summary["review_status"]["evidence_source"], "software_proof")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("hardware_material_pending", summary["blockers"])
        self.assertIn("vendor-backed hardware baseline packet", summary["next_required_evidence"])
        self.assertEqual(summary["review_summary"]["owner"], "Hardware")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://hardware-baseline-review-1")
        self.assertIn("software_proof", summary["not_proven"])
        self.assertIn("hardware_material_pending", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["hardware_material_pending"])
        self.assertFalse(summary["real_hardware_observed"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # baseline review 是 diagnostics consumer，不能触发控制、ACK、Nav2/fixed-route、HIL 或硬件动作。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertIn("delivery_success=false", summary["robot_diagnostics_summary"]["safe_phone_copy"])
        self.assertNotIn(str(review_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_hardware_baseline_review_env_diagnostics_bad_json_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "hardware_baseline_review_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_baseline_review_summary.v1",
                        "source_schema": "trashbot.hardware_baseline_review_gate.v1",
                        "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                        "source_evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                        "safe_evidence_ref": "evidence://hardware-baseline-review-2",
                        "review_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "real hardware material is pending",
                        },
                        "blockers": ["hardware_material_pending"],
                        "next_required_evidence": ["reviewed vendor-backed hardware packet"],
                        "review_summary": {"status": "hardware_material_pending"},
                        "robot_diagnostics_summary": {
                            "safe_copy": "Hardware baseline review is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_HARDWARE_BASELINE_REVIEW")
            previous_summary = os.environ.get("TRASHBOT_HARDWARE_BASELINE_REVIEW_SUMMARY")
            os.environ.pop("TRASHBOT_HARDWARE_BASELINE_REVIEW", None)
            os.environ["TRASHBOT_HARDWARE_BASELINE_REVIEW_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "hardware_baseline_review"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_HARDWARE_BASELINE_REVIEW", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_BASELINE_REVIEW"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_HARDWARE_BASELINE_REVIEW_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_BASELINE_REVIEW_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "hardware_baseline_review_summary": {
                            "schema": "trashbot.hardware_baseline_review_summary.v1",
                            "source_schema": "trashbot.hardware_baseline_review_gate.v1",
                            "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                            "source_evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                            "review_status": {
                                "status": "hardware_material_pending",
                                "verdict": "not_proven",
                                "evidence_source": "software_proof",
                            },
                            "robot_diagnostics_summary": {
                                "safe_copy": "Hardware baseline review is metadata-only; delivery_success=false.",
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["hardware_baseline_review"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_hardware_baseline_review.json"
            missing_summary = summarize_hardware_baseline_review(str(missing_path))

            bad_json_path = Path(td) / "bad_hardware_baseline_review.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_hardware_baseline_review(str(bad_json_path))

            unsupported_summary = summarize_hardware_baseline_review(
                {
                    "schema": "trashbot.hardware_diagnostics_proof.v1",
                    "evidence_boundary": "software_proof_docker_hardware_diagnostics_proof_gate",
                    "safe_copy": "Unsupported hardware baseline review is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_hardware_baseline_review(
                {
                    "schema": "trashbot.hardware_baseline_review_gate.v1",
                    "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "nav2_triggered": True,
                    "hil_pass": True,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware baseline review confirms delivery success and ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["review_status"]["status"], "hardware_material_pending")
        self.assertEqual(diagnostics_summary["review_status"]["status"], "hardware_material_pending")
        self.assertEqual(missing_summary["review_status"]["status"], "missing")
        self.assertEqual(bad_json_summary["review_status"]["status"], "read_error")
        self.assertEqual(unsupported_summary["review_status"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["review_status"]["status"], "unsafe_fields")
        self.assertEqual(env_summary["review_status"]["evidence_source"], "software_proof")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_hardware_baseline_review_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("hardware_material_pending", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)

    def test_hardware_baseline_review_accepts_pc_summary_output_schema(self):
        # PC --summary-output 直接交接 summary，不再额外包 source_schema/source_evidence_boundary。
        pc_summary = {
            "schema": "trashbot.hardware_baseline_review_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
            "status": "hardware_baseline_review_not_proven",
            "hardware_material_status": "hardware_material_pending",
            "source_boundary_doc": "docs/product/production_hardware_boundary.md",
            "sensor_responsibility_summary": [
                {
                    "sensor": "2D LiDAR",
                    "material_status": "hardware_material_pending",
                    "field_status": "not_proven",
                    "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                }
            ],
            "missing_required_phrases": [],
            "not_proven": ["real_lidar_field_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

        summary = summarize_hardware_baseline_review(pc_summary)

        # Robot diagnostics 必须接收该 summary schema，同时保持软件证明和 not_proven 边界。
        self.assertEqual(summary["schema"], "trashbot.hardware_baseline_review_summary.v1")
        self.assertEqual(summary["source_schema"], "trashbot.hardware_baseline_review_summary.v1")
        self.assertEqual(
            summary["source_evidence_boundary"],
            "software_proof_docker_hardware_baseline_review_gate",
        )
        self.assertEqual(
            summary["review_status"]["status"],
            "hardware_baseline_review_not_proven",
        )
        self.assertNotEqual(summary["review_status"]["status"], "unsupported_schema")
        self.assertEqual(summary["review_status"]["evidence_source"], "software_proof")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("delivery_success", summary["not_proven"])

    def test_diagnostics_payload_includes_hardware_baseline_source_alignment_summary(self):
        with tempfile.TemporaryDirectory() as td:
            alignment_path = Path(td) / "hardware_baseline_source_alignment.json"
            alignment_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_baseline_source_alignment.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_hardware_baseline_source_alignment_gate",
                        "evidence_ref": "evidence://hardware-baseline-source-alignment-1",
                        "overall_status": "hardware_baseline_source_aligned_not_proven",
                        "hardware_baseline_source_alignment": "hardware_baseline_source_aligned_not_proven",
                        "blockers": ["hardware_material_pending"],
                        "baseline_source_summary": {
                            "status": "hardware_material_pending",
                            "owner": "Hardware",
                        },
                        "default_hardware_set_summary": {
                            "source_section": "Default Hardware Set",
                            "items": ["WAVE ROVER mobile chassis.", "Orange Pi Zero 3 upper computer."],
                            "default_lidar_or_tof_included": False,
                            "status": "loaded_not_proven",
                        },
                        "target_sensor_baseline_summary": {
                            "target_combo": "monocular camera + one 2D LiDAR + ToF safety ring",
                            "hardware_material_status": "hardware_material_pending",
                            "evidence_status": "not_proven",
                            "status": "loaded_not_proven",
                        },
                        "vendor_source_boundary": {
                            "source_docs": {
                                "boundary_doc": "docs/product/production_hardware_boundary.md",
                                "vendor_index": "docs/vendor/VENDOR_INDEX.md",
                            },
                            "lidar_tof_source_boundary": "hardware_material_pending_not_proven",
                        },
                        "missing_alignment_items": [],
                        "source_inventory_summary": [
                            {"source": "vendor_index", "status": "aligned"}
                        ],
                        "unresolved_sources": ["real wiring proof"],
                        "owner_handoff": ["Hardware owns source and baseline verification."],
                        "next_required_evidence": ["real hardware baseline proof"],
                        "operator_next_steps": ["Keep robot actions disabled until Hardware review."],
                        "review_summary": {
                            "schema": "trashbot.hardware_baseline_source_alignment_summary.v1",
                            "source_schema": "trashbot.hardware_baseline_source_alignment.v1",
                            "evidence_boundary": "software_proof_docker_hardware_baseline_source_alignment_gate",
                            "status": "hardware_baseline_source_aligned_not_proven",
                            "hardware_baseline_source_alignment": "hardware_baseline_source_aligned_not_proven",
                            "safe_copy": (
                                "Hardware baseline source alignment is metadata-only; software_proof only, "
                                "delivery_success=false and primary_actions_enabled=false."
                            ),
                            "missing_alignment_items": [],
                        },
                        "not_proven": ["hardware_material_pending", "vendor_source_alignment_review"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "hardware_baseline_source_alignment": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_baseline_source_alignment_ref=str(alignment_path),
            )
            summary = payload["hardware_baseline_source_alignment"]
            summary_alias = payload["hardware_baseline_source_alignment_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("hardware_baseline_source_alignment", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.hardware_baseline_source_alignment_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_hardware_baseline_source_alignment_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.hardware_baseline_source_alignment.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(
            summary["source_contract"]["evidence_boundary"],
            "software_proof_docker_hardware_baseline_source_alignment_gate",
        )
        self.assertEqual(
            summary["alignment_status"]["status"],
            "hardware_baseline_source_aligned_not_proven",
        )
        self.assertEqual(summary["alignment_status"]["verdict"], "not_proven")
        self.assertEqual(summary["alignment_status"]["evidence_source"], "software_proof")
        self.assertEqual(
            summary["source_alignment_status"],
            "hardware_baseline_source_aligned_not_proven",
        )
        self.assertEqual(summary["baseline_source_summary"]["owner"], "Hardware")
        self.assertEqual(
            summary["default_hardware_set_summary"]["status"],
            "loaded_not_proven",
        )
        self.assertFalse(
            summary["default_hardware_set_summary"]["default_lidar_or_tof_included"]
        )
        self.assertEqual(
            summary["target_sensor_baseline_summary"]["target_combo"],
            "monocular camera + one 2D LiDAR + ToF safety ring",
        )
        self.assertEqual(
            summary["vendor_source_boundary"]["lidar_tof_source_boundary"],
            "hardware_material_pending_not_proven",
        )
        self.assertEqual(summary["missing_alignment_items"], [])
        self.assertEqual(summary["source_inventory_summary"][0]["source"], "vendor_index")
        self.assertIn("real wiring proof", summary["unresolved_sources"])
        self.assertIn("Hardware owns source and baseline verification.", summary["owner_handoff"])
        self.assertIn("real hardware baseline proof", summary["next_required_evidence"])
        self.assertEqual(summary["safe_evidence_ref"], "evidence://hardware-baseline-source-alignment-1")
        self.assertIn("software_proof", summary["not_proven"])
        self.assertIn("vendor_source_alignment_review", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["hardware_material_pending"])
        self.assertFalse(summary["source_alignment_reviewed"])
        self.assertFalse(summary["sensor_procurement_completed"])
        self.assertFalse(summary["sensor_installed_on_robot"])
        self.assertFalse(summary["sensor_wiring_verified"])
        self.assertFalse(summary["sensor_power_budget_verified"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # source alignment 是 metadata-only consumer，不能触发控制、ACK、cursor、Nav2、硬件或 HIL。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertIn("delivery_success=false", summary["robot_diagnostics_summary"]["safe_phone_copy"])
        self.assertNotIn(str(alignment_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_hardware_baseline_source_alignment_env_nested_bad_json_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "hardware_baseline_source_alignment_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_baseline_source_alignment_summary.v1",
                        "source_schema": "trashbot.hardware_baseline_source_alignment.v1",
                        "evidence_boundary": "software_proof_docker_hardware_baseline_source_alignment_gate",
                        "status": "hardware_baseline_source_aligned_not_proven",
                        "hardware_baseline_source_alignment": "hardware_baseline_source_aligned_not_proven",
                        "default_hardware_set_summary": {
                            "status": "loaded_not_proven",
                            "items": ["WAVE ROVER mobile chassis."],
                            "default_lidar_or_tof_included": False,
                        },
                        "target_sensor_baseline_summary": {
                            "status": "loaded_not_proven",
                            "target_combo": "monocular camera + one 2D LiDAR + ToF safety ring",
                        },
                        "vendor_source_boundary": {
                            "lidar_tof_source_boundary": "hardware_material_pending_not_proven",
                            "source_docs": {"vendor_index": "docs/vendor/VENDOR_INDEX.md"},
                        },
                        "missing_alignment_items": [],
                        "alignment_status": {
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                        },
                        "robot_diagnostics_summary": {
                            "safe_copy": "Hardware baseline source alignment is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT")
            previous_summary = os.environ.get("TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY")
            os.environ.pop("TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT", None)
            os.environ["TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "hardware_baseline_source_alignment"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "hardware_baseline_source_alignment_summary": {
                            "schema": "trashbot.hardware_baseline_source_alignment_summary.v1",
                            "source_schema": "trashbot.hardware_baseline_source_alignment.v1",
                            "evidence_boundary": "software_proof_docker_hardware_baseline_source_alignment_gate",
                            "status": "hardware_baseline_source_aligned_not_proven",
                            "hardware_baseline_source_alignment": "hardware_baseline_source_aligned_not_proven",
                            "default_hardware_set_summary": {
                                "status": "loaded_not_proven",
                                "items": ["WAVE ROVER mobile chassis."],
                                "default_lidar_or_tof_included": False,
                            },
                            "target_sensor_baseline_summary": {
                                "status": "loaded_not_proven",
                                "target_combo": "monocular camera + one 2D LiDAR + ToF safety ring",
                            },
                            "vendor_source_boundary": {
                                "lidar_tof_source_boundary": "hardware_material_pending_not_proven",
                                "source_docs": {"vendor_index": "docs/vendor/VENDOR_INDEX.md"},
                            },
                            "missing_alignment_items": [],
                            "alignment_status": {
                                "verdict": "not_proven",
                                "evidence_source": "software_proof",
                            },
                            "robot_diagnostics_summary": {
                                "safe_copy": "Hardware baseline source alignment is metadata-only; delivery_success=false.",
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["hardware_baseline_source_alignment"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_hardware_baseline_source_alignment.json"
            missing_summary = summarize_hardware_baseline_source_alignment(str(missing_path))

            bad_json_path = Path(td) / "bad_hardware_baseline_source_alignment.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_hardware_baseline_source_alignment(str(bad_json_path))

            unsupported_summary = summarize_hardware_baseline_source_alignment(
                {
                    "schema": "trashbot.hardware_baseline_review_gate.v1",
                    "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                    "safe_copy": "Unsupported source alignment is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_hardware_baseline_source_alignment(
                {
                    "schema": "trashbot.hardware_baseline_source_alignment.v1",
                    "evidence_boundary": "software_proof_docker_hardware_baseline_source_alignment_gate",
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "raw_ack_payload": {"ack": "posted"},
                    "serial_device": "/dev/ttyUSB0",
                    "hardware_detail": "WAVE ROVER UART raw wiring",
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware baseline source alignment confirms delivery success and ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )
            unsafe_encoded = json.dumps(unsafe_summary, ensure_ascii=False)

        self.assertEqual(
            env_summary["alignment_status"]["status"],
            "hardware_baseline_source_aligned_not_proven",
        )
        self.assertEqual(
            diagnostics_summary["alignment_status"]["status"],
            "hardware_baseline_source_aligned_not_proven",
        )
        self.assertEqual(env_summary["source_schema"], "trashbot.hardware_baseline_source_alignment.v1")
        self.assertEqual(
            env_summary["source_evidence_boundary"],
            "software_proof_docker_hardware_baseline_source_alignment_gate",
        )
        self.assertEqual(
            env_summary["vendor_source_boundary"]["lidar_tof_source_boundary"],
            "hardware_material_pending_not_proven",
        )
        self.assertEqual(env_summary["missing_alignment_items"], [])
        self.assertEqual(
            missing_summary["alignment_status"]["status"],
            "blocked_missing_hardware_baseline_source_alignment",
        )
        self.assertEqual(
            bad_json_summary["alignment_status"]["status"],
            "blocked_missing_hardware_baseline_source_alignment",
        )
        self.assertEqual(
            unsupported_summary["alignment_status"]["status"],
            "blocked_missing_hardware_baseline_source_alignment",
        )
        self.assertEqual(
            unsafe_summary["alignment_status"]["status"],
            "blocked_missing_hardware_baseline_source_alignment",
        )
        self.assertEqual(env_summary["alignment_status"]["evidence_source"], "software_proof")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("blocked_missing_hardware_baseline_source_alignment", encoded)
        self.assertIn("software_proof_docker_hardware_baseline_source_alignment_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("hardware_material_pending", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("raw_ack_payload", encoded)
        self.assertNotIn("WAVE ROVER", unsafe_encoded)

    def test_diagnostics_payload_includes_hardware_sensor_procurement_intake_summary(self):
        with tempfile.TemporaryDirectory() as td:
            intake_path = Path(td) / "hardware_sensor_procurement_intake.json"
            intake_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_intake_gate.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                        "evidence_ref": "evidence://hardware-sensor-procurement-1",
                        "intake_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "waiting for sensor procurement material review",
                        },
                        "blockers": ["hardware_material_pending"],
                        "next_required_evidence": ["reviewed sensor procurement packet"],
                        "procurement_summary": {
                            "status": "hardware_material_pending",
                            "owner": "Hardware",
                        },
                        "sensor_responsibility_summary": [
                            {
                                "sensor": "2D LiDAR",
                                "material_status": "hardware_material_pending",
                                "field_status": "not_proven",
                                "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                                "vendor_source_doc": "docs/vendor/full-private-source.md",
                            }
                        ],
                        "operator_next_steps": ["Attach reviewed sensor procurement packet."],
                        "robot_diagnostics_summary": {
                            "safe_copy": (
                                "Hardware sensor procurement intake is metadata-only; software_proof only, "
                                "delivery_success=false and primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["hardware_material_pending", "delivery_success"],
                        "real_hardware_observed": False,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "hardware_sensor_procurement_intake": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_sensor_procurement_intake_ref=str(intake_path),
            )
            summary = payload["hardware_sensor_procurement_intake"]
            summary_alias = payload["hardware_sensor_procurement_intake_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("hardware_sensor_procurement_intake", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_intake_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_hardware_sensor_procurement_intake_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.hardware_sensor_procurement_intake_gate.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["intake_status"]["status"], "hardware_material_pending")
        self.assertEqual(summary["intake_status"]["verdict"], "not_proven")
        self.assertEqual(summary["intake_status"]["evidence_source"], "software_proof")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("hardware_material_pending", summary["blockers"])
        self.assertIn("reviewed sensor procurement packet", summary["next_required_evidence"])
        self.assertEqual(summary["procurement_summary"]["owner"], "Hardware")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://hardware-sensor-procurement-1")
        self.assertEqual(summary["sensor_responsibility_summary"][0]["sensor"], "2D LiDAR")
        self.assertNotIn("vendor_source_doc", encoded)
        self.assertNotIn("docs/vendor/full-private-source.md", encoded)
        self.assertIn("software_proof", summary["not_proven"])
        self.assertIn("hardware_material_pending", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["hardware_material_pending"])
        self.assertFalse(summary["real_hardware_observed"])
        self.assertFalse(summary["sensor_procurement_completed"])
        self.assertFalse(summary["sensor_installed_on_robot"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # procurement intake 是 diagnostics metadata-only consumer，不能触发控制、ACK、cursor、Nav2、HIL 或完成语义。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertIn("delivery_success=false", summary["robot_diagnostics_summary"]["safe_phone_copy"])
        self.assertNotIn(str(intake_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_hardware_sensor_procurement_intake_env_diagnostics_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "hardware_sensor_procurement_intake_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_intake_summary.v1",
                        "source_schema": "trashbot.hardware_sensor_procurement_intake_gate.v1",
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                        "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                        "safe_evidence_ref": "evidence://hardware-sensor-procurement-2",
                        "intake_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "real sensor procurement evidence is pending",
                        },
                        "blockers": ["hardware_material_pending"],
                        "robot_diagnostics_summary": {
                            "safe_copy": "Hardware sensor procurement intake is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE")
            previous_summary = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY")
            os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE", None)
            os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "hardware_sensor_procurement_intake"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "hardware_sensor_procurement_intake_summary": {
                            "schema": "trashbot.hardware_sensor_procurement_intake_summary.v1",
                            "source_schema": "trashbot.hardware_sensor_procurement_intake_gate.v1",
                            "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                            "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                            "intake_status": {
                                "status": "hardware_material_pending",
                                "verdict": "not_proven",
                                "evidence_source": "software_proof",
                            },
                            "robot_diagnostics_summary": {
                                "safe_copy": "Hardware sensor procurement intake is metadata-only; delivery_success=false.",
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["hardware_sensor_procurement_intake"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_hardware_sensor_procurement_intake.json"
            missing_summary = summarize_hardware_sensor_procurement_intake(str(missing_path))

            bad_json_path = Path(td) / "bad_hardware_sensor_procurement_intake.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_hardware_sensor_procurement_intake(str(bad_json_path))

            unsupported_summary = summarize_hardware_sensor_procurement_intake(
                {
                    "schema": "trashbot.hardware_baseline_review_gate.v1",
                    "evidence_boundary": "software_proof_docker_hardware_baseline_review_gate",
                    "safe_copy": "Unsupported procurement intake is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_hardware_sensor_procurement_intake(
                {
                    "schema": "trashbot.hardware_sensor_procurement_intake_gate.v1",
                    "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "raw_ros_topic": "/trashbot/debug/raw",
                    "serial_device": "/dev/ttyUSB0",
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware procurement confirms delivery success and ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["intake_status"]["status"], "hardware_material_pending")
        self.assertEqual(diagnostics_summary["intake_status"]["status"], "hardware_material_pending")
        self.assertEqual(missing_summary["intake_status"]["status"], "missing")
        self.assertEqual(bad_json_summary["intake_status"]["status"], "read_error")
        self.assertEqual(unsupported_summary["intake_status"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["intake_status"]["status"], "unsafe_fields")
        self.assertEqual(env_summary["intake_status"]["evidence_source"], "software_proof")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("software_proof_docker_hardware_sensor_procurement_intake_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("hardware_material_pending", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("/trashbot/debug/raw", encoded)

    def test_diagnostics_payload_includes_hardware_sensor_procurement_review_decision_summary(self):
        with tempfile.TemporaryDirectory() as td:
            review_path = Path(td) / "hardware_sensor_procurement_review_decision.json"
            review_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_review_decision.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
                        "evidence_ref": "evidence://hardware-sensor-procurement-review-1",
                        "review_decision_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "approved for next hardware owner handoff, not procurement completion",
                        },
                        "blockers": ["hardware_material_pending"],
                        "next_required_evidence": ["purchase order and installed sensor proof"],
                        "review_decision_summary": {
                            "status": "hardware_material_pending",
                            "decision": "approve_retest_after_procurement",
                            "owner": "Hardware",
                        },
                        "owner_handoff": ["Hardware owns procurement execution."],
                        "rerun_commands": ["python3 pc-tools/hardware_sensor_procurement_review_decision.py --summary-output out.json"],
                        "operator_next_steps": ["Wait for real procurement and installation evidence."],
                        "robot_diagnostics_summary": {
                            "safe_copy": (
                                "Hardware sensor procurement review decision is metadata-only; software_proof only, "
                                "delivery_success=false and primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["hardware_material_pending", "delivery_success"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "hardware_sensor_procurement_review_decision": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_sensor_procurement_review_decision_ref=str(review_path),
            )
            summary = payload["hardware_sensor_procurement_review_decision"]
            summary_alias = payload["hardware_sensor_procurement_review_decision_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("hardware_sensor_procurement_review_decision", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_review_decision_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.hardware_sensor_procurement_review_decision.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["review_decision_status"]["status"], "hardware_material_pending")
        self.assertEqual(summary["review_decision_status"]["verdict"], "not_proven")
        self.assertEqual(summary["review_decision_status"]["evidence_source"], "software_proof")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("hardware_material_pending", summary["blockers"])
        self.assertIn("purchase order and installed sensor proof", summary["next_required_evidence"])
        self.assertEqual(summary["review_decision_summary"]["owner"], "Hardware")
        self.assertEqual(summary["safe_evidence_ref"], "evidence://hardware-sensor-procurement-review-1")
        self.assertIn("Hardware owns procurement execution.", summary["owner_handoff"])
        self.assertIn("summary-output", summary["rerun_commands"][0])
        self.assertIn("software_proof", summary["not_proven"])
        self.assertIn("hardware_material_pending", summary["not_proven"])
        self.assertIn("sensor_procurement_completed", summary["not_proven"])
        self.assertIn("sensor_installed_on_robot", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["hardware_material_pending"])
        self.assertFalse(summary["real_hardware_observed"])
        self.assertFalse(summary["sensor_procurement_completed"])
        self.assertFalse(summary["sensor_installed_on_robot"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # review decision 只进 Robot diagnostics metadata，不能触发 collect/dropoff/cancel、ACK、cursor、Nav2 或 HIL。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertIn("delivery_success=false", summary["robot_diagnostics_summary"]["safe_phone_copy"])
        self.assertNotIn(str(review_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_hardware_sensor_procurement_review_decision_summary_missing_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "hardware_sensor_procurement_review_decision_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_review_decision_summary.v1",
                        "source_schema": "trashbot.hardware_sensor_procurement_review_decision.v1",
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
                        "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
                        "safe_evidence_ref": "evidence://hardware-sensor-procurement-review-2",
                        "review_decision_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "reviewed decision still waits for real procurement proof",
                        },
                        "blockers": ["hardware_material_pending"],
                        "robot_diagnostics_summary": {
                            "safe_copy": "Hardware sensor procurement review decision is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION")
            previous_summary = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY")
            os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION", None)
            os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "hardware_sensor_procurement_review_decision"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "hardware_sensor_procurement_review_decision_summary": {
                            "schema": "trashbot.hardware_sensor_procurement_review_decision_summary.v1",
                            "source_schema": "trashbot.hardware_sensor_procurement_review_decision.v1",
                            "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
                            "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
                            "review_decision_status": {
                                "status": "hardware_material_pending",
                                "verdict": "not_proven",
                                "evidence_source": "software_proof",
                            },
                            "robot_diagnostics_summary": {
                                "safe_copy": "Hardware sensor procurement review decision is metadata-only; delivery_success=false.",
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["hardware_sensor_procurement_review_decision"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_hardware_sensor_procurement_review_decision.json"
            missing_summary = summarize_hardware_sensor_procurement_review_decision(str(missing_path))

            unsupported_summary = summarize_hardware_sensor_procurement_review_decision(
                {
                    "schema": "trashbot.hardware_sensor_procurement_intake_gate.v1",
                    "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
                    "safe_copy": "Unsupported review decision is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_hardware_sensor_procurement_review_decision(
                {
                    "schema": "trashbot.hardware_sensor_procurement_review_decision.v1",
                    "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "raw_ack_payload": {"ack": "posted"},
                    "serial_device": "/dev/ttyUSB0",
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware procurement review confirms delivery success and ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["review_decision_status"]["status"], "hardware_material_pending")
        self.assertEqual(diagnostics_summary["review_decision_status"]["status"], "hardware_material_pending")
        self.assertEqual(
            missing_summary["review_decision_status"]["status"],
            "blocked_missing_hardware_sensor_procurement_review_decision",
        )
        self.assertEqual(unsupported_summary["review_decision_status"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["review_decision_status"]["status"], "unsafe_fields")
        self.assertEqual(env_summary["review_decision_status"]["evidence_source"], "software_proof")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("blocked_missing_hardware_sensor_procurement_review_decision", encoded)
        self.assertIn("software_proof_docker_hardware_sensor_procurement_review_decision_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("hardware_material_pending", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("raw_ack_payload", encoded)

    def test_diagnostics_payload_includes_hardware_sensor_procurement_execution_pack_summary(self):
        with tempfile.TemporaryDirectory() as td:
            pack_path = Path(td) / "hardware_sensor_procurement_execution_pack.json"
            pack_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_execution_pack.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
                        "evidence_ref": "evidence://hardware-sensor-procurement-execution-pack-1",
                        "execution_pack_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "execution pack is ready for Hardware owner procurement work only",
                        },
                        "blockers": ["hardware_material_pending"],
                        "material_templates": [
                            {
                                "name": "sensor_sku_capture",
                                "required_fields": ["vendor", "model", "quantity", "owner"],
                            }
                        ],
                        "owner_handoff": ["Hardware owns SKU/source/procurement execution."],
                        "rerun_commands": ["python3 pc-tools/evidence/hardware_sensor_procurement_execution_pack_gate.py --once-json"],
                        "blocked_reason": "waiting for purchase order, installation, calibration, and HIL evidence",
                        "next_required_evidence": ["purchase order", "installed sensor proof", "calibration log"],
                        "operator_next_steps": ["Wait for Hardware execution before enabling robot actions."],
                        "robot_diagnostics_summary": {
                            "safe_copy": (
                                "Hardware sensor procurement execution pack is metadata-only; software_proof only, "
                                "delivery_success=false and primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["hardware_material_pending", "sensor_installed_on_robot"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "hardware_sensor_procurement_execution_pack": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_sensor_procurement_execution_pack_ref=str(pack_path),
            )
            summary = payload["hardware_sensor_procurement_execution_pack"]
            summary_alias = payload["hardware_sensor_procurement_execution_pack_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("hardware_sensor_procurement_execution_pack", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_execution_pack_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.hardware_sensor_procurement_execution_pack.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["execution_pack_status"]["status"], "hardware_material_pending")
        self.assertEqual(summary["execution_pack_status"]["verdict"], "not_proven")
        self.assertEqual(summary["execution_pack_status"]["evidence_source"], "software_proof")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("hardware_material_pending", summary["blockers"])
        self.assertEqual(summary["material_templates"][0]["name"], "sensor_sku_capture")
        self.assertIn("Hardware owns SKU/source/procurement execution.", summary["owner_handoff"])
        self.assertIn("execution_pack_gate.py", summary["rerun_commands"][0])
        self.assertIn("purchase order", summary["next_required_evidence"])
        self.assertEqual(summary["safe_evidence_ref"], "evidence://hardware-sensor-procurement-execution-pack-1")
        self.assertIn("software_proof", summary["not_proven"])
        self.assertIn("sensor_procurement_completed", summary["not_proven"])
        self.assertIn("sensor_installed_on_robot", summary["not_proven"])
        self.assertIn("sensor_calibrated_on_robot", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["hardware_material_pending"])
        self.assertFalse(summary["real_hardware_observed"])
        self.assertFalse(summary["sensor_procurement_completed"])
        self.assertFalse(summary["sensor_installed_on_robot"])
        self.assertFalse(summary["sensor_calibrated_on_robot"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # execution pack 只进 Robot diagnostics metadata，不能触发 collect/dropoff/cancel、ACK、cursor、Nav2 或 HIL。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertIn("delivery_success=false", summary["robot_diagnostics_summary"]["safe_phone_copy"])
        self.assertNotIn(str(pack_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_hardware_sensor_procurement_execution_pack_summary_missing_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "hardware_sensor_procurement_execution_pack_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_execution_pack_summary.v1",
                        "source_schema": "trashbot.hardware_sensor_procurement_execution_pack.v1",
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
                        "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
                        "safe_evidence_ref": "evidence://hardware-sensor-procurement-execution-pack-2",
                        "execution_pack_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "execution pack still waits for real procurement and installation proof",
                        },
                        "blockers": ["hardware_material_pending"],
                        "material_templates": [{"name": "owner_handoff_checklist"}],
                        "robot_diagnostics_summary": {
                            "safe_copy": "Hardware sensor procurement execution pack is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK")
            previous_summary = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY")
            os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK", None)
            os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "hardware_sensor_procurement_execution_pack"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "hardware_sensor_procurement_execution_pack_summary": {
                            "schema": "trashbot.hardware_sensor_procurement_execution_pack_summary.v1",
                            "source_schema": "trashbot.hardware_sensor_procurement_execution_pack.v1",
                            "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
                            "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
                            "execution_pack_status": {
                                "status": "hardware_material_pending",
                                "verdict": "not_proven",
                                "evidence_source": "software_proof",
                            },
                            "robot_diagnostics_summary": {
                                "safe_copy": "Hardware sensor procurement execution pack is metadata-only; delivery_success=false.",
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["hardware_sensor_procurement_execution_pack"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_hardware_sensor_procurement_execution_pack.json"
            missing_summary = summarize_hardware_sensor_procurement_execution_pack(str(missing_path))

            unsupported_summary = summarize_hardware_sensor_procurement_execution_pack(
                {
                    "schema": "trashbot.hardware_sensor_procurement_review_decision.v1",
                    "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
                    "safe_copy": "Unsupported execution pack is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_hardware_sensor_procurement_execution_pack(
                {
                    "schema": "trashbot.hardware_sensor_procurement_execution_pack.v1",
                    "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "raw_ack_payload": {"ack": "posted"},
                    "serial_device": "/dev/ttyUSB0",
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware execution pack confirms delivery success and ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["execution_pack_status"]["status"], "hardware_material_pending")
        self.assertEqual(diagnostics_summary["execution_pack_status"]["status"], "hardware_material_pending")
        self.assertEqual(
            missing_summary["execution_pack_status"]["status"],
            "blocked_missing_hardware_sensor_procurement_execution_pack",
        )
        self.assertEqual(unsupported_summary["execution_pack_status"]["status"], "unsupported_schema")
        self.assertEqual(unsafe_summary["execution_pack_status"]["status"], "unsafe_fields")
        self.assertEqual(env_summary["execution_pack_status"]["evidence_source"], "software_proof")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("blocked_missing_hardware_sensor_procurement_execution_pack", encoded)
        self.assertIn("software_proof_docker_hardware_sensor_procurement_execution_pack_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("hardware_material_pending", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("raw_ack_payload", encoded)

    def test_diagnostics_payload_includes_hardware_sensor_procurement_receipt_intake_summary(self):
        with tempfile.TemporaryDirectory() as td:
            receipt_path = Path(td) / "hardware_sensor_procurement_receipt_intake.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_receipt_intake.v1",
                        "schema_version": 1,
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
                        "evidence_ref": "evidence://hardware-sensor-procurement-receipt-1",
                        "receipt_intake_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "receipt material is staged for Hardware owner review only",
                        },
                        "material_status": "hardware_material_pending",
                        "blockers": ["hardware_material_pending"],
                        "accepted_materials": [{"sensor": "2D LiDAR", "status": "received_copy_staged"}],
                        "missing_materials": ["ToF receipt"],
                        "rejected_materials": [{"sensor": "camera", "reason": "not in current scope"}],
                        "owner_handoff": ["Hardware owns receipt/source/SKU verification."],
                        "next_required_evidence": ["real receipt and installation evidence"],
                        "operator_next_steps": ["Wait for Hardware verification before enabling robot actions."],
                        "robot_diagnostics_summary": {
                            "safe_copy": (
                                "Hardware sensor procurement receipt intake is metadata-only; software_proof only, "
                                "delivery_success=false and primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["hardware_material_pending", "sensor_receipt_verified"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "hardware_sensor_procurement_receipt_intake": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_sensor_procurement_receipt_intake_ref=str(receipt_path),
            )
            summary = payload["hardware_sensor_procurement_receipt_intake"]
            summary_alias = payload["hardware_sensor_procurement_receipt_intake_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("hardware_sensor_procurement_receipt_intake", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.hardware_sensor_procurement_receipt_intake.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(summary["receipt_intake_status"]["status"], "hardware_material_pending")
        self.assertEqual(summary["receipt_intake_status"]["verdict"], "not_proven")
        self.assertEqual(summary["receipt_intake_status"]["evidence_source"], "software_proof")
        self.assertEqual(summary["material_status"], "hardware_material_pending")
        self.assertIn("hardware_material_pending", summary["blockers"])
        self.assertEqual(summary["accepted_materials"][0]["sensor"], "2D LiDAR")
        self.assertIn("ToF receipt", summary["missing_materials"])
        self.assertEqual(summary["rejected_materials"][0]["sensor"], "camera")
        self.assertIn("Hardware owns receipt/source/SKU verification.", summary["owner_handoff"])
        self.assertIn("real receipt and installation evidence", summary["next_required_evidence"])
        self.assertEqual(summary["safe_evidence_ref"], "evidence://hardware-sensor-procurement-receipt-1")
        self.assertIn("software_proof", summary["not_proven"])
        self.assertIn("sensor_receipt_verified", summary["not_proven"])
        self.assertIn("sensor_procurement_completed", summary["not_proven"])
        self.assertIn("sensor_installed_on_robot", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertFalse(summary["sensor_receipt_verified"])
        self.assertFalse(summary["sensor_procurement_completed"])
        self.assertFalse(summary["sensor_installed_on_robot"])
        self.assertFalse(summary["sensor_wiring_verified"])
        self.assertFalse(summary["sensor_power_budget_verified"])
        self.assertFalse(summary["sensor_calibrated_on_robot"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # receipt intake 是只读 metadata consumer，不能触发控制、ACK、cursor、Nav2、HIL 或完成语义。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertIn("delivery_success=false", summary["robot_diagnostics_summary"]["safe_phone_copy"])
        self.assertNotIn(str(receipt_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_hardware_sensor_procurement_receipt_intake_env_inline_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "hardware_sensor_procurement_receipt_intake_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1",
                        "source_schema": "trashbot.hardware_sensor_procurement_receipt_intake.v1",
                        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
                        "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
                        "receipt_intake_status": {
                            "status": "hardware_material_pending",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                        },
                        "robot_diagnostics_summary": {
                            "safe_copy": "Hardware sensor procurement receipt intake is metadata-only; delivery_success=false.",
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE")
            previous_summary = os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY")
            os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE", None)
            os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "hardware_sensor_procurement_receipt_intake"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "hardware_sensor_procurement_receipt_intake_summary": {
                            "schema": "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1",
                            "source_schema": "trashbot.hardware_sensor_procurement_receipt_intake.v1",
                            "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
                            "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
                            "receipt_intake_status": {
                                "status": "hardware_material_pending",
                                "verdict": "not_proven",
                                "evidence_source": "software_proof",
                            },
                            "robot_diagnostics_summary": {
                                "safe_copy": "Hardware sensor procurement receipt intake is metadata-only; delivery_success=false.",
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["hardware_sensor_procurement_receipt_intake"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_hardware_sensor_procurement_receipt_intake.json"
            missing_summary = summarize_hardware_sensor_procurement_receipt_intake(str(missing_path))

            bad_json_path = Path(td) / "bad_hardware_sensor_procurement_receipt_intake.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_hardware_sensor_procurement_receipt_intake(str(bad_json_path))

            unsupported_summary = summarize_hardware_sensor_procurement_receipt_intake(
                {
                    "schema": "trashbot.hardware_sensor_procurement_execution_pack.v1",
                    "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
                    "safe_copy": "Unsupported receipt intake is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_hardware_sensor_procurement_receipt_intake(
                {
                    "schema": "trashbot.hardware_sensor_procurement_receipt_intake.v1",
                    "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "raw_ack_payload": {"ack": "posted"},
                    "serial_device": "/dev/ttyUSB0",
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware receipt intake confirms delivery success and ACK posted.",
                    },
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    unsafe_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["receipt_intake_status"]["status"], "hardware_material_pending")
        self.assertEqual(diagnostics_summary["receipt_intake_status"]["status"], "hardware_material_pending")
        self.assertEqual(
            missing_summary["receipt_intake_status"]["status"],
            "blocked_missing_hardware_sensor_procurement_receipt_intake",
        )
        self.assertEqual(
            bad_json_summary["receipt_intake_status"]["status"],
            "blocked_missing_hardware_sensor_procurement_receipt_intake",
        )
        self.assertEqual(
            unsupported_summary["receipt_intake_status"]["status"],
            "blocked_missing_hardware_sensor_procurement_receipt_intake",
        )
        self.assertEqual(
            unsafe_summary["receipt_intake_status"]["status"],
            "blocked_missing_hardware_sensor_procurement_receipt_intake",
        )
        self.assertEqual(env_summary["receipt_intake_status"]["evidence_source"], "software_proof")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("blocked_missing_hardware_sensor_procurement_receipt_intake", encoded)
        self.assertIn("software_proof_docker_hardware_sensor_procurement_receipt_intake_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("hardware_material_pending", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("raw_ack_payload", encoded)

    def test_diagnostics_payload_includes_hardware_sensor_hil_entry_config_precheck_summary(self):
        with tempfile.TemporaryDirectory() as td:
            precheck_path = Path(td) / "hardware_sensor_hil_entry_config_precheck.json"
            precheck_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_hil_entry_config_precheck.v1",
                        "schema_version": 1,
                        "evidence_boundary": (
                            "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
                        ),
                        "evidence_ref": "evidence://hardware-sensor-hil-entry-config-precheck-1",
                        "precheck_status": {
                            "status": "config_precheck_blocked_missing_materials",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                            "reason": "HIL-entry config shape is staged but field materials are still missing",
                        },
                        "blockers": ["missing_sensor_install_materials"],
                        "sensor_config_summary": {
                            "sensor_count": "parameterized",
                            "tof_channel_count": "parameterized",
                            "thresholds": "parameterized",
                            "frame_ids": "parameterized",
                            "safety_policy": "fail_closed",
                        },
                        "missing_config_categories": ["calibration_frame"],
                        "missing_material_categories": ["install_wiring", "power_budget", "hil_entry_log"],
                        "next_required_evidence": ["real install/wiring/power/calibration/HIL-entry material"],
                        "owner_handoff": ["Hardware owns physical sensor material collection."],
                        "robot_diagnostics_summary": {
                            "safe_copy": (
                                "Hardware sensor HIL-entry config precheck is metadata-only; "
                                "software_proof only, delivery_success=false and primary_actions_enabled=false."
                            ),
                        },
                        "not_proven": ["real_sensor_device_proof", "real_hil_pass"],
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {
                    "state": "waiting_for_trash",
                    "hardware_sensor_hil_entry_config_precheck": {"delivery_success": True},
                },
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                hardware_sensor_hil_entry_config_precheck_ref=str(precheck_path),
            )
            summary = payload["hardware_sensor_hil_entry_config_precheck"]
            summary_alias = payload["hardware_sensor_hil_entry_config_precheck_summary"]
            encoded = json.dumps(summary, ensure_ascii=False)

        self.assertEqual(summary, summary_alias)
        self.assertNotIn("hardware_sensor_hil_entry_config_precheck", payload["latest_status"])
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1")
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate",
        )
        self.assertEqual(summary["source_schema"], "trashbot.hardware_sensor_hil_entry_config_precheck.v1")
        self.assertEqual(summary["source_schema_version"], 1)
        self.assertEqual(
            summary["source_contract"]["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate",
        )
        self.assertEqual(summary["precheck_status"]["status"], "config_precheck_blocked_missing_materials")
        self.assertEqual(summary["precheck_status"]["verdict"], "not_proven")
        self.assertEqual(summary["precheck_status"]["evidence_source"], "software_proof")
        self.assertEqual(summary["config_precheck_status"], "config_precheck_blocked_missing_materials")
        self.assertEqual(summary["sensor_config_summary"]["sensor_count"], "parameterized")
        self.assertEqual(summary["sensor_config_summary"]["tof_channel_count"], "parameterized")
        self.assertEqual(summary["sensor_config_summary"]["thresholds"], "parameterized")
        self.assertEqual(summary["sensor_config_summary"]["frame_ids"], "parameterized")
        self.assertEqual(summary["sensor_config_summary"]["safety_policy"], "fail_closed")
        self.assertIn("calibration_frame", summary["missing_config_categories"])
        self.assertIn("install_wiring", summary["missing_material_categories"])
        self.assertIn("real install/wiring/power/calibration/HIL-entry material", summary["next_required_evidence"])
        self.assertIn("Hardware owns physical sensor material collection.", summary["owner_handoff"])
        self.assertEqual(
            summary["safe_evidence_ref"],
            "evidence://hardware-sensor-hil-entry-config-precheck-1",
        )
        self.assertIn("software_proof", summary["not_proven"])
        self.assertIn("real_sensor_device_proof", summary["not_proven"])
        self.assertIn("real_hil_pass", summary["not_proven"])
        self.assertIn("delivery_success", summary["not_proven"])
        self.assertTrue(summary["metadata_only"])
        self.assertTrue(summary["sensor_config_precheck_only"])
        self.assertFalse(summary["sensor_config_validated_for_hil_entry"])
        self.assertFalse(summary["sensor_procurement_completed"])
        self.assertFalse(summary["sensor_installed_on_robot"])
        self.assertFalse(summary["sensor_wiring_verified"])
        self.assertFalse(summary["sensor_power_budget_verified"])
        self.assertFalse(summary["sensor_calibrated_on_robot"])
        self.assertFalse(summary["route_elevator_field_pass"])
        self.assertFalse(summary["nav2_fixed_route_run"])
        self.assertFalse(summary["dropoff_completion"])
        self.assertFalse(summary["cancel_completion"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        # config precheck 是 metadata-only consumer，不能触发 collect/dropoff/cancel、ACK、cursor、Nav2 或 HIL。
        self.assertFalse(summary["collect_triggered"])
        self.assertFalse(summary["dropoff_triggered"])
        self.assertFalse(summary["cancel_triggered"])
        self.assertFalse(summary["ack_post_allowed"])
        self.assertFalse(summary["remote_ack_allowed"])
        self.assertFalse(summary["cursor_updates_allowed"])
        self.assertFalse(summary["persistence_updates_allowed"])
        self.assertFalse(summary["terminal_ack_allowed"])
        self.assertFalse(summary["nav2_triggered"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["production_ready"])
        self.assertIn("metadata-only", summary["safe_copy"])
        self.assertIn("delivery_success=false", summary["robot_diagnostics_summary"]["safe_phone_copy"])
        self.assertNotIn(str(precheck_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)

    def test_hardware_sensor_hil_entry_config_precheck_env_inline_unsupported_and_unsafe_block(self):
        with tempfile.TemporaryDirectory() as td:
            summary_path = Path(td) / "hardware_sensor_hil_entry_config_precheck_summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1",
                        "source_schema": "trashbot.hardware_sensor_hil_entry_config_precheck.v1",
                        "evidence_boundary": (
                            "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
                        ),
                        "source_evidence_boundary": (
                            "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
                        ),
                        "precheck_status": {
                            "status": "config_precheck_blocked_missing_materials",
                            "verdict": "not_proven",
                            "evidence_source": "software_proof",
                        },
                        "sensor_config_summary": {"sensor count": "parameterized"},
                        "robot_diagnostics_summary": {
                            "safe_copy": (
                                "Hardware sensor HIL-entry config precheck is metadata-only; "
                                "delivery_success=false and primary_actions_enabled=false."
                            ),
                        },
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                    }
                ),
                encoding="utf-8",
            )
            previous_artifact = os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK")
            previous_summary = os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY")
            os.environ.pop("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK", None)
            os.environ["TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY"] = str(summary_path)
            try:
                env_summary = self._base_build_payload({"state": "waiting_for_trash"})[
                    "hardware_sensor_hil_entry_config_precheck"
                ]
            finally:
                if previous_artifact is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK"] = previous_artifact
                if previous_summary is None:
                    os.environ.pop("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY", None)
                else:
                    os.environ["TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY"] = previous_summary

            diagnostics_summary = self._base_build_payload(
                {
                    "state": "waiting_for_trash",
                    "diagnostics": {
                        "hardware_sensor_hil_entry_config_precheck_summary": {
                            "schema": "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1",
                            "source_schema": "trashbot.hardware_sensor_hil_entry_config_precheck.v1",
                            "evidence_boundary": (
                                "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
                            ),
                            "source_evidence_boundary": (
                                "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
                            ),
                            "precheck_status": {
                                "status": "config_precheck_blocked_missing_materials",
                                "verdict": "not_proven",
                                "evidence_source": "software_proof",
                            },
                            "sensor_config_summary": {"sensor count": "parameterized"},
                            "robot_diagnostics_summary": {
                                "safe_copy": (
                                    "Hardware sensor HIL-entry config precheck is metadata-only; "
                                    "delivery_success=false and primary_actions_enabled=false."
                                ),
                            },
                            "delivery_success": False,
                            "primary_actions_enabled": False,
                        }
                    },
                }
            )["hardware_sensor_hil_entry_config_precheck"]

            missing_path = Path(td) / "Bearer-secret-token" / "missing_hardware_sensor_hil_entry_config_precheck.json"
            missing_summary = summarize_hardware_sensor_hil_entry_config_precheck(str(missing_path))

            bad_json_path = Path(td) / "bad_hardware_sensor_hil_entry_config_precheck.json"
            bad_json_path.write_text("{bad-json", encoding="utf-8")
            bad_json_summary = summarize_hardware_sensor_hil_entry_config_precheck(str(bad_json_path))

            unsupported_summary = summarize_hardware_sensor_hil_entry_config_precheck(
                {
                    "schema": "trashbot.hardware_sensor_procurement_receipt_intake.v1",
                    "evidence_boundary": (
                        "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate"
                    ),
                    "safe_copy": "Unsupported precheck is metadata-only; delivery_success=false.",
                }
            )
            unsafe_summary = summarize_hardware_sensor_hil_entry_config_precheck(
                {
                    "schema": "trashbot.hardware_sensor_hil_entry_config_precheck.v1",
                    "evidence_boundary": (
                        "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
                    ),
                    "delivery_success": True,
                    "primary_actions_enabled": True,
                    "raw_artifact": {"serial_device": "/dev/ttyUSB0"},
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor precheck confirms HIL pass and delivery success.",
                    },
                }
            )
            weak_boundary_summary = summarize_hardware_sensor_hil_entry_config_precheck(
                {
                    "schema": "trashbot.hardware_sensor_hil_entry_config_precheck.v1",
                    "evidence_boundary": "software_proof",
                    "safe_copy": "Hardware sensor precheck is metadata-only; delivery_success=false.",
                }
            )
            encoded = json.dumps(
                [
                    env_summary,
                    diagnostics_summary,
                    missing_summary,
                    bad_json_summary,
                    unsupported_summary,
                    unsafe_summary,
                    weak_boundary_summary,
                ],
                ensure_ascii=False,
            )

        self.assertEqual(env_summary["precheck_status"]["status"], "config_precheck_blocked_missing_materials")
        self.assertEqual(
            diagnostics_summary["precheck_status"]["status"],
            "config_precheck_blocked_missing_materials",
        )
        self.assertEqual(
            missing_summary["precheck_status"]["status"],
            "blocked_missing_hardware_sensor_hil_entry_config_precheck",
        )
        self.assertEqual(
            bad_json_summary["precheck_status"]["status"],
            "blocked_missing_hardware_sensor_hil_entry_config_precheck",
        )
        self.assertEqual(
            unsupported_summary["precheck_status"]["status"],
            "blocked_missing_hardware_sensor_hil_entry_config_precheck",
        )
        self.assertEqual(
            unsafe_summary["precheck_status"]["status"],
            "blocked_missing_hardware_sensor_hil_entry_config_precheck",
        )
        self.assertEqual(
            weak_boundary_summary["precheck_status"]["status"],
            "blocked_missing_hardware_sensor_hil_entry_config_precheck",
        )
        self.assertEqual(env_summary["precheck_status"]["evidence_source"], "software_proof")
        self.assertFalse(env_summary["delivery_success"])
        self.assertFalse(env_summary["primary_actions_enabled"])
        self.assertFalse(diagnostics_summary["delivery_success"])
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertIn("blocked_missing_hardware_sensor_hil_entry_config_precheck", encoded)
        self.assertIn("software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("hardware_material_pending", encoded)
        self.assertIn("metadata-only", encoded)
        self.assertNotIn(str(missing_path), encoded)
        self.assertNotIn(str(Path(td)), encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("raw_artifact", encoded)

    def test_diagnostics_payload_includes_phone_safe_oss_cdn_manifest_summary(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "oss_cdn_manifest.json"
            create_oss_cdn_manifest_artifact(
                manifest_path,
                "robot-diagnostics",
                "task-diagnostics",
                date_text="2026-05-12",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                oss_cdn_manifest_artifact_ref=str(manifest_path),
            )
            encoded = json.dumps(payload["oss_cdn_manifest"], ensure_ascii=False)

        self.assertEqual(payload["oss_cdn_manifest"]["state"], "ready")
        self.assertEqual(
            payload["oss_cdn_manifest"]["evidence_boundary"],
            "software_proof_docker_phone_manifest_consumption",
        )
        self.assertIn("real_oss_upload", payload["oss_cdn_manifest"]["not_proven"])
        self.assertNotIn(str(manifest_path), encoded)
        self.assertNotIn("object_key", encoded)

    def test_diagnostics_payload_includes_phone_safe_network_recovery_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "network_recovery.json"
            create_network_recovery_artifact(
                artifact_path,
                Path(td) / "network_recovery.sqlite",
                state_backend="sqlite",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                network_recovery_artifact_ref=str(artifact_path),
            )
            encoded = json.dumps(payload["network_recovery_drill"], ensure_ascii=False)

        self.assertEqual(payload["network_recovery_drill"]["state"], "ready")
        self.assertEqual(
            payload["network_recovery_drill"]["evidence_boundary"],
            "software_proof_docker_network_recovery_phone_consumption",
        )
        self.assertIn("delivery_success", payload["network_recovery_drill"]["not_proven"])
        self.assertNotIn(str(artifact_path), encoded)
        self.assertNotIn("steps", encoded)
        self.assertNotIn("checksum", encoded)

    def test_diagnostics_payload_includes_phone_safe_credential_rotation_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "credential_rotation.json"
            create_credential_rotation_artifact(
                artifact_path,
                "robot-diagnostics",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                credential_rotation_artifact_ref=str(artifact_path),
            )
            encoded = json.dumps(payload["credential_rotation"], ensure_ascii=False)

        self.assertEqual(payload["credential_rotation"]["state"], "ready")
        self.assertEqual(
            payload["credential_rotation"]["evidence_boundary"],
            "software_proof_docker_credential_rotation_phone_consumption",
        )
        self.assertIn("production_credential_rotation", payload["credential_rotation"]["not_proven"])
        self.assertNotIn(str(artifact_path), encoded)
        self.assertNotIn("robot-diagnostics", encoded)
        self.assertNotIn("checksum", encoded)

    def test_diagnostics_payload_includes_phone_safe_provisioning_audit_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "provisioning_audit.json"
            create_provisioning_audit_artifact(
                artifact_path,
                "robot-diagnostics",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                provisioning_audit_artifact_ref=str(artifact_path),
            )
            encoded = json.dumps(payload["provisioning_audit"], ensure_ascii=False)

        self.assertEqual(payload["provisioning_audit"]["state"], "ready")
        self.assertEqual(
            payload["provisioning_audit"]["evidence_boundary"],
            "software_proof_docker_provisioning_audit_phone_consumption",
        )
        self.assertFalse(payload["provisioning_audit"]["production_ready"])
        self.assertEqual(payload["provisioning_audit"]["overall_status"], "blocked")
        self.assertIn("real_sts_issuance", payload["provisioning_audit"]["not_proven"])
        self.assertNotIn(str(artifact_path), encoded)
        self.assertNotIn("robot-diagnostics", encoded)
        self.assertNotIn("checksum", encoded)

    def test_diagnostics_payload_includes_phone_safe_production_store_queue_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "production_store_queue.json"
            create_production_store_queue_artifact(
                artifact_path,
                "robot-diagnostics",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                production_store_queue_artifact_ref=str(artifact_path),
            )
            encoded = json.dumps(payload["production_store_queue"], ensure_ascii=False)

        self.assertEqual(payload["production_store_queue"]["state"], "ready")
        self.assertEqual(
            payload["production_store_queue"]["evidence_boundary"],
            "software_proof_docker_production_store_queue_phone_consumption",
        )
        self.assertFalse(payload["production_store_queue"]["production_ready"])
        self.assertEqual(payload["production_store_queue"]["overall_status"], "blocked")
        self.assertIn("production_db_or_queue", payload["production_store_queue"]["not_proven"])
        self.assertIn("multi_instance_consistency", payload["production_store_queue"]["not_proven"])
        self.assertNotIn(str(artifact_path), encoded)
        self.assertNotIn("robot-diagnostics", encoded)
        self.assertNotIn("checksum", encoded)

    def test_diagnostics_payload_includes_phone_safe_queue_ordering_drill_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "queue_ordering_drill.json"
            create_queue_ordering_drill_artifact(
                artifact_path,
                "robot-diagnostics",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                queue_ordering_drill_artifact_ref=str(artifact_path),
            )
            encoded = json.dumps(payload["queue_ordering_drill"], ensure_ascii=False)

        self.assertEqual(payload["queue_ordering_drill"]["state"], "ready")
        self.assertEqual(
            payload["queue_ordering_drill"]["evidence_boundary"],
            "software_proof_docker_queue_ordering_phone_consumption",
        )
        self.assertEqual(payload["queue_ordering_drill"]["adjacent_command_ids"], ["cmd-9", "cmd-10"])
        self.assertFalse(payload["queue_ordering_drill"]["production_ready"])
        self.assertIn("production_queue_ordering", payload["queue_ordering_drill"]["not_proven"])
        self.assertIn("production_db_or_queue", payload["queue_ordering_drill"]["not_proven"])
        self.assertNotIn(str(artifact_path), encoded)
        self.assertNotIn("robot-diagnostics", encoded)
        self.assertNotIn("checksum", encoded)

    def test_diagnostics_payload_includes_phone_safe_transaction_isolation_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "transaction_isolation.json"
            create_transaction_isolation_artifact(
                artifact_path,
                "robot-diagnostics",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                transaction_isolation_artifact_ref=str(artifact_path),
            )
            encoded = json.dumps(payload["transaction_isolation"], ensure_ascii=False)

        self.assertEqual(payload["transaction_isolation"]["state"], "ready")
        self.assertEqual(
            payload["transaction_isolation"]["evidence_boundary"],
            "software_proof_docker_transaction_isolation_phone_consumption",
        )
        self.assertEqual(
            payload["transaction_isolation"]["cursor_after_interleaving"],
            "cmd-before-transaction-a",
        )
        self.assertFalse(payload["transaction_isolation"]["delivery_success"])
        self.assertFalse(payload["transaction_isolation"]["production_ready"])
        self.assertIn("production_transaction_isolation", payload["transaction_isolation"]["not_proven"])
        self.assertIn("production_db_or_queue", payload["transaction_isolation"]["not_proven"])
        self.assertNotIn(str(artifact_path), encoded)
        self.assertNotIn("robot-diagnostics", encoded)
        self.assertNotIn("checksum", encoded)

    def test_diagnostics_payload_includes_phone_safe_production_recovery_summary(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "production_recovery.json"
            create_production_recovery_artifact(
                artifact_path,
                "robot-diagnostics",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                review_decision_log_ref="",
                operator_status_file="/tmp/status.json",
                production_recovery_artifact_ref=str(artifact_path),
            )
            encoded = json.dumps(payload["production_recovery"], ensure_ascii=False)

        self.assertEqual(payload["production_recovery"]["state"], "ready")
        self.assertEqual(
            payload["production_recovery"]["evidence_boundary"],
            "software_proof_docker_production_recovery_phone_consumption",
        )
        self.assertFalse(payload["production_recovery"]["production_ready"])
        self.assertEqual(payload["production_recovery"]["overall_status"], "blocked")
        self.assertIn("production_backup_policy", payload["production_recovery"]["not_proven"])
        self.assertIn("real_disaster_recovery", payload["production_recovery"]["not_proven"])
        self.assertNotIn(str(artifact_path), encoded)
        self.assertNotIn("robot-diagnostics", encoded)
        self.assertNotIn("checksum", encoded)

    def test_diagnostics_phone_support_bundle_is_phone_safe(self):
        class Gateway:
            def snapshot(self):
                return {
                    "state": "remote_degraded",
                    "message": "remote blocked; hide token secret-token and /cmd_vel",
                    "can_collect": False,
                    "can_confirm_dropoff": False,
                    "can_cancel": True,
                    "source": "software_proof",
                    "task_id": "task-support-1",
                    "queue_url": "postgres://robot:secret@db.local/queue",
                    "local_path": "/tmp/robot/status.json",
                }

            def diagnostics(self):
                return {
                    "state": "diagnostics_ready",
                    "software_version": "0.1.0",
                    "map_version": "map-a",
                    "route_version": "route-a",
                    "source": "software_proof",
                    "failure_code": "REMOTE_BLOCKED",
                    "latest_status": self.snapshot(),
                    "failure": {
                        "state": "failed",
                        "message": "raw ROS topic /cmd_vel and Authorization must stay hidden",
                        "error_code": "REMOTE_BLOCKED",
                        "final_state": "blocked",
                    },
                    "last_task": {
                        "task_id": "task-support-1",
                        "serial": "/dev/ttyUSB0",
                        "baudrate": 115200,
                        "token": "secret-token",
                        "Authorization": "Bearer secret-token",
                    },
                    "phone_support_bundle": {
                        "schema": "trashbot.phone_support_bundle.v1",
                        "safe_copy": "用户可复制摘要，但 ACK 不是送达成功。",
                        "support_refs": {
                            "raw_ros_topic": "/cmd_vel",
                            "serial": "/dev/ttyUSB0",
                            "baudrate": 115200,
                            "token": "secret-token",
                            "Authorization": "Bearer secret-token",
                            "queue_url": "postgres://robot:secret@db.local/queue",
                            "local_path": "/tmp/robot/status.json",
                        },
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                    },
                }

        payload = _diagnostics_with_phone_task_flow(Gateway(), MockCloudStore())
        bundle = payload["phone_support_bundle"]
        latest_bundle = payload["latest_status"]["phone_support_bundle"]

        self.assertEqual(bundle["schema"], "trashbot.phone_support_bundle.v1")
        self.assertEqual(latest_bundle["schema"], "trashbot.phone_support_bundle.v1")
        self.assertEqual(bundle["evidence_boundary"], "software_proof_docker_phone_support_bundle_gate")
        self.assertEqual(bundle["support_refs"]["software_version"], "0.1.0")
        self.assertEqual(bundle["support_refs"]["map_version"], "map-a")
        self.assertEqual(bundle["support_refs"]["route_version"], "route-a")
        self.assertEqual(bundle["support_refs"]["source"], "software_proof")
        self.assertNotEqual(bundle.get("ack_semantics"), "delivery_success")
        self.assertNotEqual(bundle.get("delivery_success"), True)
        self.assertIn("ack_as_delivery_success", bundle["not_proven"])

        for forbidden_key in (
            "raw_ros_topic",
            "serial",
            "baudrate",
            "token",
            "Authorization",
            "queue_url",
            "local_path",
        ):
            self.assertNotIn(forbidden_key, bundle["support_refs"])
        encoded = json.dumps(bundle, ensure_ascii=False)
        # 这里直接覆盖 /api/diagnostics 的已接线 wrapper，不能再用 skip 掩盖未脱敏输出。
        for forbidden in (
            "raw_ros_topic",
            "/cmd_vel",
            "/dev/ttyUSB0",
            "baudrate",
            "token",
            "Authorization",
            "Bearer",
            "postgres://",
            "queue_url",
            "/tmp/robot/status.json",
            "local_path",
        ):
            self.assertNotIn(forbidden, encoded)

        offline_resume = payload["phone_offline_resume_readiness"]
        latest_offline_resume = payload["latest_status"]["phone_offline_resume_readiness"]
        self.assertEqual(offline_resume["schema"], "trashbot.phone_offline_resume_readiness.v1")
        self.assertEqual(latest_offline_resume["schema"], "trashbot.phone_offline_resume_readiness.v1")
        self.assertEqual(
            offline_resume["evidence_boundary"],
            "software_proof_docker_phone_offline_resume_gate",
        )
        self.assertFalse(offline_resume["primary_actions_enabled"])
        self.assertTrue(offline_resume["support_entry_enabled"])
        self.assertIn("ACK 只表示", offline_resume["ack_semantics"])
        encoded_offline_resume = json.dumps(offline_resume, ensure_ascii=False)
        for forbidden in (
            "raw_ros_topic",
            "/cmd_vel",
            "/dev/ttyUSB0",
            "baudrate",
            "token",
            "Authorization",
            "Bearer",
            "postgres://",
            "queue_url",
            "/tmp/robot/status.json",
            "checksum",
        ):
            self.assertNotIn(forbidden, encoded_offline_resume)

    def test_diagnostics_payload_does_not_forward_preexisting_support_bundle(self):
        payload = build_diagnostics_payload(
            {
                "state": "remote_degraded",
                "phone_support_bundle": {
                    "schema": "trashbot.phone_support_bundle.v1",
                    "safe_copy": "用户可复制摘要，但 ACK 不是送达成功。",
                    "support_refs": {
                        "raw_ros_topic": "/cmd_vel",
                        "serial": "/dev/ttyUSB0",
                        "baudrate": 115200,
                        "token": "secret-token",
                        "Authorization": "Bearer secret-token",
                        "queue_url": "postgres://robot:secret@db.local/queue",
                        "local_path": "/tmp/robot/status.json",
                    },
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                },
            },
            software_version="",
            map_version="",
            route_version="",
            log_refs=[],
            vision_sample_manifest_ref="",
            review_decision_log_ref="",
            operator_status_file="/tmp/status.json",
        )

        # diagnostics core payload 不信任 latest_status 内既有 bundle；HTTP wrapper 负责重新生成脱敏版本。
        self.assertNotIn("phone_support_bundle", payload)

    def test_diagnostics_payload_does_not_forward_preexisting_voice_prompt_readiness(self):
        payload = build_diagnostics_payload(
            {
                "state": "remote_degraded",
                "voice_prompt_readiness": {
                    "schema": "trashbot.voice_prompt_readiness.v1",
                    "current_prompt": "raw prompt with /cmd_vel and secret-token",
                    "support_refs": {
                        "raw_ros_topic": "/cmd_vel",
                        "serial": "/dev/ttyUSB0",
                        "baudrate": 115200,
                        "token": "secret-token",
                        "Authorization": "Bearer secret-token",
                        "queue_url": "postgres://robot:secret@db.local/queue",
                        "local_path": "/tmp/robot/status.json",
                    },
                    "ack_semantics": "delivery_success",
                    "playback_ready": True,
                    "delivery_success": True,
                },
            },
            software_version="",
            map_version="",
            route_version="",
            log_refs=[],
            vision_sample_manifest_ref="",
            review_decision_log_ref="",
            operator_status_file="/tmp/status.json",
        )

        # diagnostics core 不信任 latest_status 中的预置 voice metadata；HTTP wrapper 负责生成脱敏版本。
        self.assertNotIn("voice_prompt_readiness", payload)

    def test_diagnostics_payload_does_not_forward_preexisting_offline_resume_readiness(self):
        payload = build_diagnostics_payload(
            {
                "state": "remote_degraded",
                "phone_offline_resume_readiness": {
                    "schema": "trashbot.phone_offline_resume_readiness.v1",
                    "safe_phone_copy": "raw /cmd_vel token checksum /tmp/robot/status.json",
                    "ack_semantics": "delivery_success",
                    "can_resume": True,
                    "delivery_success": True,
                },
            },
            software_version="",
            map_version="",
            route_version="",
            log_refs=[],
            vision_sample_manifest_ref="",
            review_decision_log_ref="",
            operator_status_file="/tmp/status.json",
        )

        # diagnostics core 不信任 latest_status 中的预置 offline/resume metadata；HTTP wrapper 负责重新生成。
        self.assertNotIn("phone_offline_resume_readiness", payload)

    def test_log_refs_are_normalized_without_claiming_file_existence(self):
        self.assertEqual(normalize_log_refs(None), [])
        self.assertEqual(normalize_log_refs(""), [])
        self.assertEqual(normalize_log_refs("a,b, c "), ["a", "b", "c"])
        self.assertEqual(normalize_log_refs(["a", 3, ""]), ["a", "3"])

    def test_vision_manifest_summary_reports_latest_sample(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            samples = root / "samples"
            samples.mkdir()
            (samples / "old.json").write_text("{}", encoding="utf-8")
            (samples / "old_raw.jpg").write_bytes(b"old")
            (samples / "new.json").write_text("{}", encoding="utf-8")
            (samples / "new_raw.jpg").write_bytes(b"new")
            (samples / "new_annotated.jpg").write_bytes(b"annotated")
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "sample_output_dir": str(root),
                        "samples": [
                            {
                                "sample_id": "old",
                                "sample_ref": "vision_sample://samples/old.json",
                                "timestamp": 1.0,
                                "frame_id": "map",
                                "raw_image": "samples/old_raw.jpg",
                                "annotated_image": "",
                                "json": "samples/old.json",
                                "context": {"route_id": "old-route", "event_type": "route_keyframe"},
                                "detection_count": 0,
                                "max_confidence": 0,
                            },
                            {
                                "sample_id": "new",
                                "sample_ref": "vision_sample://samples/new.json",
                                "timestamp": 2.0,
                                "frame_id": "camera",
                                "raw_image": "samples/new_raw.jpg",
                                "annotated_image": "samples/new_annotated.jpg",
                                "json": "samples/new.json",
                                "context": {
                                    "task_id": "task-7",
                                    "route_id": "route-a",
                                    "checkpoint_id": "cp-3",
                                    "event_type": "anomaly",
                                },
                                "detection_count": 2,
                                "max_confidence": 91,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["latest_sample_ref"], "vision_sample://samples/new.json")
        self.assertEqual(summary["latest_timestamp"], 2.0)
        self.assertEqual(summary["latest_context"]["task_id"], "task-7")
        self.assertEqual(summary["latest_detection_count"], 2)
        self.assertEqual(summary["latest_max_confidence"], 91)
        self.assertEqual(summary["event_counts"], {"route_keyframe": 1, "anomaly": 1})
        self.assertEqual(summary["review_queue_count"], 2)
        self.assertEqual(summary["review_queue"][0]["reason"], "route_keyframe_review")
        self.assertEqual(summary["review_queue"][1]["reason"], "anomaly_sample")
        self.assertEqual(summary["review_queue"][0]["review_status"], "pending")
        self.assertIsNone(summary["review_queue"][0]["last_decision"])
        self.assertEqual(summary["progress_summary"]["total"], 2)
        self.assertEqual(summary["progress_summary"]["decided"], 0)
        self.assertEqual(summary["progress_summary"]["pending"], 2)
        self.assertEqual(summary["progress_summary"]["coverage_rate"], 0.0)
        self.assertEqual(summary["decision_distribution"]["approved"]["count"], 0)
        self.assertEqual(summary["decision_distribution"]["approved"]["ratio"], 0.0)
        self.assertEqual(summary["next_pending_sample"]["sample_id"], "old")
        self.assertEqual(summary["integrity_summary"]["status"], "ok")
        self.assertEqual(summary["integrity_error_count"], 0)
        self.assertEqual(summary["integrity_warning_count"], 0)
        self.assertEqual(summary["missing_file_ref_count"], 0)
        self.assertEqual(summary["file_counts"]["sample_ref"]["present"], 2)
        self.assertEqual(summary["file_counts"]["raw_image"]["present"], 2)
        self.assertEqual(summary["file_counts"]["annotated_image"]["present"], 1)
        self.assertEqual(summary["context_field_coverage"]["present"]["event_type"], 2)
        self.assertEqual(summary["context_field_coverage"]["present"]["route_id"], 2)
        self.assertEqual(summary["context_field_coverage"]["missing"]["task_id"], 1)
        self.assertEqual(summary["read_error"], "")

    def test_vision_manifest_summary_builds_bounded_review_queue(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            samples = [
                {
                    "sample_id": "normal-reviewed",
                    "sample_ref": "vision_sample://normal-reviewed.json",
                    "timestamp": 1.0,
                    "context": {"event_type": "detection"},
                    "detection_count": 1,
                    "max_confidence": 95,
                    "review_status": "accepted",
                },
                {
                    "sample_id": "low-confidence",
                    "sample_ref": "vision_sample://low-confidence.json",
                    "timestamp": 2.0,
                    "context": {"event_type": "detection"},
                    "detection_count": 1,
                    "max_confidence": 62,
                },
                {
                    "sample_id": "route-keyframe",
                    "sample_ref": "vision_sample://route-keyframe.json",
                    "timestamp": 3.0,
                    "context": {"event_type": "route_keyframe", "route_id": "route-a"},
                    "detection_count": 0,
                    "max_confidence": 0,
                },
                {
                    "sample_id": "anomaly",
                    "sample_ref": "vision_sample://anomaly.json",
                    "timestamp": 4.0,
                    "context": {"event_type": "anomaly", "anomaly_type": "blocked_view"},
                    "detection_count": 0,
                    "max_confidence": 0,
                },
            ]
            manifest_path.write_text(
                json.dumps({"schema": "trashbot.vision_samples.v1", "samples": samples}),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertEqual(summary["event_counts"], {"detection": 2, "route_keyframe": 1, "anomaly": 1})
        self.assertEqual(summary["review_queue_count"], 3)
        self.assertEqual(
            [item["reason"] for item in summary["review_queue"]],
            ["low_confidence_detection", "route_keyframe_review", "anomaly_sample"],
        )
        self.assertEqual(summary["review_queue"][-1]["sample_ref"], "vision_sample://anomaly.json")
        self.assertEqual(summary["progress_summary"]["total"], 3)
        self.assertEqual(summary["progress_summary"]["decided"], 0)
        self.assertEqual(summary["progress_summary"]["pending"], 3)
        self.assertEqual(summary["progress_summary"]["coverage_rate"], 0.0)
        self.assertEqual(summary["next_pending_sample"]["sample_id"], "low-confidence")

    def test_diagnostics_merges_last_review_decision_into_queue(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "manifest.json"
            decision_log_path = root / "review_decisions.jsonl"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "samples": [
                            {
                                "sample_id": "sample-1",
                                "sample_ref": "vision_sample://sample-1.json",
                                "timestamp": 1.0,
                                "context": {"event_type": "route_keyframe"},
                                "detection_count": 0,
                                "max_confidence": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            decision_log_path.write_text(
                json.dumps(
                    {
                        "decision_id": "d-1",
                        "sample_id": "sample-1",
                        "decision": "approved",
                        "option": "route_keyframe_review",
                        "comment": "looks correct",
                        "operator": "op-7",
                        "timestamp": 100.0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref=str(manifest_path),
                review_decision_log_ref=str(decision_log_path),
                operator_status_file="/tmp/status.json",
            )

        self.assertEqual(payload["review_decision_log"]["status"], "ok")
        self.assertEqual(payload["review_decision_log"]["decision_count"], 1)
        self.assertEqual(payload["review_decision_log"]["sample_count"], 1)
        self.assertEqual(payload["vision_samples"]["review_queue_count"], 1)
        queue_item = payload["vision_samples"]["review_queue"][0]
        self.assertEqual(queue_item["sample_id"], "sample-1")
        self.assertEqual(queue_item["review_status"], "decided")
        self.assertEqual(queue_item["last_decision"]["decision"], "approved")
        self.assertEqual(payload["vision_samples"]["progress_summary"]["total"], 1)
        self.assertEqual(payload["vision_samples"]["progress_summary"]["decided"], 1)
        self.assertEqual(payload["vision_samples"]["progress_summary"]["pending"], 0)
        self.assertEqual(payload["vision_samples"]["progress_summary"]["coverage_rate"], 1.0)
        self.assertEqual(payload["vision_samples"]["decision_distribution"]["approved"]["count"], 1)
        self.assertEqual(payload["vision_samples"]["decision_distribution"]["approved"]["ratio"], 1.0)
        self.assertEqual(payload["vision_samples"]["decision_distribution"]["rejected"]["count"], 0)
        self.assertIsNone(payload["vision_samples"]["next_pending_sample"])

    def test_vision_manifest_summary_handles_missing_and_corrupt_files(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            corrupt = Path(td) / "corrupt.json"
            corrupt.write_text("{bad json", encoding="utf-8")

            missing_summary = summarize_vision_manifest(str(missing))
            corrupt_summary = summarize_vision_manifest(str(corrupt))

        self.assertFalse(missing_summary["exists"])
        self.assertIn("not found", missing_summary["read_error"])
        self.assertEqual(missing_summary["integrity_summary"]["status"], "error")
        self.assertEqual(missing_summary["integrity_error_count"], 1)
        self.assertTrue(corrupt_summary["exists"])
        self.assertIn("failed reading", corrupt_summary["read_error"])
        self.assertEqual(corrupt_summary["integrity_summary"]["status"], "error")
        self.assertGreaterEqual(corrupt_summary["integrity_error_count"], 1)

    def test_vision_manifest_summary_reports_missing_file_refs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sample.json").write_text("{}", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "sample_output_dir": ".",
                        "samples": [
                            {
                                "sample_id": "bad",
                                "sample_ref": "vision_sample://sample.json",
                                "timestamp": 1.0,
                                "frame_id": "camera",
                                "raw_image": "missing_raw.jpg",
                                "annotated_image": "missing_annotated.jpg",
                                "json": "sample.json",
                                "context": {"event_type": "detection", "anomaly_type": ""},
                                "detection_count": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["sample_count"], 1)
        self.assertEqual(summary["integrity_summary"]["status"], "error")
        self.assertEqual(summary["integrity_error_count"], 1)
        self.assertEqual(summary["integrity_warning_count"], 1)
        self.assertEqual(summary["missing_file_ref_count"], 2)
        self.assertEqual(summary["file_counts"]["raw_image"]["missing"], 1)
        self.assertEqual(summary["file_counts"]["annotated_image"]["missing"], 1)
        self.assertEqual(summary["context_field_coverage"]["present"]["event_type"], 1)
        self.assertEqual(summary["context_field_coverage"]["missing"]["task_id"], 1)
        self.assertEqual(summary["missing_file_refs"][0]["field"], "raw_image")

    def test_vision_manifest_summary_handles_empty_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(
                json.dumps({"schema": "trashbot.vision_samples.v1", "samples": []}),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(summary["sample_count"], 0)
        self.assertEqual(summary["latest_sample_ref"], "")
        self.assertEqual(summary["latest_context"], {})
        self.assertEqual(summary["event_counts"], {})
        self.assertEqual(summary["review_queue_count"], 0)
        self.assertEqual(summary["review_queue"], [])
        self.assertEqual(summary["progress_summary"]["total"], 0)
        self.assertEqual(summary["progress_summary"]["decided"], 0)
        self.assertEqual(summary["progress_summary"]["pending"], 0)
        self.assertEqual(summary["progress_summary"]["coverage_rate"], 0.0)
        self.assertEqual(summary["decision_distribution"]["approved"]["count"], 0)
        self.assertEqual(summary["decision_distribution"]["approved"]["ratio"], 0.0)
        self.assertIsNone(summary["next_pending_sample"])
        self.assertEqual(summary["read_error"], "")

    def test_review_progress_uses_last_valid_decision_per_sample(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "manifest.json"
            decision_log_path = root / "review_decisions.jsonl"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "samples": [
                            {
                                "sample_id": "sample-1",
                                "sample_ref": "vision_sample://sample-1.json",
                                "timestamp": 1.0,
                                "context": {"event_type": "route_keyframe"},
                                "detection_count": 0,
                                "max_confidence": 0,
                            },
                            {
                                "sample_id": "sample-2",
                                "sample_ref": "vision_sample://sample-2.json",
                                "timestamp": 2.0,
                                "context": {"event_type": "anomaly"},
                                "detection_count": 0,
                                "max_confidence": 0,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            decision_log_path.write_text(
                (
                    json.dumps(
                        {
                            "decision_id": "d-1",
                            "sample_id": "sample-1",
                            "decision": "approved",
                            "timestamp": 100.0,
                        }
                    )
                    + "\n"
                    + json.dumps(
                        {
                            "decision_id": "d-2",
                            "sample_id": "sample-1",
                            "decision": "rejected",
                            "timestamp": 101.0,
                        }
                    )
                    + "\n"
                ),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref=str(manifest_path),
                review_decision_log_ref=str(decision_log_path),
                operator_status_file="/tmp/status.json",
            )

        review_log = payload["review_decision_log"]
        vision_samples = payload["vision_samples"]
        self.assertEqual(review_log["decision_count"], 2)
        self.assertEqual(review_log["sample_count"], 1)
        self.assertEqual(vision_samples["progress_summary"]["total"], 2)
        self.assertEqual(vision_samples["progress_summary"]["decided"], 1)
        self.assertEqual(vision_samples["progress_summary"]["pending"], 1)
        self.assertEqual(vision_samples["progress_summary"]["coverage_rate"], 0.5)
        self.assertEqual(vision_samples["decision_distribution"]["approved"]["count"], 0)
        self.assertEqual(vision_samples["decision_distribution"]["approved"]["ratio"], 0.0)
        self.assertEqual(vision_samples["decision_distribution"]["rejected"]["count"], 1)
        self.assertEqual(vision_samples["decision_distribution"]["rejected"]["ratio"], 1.0)
        self.assertEqual(vision_samples["decision_distribution"]["needs_retry"]["count"], 0)
        self.assertEqual(vision_samples["next_pending_sample"]["sample_id"], "sample-2")
        self.assertEqual(vision_samples["review_queue"][0]["last_decision"]["decision"], "rejected")


if __name__ == "__main__":
    unittest.main()

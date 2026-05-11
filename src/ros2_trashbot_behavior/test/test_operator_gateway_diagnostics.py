import unittest
import json
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
    summarize_hardware_proof,
    summarize_vision_manifest,
)
from ros2_trashbot_behavior.operator_gateway_http import ELEVATOR_ASSIST_SPEAKER_PROMPT


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
                        "hil_recipe": {"no_motion": "python3 scripts/hardware_smoke_wave_rover.py"},
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

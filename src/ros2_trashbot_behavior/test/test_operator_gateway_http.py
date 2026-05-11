import json
import socket
import sys
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path


BEHAVIOR_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BEHAVIOR_PACKAGE_ROOT))

from ros2_trashbot_behavior.operator_gateway_http import (
    ELEVATOR_ASSIST_SPEAKER_PROMPT,
    MockCloudStore,
    OPERATOR_PROMPTS,
    REMOTE_PROTOCOL_VERSION,
    make_handler,
    normalize_elevator_assist,
    operator_prompt_for_state,
    status_payload,
)


class FakeGateway:
    def __init__(self):
        self.mock_cloud_bearer_token = ""
        self.collect_status = 202
        self.collect_payload = {"state": "loaded_and_ready"}
        self.dropoff_status = 200
        self.dropoff_payload = {"state": "returning"}
        self.cancel_status = 202
        self.cancel_payload = {"state": "canceled"}
        self.review_queue_status = 200
        self.review_queue_payload = {
            "ok": True,
            "review_queue_count": 1,
            "review_queue": [
                {
                    "sample_id": "route-001",
                    "sample_ref": "vision_sample://20260510/route-001.json",
                    "reason": "route_keyframe_review",
                    "review_status": "pending",
                    "last_decision": None,
                }
            ],
            "progress_summary": {
                "total": 3,
                "decided": 2,
                "pending": 1,
                "coverage_rate": 0.6667,
            },
            "decision_distribution": {
                "approved": {"count": 1, "ratio": 0.5},
                "rejected": {"count": 1, "ratio": 0.5},
                "needs_retry": {"count": 0, "ratio": 0.0},
            },
            "next_pending_sample": {
                "sample_id": "route-001",
                "sample_ref": "vision_sample://20260510/route-001.json",
                "reason": "route_keyframe_review",
                "event_type": "route_keyframe",
                "timestamp": 1778356990.0,
            },
            "manifest_read_error": "",
        }
        self.review_submit_status = 201
        self.review_submit_payload = {
            "ok": True,
            "decision_id": "decision-1",
            "sample_id": "route-001",
            "decision": "approved",
            "stored_at": "2026-05-10T12:00:00Z",
        }
        self.last_collect = None
        self.last_confirm = None
        self.last_review_decision = None
        self.snapshot_payload = {
            "api_version": "slice2.operator.v1",
            "state": "waiting_for_trash",
            "message": "Waiting for trash.",
            "phone_copy": "Waiting for trash. Place trash on the robot, then start delivery.",
            "speaker_prompt": "Please place trash on the robot.",
            "can_collect": True,
            "can_confirm_dropoff": False,
            "can_cancel": False,
            "robot_pose": {
                "frame_id": "map",
                "x": 1.25,
                "y": -0.5,
                "yaw": 0.75,
                "updated_at": 10.0,
            },
            "robot_path": [
                {"x": 0.0, "y": 0.0, "yaw": 0.0, "updated_at": 9.0},
                {"x": 1.25, "y": -0.5, "yaw": 0.75, "updated_at": 10.0},
            ],
        }
        self.diagnostics_payload = {
            "api_version": "slice2.operator.v1",
            "state": "diagnostics_ready",
            "software_version": "0.1.0",
            "map_version": "map-a",
            "route_version": "route-a",
            "latest_status": self.snapshot_payload,
            "source": "software_proof",
            "evidence_ref": "/tmp/task.json",
            "failure_code": "timed_out",
            "human_intervention_required": True,
            "state_transition_history": [
                {
                    "timestamp": 1710000000.0,
                    "event": "timed_out",
                    "from_state": "navigating",
                    "to_state": "error",
                    "message": "timeout waiting for gate",
                }
            ],
            "last_task": {
                "task_record_path": "/tmp/task.json",
                "source": "software_proof",
                "evidence_ref": "/tmp/task.json",
                "error_code": "timed_out",
                "failure_code": "TIMED_OUT",
                "human_intervention_required": True,
                "state_transition_history": [
                    {
                        "timestamp": 1710000000.0,
                        "event": "timed_out",
                        "from_state": "navigating",
                        "to_state": "error",
                        "message": "timeout waiting for gate",
                    }
                ],
                "final_state": "error",
            },
            "failure": {
                "state": "failed",
                "message": "fixed route timed out",
                "error_code": "timed_out",
                "final_state": "error",
                "task_record_path": "/tmp/task.json",
                "source": "software_proof",
                "evidence_ref": "/tmp/task.json",
                "failure_code": "TIMED_OUT",
                "human_intervention_required": True,
                "state_transition_history": [
                    {
                        "timestamp": 1710000000.0,
                        "event": "timed_out",
                        "from_state": "navigating",
                        "to_state": "error",
                        "message": "timeout waiting for gate",
                    }
                ],
            },
            "log_refs": ["/tmp/trashbot.log"],
            "vision_sample_manifest_ref": "/tmp/vision/manifest.json",
            "vision_samples": {
                "manifest_ref": "/tmp/vision/manifest.json",
                "exists": True,
                "schema": "trashbot.vision_samples.v1",
                "sample_count": 3,
                "latest_sample_ref": "vision_sample://20260510/latest.json",
                "latest_timestamp": 1778357000.0,
                "latest_context": {"task_id": "task-7", "route_id": "route-a"},
                "latest_detection_count": 1,
                "latest_max_confidence": 88,
                "event_counts": {"route_keyframe": 2, "anomaly": 1},
                "review_queue_count": 2,
                "review_queue": [
                    {
                        "sample_id": "route-001",
                        "sample_ref": "vision_sample://20260510/route-001.json",
                        "timestamp": 1778356990.0,
                        "context": {"event_type": "route_keyframe", "route_id": "route-a"},
                        "event_type": "route_keyframe",
                        "detection_count": 0,
                        "max_confidence": 0,
                        "reason": "route_keyframe_review",
                        "review_status": "pending",
                        "last_decision": None,
                    },
                    {
                        "sample_id": "latest",
                        "sample_ref": "vision_sample://20260510/latest.json",
                        "timestamp": 1778357000.0,
                        "context": {"event_type": "anomaly", "route_id": "route-a"},
                        "event_type": "anomaly",
                        "detection_count": 1,
                        "max_confidence": 88,
                        "reason": "anomaly_sample",
                        "review_status": "pending",
                        "last_decision": None,
                    },
                ],
                "progress_summary": {
                    "total": 3,
                    "decided": 1,
                    "pending": 2,
                    "coverage_rate": 0.3333,
                },
                "decision_distribution": {
                    "approved": {"count": 1, "ratio": 1.0},
                    "rejected": {"count": 0, "ratio": 0.0},
                    "needs_retry": {"count": 0, "ratio": 0.0},
                },
                "next_pending_sample": {
                    "sample_id": "route-001",
                    "sample_ref": "vision_sample://20260510/route-001.json",
                    "reason": "route_keyframe_review",
                    "event_type": "route_keyframe",
                    "timestamp": 1778356990.0,
                },
                "read_error": "",
                "integrity_summary": {"status": "warning"},
                "integrity_error_count": 0,
                "integrity_warning_count": 1,
                "missing_file_ref_count": 1,
                "missing_file_refs": [
                    {
                        "field": "raw_image",
                        "resolved_path": "/tmp/vision/missing/raw.jpg",
                    }
                ],
                "integrity_errors": [],
                "integrity_warnings": ["annotated image coverage is incomplete"],
                "context_field_coverage": {
                    "present": {"task_id": 3, "route_id": 3},
                    "missing": {"checkpoint_id": 1},
                },
                "file_counts": {"raw_image": {"present": 2, "missing": 1}},
            },
            "route_proof_summary": {
                "coverage_rate": 0.5,
                "covered_checkpoints": 1,
                "total_checkpoints": 2,
                "missing_checkpoints": ["checkpoint_2"],
                "gate_status": "passed",
                "last_block_reason": "",
            },
            "route_proof_status": {
                "state": "insufficient_coverage",
                "reason": "missing checkpoints: checkpoint_2",
                "blocking_reason": "",
                "missing_fields": [],
                "source": "task_record.nav_results.evidence.route_proof_summary",
            },
            "elevator_assist": {
                "enabled": False,
                "mode": "",
                "state": "disabled",
                "phase": "",
                "requires_human_help": False,
                "reason": "",
                "target_floor": "",
                "phone_copy": "",
                "speaker_prompt": "",
                "evidence": {},
                "events": [],
            },
            "elevator_assist_status": {
                "state": "disabled",
                "reason": "elevator assisted delivery is not active",
                "next_step": "Continue the normal trash delivery flow.",
                "source": "",
            },
            "hardware_proof": {
                "status": "needs_hil",
                "artifact_ref": "/tmp/hardware-proof.json",
                "source_status": "software_proof_ready",
                "exists": True,
                "read_error": "",
                "summary": "Software proof exists, hardware-in-loop still required before treating the robot as validated.",
                "next_step": "Run the WAVE ROVER HIL recipe on a prepared robot.",
                "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                "risk_flags": [
                    {
                        "id": "hil_required",
                        "severity": "high",
                        "detail": "Offline proof does not validate real UART, motion, IMU, or battery.",
                    }
                ],
                "hil_recipe": {"no_motion": "python3 scripts/hardware_smoke_wave_rover.py"},
            },
            "operator_status_file": "/tmp/trashbot_operator_status.json",
        }

    def snapshot(self):
        return dict(self.snapshot_payload)

    def diagnostics(self):
        return dict(self.diagnostics_payload)

    def start_collection(self, target, trash_type=0):
        self.last_collect = {"target": target, "trash_type": trash_type}
        return self.collect_status, self.collect_payload

    def confirm_dropoff(self, accepted=True):
        self.last_confirm = accepted
        return self.dropoff_status, self.dropoff_payload

    def cancel_collection(self):
        return self.cancel_status, self.cancel_payload

    def vision_review_queue(self):
        return dict(self.review_queue_payload)

    def submit_review_decision(self, payload):
        self.last_review_decision = dict(payload)
        return self.review_submit_status, dict(self.review_submit_payload)


class OperatorGatewayHttpTest(unittest.TestCase):
    def setUp(self):
        self.gateway = FakeGateway()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.gateway))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)

    def request(self, method, path, body=None, headers=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        headers = dict(headers or {})
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8") if not isinstance(body, bytes) else body
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, payload

    def auth_request(self, method, path, body=None, token="phone-token"):
        return self.request(method, path, body, headers={"Authorization": f"Bearer {token}"})

    def test_status(self):
        status, payload = self.request("GET", "/api/status")

        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "waiting_for_trash")
        self.assertEqual(payload["phone_copy"], self.gateway.snapshot_payload["phone_copy"])
        self.assertEqual(payload["speaker_prompt"], self.gateway.snapshot_payload["speaker_prompt"])

    def test_status_payload_exposes_phone_and_speaker_copy_for_documented_states(self):
        for state, expected in OPERATOR_PROMPTS.items():
            with self.subTest(state=state):
                payload = status_payload(state)

                self.assertEqual(payload["phone_copy"], expected["phone_copy"])
                self.assertEqual(payload["speaker_prompt"], expected["speaker_prompt"])
                self.assertEqual(payload["elevator_assist"]["state"], "disabled")

    def test_status_payload_exposes_elevator_assist_copy_without_breaking_state_contract(self):
        payload = status_payload(
            "requesting_floor_help",
            "entered elevator",
            elevator_assist={
                "enabled": True,
                "mode": "dry_run",
                "phase": "requesting_floor_help",
                "requires_human_help": True,
                "target_floor": "1",
                "evidence": {"inside_elevator": True},
            },
        )

        self.assertEqual(payload["state"], "requesting_floor_help")
        self.assertEqual(payload["elevator_assist"]["phase"], "requesting_floor_help")
        self.assertEqual(payload["elevator_assist"]["target_floor"], "1")
        self.assertEqual(payload["elevator_assist"]["evidence"]["inside_elevator"], True)
        self.assertEqual(payload["speaker_prompt"], ELEVATOR_ASSIST_SPEAKER_PROMPT)
        self.assertIn("请求帮忙按楼层", payload["phone_copy"])

    def test_elevator_assist_can_be_inferred_from_elevator_state(self):
        payload = status_payload("waiting_target_floor", "waiting for target floor")

        self.assertTrue(payload["elevator_assist"]["enabled"])
        self.assertEqual(payload["elevator_assist"]["phase"], "waiting_target_floor")
        self.assertIn("等待目标楼层", payload["phone_copy"])
        self.assertEqual(
            normalize_elevator_assist({"state": "target_floor_unconfirmed"})["requires_human_help"],
            True,
        )

    def test_unknown_operator_state_falls_back_to_human_help_prompt(self):
        self.assertEqual(
            operator_prompt_for_state("unexpected_state"),
            OPERATOR_PROMPTS["needs_human_help"],
        )

    def test_diagnostics_endpoint_returns_remote_support_package(self):
        status, payload = self.request("GET", "/api/diagnostics")

        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "diagnostics_ready")
        self.assertEqual(payload["software_version"], "0.1.0")
        self.assertEqual(payload["map_version"], "map-a")
        self.assertEqual(payload["route_version"], "route-a")
        self.assertEqual(payload["latest_status"]["state"], "waiting_for_trash")
        self.assertEqual(payload["last_task"]["error_code"], "timed_out")
        self.assertEqual(payload["failure"]["final_state"], "error")
        self.assertEqual(payload["log_refs"], ["/tmp/trashbot.log"])
        self.assertEqual(payload["vision_sample_manifest_ref"], "/tmp/vision/manifest.json")
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["evidence_ref"], "/tmp/task.json")
        self.assertEqual(payload["failure_code"], "timed_out")
        self.assertEqual(payload["human_intervention_required"], True)
        self.assertEqual(payload["state_transition_history"][0]["event"], "timed_out")
        self.assertEqual(payload["vision_samples"]["sample_count"], 3)
        self.assertEqual(payload["vision_samples"]["latest_sample_ref"], "vision_sample://20260510/latest.json")
        self.assertEqual(payload["vision_samples"]["review_queue_count"], 2)
        self.assertEqual(payload["vision_samples"]["review_queue"][-1]["reason"], "anomaly_sample")
        self.assertEqual(payload["vision_samples"]["review_queue"][0]["review_status"], "pending")
        self.assertIsNone(payload["vision_samples"]["review_queue"][0]["last_decision"])
        self.assertEqual(payload["vision_samples"]["progress_summary"]["total"], 3)
        self.assertEqual(payload["vision_samples"]["progress_summary"]["decided"], 1)
        self.assertEqual(payload["vision_samples"]["progress_summary"]["pending"], 2)
        self.assertEqual(payload["vision_samples"]["decision_distribution"]["approved"]["count"], 1)
        self.assertEqual(payload["vision_samples"]["decision_distribution"]["approved"]["ratio"], 1.0)
        self.assertEqual(payload["vision_samples"]["decision_distribution"]["needs_retry"]["count"], 0)
        self.assertEqual(payload["vision_samples"]["next_pending_sample"]["sample_id"], "route-001")
        self.assertEqual(payload["vision_samples"]["integrity_summary"]["status"], "warning")
        self.assertEqual(payload["vision_samples"]["integrity_error_count"], 0)
        self.assertEqual(payload["vision_samples"]["integrity_warning_count"], 1)
        self.assertEqual(payload["vision_samples"]["missing_file_ref_count"], 1)
        self.assertEqual(payload["vision_samples"]["missing_file_refs"][0]["field"], "raw_image")
        self.assertEqual(payload["vision_samples"]["missing_file_refs"][0]["resolved_path"], "/tmp/vision/missing/raw.jpg")
        self.assertEqual(payload["vision_samples"]["integrity_warnings"], ["annotated image coverage is incomplete"])
        self.assertEqual(payload["vision_samples"]["context_field_coverage"]["present"]["task_id"], 3)
        self.assertEqual(payload["vision_samples"]["file_counts"]["raw_image"]["missing"], 1)
        self.assertEqual(payload["route_proof_summary"]["coverage_rate"], 0.5)
        self.assertEqual(payload["route_proof_summary"]["missing_checkpoints"], ["checkpoint_2"])
        self.assertEqual(payload["route_proof_status"]["state"], "insufficient_coverage")
        self.assertEqual(payload["route_proof_status"]["source"], "task_record.nav_results.evidence.route_proof_summary")
        self.assertEqual(payload["failure"]["source"], "software_proof")
        self.assertEqual(payload["failure"]["evidence_ref"], "/tmp/task.json")
        self.assertEqual(payload["failure"]["failure_code"], "TIMED_OUT")
        self.assertEqual(payload["failure"]["human_intervention_required"], True)
        self.assertEqual(payload["failure"]["state_transition_history"][0]["from_state"], "navigating")
        self.assertEqual(payload["hardware_proof"]["status"], "needs_hil")
        self.assertEqual(payload["hardware_proof"]["summary"], "Software proof exists, hardware-in-loop still required before treating the robot as validated.")
        self.assertEqual(payload["hardware_proof"]["next_step"], "Run the WAVE ROVER HIL recipe on a prepared robot.")
        self.assertEqual(payload["hardware_proof"]["read_error"], "")
        self.assertEqual(payload["hardware_proof"]["risk_flags"][0]["id"], "hil_required")
        self.assertEqual(payload["elevator_assist"]["state"], "disabled")
        self.assertEqual(payload["elevator_assist_status"]["state"], "disabled")

    def test_status_preserves_robot_location_snapshot_fields(self):
        self.gateway.snapshot_payload["robot_location"] = {
            "frame_id": "map",
            "x": 1.25,
            "y": -0.5,
            "yaw": 1.57,
            "source": "odom",
            "updated_at": 1710000000.0,
        }

        status, payload = self.request("GET", "/api/status")

        self.assertEqual(status, 200)
        self.assertEqual(payload["robot_location"]["frame_id"], "map")
        self.assertEqual(payload["robot_location"]["x"], 1.25)
        self.assertEqual(payload["robot_location"]["y"], -0.5)
        self.assertEqual(payload["robot_location"]["yaw"], 1.57)

    def get_text(self, path):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request("GET", path)
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        return response, body

    def test_index_page_contains_operator_controls(self):
        response, body = self.get_text("/")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "text/html; charset=utf-8")
        self.assertIn("Trashbot Operator", body)
        self.assertIn("Start Delivery", body)
        self.assertIn("Confirm Dropoff", body)
        self.assertIn("Cancel", body)
        self.assertIn("Diagnostics", body)
        self.assertIn("Phone control for trash delivery", body)
        self.assertIn("journeySteps", body)
        self.assertIn("Support Diagnostics", body)
        self.assertIn("phone_copy", body)
        self.assertIn("speaker_prompt", body)
        self.assertIn("showDiagnostics", body)
        self.assertIn("diagSoftware", body)
        self.assertIn("diagFailure", body)
        self.assertIn("diagSource", body)
        self.assertIn("diagFailureCode", body)
        self.assertIn("diagEvidenceRef", body)
        self.assertIn("diagHumanIntervention", body)
        self.assertIn("diagStateTransitionHistory", body)
        self.assertIn("diagStateTransitionHistoryList", body)
        self.assertIn("diagRecoveryHint", body)
        self.assertIn("diagVisionSamples", body)
        self.assertIn("diagLatestVisionSample", body)
        self.assertIn("diagReviewQueue", body)
        self.assertIn("diagNextReviewSample", body)
        self.assertIn("diagRouteProofState", body)
        self.assertIn("diagRouteProofReason", body)
        self.assertIn("diagRouteProofSource", body)
        self.assertIn("diagElevatorAssistState", body)
        self.assertIn("diagElevatorAssistPrompt", body)
        self.assertIn("diagElevatorAssistEvidence", body)
        self.assertIn("diagElevatorAssistNextStep", body)
        self.assertIn("diagVisionIntegrity", body)
        self.assertIn("diagVisionIntegrityBadge", body)
        self.assertIn("diagVisionIntegritySummary", body)
        self.assertIn("diagVisionIntegrityReasons", body)
        self.assertIn("diagVisionIntegrityAdvice", body)
        self.assertIn("diagHardwareProof", body)
        self.assertIn("diagHardwareProofBadge", body)
        self.assertIn("diagHardwareProofSummary", body)
        self.assertIn("diagHardwareProofNextStep", body)
        self.assertIn("diagHardwareProofReasons", body)
        self.assertIn("renderHardwareProof", body)
        self.assertIn("hardwareProofView", body)
        self.assertIn("hardware_proof", body)
        self.assertIn("software_proof", body)
        self.assertIn("needs_hil", body)
        self.assertIn("invalid_config", body)
        self.assertIn("read_error", body)
        self.assertIn("Software proof exists, hardware-in-loop still required", body)
        self.assertIn("renderVisionIntegrity", body)
        self.assertIn("visionIntegrityView", body)
        self.assertIn("vision_samples", body)
        self.assertIn("latest_sample_ref", body)
        self.assertIn("review_queue", body)
        self.assertIn("review_queue_count", body)
        self.assertIn("integrity_summary", body)
        self.assertIn("missing_file_refs", body)
        self.assertIn("context_field_coverage", body)
        self.assertIn("file_counts", body)
        self.assertIn("robotMap", body)
        self.assertIn("robot_pose", body)
        self.assertIn("robot_path", body)
        self.assertIn("waiting for /amcl_pose", body)
        self.assertIn("/api/status", body)
        self.assertIn("/api/diagnostics", body)
        self.assertIn("/api/vision/review-queue", body)
        self.assertIn("/api/vision/review-decisions", body)
        self.assertIn("/api/collect", body)
        self.assertIn("/api/dropoff/confirm", body)
        self.assertIn("/api/cancel", body)
        self.assertIn("Vision Review Queue", body)
        self.assertIn("Submit Review Decision", body)
        self.assertIn("reviewSampleSelect", body)
        self.assertIn("reviewDecisionSelect", body)
        self.assertIn("reviewCommentInput", body)
        self.assertIn("reviewProgressSummary", body)
        self.assertIn("reviewDecisionDistribution", body)
        self.assertIn("reviewNextPending", body)
        self.assertIn("route_proof_summary", body)
        self.assertIn("route_proof_status", body)
        self.assertIn("elevator_assist", body)
        self.assertIn("elevator_assist_status", body)
        self.assertIn("你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,", body)
        self.assertIn("reviewJumpPendingButton", body)
        self.assertIn("jumpToNextPending", body)
        self.assertIn("applyReviewProgress", body)
        self.assertIn("loadReviewQueue", body)
        self.assertIn("submitReviewDecision", body)
        self.assertIn("collectButton.disabled = !Boolean(payload.can_collect)", body)
        self.assertIn("dropoffButton.disabled = !Boolean(payload.can_confirm_dropoff)", body)
        self.assertIn("cancelButton.disabled = !Boolean(payload.can_cancel)", body)
        self.assertIn("catch (error)", body)
        self.assertIn('id="locationPanel"', body)
        self.assertIn('id="locationFrame"', body)
        self.assertIn('id="locationX"', body)
        self.assertIn('id="locationY"', body)
        self.assertIn('id="locationYaw"', body)
        self.assertIn("const location = payload.robot_location || payload.location", body)
        self.assertIn("locationPanel.hidden = !location", body)

    def test_index_html_route_serves_operator_page(self):
        response, body = self.get_text("/index.html")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "text/html; charset=utf-8")
        self.assertIn("Trashbot Operator", body)

    def test_collect_accepts_empty_body_and_query_target(self):
        status, _payload = self.request("POST", "/api/collect?target=trash_station")

        self.assertEqual(status, 202)
        self.assertEqual(self.gateway.last_collect["target"], "trash_station")
        self.assertEqual(self.gateway.last_collect["trash_type"], 0)

    def test_collect_accepts_json_body(self):
        status, _payload = self.request("POST", "/api/collect", {"target": "bin_a", "trash_type": 2})

        self.assertEqual(status, 202)
        self.assertEqual(self.gateway.last_collect, {"target": "bin_a", "trash_type": 2})

    def test_collect_propagates_busy_and_unavailable(self):
        self.gateway.collect_status = 409
        status, _payload = self.request("POST", "/api/collect")
        self.assertEqual(status, 409)

        self.gateway.collect_status = 503
        status, _payload = self.request("POST", "/api/collect")
        self.assertEqual(status, 503)

    def test_dropoff_confirm_and_cancel(self):
        status, _payload = self.request("POST", "/api/dropoff/confirm")
        self.assertEqual(status, 200)
        self.assertTrue(self.gateway.last_confirm)

        status, _payload = self.request("POST", "/api/cancel")
        self.assertEqual(status, 202)

    def test_dropoff_confirm_parses_string_false(self):
        status, _payload = self.request("POST", "/api/dropoff/confirm", {"accepted": "false"})

        self.assertEqual(status, 200)
        self.assertFalse(self.gateway.last_confirm)

    def test_dropoff_confirm_rejects_invalid_boolean(self):
        status, payload = self.request("POST", "/api/dropoff/confirm", {"accepted": "maybe"})

        self.assertEqual(status, 400)
        self.assertEqual(payload["state"], "bad_request")

    def test_review_queue_endpoint(self):
        status, payload = self.request("GET", "/api/vision/review-queue")

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["review_queue_count"], 1)
        self.assertEqual(payload["review_queue"][0]["sample_id"], "route-001")
        self.assertEqual(payload["review_queue"][0]["review_status"], "pending")
        self.assertEqual(payload["progress_summary"]["total"], 3)
        self.assertEqual(payload["progress_summary"]["decided"], 2)
        self.assertEqual(payload["decision_distribution"]["approved"]["count"], 1)
        self.assertEqual(payload["decision_distribution"]["rejected"]["ratio"], 0.5)
        self.assertEqual(payload["next_pending_sample"]["sample_id"], "route-001")

    def test_review_decision_submission_endpoint(self):
        body = {
            "sample_id": "route-001",
            "decision": "approved",
            "comment": "looks correct",
            "option": "route_keyframe_review",
        }
        status, payload = self.request("POST", "/api/vision/review-decisions", body)

        self.assertEqual(status, 201)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["sample_id"], "route-001")
        self.assertEqual(payload["decision"], "approved")
        self.assertEqual(self.gateway.last_review_decision["sample_id"], "route-001")
        self.assertEqual(self.gateway.last_review_decision["decision"], "approved")

    def test_mock_cloud_command_status_and_ack_loop(self):
        command = {
            "protocol_version": REMOTE_PROTOCOL_VERSION,
            "id": "cmd-0001",
            "type": "collect",
            "expires_at": 4102444800.0,
            "payload": {"target": "trash_station", "trash_type": 0},
        }

        status, payload = self.request("POST", "/robots/trashbot-001/commands", command)
        self.assertEqual(status, 201)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"]["protocol_version"], REMOTE_PROTOCOL_VERSION)
        self.assertEqual(payload["command"]["id"], "cmd-0001")
        self.assertEqual(payload["command"]["type"], "collect")
        self.assertEqual(payload["command"]["payload"]["target"], "trash_station")
        self.assertNotIn("/cmd_vel", json.dumps(payload))
        self.assertNotIn("serial", json.dumps(payload).lower())
        self.assertNotIn("baudrate", json.dumps(payload).lower())

        status, payload = self.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=")
        self.assertEqual(status, 200)
        self.assertEqual(payload["command"]["id"], "cmd-0001")

        status, payload = self.request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "state": "delivering",
                "message": "remote collect command accepted",
                "updated_at": time.time(),
                "diagnostics": {"network": "mock_cloud"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"]["state"], "delivering")
        self.assertEqual(payload["status"]["robot_id"], "trashbot-001")

        status, payload = self.request("GET", "/robots/trashbot-001/status")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"]["message"], "remote collect command accepted")
        self.assertTrue(payload["remote_readiness"]["remote_ready"])
        self.assertTrue(payload["remote_readiness"]["cloud_reachable"])
        self.assertFalse(payload["remote_readiness"]["status_stale"])
        self.assertEqual(payload["remote_readiness"]["auth_state"], "mock_not_required")
        self.assertEqual(payload["remote_readiness"]["retry_hint"], "wait_for_command_ack")

        status, payload = self.request(
            "POST",
            "/robots/trashbot-001/commands/cmd-0001/ack",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "state": "acked",
                "message": "collect command submitted",
                "updated_at": 1778256013.0,
                "result": {"behavior": "submitted"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["ack"]["state"], "acked")
        self.assertEqual(payload["ack"]["command_id"], "cmd-0001")
        self.assertEqual(payload["remote_readiness"]["last_command_ack"], "cmd-0001")
        self.assertEqual(payload["remote_readiness"]["retry_hint"], "ok")

        status, payload = self.request("GET", "/robots/trashbot-001/commands/cmd-0001/ack")
        self.assertEqual(status, 200)
        self.assertEqual(payload["ack"]["result"]["behavior"], "submitted")

        status, payload = self.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=cmd-0001")
        self.assertEqual(status, 200)
        self.assertIsNone(payload["command"])

    def test_mock_cloud_bearer_auth_gate_blocks_missing_or_wrong_token(self):
        self.gateway.mock_cloud_bearer_token = "phone-token"

        status, payload = self.request("GET", "/robots/trashbot-001/status")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"]["code"], "unauthorized")
        self.assertEqual(payload["remote_readiness"]["auth_state"], "auth_failed")
        self.assertEqual(payload["remote_readiness"]["degradation_state"], "auth_failed")
        self.assertEqual(payload["remote_readiness"]["retry_hint"], "check_auth")
        self.assertIn("手机登录已失效", payload["remote_readiness"]["safe_phone_copy"])
        self.assertNotIn("phone-token", json.dumps(payload, ensure_ascii=False))
        self.assertNotIn("Authorization", json.dumps(payload, ensure_ascii=False))

        status, payload = self.request(
            "POST",
            "/robots/trashbot-001/commands",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "id": "cmd-auth-blocked",
                "type": "collect",
                "expires_at": 4102444800.0,
                "payload": {"target": "trash_station"},
            },
            headers={"Authorization": "Bearer wrong-token"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["remote_readiness"]["auth_state"], "auth_failed")

    def test_mock_cloud_bearer_auth_gate_allows_authorized_phone_flow(self):
        self.gateway.mock_cloud_bearer_token = "phone-token"
        command = {
            "protocol_version": REMOTE_PROTOCOL_VERSION,
            "id": "cmd-auth-1",
            "type": "collect",
            "expires_at": 4102444800.0,
            "payload": {"target": "trash_station"},
        }

        status, payload = self.auth_request("POST", "/robots/trashbot-001/commands", command)
        self.assertEqual(status, 201)
        self.assertEqual(payload["remote_readiness"]["auth_state"], "authorized")
        self.assertEqual(payload["remote_readiness"]["degradation_state"], "status_stale")
        self.assertEqual(payload["remote_readiness"]["retry_hint"], "wait_for_robot_status")

        status, payload = self.auth_request(
            "POST",
            "/robots/trashbot-001/status",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "state": "delivering",
                "message": "remote collect command accepted",
                "updated_at": time.time(),
                "diagnostics": {"cloud_url": "https://user:secret@example.invalid/control"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["remote_readiness"]["auth_state"], "authorized")
        self.assertEqual(payload["remote_readiness"]["degradation_state"], "command_pending")
        self.assertEqual(payload["remote_readiness"]["retry_hint"], "wait_for_command_ack")
        self.assertNotIn("secret@example", json.dumps(payload, ensure_ascii=False))

        status, payload = self.auth_request(
            "POST",
            "/robots/trashbot-001/commands/cmd-auth-1/ack",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "state": "acked",
                "message": "submitted",
                "updated_at": time.time(),
                "result": {"behavior": "submitted", "bearer": "must-not-leak"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["remote_readiness"]["auth_state"], "authorized")
        self.assertEqual(payload["remote_readiness"]["degradation_state"], "ok")
        self.assertEqual(payload["remote_readiness"]["safe_phone_copy"], "手机远程控制通道可用，可以继续操作。")
        self.assertNotIn("must-not-leak", json.dumps(payload, ensure_ascii=False))

    def test_mock_cloud_persists_queue_status_ack_without_sensitive_fields(self):
        with tempfile.TemporaryDirectory() as td:
            state_path = Path(td) / "mock_cloud_state.json"
            store = MockCloudStore(state_path=state_path)
            store.submit_command(
                "trashbot-001",
                {
                    "protocol_version": REMOTE_PROTOCOL_VERSION,
                    "id": "cmd-persist-1",
                    "type": "collect",
                    "expires_at": 4102444800.0,
                    "payload": {
                        "target": "trash_station",
                        "token": "must-not-persist",
                        "ros_topic": "/cmd_vel",
                        "serial_port": "/dev/ttyUSB0",
                    },
                },
            )
            store.post_status(
                "trashbot-001",
                {
                    "protocol_version": REMOTE_PROTOCOL_VERSION,
                    "state": "delivering",
                    "message": "robot accepted command",
                    "updated_at": time.time(),
                    "diagnostics": {
                        "network": "mock_cloud",
                        "bearer_token": "must-not-persist",
                        "baudrate": 115200,
                    },
                },
            )
            store.post_ack(
                "trashbot-001",
                "cmd-persist-1",
                {
                    "protocol_version": REMOTE_PROTOCOL_VERSION,
                    "state": "acked",
                    "message": "submitted",
                    "updated_at": time.time(),
                    "result": {"behavior": "submitted", "authorization": "must-not-persist"},
                },
            )

            persisted = state_path.read_text(encoding="utf-8")
            self.assertIn("trashbot.mock_cloud_store.v1", persisted)
            self.assertIn("cmd-persist-1", persisted)
            self.assertNotIn("must-not-persist", persisted)
            self.assertNotIn("/cmd_vel", persisted)
            self.assertNotIn("ttyUSB", persisted)
            self.assertNotIn("baudrate", persisted)
            self.assertNotIn("command_index", persisted)
            self.assertNotIn("Authorization", persisted)
            self.assertNotIn("https://user:secret@", persisted)

            restored = MockCloudStore(state_path=state_path)
            next_payload = restored.next_command("trashbot-001", last_ack_id="")
            self.assertIsNone(next_payload["command"])
            status_payload = restored.get_status("trashbot-001")
            self.assertEqual(status_payload["status"]["state"], "delivering")
            self.assertEqual(status_payload["remote_readiness"]["last_command_ack"], "cmd-persist-1")
            self.assertTrue(status_payload["remote_readiness"]["queue_persisted"])

    def test_mock_cloud_status_defaults_to_phone_readable_not_ready(self):
        status, payload = self.request("GET", "/robots/trashbot-new/status")

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"]["state"], "unknown")
        self.assertFalse(payload["remote_readiness"]["remote_ready"])
        self.assertTrue(payload["remote_readiness"]["cloud_reachable"])
        self.assertTrue(payload["remote_readiness"]["status_stale"])
        self.assertEqual(payload["remote_readiness"]["retry_hint"], "wait_for_robot_status")
        self.assertEqual(payload["remote_readiness"]["auth_state"], "mock_not_required")

    def test_mock_cloud_next_command_uses_queue_order_not_string_order(self):
        for command_id in ("cmd-9", "cmd-10"):
            status, payload = self.request(
                "POST",
                "/robots/trashbot-001/commands",
                {
                    "protocol_version": REMOTE_PROTOCOL_VERSION,
                    "id": command_id,
                    "type": "collect",
                    "expires_at": 4102444800.0,
                    "payload": {"target": "trash_station"},
                },
            )
            self.assertEqual(status, 201)
            self.assertEqual(payload["command"]["id"], command_id)

        status, payload = self.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=")
        self.assertEqual(status, 200)
        self.assertEqual(payload["command"]["id"], "cmd-9")

        status, payload = self.request(
            "POST",
            "/robots/trashbot-001/commands/cmd-9/ack",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "state": "acked",
                "message": "first command submitted",
                "updated_at": 1778256013.0,
                "result": {"behavior": "submitted"},
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["ack"]["command_id"], "cmd-9")

        status, payload = self.request("GET", "/robots/trashbot-001/commands/next?last_ack_id=cmd-9")
        self.assertEqual(status, 200)
        self.assertEqual(payload["command"]["id"], "cmd-10")

    def test_mock_cloud_rejects_malformed_or_unsafe_commands(self):
        status, payload = self.request(
            "POST",
            "/robots/trashbot-001/commands",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "id": "cmd-bad",
                "type": "collect",
                "expires_at": 4102444800.0,
                "payload": {},
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "bad_request")
        self.assertIn("payload.target", payload["error"]["message"])

        status, payload = self.request(
            "POST",
            "/robots/trashbot-001/commands",
            {
                "protocol_version": REMOTE_PROTOCOL_VERSION,
                "id": "cmd-raw",
                "type": "cmd_vel",
                "expires_at": 4102444800.0,
                "payload": {"linear": 1.0},
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("type must be one of", payload["error"]["message"])

    def test_mock_cloud_ack_lookup_reports_missing_ack(self):
        status, payload = self.request("GET", "/robots/trashbot-001/commands/missing/ack")

        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "ack_not_found")

    def test_malformed_json_returns_400(self):
        status, payload = self.request("POST", "/api/collect", b"{bad")

        self.assertEqual(status, 400)
        self.assertEqual(payload["state"], "bad_request")

    def test_non_object_json_returns_400(self):
        status, payload = self.request("POST", "/api/collect", b"[]")

        self.assertEqual(status, 400)
        self.assertEqual(payload["state"], "bad_request")

    def test_malformed_content_length_returns_json_400(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=2) as sock:
            sock.sendall(
                b"POST /api/collect HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: nope\r\n"
                b"Connection: close\r\n"
                b"\r\n"
            )
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            response = b"".join(chunks).decode("utf-8", errors="replace")

        self.assertIn("400", response.splitlines()[0])
        self.assertIn('"state": "bad_request"', response)


if __name__ == "__main__":
    unittest.main()

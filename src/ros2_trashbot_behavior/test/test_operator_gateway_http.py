import json
import socket
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from ros2_trashbot_behavior.operator_gateway_http import (
    OPERATOR_PROMPTS,
    make_handler,
    operator_prompt_for_state,
    status_payload,
)


class FakeGateway:
    def __init__(self):
        self.collect_status = 202
        self.collect_payload = {"state": "loaded_and_ready"}
        self.dropoff_status = 200
        self.dropoff_payload = {"state": "returning"}
        self.cancel_status = 202
        self.cancel_payload = {"state": "canceled"}
        self.last_collect = None
        self.last_confirm = None
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
            "last_task": {
                "task_record_path": "/tmp/task.json",
                "error_code": "timed_out",
                "final_state": "error",
            },
            "failure": {
                "state": "failed",
                "message": "fixed route timed out",
                "error_code": "timed_out",
                "final_state": "error",
                "task_record_path": "/tmp/task.json",
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
                    },
                ],
                "read_error": "",
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

    def request(self, method, path, body=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        headers = {}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8") if not isinstance(body, bytes) else body
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, payload

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
        self.assertEqual(payload["vision_samples"]["sample_count"], 3)
        self.assertEqual(payload["vision_samples"]["latest_sample_ref"], "vision_sample://20260510/latest.json")
        self.assertEqual(payload["vision_samples"]["review_queue_count"], 2)
        self.assertEqual(payload["vision_samples"]["review_queue"][-1]["reason"], "anomaly_sample")

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
        self.assertIn("diagVisionSamples", body)
        self.assertIn("diagLatestVisionSample", body)
        self.assertIn("diagReviewQueue", body)
        self.assertIn("diagNextReviewSample", body)
        self.assertIn("vision_samples", body)
        self.assertIn("latest_sample_ref", body)
        self.assertIn("review_queue", body)
        self.assertIn("review_queue_count", body)
        self.assertIn("robotMap", body)
        self.assertIn("robot_pose", body)
        self.assertIn("robot_path", body)
        self.assertIn("waiting for /amcl_pose", body)
        self.assertIn("/api/status", body)
        self.assertIn("/api/diagnostics", body)
        self.assertIn("/api/collect", body)
        self.assertIn("/api/dropoff/confirm", body)
        self.assertIn("/api/cancel", body)
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

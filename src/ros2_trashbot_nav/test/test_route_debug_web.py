import json
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_nav.route_debug_web import HTML, make_handler  # noqa: E402


class RouteDebugWebTest(unittest.TestCase):
    def request_status(self, status_file):
        server = HTTPServer(("127.0.0.1", 0), make_handler(str(status_file)))
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            conn.request("GET", "/api/status")
            response = conn.getresponse()
            body = response.read().decode("utf-8")
            conn.close()
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
        return response.status, json.loads(body)

    def test_home_page_exposes_route_debug_panel_contract(self):
        for dom_id in (
            "routeStateBadge",
            "routeSummary",
            "routeProgress",
            "routeTarget",
            "visualGateStatus",
            "keyframePreflight",
            "routeFailureReason",
            "recentTask",
            "rawStatus",
        ):
            self.assertIn(f'id="{dom_id}"', HTML)

        for function_name in (
            "routeStateView",
            "visualGateView",
            "renderStatus",
            "renderKeyframePreflight",
        ):
            self.assertIn(f"function {function_name}", HTML)

        self.assertIn("overflow-wrap: anywhere", HTML)
        self.assertIn("Raw Status", HTML)

    def test_status_api_returns_missing_status_file_state(self):
        with tempfile.TemporaryDirectory() as td:
            status, payload = self.request_status(Path(td) / "missing.json")

        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "missing_status_file")
        self.assertIn("status_file", payload)

    def test_status_api_returns_invalid_status_file_state(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            status_file.write_text("{broken json", encoding="utf-8")

            status, payload = self.request_status(status_file)

        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "invalid_status_file")
        self.assertIn("error", payload)
        self.assertIn("status_file", payload)

    def test_status_api_passes_through_normal_status_json(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            payload = {
                "state": "waiting_visual_gate",
                "mode": "dry_run",
                "current_index": 1,
                "total": 3,
                "visual_gate_status": "waiting_camera_frame",
                "task_record_path": "/tmp/task-record.json",
            }
            status_file.write_text(json.dumps(payload), encoding="utf-8")

            status, returned = self.request_status(status_file)

        self.assertEqual(status, 200)
        self.assertEqual(returned, payload)


if __name__ == "__main__":
    unittest.main()

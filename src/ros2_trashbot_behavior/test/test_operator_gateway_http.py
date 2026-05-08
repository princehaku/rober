import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from ros2_trashbot_behavior.operator_gateway_http import make_handler


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

    def snapshot(self):
        return {
            "api_version": "slice2.operator.v1",
            "state": "waiting_for_trash",
            "message": "Waiting for trash.",
            "can_collect": True,
            "can_confirm_dropoff": False,
            "can_cancel": False,
        }

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

    def test_malformed_json_returns_400(self):
        status, payload = self.request("POST", "/api/collect", b"{bad")

        self.assertEqual(status, 400)
        self.assertEqual(payload["state"], "bad_request")

    def test_non_object_json_returns_400(self):
        status, payload = self.request("POST", "/api/collect", b"[]")

        self.assertEqual(status, 400)
        self.assertEqual(payload["state"], "bad_request")


if __name__ == "__main__":
    unittest.main()

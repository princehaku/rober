#!/usr/bin/env python3
"""PC route debug console 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_debug_web  # noqa: E402


class PcRouteDebugWebTest(unittest.TestCase):
    def sample_status(self, evidence_ref: str) -> dict:
        # 样例保留 route_progress/keyframe_preflight 主字段，覆盖 O2/O3 复盘口径。
        return {
            "state": "waiting_visual_gate",
            "route_contract_version": "fixed_route.v1",
            "route_file": "/tmp/private/fixed_route.yaml",
            "route_file_basename": "fixed_route.yaml",
            "route_id": "fixed_route",
            "checkpoint": 1,
            "current_index": 1,
            "total": 3,
            "evidence_ref": evidence_ref,
            "route_progress": {
                "route_id": "fixed_route",
                "route_file_basename": "fixed_route.yaml",
                "checkpoint_id": "fixed_route:001",
                "evidence_ref": evidence_ref,
                "checkpoint": 1,
                "current_index": 1,
                "total_checkpoints": 3,
                "target": {"x": 1.2, "y": 0.4, "qw": 1.0},
                "route_contract_version": "fixed_route.v1",
                "source": "fixed_route",
                "failure_code": "CHECKPOINT_MISSING",
            },
            "keyframe_preflight": {
                "enabled": True,
                "route_visual_ready": False,
                "total_checkpoints": 3,
                "loaded_keyframes": [{"index": 0}],
                "missing_keyframes": [{"index": 1, "reason": "missing"}],
                "invalid_keyframes": [],
            },
            "visual_gate_status": "keyframe_preflight_failed",
            "failure_code": "CHECKPOINT_MISSING",
            "failure_reason": "missing keyframes",
            "last_nav_result": "not_started",
        }

    def test_build_console_summary_exposes_required_boundary_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "route_replay_evidence.json")
            status_path = root / "fixed_route_status.json"
            task_path = root / "task_record.json"
            status_path.write_text(json.dumps(self.sample_status(evidence_ref)), encoding="utf-8")
            task_path.write_text(
                json.dumps(
                    {
                        "task_id": "task-1",
                        "final_status": "ERROR",
                        "failure_code": "CHECKPOINT_MISSING",
                        "evidence_ref": evidence_ref,
                        "route_progress": {"evidence_ref": evidence_ref},
                    }
                ),
                encoding="utf-8",
            )

            summary = route_debug_web.build_console_summary(str(status_path), str(task_path))

        self.assertEqual(summary["schema"], "trashbot.pc_route_debug_console.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_pc_route_debug_console_gate")
        self.assertEqual(summary["route_progress"]["checkpoint_id"], "fixed_route:001")
        self.assertEqual(summary["keyframe_preflight"]["visual_gate_status"], "keyframe_preflight_failed")
        self.assertEqual(summary["recent_task"]["task_id"], "task-1")
        self.assertFalse(summary["delivery_success"])
        self.assertIn("delivery_success", summary["not_proven"])

    def test_task_record_dir_selects_matching_evidence_ref(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "expected.ref")
            status_path = root / "fixed_route_status.json"
            task_dir = root / "tasks"
            task_dir.mkdir()
            status_path.write_text(json.dumps(self.sample_status(evidence_ref)), encoding="utf-8")
            (task_dir / "wrong.json").write_text(json.dumps({"evidence_ref": "/tmp/other"}), encoding="utf-8")
            (task_dir / "match.json").write_text(
                json.dumps({"task_id": "matched", "route_progress": {"evidence_ref": evidence_ref}}),
                encoding="utf-8",
            )

            summary = route_debug_web.build_console_summary(str(status_path), task_record_dir=str(task_dir))

        self.assertEqual(summary["recent_task"]["task_id"], "matched")
        self.assertEqual(summary["recent_task"]["lookup_status"], "found")

    def test_missing_status_json_is_blocked_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            summary = route_debug_web.build_console_summary(str(Path(td) / "missing.json"))

        self.assertEqual(summary["status"], "blocked_status_json_unavailable")
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertIn("real_hil_pass", summary["not_proven"])

    def test_html_and_api_do_not_expose_full_paths_or_hardware_terms(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            status_path = root / "status.json"
            evidence_ref = str(root / "route_evidence.json")
            payload = self.sample_status(evidence_ref)
            payload["last_error"] = "Traceback (most recent call last): /dev/ttyUSB0 baudrate=115200 WAVE ROVER"
            status_path.write_text(json.dumps(payload), encoding="utf-8")

            summary = route_debug_web.build_console_summary(str(status_path))
            page = route_debug_web.render_html(summary)

        encoded = json.dumps(summary, ensure_ascii=False) + page
        self.assertNotIn(str(root), encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("WAVE ROVER", encoded)

    def test_http_api_returns_same_schema(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            status_path = root / "status.json"
            status_path.write_text(json.dumps(self.sample_status(str(root / "evidence.json"))), encoding="utf-8")
            server = HTTPServer(("127.0.0.1", 0), route_debug_web.make_handler(str(status_path)))
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

        self.assertEqual(response.status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["schema"], "trashbot.pc_route_debug_console.v1")
        self.assertEqual(payload["console_controls"], "read_only")


if __name__ == "__main__":
    unittest.main()

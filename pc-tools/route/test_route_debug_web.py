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

    def sample_elevator_route_reconciliation(self, evidence_ref: str) -> dict:
        # 样例模拟上一轮 gate 输出，覆盖 artifact 与 phone_safe_summary 双入口。
        return {
            "schema": "trashbot.elevator_route_evidence_reconciliation.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_elevator_route_evidence_reconciliation_gate",
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched_same_evidence_ref",
            "evidence_ref": evidence_ref,
            "reconciliation_verdict": "reconciled_not_proven",
            "source_states": {
                "elevator_rehearsal": {"status": "ready_for_operator_review_not_proven"},
                "route_completion": {"status": "completed_not_proven"},
            },
            "materials_status": {
                "missing_materials": [],
                "mismatch_reasons": [],
                "unsafe_copy_detected": False,
                "success_claimed_by_input": False,
                "control_claimed_by_input": False,
            },
            "operator_next_steps": ["Compare this reconciliation with Robot diagnostics and mobile read-only summary."],
            "phone_safe_summary": {
                "schema": "trashbot.elevator_route_evidence_reconciliation_summary.v1",
                "schema_version": 1,
                "source": "software_proof",
                "evidence_boundary": "software_proof_docker_elevator_route_evidence_reconciliation_gate",
                "status": "reconciled_not_proven",
                "reconciliation_verdict": "reconciled_not_proven",
                "same_evidence_ref_required": True,
                "same_evidence_ref_status": "matched_same_evidence_ref",
                "evidence_ref": evidence_ref,
                "source_states": {
                    "elevator_status": "ready_for_operator_review_not_proven",
                    "route_completion_verdict": "completed_not_proven",
                },
                "missing_materials_count": 0,
                "mismatch_reasons_count": 0,
                "operator_next_steps": ["Keep this as software proof only."],
                "not_proven": ["real_elevator_door_state", "real_nav2_fixed_route_run", "delivery_success"],
                "safe_copy": "Elevator-route reconciliation metadata only; delivery_success=false.",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_elevator_door_state", "real_nav2_fixed_route_run", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
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
        self.assertEqual(
            summary["evidence_boundary"],
            "software_proof_docker_pc_route_debug_console_gate",
        )
        self.assertEqual(summary["route_progress"]["checkpoint_id"], "fixed_route:001")
        self.assertEqual(summary["keyframe_preflight"]["visual_gate_status"], "keyframe_preflight_failed")
        self.assertEqual(summary["recent_task"]["task_id"], "task-1")
        self.assertEqual(summary["route_elevator_reconciliation"]["lookup_status"], "not_provided")
        self.assertFalse(summary["delivery_success"])
        self.assertIn("delivery_success", summary["not_proven"])

    def test_elevator_route_reconciliation_artifact_is_exposed_as_safe_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "same-evidence.json")
            status_path = root / "fixed_route_status.json"
            reconciliation_path = root / "elevator_route_evidence_reconciliation.json"
            status_path.write_text(json.dumps(self.sample_status(evidence_ref)), encoding="utf-8")
            reconciliation_path.write_text(
                json.dumps(self.sample_elevator_route_reconciliation(evidence_ref)),
                encoding="utf-8",
            )

            summary = route_debug_web.build_console_summary(
                str(status_path),
                elevator_route_reconciliation=str(reconciliation_path),
            )
            page = route_debug_web.render_html(summary)

        reconciliation = summary["route_elevator_reconciliation"]
        self.assertEqual(reconciliation["lookup_status"], "found")
        self.assertEqual(reconciliation["source_schema"], "trashbot.elevator_route_evidence_reconciliation_summary.v1")
        self.assertEqual(reconciliation["reconciliation_verdict"], "reconciled_not_proven")
        self.assertEqual(
            reconciliation["evidence_boundary"],
            "software_proof_docker_pc_route_elevator_console_integration_gate",
        )
        self.assertEqual(
            reconciliation["source_evidence_boundary"],
            "software_proof_docker_elevator_route_evidence_reconciliation_gate",
        )
        self.assertEqual(reconciliation["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertEqual(reconciliation["evidence_ref"], "file:same-evidence.json")
        self.assertIn("real_elevator_door_state", reconciliation["not_proven"])
        self.assertFalse(reconciliation["delivery_success"])
        self.assertFalse(reconciliation["primary_actions_enabled"])
        self.assertIn("Elevator Route Reconciliation", page)
        self.assertNotIn(str(root), json.dumps(summary, ensure_ascii=False) + page)

    def test_elevator_route_reconciliation_blocks_unsupported_unsafe_and_success_claims(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            status_path = root / "fixed_route_status.json"
            status_path.write_text(json.dumps(self.sample_status("run-unsafe")), encoding="utf-8")
            unsupported_path = root / "unsupported.json"
            unsupported_path.write_text(json.dumps({"schema": "trashbot.wrong.v1"}), encoding="utf-8")
            unsafe_path = root / "unsafe.json"
            unsafe_payload = self.sample_elevator_route_reconciliation("run-unsafe")
            unsafe_payload["operator_next_steps"] = ["Read /dev/ttyUSB0 then publish /cmd_vel"]
            unsafe_path.write_text(json.dumps(unsafe_payload), encoding="utf-8")
            success_path = root / "success.json"
            success_payload = self.sample_elevator_route_reconciliation("run-success")
            success_payload["phone_safe_summary"]["safe_copy"] = "delivery success completed"
            success_path.write_text(json.dumps(success_payload), encoding="utf-8")

            unsupported = route_debug_web.build_console_summary(
                str(status_path),
                elevator_route_reconciliation=str(unsupported_path),
            )
            unsafe = route_debug_web.build_console_summary(
                str(status_path),
                elevator_route_reconciliation=str(unsafe_path),
            )
            success = route_debug_web.build_console_summary(
                str(status_path),
                elevator_route_reconciliation=str(success_path),
            )

        self.assertEqual(unsupported["route_elevator_reconciliation"]["lookup_status"], "unsupported_schema")
        self.assertEqual(unsafe["route_elevator_reconciliation"]["lookup_status"], "unsafe_copy")
        self.assertEqual(success["route_elevator_reconciliation"]["lookup_status"], "success_claim")
        encoded = json.dumps(unsafe, ensure_ascii=False) + json.dumps(success, ensure_ascii=False)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertIn("delivery_success", success["route_elevator_reconciliation"]["not_proven"])

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
            reconciliation_path = root / "elevator_route_evidence_reconciliation.json"
            reconciliation_path.write_text(
                json.dumps(self.sample_elevator_route_reconciliation(str(root / "evidence.json"))),
                encoding="utf-8",
            )
            server = HTTPServer(
                ("127.0.0.1", 0),
                route_debug_web.make_handler(
                    str(status_path),
                    elevator_route_reconciliation=str(reconciliation_path),
                ),
            )
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
        self.assertEqual(payload["route_elevator_reconciliation"]["lookup_status"], "found")


if __name__ == "__main__":
    unittest.main()

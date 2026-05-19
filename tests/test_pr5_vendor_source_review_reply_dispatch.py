#!/usr/bin/env python3
"""pr5_vendor_source_review_reply_dispatch 的顶层验收测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式导入同源 CLI，避免复制 dispatch 逻辑。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_vendor_source_review_reply_dispatch as gate  # noqa: E402


def _valid_packet_summary() -> dict:
    # 这个 fixture 只模拟上一轮 sanitized summary，不包含 raw GitHub body 或硬件日志。
    return {
        "schema": "trashbot.pr5_vendor_source_review_packet_summary.v1",
        "schema_version": 1,
        "source": "software_proof",
        "thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "proof_boundary": "software_proof_docker_pr5_vendor_source_review_packet_gate",
        "overall_status": "not_proven",
        "hardware_material_status": "hardware_material_pending",
        "vendor_source_boundary": {
            "entrypoint": "docs/vendor/VENDOR_INDEX.md",
            "review_thread_id": "PRRT_kwDOSWB9286CJ3tX",
            "source_refs": [
                "docs/vendor/VENDOR_INDEX.md",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
            ],
            "lidar_tof_boundary": "hardware_material_pending_not_proven",
        },
        "missing_materials": list(gate.REQUIRED_MISSING_MATERIALS),
        "not_proven": list(gate.REQUIRED_NOT_PROVEN),
        "next_required_evidence": [
            "Provide reviewed 2D LiDAR SKU/source/receipt or purchase-order material.",
            "Provide reviewed ToF SKU/source/channel-count material.",
            "Run a separate HIL-entry review after real materials exist.",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


class Pr5VendorSourceReviewReplyDispatchTest(unittest.TestCase):
    def test_live_packet_summary_generates_manual_reply_dispatch(self):
        artifact, summary, markdown, exit_code = gate.build_pr5_vendor_source_review_reply_dispatch()

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.pr5_vendor_source_review_reply_dispatch.v1")
        self.assertEqual(summary["schema"], "trashbot.pr5_vendor_source_review_reply_dispatch_summary.v1")
        self.assertEqual(artifact["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["proof_boundary"], "software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", markdown)
        self.assertIn("2D LiDAR", markdown)
        self.assertIn("ToF", markdown)
        self.assertIn("delivery_success=false", markdown)
        self.assertIn("primary_actions_enabled=false", markdown)

    def test_packet_without_vendor_index_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            packet = _valid_packet_summary()
            packet["vendor_source_boundary"]["source_refs"] = []
            packet_path = Path(td) / "packet_summary.json"
            packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
            artifact, summary, _markdown, exit_code = gate.build_pr5_vendor_source_review_reply_dispatch(packet_path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["reply_status"], "blocked_unsupported_pr5_vendor_source_review_packet_summary")
        self.assertIn("vendor_source_boundary.vendor_index_ref_missing", artifact["blocked_reasons"])
        self.assertEqual(summary["overall_status"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_packet_success_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            packet = _valid_packet_summary()
            packet["delivery_success"] = True
            packet_path = Path(td) / "packet_summary.json"
            packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
            artifact, _summary, _markdown, exit_code = gate.build_pr5_vendor_source_review_reply_dispatch(packet_path)

        self.assertEqual(exit_code, 2)
        self.assertIn("delivery_success.not_false", artifact["blocked_reasons"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_missing_packet_still_emits_blocked_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            artifact, summary, markdown, exit_code = gate.build_pr5_vendor_source_review_reply_dispatch(Path(td) / "missing.json")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["reply_status"], "blocked_missing_pr5_vendor_source_review_packet_summary")
        self.assertIn("packet_summary.missing", artifact["blocked_reasons"])
        self.assertIn("not_proven", markdown)
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")

    def test_cli_writes_artifact_summary_and_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet_path = root / "packet_summary.json"
            packet_path.write_text(json.dumps(_valid_packet_summary(), ensure_ascii=False), encoding="utf-8")
            artifact_path = root / "dispatch.json"
            summary_path = root / "dispatch_summary.json"
            markdown_path = root / "reply.md"

            exit_code = gate.main(
                [
                    "--packet-summary",
                    str(packet_path),
                    "--output",
                    str(artifact_path),
                    "--summary-output",
                    str(summary_path),
                    "--markdown-output",
                    str(markdown_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            # CLI 产物只代表软件证明；reply-ready 不能被消费成真实硬件或控制证明。
            self.assertEqual(artifact["reply_status"], "ready_for_manual_github_review_reply_not_proven")
            self.assertEqual(summary["evidence_status"], "not_proven")
            self.assertFalse(summary["delivery_success"])
            self.assertFalse(summary["primary_actions_enabled"])
            self.assertIn("hardware_material_pending", markdown)


if __name__ == "__main__":
    unittest.main()

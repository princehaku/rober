#!/usr/bin/env python3
"""o1_lidar_scan_proof_collector 只读 proof 归并测试。"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "o1_lidar_scan_proof_collector.py"


def load_collector_module():
    """按脚本路径加载 collector，避免依赖上车端安装状态。"""
    spec = importlib.util.spec_from_file_location("o1_lidar_scan_proof_collector_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("o1_lidar_scan_proof_collector.py module spec was not created")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class O1LidarScanProofCollectorTest(unittest.TestCase):
    def test_fresh_upper_status_is_not_treated_as_blocker(self) -> None:
        """8787 已返回 fresh_scan_proof_observed 时，collector 不应保留旧 blocker。"""
        module = load_collector_module()

        def fake_path_exists(path: str) -> bool:
            return path in {
                module.ROS_HUMBLE_SETUP,
                module.ROBER_INSTALL_SETUP,
                "/dev/ttyACM0",
            }

        def fake_path_describer(path: str) -> dict[str, Any]:
            return {"path": path, "exists": path == "/dev/ttyACM0"}

        def fake_url_fetcher(url: str, timeout_s: float) -> dict[str, Any]:
            if url.endswith("/api/radar/status"):
                return {
                    "ok": True,
                    "status": "loaded",
                    "payload": {
                        "scan_status": "fresh_scan_proof_observed",
                        "latest_scan_proof": {
                            "fresh_while_observed": True,
                            "all_required_observations_observed": True,
                            "scan_once_observed": True,
                            "scan_hz_observed": True,
                            "scan_hz_average_rate_hz": 18.5,
                            "raw_packet_once_observed": True,
                            "tf_observed": True,
                        },
                    },
                }
            return {"ok": True, "status": "loaded", "payload": {"status": "ok"}}

        def fake_command_runner(command: str, timeout_s: float) -> dict[str, Any]:
            if "command -v ros2" in command:
                return {"ok": True, "returncode": 0, "stdout_preview": "/opt/ros/humble/bin/ros2\n", "stderr_preview": ""}
            return {"ok": False, "returncode": 124, "stdout_preview": "", "stderr_preview": "timeout"}

        payload = module.build_probe_payload(
            expect_existing_topics=True,
            path_exists=fake_path_exists,
            path_describer=fake_path_describer,
            url_fetcher=fake_url_fetcher,
            command_runner=fake_command_runner,
        )

        self.assertEqual(payload["proof"]["status"], "scan_once_hz_raw_packet_tf_observed")
        self.assertTrue(payload["proof"]["all_required_observations_observed"])
        self.assertTrue(payload["proof"]["runtime_summary_fallback_used"])
        self.assertNotIn("upper_api_scan_not_proven", [item["code"] for item in payload["blockers"]])


if __name__ == "__main__":
    unittest.main()

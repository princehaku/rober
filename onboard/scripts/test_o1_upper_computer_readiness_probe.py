#!/usr/bin/env python3
"""O1 上位机 readiness probe 的 LiDAR ROS2 bootstrap 单元测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import o1_upper_computer_readiness_probe as probe  # noqa: E402


class CommandStub:
    """用关键字匹配替代真实 shell，确保单测不依赖本机 ROS2 或 Docker。"""

    def __init__(self, responses: dict[str, dict] | None = None) -> None:
        self.commands: list[str] = []
        self.responses = responses or {}

    def __call__(self, command: str, _: float) -> dict:
        self.commands.append(command)
        for key, value in self.responses.items():
            if key in command:
                payload = dict(value)
                payload.setdefault("command", command)
                return payload
        return {"command": command, "returncode": 1, "ok": False, "stdout_preview": "", "stderr_preview": "missing"}


def fake_globber(pattern: str) -> list[str]:
    """只模拟 STC/ttyACM 雷达候选，不读取真实 /dev。"""
    if pattern == "/dev/ttyACM*":
        return ["/dev/ttyACM0"]
    if pattern == "/dev/serial/by-id/*":
        return ["/dev/serial/by-id/usb-STC_STC_USB_Serial-if00"]
    return []


def empty_globber(_: str) -> list[str]:
    """模拟未接入 LiDAR 的上位机。"""
    return []


def serial_summary_with_lidar() -> dict:
    return probe.summarize_serial_candidates(globber=fake_globber)


def serial_summary_without_lidar() -> dict:
    return probe.summarize_serial_candidates(globber=empty_globber)


def make_repo(*, install: bool = True, driver: bool = True, entrypoint: bool = True) -> tuple[tempfile.TemporaryDirectory, Path]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    package_root = root / "onboard" / "src" / "ros2_trashbot_hardware"
    module_root = package_root / "ros2_trashbot_hardware"
    module_root.mkdir(parents=True)
    if driver:
        (module_root / "lidar_driver.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    setup_body = (
        "'lidar_driver = ros2_trashbot_hardware.lidar_driver:main',\n"
        if entrypoint
        else "'esp32_bridge = ros2_trashbot_hardware.esp32_bridge:main',\n"
    )
    (package_root / "setup.py").write_text(setup_body, encoding="utf-8")
    if install:
        install_bin = root / "onboard" / "install" / "ros2_trashbot_hardware" / "lib" / "ros2_trashbot_hardware"
        install_bin.mkdir(parents=True)
        (install_bin / "lidar_driver").write_text("#!/bin/sh\n", encoding="utf-8")
    return temp, root


class O1UpperComputerReadinessProbeTest(unittest.TestCase):
    def test_payload_exposes_lidar_ros2_bootstrap_fail_closed(self) -> None:
        runner = CommandStub()

        payload = probe.build_probe_payload(globber=fake_globber, argv=["--once-json"], command_runner=runner)

        bootstrap = payload["lidar_ros2_bootstrap"]
        self.assertEqual(bootstrap["status"], "runtime_missing")
        self.assertIn("runtime_missing", bootstrap["blocker_codes"])
        self.assertFalse(bootstrap["safe_to_control"])
        self.assertFalse(bootstrap["sends_wave_rover_t_commands"])
        self.assertFalse(bootstrap["calls_base_manual"])
        self.assertFalse(bootstrap["publishes_cmd_vel"])
        self.assertEqual(bootstrap["commands_if_ready"], [])

    def test_bootstrap_status_repo_missing_after_runtime_ok(self) -> None:
        runner = CommandStub({"command -v ros2": {"returncode": 0, "ok": True, "stdout_preview": "/opt/ros/humble/bin/ros2\n"}})

        bootstrap = probe.build_lidar_ros2_bootstrap_readiness(
            repo_root=None,
            onboard_path=Path("/missing/onboard"),
            humble_setup_exists=True,
            install_setup_exists=False,
            serial_summary=serial_summary_with_lidar(),
            command_runner=runner,
        )

        self.assertEqual(bootstrap["status"], "repo_missing")
        self.assertIn("repo_missing", bootstrap["blocker_codes"])

    def test_bootstrap_status_install_missing_after_repo_ok(self) -> None:
        temp, root = make_repo(install=False)
        self.addCleanup(temp.cleanup)
        runner = CommandStub({"command -v ros2": {"returncode": 0, "ok": True, "stdout_preview": "/opt/ros/humble/bin/ros2\n"}})

        bootstrap = probe.build_lidar_ros2_bootstrap_readiness(
            repo_root=root,
            onboard_path=root / "onboard",
            humble_setup_exists=True,
            install_setup_exists=False,
            serial_summary=serial_summary_with_lidar(),
            command_runner=runner,
        )

        self.assertEqual(bootstrap["status"], "install_missing")
        self.assertIn("install_missing", bootstrap["blocker_codes"])
        self.assertNotIn("driver_missing", bootstrap["blocker_codes"])

    def test_bootstrap_status_driver_missing_when_entrypoint_absent(self) -> None:
        temp, root = make_repo(install=True, driver=True, entrypoint=False)
        self.addCleanup(temp.cleanup)
        runner = CommandStub({"command -v ros2": {"returncode": 0, "ok": True, "stdout_preview": "/opt/ros/humble/bin/ros2\n"}})

        bootstrap = probe.build_lidar_ros2_bootstrap_readiness(
            repo_root=root,
            onboard_path=root / "onboard",
            humble_setup_exists=True,
            install_setup_exists=True,
            serial_summary=serial_summary_with_lidar(),
            command_runner=runner,
        )

        self.assertEqual(bootstrap["status"], "driver_missing")
        self.assertIn("driver_missing", bootstrap["blocker_codes"])

    def test_bootstrap_status_lidar_device_missing_after_driver_ok(self) -> None:
        temp, root = make_repo(install=True)
        self.addCleanup(temp.cleanup)
        runner = CommandStub({"command -v ros2": {"returncode": 0, "ok": True, "stdout_preview": "/opt/ros/humble/bin/ros2\n"}})

        bootstrap = probe.build_lidar_ros2_bootstrap_readiness(
            repo_root=root,
            onboard_path=root / "onboard",
            humble_setup_exists=True,
            install_setup_exists=True,
            serial_summary=serial_summary_without_lidar(),
            command_runner=runner,
        )

        self.assertEqual(bootstrap["status"], "lidar_device_missing")
        self.assertIn("lidar_device_missing", bootstrap["blocker_codes"])

    def test_bootstrap_ready_commands_are_lidar_only_and_readonly_topics(self) -> None:
        temp, root = make_repo(install=True)
        self.addCleanup(temp.cleanup)
        runner = CommandStub({"command -v ros2": {"returncode": 0, "ok": True, "stdout_preview": "/opt/ros/humble/bin/ros2\n"}})

        bootstrap = probe.build_lidar_ros2_bootstrap_readiness(
            repo_root=root,
            onboard_path=root / "onboard",
            humble_setup_exists=True,
            install_setup_exists=True,
            serial_summary=serial_summary_with_lidar(),
            command_runner=runner,
        )

        self.assertEqual(bootstrap["status"], "ready_for_scan_bootstrap")
        self.assertEqual(bootstrap["blocker_codes"], [])
        joined = "\n".join(bootstrap["commands_if_ready"])
        self.assertIn("ros2 topic echo --once /scan", joined)
        self.assertIn("ros2 run ros2_trashbot_hardware lidar_driver", joined)
        for forbidden in ("/api/base/manual", "/cmd_vel", '"T":1', '"T":13', '"T":130', '"T":131'):
            self.assertNotIn(forbidden, joined)
        self.assertFalse(bootstrap["safe_to_control"])
        self.assertFalse(bootstrap["sends_motion_commands"])
        self.assertFalse(bootstrap["starts_ros2_driver"])

    def test_runtime_remediation_points_to_executable_bootstrap_scripts(self) -> None:
        temp, root = make_repo(install=False)
        self.addCleanup(temp.cleanup)
        runner = CommandStub()

        plan = probe.build_ros2_runtime_remediation_plan(
            repo_root=root,
            onboard_path=root / "onboard",
            humble_setup_exists=False,
            install_setup_exists=False,
            lidar_candidates=["/dev/ttyACM0"],
            command_runner=runner,
        )

        self.assertEqual(plan["next_action"], "install_or_provide_ros2_humble_runtime")
        self.assertIn("o1_ros2_humble_arm64_bootstrap.sh", plan["next_command"])
        forbidden = ("/api/base/manual", "/cmd_vel", '"T":1', '"T":13', '"T":130', '"T":131', "/dev/ttyS5")
        for item in forbidden:
            self.assertNotIn(item, plan["next_command"])

    def test_topics_not_running_points_to_lidar_smoke_script(self) -> None:
        temp, root = make_repo(install=True)
        self.addCleanup(temp.cleanup)
        runner = CommandStub(
            {
                "docker version": {"returncode": 0, "ok": True, "stdout_preview": "arm64\n"},
                "command -v ros2": {"returncode": 0, "ok": True, "stdout_preview": "/opt/ros/humble/bin/ros2\n"},
                "ros2 topic list": {"returncode": 0, "ok": True, "stdout_preview": "/parameter_events\n/rosout\n"},
            }
        )

        plan = probe.build_ros2_runtime_remediation_plan(
            repo_root=root,
            onboard_path=root / "onboard",
            humble_setup_exists=True,
            install_setup_exists=True,
            lidar_candidates=["/dev/ttyACM0"],
            command_runner=runner,
        )

        self.assertEqual(plan["next_action"], "start_lidar_driver_no_motion")
        self.assertIn("o1_lidar_ros2_scan_smoke.sh", plan["next_command"])
        self.assertIn("--serial-port /dev/ttyACM0", plan["next_command"])

    def test_lidar_smoke_script_rejects_base_uart_and_broad_by_path(self) -> None:
        script = (SCRIPT_DIR / "o1_lidar_ros2_scan_smoke.sh").read_text(encoding="utf-8")

        self.assertIn('if [[ "$SERIAL_PORT" == "/dev/ttyS5" ]]', script)
        self.assertIn("/dev/serial/by-id/*STC*", script)
        self.assertNotIn("/dev/serial/by-path/*)", script)


if __name__ == "__main__":
    unittest.main()

"""LiDAR lifecycle shell 脚本的安全边界测试。

这些测试只跑不需要 ROS2 的 status/guard 分支，避免本地开发机依赖真实雷达。
真实 start/stop HIL 由远端 smoke 负责，本文件锁定脚本不能误碰底盘 UART。
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "o1_lidar_lifecycle.sh"


class LidarLifecycleScriptTests(unittest.TestCase):
    """验证 lifecycle 脚本的可解析状态和危险串口拒绝逻辑。"""

    @contextmanager
    def _fake_running_holder(
        self,
        runtime_dir: Path,
        *,
        serial_baudrate: int | None,
        serial_port: str = "/dev/ttyACM0",
    ):
        """用真实存活 PID + 隔离 proc fixture 模拟 manager，避免测试启动 ROS2。"""
        # sleep 只提供可被 kill -0 观察的存活 PID，不打开串口也不加载 ROS2。
        holder = subprocess.Popen(["sleep", "30"])
        # 隔离 proc root 避免测试伪造系统 /proc，同时让脚本走与真机相同的 NUL argv 解析。
        proc_root = runtime_dir / "proc"
        proc_pid = proc_root / str(holder.pid)
        proc_pid.mkdir(parents=True)
        argv = [
            # 脚本名与 __run 两项共同满足受管 manager 身份检查。
            "bash",
            "/root/rober/onboard/scripts/o1_lidar_lifecycle.sh",
            "__run",
            "--serial-port",
            serial_port,
        ]
        if serial_baudrate is not None:
            # baudrate=None 专门模拟 holder argv 缺 current 字段的降级分支。
            argv.extend(["--serial-baudrate", str(serial_baudrate)])
        # /proc/cmdline 使用 NUL 分隔；保留尾 NUL 可贴近 Linux 真机格式。
        (proc_pid / "cmdline").write_bytes(b"\0".join(item.encode() for item in argv) + b"\0")
        (runtime_dir / "lidar_lifecycle.pid").write_text(str(holder.pid), encoding="utf-8")
        try:
            yield holder.pid, proc_root
        finally:
            # fixture 必须回收 sleep，避免单元测试给开发机留下后台进程。
            holder.terminate()
            try:
                holder.wait(timeout=2)
            except subprocess.TimeoutExpired:
                holder.kill()
                holder.wait(timeout=2)

    def _status(self, runtime_dir: Path, proc_root: Path | None = None) -> dict:
        """统一执行只读 status，并在失败时把 stderr 留给断言定位。"""
        # 复制环境可保留开发机必要 PATH，同时只覆盖测试专用 proc root。
        env = os.environ.copy()
        if proc_root is not None:
            env["ROBER_LIDAR_PROC_ROOT"] = str(proc_root)
        completed = subprocess.run(
            # 所有测试只调用 status；start/stop 的串口 guard 另有独立测试覆盖。
            ["bash", str(SCRIPT_PATH), "status", "--runtime-dir", str(runtime_dir)],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        # stdout 必须是单一 JSON object，额外日志会让这里立即失败。
        return json.loads(completed.stdout)

    def test_status_returns_structured_json_when_not_running(self) -> None:
        """status 不应打开 ROS2 或串口，本地也必须能返回结构化 JSON。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                ["bash", str(SCRIPT_PATH), "status", "--runtime-dir", temp_dir],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        # 没有 PID/holder 时 lifecycle 本身必须报告 stopped。
        self.assertFalse(payload["running"])
        self.assertIsNone(payload["pid"])
        self.assertEqual("/dev/ttyACM0", payload["serial_port"])
        # 静态 230400 只能留在 reference 字段，top-level current 必须为空。
        self.assertIsNone(payload["baudrate"])
        self.assertEqual("unknown", payload["baudrate_readback_source"])
        self.assertEqual("unknown_no_current_readback", payload["baudrate_readback_status"])
        self.assertEqual(230400, payload["vendor_reference_baudrate"])
        self.assertEqual("reference_only_not_current", payload["vendor_reference_status"])
        # readback 不能借状态查询扩大底盘、路线或 HIL 权限。
        self.assertFalse(payload["uses_base_uart"])
        self.assertFalse(payload["publishes_cmd_vel"])
        # delivery/route/HIL 三项不能由静态状态读取产生任何成功暗示。
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["route_execution_success"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["hil_pass"])
        self.assertIn("/dev/ttyS5", payload["blocked_base_uart"])

    def test_status_reads_running_holder_150000_as_current(self) -> None:
        """running manager argv 是最高优先级 current 证据，不能被默认 230400 覆盖。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            with self._fake_running_holder(runtime_dir, serial_baudrate=150000) as (pid, proc_root):
                payload = self._status(runtime_dir, proc_root)

        # running/PID 必须对应 fake holder，不能从 persisted status 倒推。
        self.assertTrue(payload["running"])
        self.assertEqual(pid, payload["pid"])
        self.assertEqual(150000, payload["baudrate"])
        self.assertEqual("running_holder.argv.--serial-baudrate", payload["baudrate_readback_source"])
        # 150000 与 vendor 230400 不同只标 reference conflict，不否定 holder current。
        self.assertEqual("current_with_reference_conflict", payload["baudrate_readback_status"])
        self.assertEqual(150000, payload["holder"]["baudrate"])
        # vendor reference 独立保留，便于现场同时看到两层事实。
        self.assertEqual(230400, payload["vendor_reference_baudrate"])

    def test_status_holder_wins_and_marks_conflicting_persisted_and_diagnostics(self) -> None:
        """holder 与其他 current 候选冲突时，以 holder 为准并显式暴露冲突。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            with self._fake_running_holder(runtime_dir, serial_baudrate=150000) as (pid, proc_root):
                # persisted/diagnostics 都故意写 230400，验证 holder 的裁决优先级。
                (runtime_dir / "lidar_lifecycle_status.json").write_text(
                    json.dumps({"running": True, "pid": pid, "baudrate": 230400}),
                    encoding="utf-8",
                )
                (runtime_dir / "lidar_driver_diagnostics.json").write_text(
                    json.dumps({"config": {"serial_port": "/dev/ttyACM0", "serial_baudrate": 230400}}),
                    encoding="utf-8",
                )
                payload = self._status(runtime_dir, proc_root)

        # current 采用 holder 150000，同时保留两个 230400 候选作为冲突证据。
        self.assertEqual(150000, payload["baudrate"])
        self.assertEqual("running_holder.argv.--serial-baudrate", payload["baudrate_readback_source"])
        self.assertEqual("current_with_candidate_conflict", payload["baudrate_readback_status"])
        self.assertEqual({230400}, {item["baudrate"] for item in payload["baudrate_conflicts"]})

    def test_status_accepts_pid_matched_persisted_current_when_holder_argv_lacks_baudrate(self) -> None:
        """受管 PID 一致时，持久状态可在 holder argv 缺字段时提供 current readback。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            with self._fake_running_holder(runtime_dir, serial_baudrate=None) as (pid, proc_root):
                # PID 与当前 holder 一致，因此 persisted 150000 可作为第二优先级 current。
                (runtime_dir / "lidar_lifecycle_status.json").write_text(
                    json.dumps(
                        {
                            "running": True,
                            "pid": pid,
                            "serial_port": "/dev/ttyACM0",
                            "baudrate": 150000,
                        }
                    ),
                    encoding="utf-8",
                )
                payload = self._status(runtime_dir, proc_root)

        # 来源必须明确为 PID-matched status，不能错误标成 holder argv。
        self.assertEqual(150000, payload["baudrate"])
        self.assertEqual("persisted_status.pid_matched.baudrate", payload["baudrate_readback_source"])
        self.assertEqual("current_with_reference_conflict", payload["baudrate_readback_status"])

    def test_status_marks_pid_mismatch_persisted_status_stale(self) -> None:
        """旧 PID 的 150000 不能作为 current；证据必须保留为 stale 候选。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            with self._fake_running_holder(runtime_dir, serial_baudrate=None) as (pid, proc_root):
                # 使用 pid+1 制造 stale 文件，但保持 baudrate 看似合理以锁定 PID gate。
                (runtime_dir / "lidar_lifecycle_status.json").write_text(
                    json.dumps({"running": True, "pid": pid + 1, "baudrate": 150000}),
                    encoding="utf-8",
                )
                payload = self._status(runtime_dir, proc_root)

        # 合理数值不能绕过 PID mismatch，top-level current 仍必须 fail closed。
        self.assertIsNone(payload["baudrate"])
        self.assertEqual("unknown_no_current_readback", payload["baudrate_readback_status"])
        stale = next(item for item in payload["baudrate_candidates"] if "pid_mismatch" in item["source"])
        # stale 候选保留用于定位，但 trusted_current 必须为 false。
        self.assertEqual("pid_mismatch_stale", stale["status"])
        self.assertFalse(stale["trusted_current"])

    def test_status_falls_back_to_loaded_driver_diagnostics(self) -> None:
        """holder argv 缺 baudrate 时，running driver diagnostics 可提供 current readback。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            with self._fake_running_holder(runtime_dir, serial_baudrate=None) as (_, proc_root):
                # serial 形态模拟 Upper API/新 diagnostics，另一个测试间接覆盖 config 形态冲突。
                (runtime_dir / "lidar_driver_diagnostics.json").write_text(
                    json.dumps({"serial": {"serial_port": "/dev/ttyACM0", "serial_baudrate": 150000}}),
                    encoding="utf-8",
                )
                payload = self._status(runtime_dir, proc_root)

        # running lifecycle 下 diagnostics 可兜底，但仍要标 current/reference 分层。
        self.assertEqual(150000, payload["baudrate"])
        self.assertEqual("driver_diagnostics.serial.serial_baudrate", payload["baudrate_readback_source"])
        self.assertEqual("current_with_reference_conflict", payload["baudrate_readback_status"])
        # diagnostics fallback 也不能提升 safe_to_control。
        self.assertFalse(payload["safe_to_control"])

    def test_start_rejects_wave_rover_base_uart_before_runtime(self) -> None:
        """即使本机没有 ROS2，/dev/ttyS5 也必须先被 guard 拒绝。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "bash",
                    str(SCRIPT_PATH),
                    "start",
                    "--serial-port",
                    "/dev/ttyS5",
                    "--runtime-dir",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

        # guard 必须在 ROS2 runtime 缺失前返回专用 41，证明底盘 UART 被硬拒绝。
        self.assertEqual(41, completed.returncode)
        self.assertIn("refusing WAVE ROVER base UART /dev/ttyS5", completed.stderr)

    def test_start_rejects_non_lidar_serial_path(self) -> None:
        """普通 USB 串口不能被当成 LiDAR，避免误接底盘或其他设备。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "bash",
                    str(SCRIPT_PATH),
                    "start",
                    "--serial-port",
                    "/dev/ttyUSB0",
                    "--runtime-dir",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

        # 非 LiDAR-looking 路径使用独立 40，现场能与 WAVE ROVER 专用拒绝区分。
        self.assertEqual(40, completed.returncode)
        self.assertIn("refusing non-LiDAR-looking serial port", completed.stderr)


if __name__ == "__main__":
    unittest.main()

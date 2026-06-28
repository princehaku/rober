import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o11_nav2_lifecycle.sh"


class O11Nav2LifecycleScriptTests(unittest.TestCase):
    def test_run_manager_records_launch_exit_status(self) -> None:
        """Nav2 launch 失败必须写 failed/stopped，不能永久留下 stale running。"""
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("set +e\n  ros2 launch ros2_trashbot_bringup autonomous.launch.py", source)
        self.assertIn('local launch_rc=$?', source)
        self.assertIn('write_status_file false "" "failed" "Nav2 stack-only launch exited with rc=$launch_rc; see $LAUNCH_LOG"', source)
        self.assertIn('rm -f "$PID_FILE"', source)

    def test_status_overwrites_stale_running_file_when_pid_is_gone(self) -> None:
        """status 分支发现 pid 不存在时必须覆盖旧 running status 文件。"""
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn('write_status_file false "" "stopped" "Nav2 lifecycle not running"', source)
        self.assertIn('emit_status_file_or_fallback false "" "stopped" "Nav2 lifecycle not running"', source)

    def test_start_preflights_nav2_bringup_dependency(self) -> None:
        """Nav2 bringup 缺失要写结构化根因，不能只把错误埋进 launch log。"""
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn('NAV2_REQUIRED_PACKAGES=("nav2_bringup")', source)
        self.assertIn('ros2 pkg prefix "$package"', source)
        self.assertIn('"failed_missing_dependency"', source)
        self.assertIn("ros-humble-nav2-bringup", source)

    def test_start_reuses_existing_bridge_and_lidar_when_auto_detected(self) -> None:
        """Nav2 start 默认 auto 避免重复打开底盘 UART 或 LiDAR 串口。"""
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn('BASE_ENABLED="${ROBER_NAV2_BASE_ENABLED:-auto}"', source)
        self.assertIn('LIDAR_ENABLED="${ROBER_NAV2_LIDAR_ENABLED:-auto}"', source)
        self.assertIn('ros_node_exists "/esp32_bridge" || port_has_holder "$BASE_PORT"', source)
        self.assertIn('scan_has_publisher || port_has_holder "$LIDAR_SERIAL_PORT"', source)
        self.assertIn('base_enabled:="$BASE_ENABLED"', source)
        self.assertIn('lidar_enabled:="$LIDAR_ENABLED"', source)
        self.assertIn('lidar_serial_port:="$LIDAR_SERIAL_PORT"', source)
        self.assertIn('static_laser_tf_enabled:="$STATIC_LASER_TF_ENABLED"', source)


if __name__ == "__main__":
    unittest.main()

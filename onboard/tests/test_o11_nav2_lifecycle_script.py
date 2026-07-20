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

    def test_sensor_owned_mode_records_zero_base_open_and_owned_scan_material(self) -> None:
        """sensor-owned start 必须记录 UART 差集、LiDAR holder 与 `/scan` publisher 归属。"""
        source = SCRIPT.read_text(encoding="utf-8")

        # 模式名是 status 的语义入口，不允许只依赖布尔位推导。
        self.assertIn('SENSOR_MODE="sensor_owned_scan"', source)
        # base 和 LiDAR 都必须保留 pre/post holder 快照，才能算归属差集。
        self.assertIn('BASE_UART_PRE_HOLDER_PIDS="$(port_holder_pids "$BASE_PORT")"', source)
        self.assertIn('BASE_UART_POST_HOLDER_PIDS="$(port_holder_pids "$BASE_PORT")"', source)
        self.assertIn('LIDAR_SERIAL_PRE_HOLDER_PIDS="$(port_holder_pids "$LIDAR_SERIAL_PORT")"', source)
        self.assertIn('LIDAR_SERIAL_POST_HOLDER_PIDS="$(port_holder_pids "$LIDAR_SERIAL_PORT")"', source)
        # new-open 必须是当前差集，不能使用历史计数器。
        self.assertIn('"base_uart_new_open_count": len(base_new_observed)', source)
        # sticky 记录函数必须真实存在，不能只新增一个永远为空的 JSON 字段。
        self.assertIn('record_base_uart_new_holders', source)
        # running 门禁必须消费 sticky 集合，确保瞬时 holder 也会阻止成功。
        self.assertIn('[[ -z "$BASE_UART_NEW_OPEN_PIDS_OBSERVED"', source)
        # PID 归一化不能依赖额外进程，避免最小板端镜像缺工具时丢失证据。
        self.assertNotIn('| xargs', source[source.index("record_base_uart_new_holders"):source.index("new_lidar_holders_are_owned")])
        # 脚本必须把观测 PID 写入 status，便于 Upper 与离线 artifact 复核具体 holder。
        self.assertIn('"base_uart_new_open_pids_observed": base_new_observed', source)
        self.assertIn('"lidar_serial_new_open_count": len(set(lidar_post) - set(lidar_pre))', source)
        # LiDAR holder 必须逐 PID 验收 PGID 归属。
        self.assertIn('new_lidar_holders_are_owned "$OWNER_PROCESS_GROUP_PID"', source)
        # publisher ownership 需要与 holder ownership 联合，不能只看 topic 存在。
        self.assertIn('SCAN_PUBLISHER_OWNED="true"', source)
        self.assertIn('"physical_motion": False', source)

    def test_sensor_conflicts_fail_closed_without_broad_kill(self) -> None:
        """已有 holder/publisher/Nav2 owner 必须拒绝，stop 只能命中 PID 文件归属进程组。"""
        source = SCRIPT.read_text(encoding="utf-8")

        # 三种冲突均必须有独立根因，便于现场精确路由。
        self.assertIn('"failed_scan_publisher_conflict"', source)
        self.assertIn('"failed_lidar_holder_conflict"', source)
        self.assertIn('"failed_owned_runtime_conflict"', source)
        self.assertIn('kill -TERM "-$pid"', source)
        self.assertIn('kill -KILL "-$pid"', source)
        self.assertNotIn("pkill", source)
        self.assertNotIn("killall", source)
        self.assertIn('"broad_kill_used": False', source)

    def test_o11_launch_keeps_base_disabled_and_sensor_mode_explicit(self) -> None:
        """O11 只接受 base-disabled 两模式，并把 reuse flag 传入 owned manager。"""
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn('if [[ "$BASE_ENABLED" != "false" ]]', source)
        self.assertIn('"$LIDAR_ENABLED" == "true" && "$REUSE_EXISTING_SCAN" == "false"', source)
        self.assertIn('"$LIDAR_ENABLED" == "false" && "$REUSE_EXISTING_SCAN" == "true"', source)
        self.assertIn('--reuse-existing-scan "$REUSE_EXISTING_SCAN"', source)
        self.assertIn('nav2_stack_only:=true', source)
        self.assertIn('base_enabled:="$BASE_ENABLED"', source)
        self.assertIn('lidar_enabled:="$LIDAR_ENABLED"', source)


if __name__ == "__main__":
    unittest.main()

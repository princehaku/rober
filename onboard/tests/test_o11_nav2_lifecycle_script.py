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


if __name__ == "__main__":
    unittest.main()

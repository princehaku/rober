import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import field_route_evidence_preflight as preflight  # noqa: E402


class FieldRouteEvidencePreflightTest(unittest.TestCase):
    def test_dry_run_packet_is_not_proven_and_safe(self):
        # dry-run 必须可在无 ROS2/SSH 的开发机运行，且不能被误判为现场成功。
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "packet.json"
            rc = preflight.main(["--mode", "local", "--dry-run", "--output", str(output)])

            self.assertEqual(rc, 0)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["schema"], preflight.SCHEMA)
            self.assertEqual(packet["status"], "dry_run_template_only_not_proven")
            self.assertTrue(packet["not_proven"])
            self.assertFalse(packet["delivery_success"])
            self.assertFalse(packet["primary_actions_enabled"])
            rendered = json.dumps(packet, ensure_ascii=False)
            self.assertIn("learn.launch.py", rendered)
            self.assertIn("fixed_route_autonomy", rendered)
            self.assertNotIn("/cmd_vel", rendered)

    def test_ssh_command_uses_argv_and_expected_port(self):
        # SSH 命令必须保持 argv 数组，避免把目标和端口拼进本地 shell 字符串。
        command = preflight.build_ssh_command("root@192.168.1.11", 37878, "true", 5)

        self.assertEqual(command[0], "ssh")
        self.assertIn("-p", command)
        self.assertEqual(command[command.index("-p") + 1], "37878")
        self.assertEqual(command[-2], "root@192.168.1.11")
        self.assertEqual(command[-1], "true")
        templates = preflight.topic_smoke_templates("root@192.168.1.11", 37878)
        self.assertIn("ssh -p 37878 root@192.168.1.11", templates[0]["command"])

    def test_ssh_unreachable_still_writes_evidence_packet(self):
        # SSH 不可达时也必须交付 JSON，不允许把本轮退化成纯网络 blocker。
        fake_result = {
            "command": ["ssh", "..."],
            "returncode": 255,
            "stdout": "",
            "stderr": "No route to host",
            "timed_out": False,
        }
        with mock.patch.object(preflight, "run_command", return_value=fake_result):
            with tempfile.TemporaryDirectory() as tmpdir:
                output = Path(tmpdir) / "ssh_packet.json"
                rc = preflight.main(
                    [
                        "--mode",
                        "ssh",
                        "--ssh-target",
                        "root@192.168.1.11",
                        "--ssh-port",
                        "37878",
                        "--timeout-s",
                        "5",
                        "--output",
                        str(output),
                    ]
                )
                packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(packet["status"], "blocked_ssh_unreachable")
        self.assertEqual(packet["blocked_reason"], "blocked_ssh_unreachable")
        self.assertTrue(packet["not_proven"])
        self.assertIn("topic_smoke", packet["commands"])

    def test_secret_redaction_covers_common_fields(self):
        # 安全摘要需要覆盖常见凭证字段，防止错误日志进入证据包后泄露。
        raw = "Bearer abc.def token=123 password:456 /Users/example/.ssh/id_rsa"
        redacted = preflight.redact_secret(raw)

        self.assertIn("Bearer <redacted>", redacted)
        self.assertIn("token=<redacted>", redacted)
        self.assertIn("password:<redacted>", redacted)

    def test_local_real_missing_setup_fails_closed_before_ros2(self):
        # 没有 setup.bash 时先报环境 blocker，避免继续执行可能误导的 ROS2 检查。
        args = preflight.parse_args(["--mode", "local", "--output", "/tmp/unused.json"])
        with mock.patch.object(preflight, "SETUP_CANDIDATES", ["/definitely/missing/setup.bash"]):
            checks, status = preflight.local_real_checks(args)

        self.assertEqual(status, "blocked_setup_missing")
        self.assertFalse(checks["setup_candidates"]["ok"])


if __name__ == "__main__":
    unittest.main()

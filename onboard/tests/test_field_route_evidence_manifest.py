import json
import tempfile
import unittest
from pathlib import Path

import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import field_route_evidence_manifest as manifest  # noqa: E402


def write_text(path: Path, text: str) -> None:
    # fixture 文件统一从这里创建，保证每个 artifact 都是非空证据材料。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_complete_fixture(root: Path) -> None:
    # 本地完整 fixture 只证明 artifact gate 逻辑，不伪装成真实现场路线成功。
    write_text(root / "map.yaml", "image: map.pgm\nresolution: 0.05\n")
    write_text(root / "route.csv", "x,y,yaw\n0,0,0\n1,0,0\n")
    write_text(root / "keyframes" / "0001.json", '{"x": 0, "y": 0}\n')
    write_text(root / "route_bag" / "metadata.yaml", "rosbag2_bagfile_information:\n")
    write_text(root / "fixed_route_replay.jsonl", '{"event":"start"}\n{"event":"done"}\n')


def write_preflight(path: Path, status: str, *, dry_run: bool = False, blocked_reason=None) -> None:
    # manifest 只读取 preflight 摘要字段，避免测试依赖完整 ROS2/SSH packet。
    payload = {
        "schema": "trashbot.board_field_evidence_preflight.v1",
        "status": status,
        "dry_run": dry_run,
        "blocked_reason": blocked_reason,
        "mode": "ssh",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class FieldRouteEvidenceManifestTest(unittest.TestCase):
    def test_complete_local_fixture_passes_artifact_gate_but_not_delivery(self):
        # SSH blocker 不能第三次吞掉研发；完整 fixture 应能证明 manifest 软件路径。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            preflight = Path(tmpdir) / "preflight.json"
            make_complete_fixture(root)
            write_preflight(preflight, "blocked_ssh_unreachable", blocked_reason="blocked_ssh_unreachable")

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_complete",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(packet["schema"], manifest.SCHEMA)
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["not_proven"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])
        self.assertEqual(packet["blocked_reason"], "blocked_ssh_unreachable")
        self.assertTrue(packet["artifacts"]["keyframes"]["present"])
        self.assertGreater(packet["artifacts"]["rosbag"]["size_bytes"], 0)
        self.assertEqual(packet["artifact_status"], "gated")
        self.assertEqual(packet["manifest_gate"]["status"], "gated")

    def test_missing_artifact_fails_closed_with_nonzero_rc(self):
        # 缺 route/replay 等必需材料时必须非零退出，方便 CI 或现场脚本 fail fast。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "missing"
            output = Path(tmpdir) / "manifest.json"
            preflight = Path(tmpdir) / "preflight.json"
            write_text(root / "map.yaml", "image: map.pgm\n")
            write_preflight(preflight, manifest.READY_PREFLIGHT_STATUS)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_missing")
        self.assertEqual(packet["blocked_reason"], "missing_required_artifact")
        self.assertFalse(packet["artifacts"]["route_csv"]["present"])

    def test_empty_keyframes_fail_closed(self):
        # keyframes 目录存在但没有图片/JSON 时仍是空证据，不能被目录名误导。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "manifest.json"
            preflight = root / "preflight.json"
            make_complete_fixture(root)
            for child in (root / "keyframes").iterdir():
                child.unlink()
            write_text(root / "keyframes" / "README.txt", "not a keyframe\n")
            write_preflight(preflight, manifest.READY_PREFLIGHT_STATUS)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_empty")
        self.assertEqual(packet["artifacts"]["keyframes"]["reason"], "no_keyframe_file")

    def test_dry_run_preflight_keeps_not_proven_even_with_complete_artifacts(self):
        # dry-run preflight 是模板证明；artifact 完整也不能解除 not_proven。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "complete"
            output = Path(tmpdir) / "manifest.json"
            preflight = Path(tmpdir) / "dry_preflight.json"
            make_complete_fixture(root)
            write_preflight(preflight, "dry_run_template_only_not_proven", dry_run=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root),
                    "--preflight-json",
                    str(preflight),
                    "--output",
                    str(output),
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["not_proven"])
        self.assertFalse(packet["safe_to_control"])
        self.assertEqual(packet["blocked_reason"], "dry_run_template_only_not_proven")

    def test_ssh_command_is_read_only_and_uses_expected_port(self):
        # SSH 模式只运行远端 python 只读扫描，不包含 ros2 launch、cmd_vel 或导航命令。
        command = manifest.build_ssh_command("root@192.168.1.11", 37878, "/tmp/artifacts", 5)
        rendered = " ".join(command)

        self.assertEqual(command[0], "ssh")
        self.assertIn("-p", command)
        self.assertEqual(command[command.index("-p") + 1], "37878")
        self.assertEqual(command[-2], "root@192.168.1.11")
        self.assertIn("python3 -c", command[-1])
        self.assertIn("/tmp/artifacts", command[-1])
        self.assertNotIn("/cmd_vel", rendered)
        self.assertNotIn("ros2 launch", rendered)


if __name__ == "__main__":
    unittest.main()

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
    write_text(root / "map.pgm", "P5 1 1 255 0")
    write_text(root / "route.csv", "x,y,yaw\n0,0,0\n1,0,0\n")
    write_text(root / "manifest.json", '{"schema":"trashbot.vision_samples.v1","samples":[]}\n')
    write_text(root / "keyframes" / "0001.json", '{"x": 0, "y": 0}\n')
    write_text(root / "route_bag" / "metadata.yaml", "rosbag2_bagfile_information:\n")
    write_text(root / "fixed_route_replay.jsonl", '{"event":"start"}\n{"event":"done"}\n')


def make_real_bundle_fixture(root: Path, *, include_route_bag: bool = True) -> None:
    # 真实现场 bundle 走 map/route/keyframes 分层目录；测试必须覆盖这条 intake 路径。
    write_text(root / "map" / "trashbot_dynamic_odom_tf_map.yaml", "image: trashbot_dynamic_odom_tf_map.pgm\nresolution: 0.05\n")
    write_text(root / "map" / "trashbot_dynamic_odom_tf_map.pgm", "P5 1 1 255 0")
    write_text(root / "route" / "manifest.json", '{"schema":"trashbot.vision_samples.v1","samples":[{"sample_id":"route_keyframe_001"}]}\n')
    write_text(
        root / "route" / "route.csv",
        "\n".join(
            [
                "index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame",
                "0,1781025357,570312018,map,0.0,0.0,0.0,0.0,0.0,0.0,1.0,000.jpg",
                "1,1781025531,470292985,map,0.01050082056,0.0,0.0,0.0,0.0,0.0,1.0,001.jpg",
                "2,1781025531,820688003,map,0.0210126711,0.0,0.0,0.0,0.0,0.0,1.0,002.jpg",
            ]
        )
        + "\n",
    )
    write_text(root / "route" / "keyframes" / "000.json", '{"sample_ref":"vision_sample://keyframes/000.json"}\n')
    write_text(root / "route" / "keyframes" / "000.jpg", "jpg-000\n")
    write_text(root / "route" / "keyframes" / "001.json", '{"sample_ref":"vision_sample://keyframes/001.json"}\n')
    write_text(root / "route" / "keyframes" / "001.jpg", "jpg-001\n")
    write_text(root / "route" / "keyframes" / "002.json", '{"sample_ref":"vision_sample://keyframes/002.json"}\n')
    write_text(root / "route" / "keyframes" / "002.jpg", "jpg-002\n")
    write_text(
        root / "route" / "manifest.json",
        json.dumps(
            {
                "schema": "trashbot.vision_samples.v1",
                "samples": [{"sample_ref": "vision_sample://keyframes/000.json"}],
            }
        )
        + "\n",
    )
    if include_route_bag:
        write_text(root / "route_bag" / "metadata.yaml", "rosbag2_bagfile_information:\n")


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


def write_existing_manifest(path: Path, **overrides) -> None:
    # 离线导入会读取现场包中已有 manifest；测试只放最小字段来验证安全 gate。
    payload = {
        "schema": manifest.SCHEMA,
        "gate_pass": True,
        "delivery_success": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }
    payload.update(overrides)
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
        self.assertTrue(packet["artifacts"]["source_manifest"]["present"])
        self.assertEqual(packet["source_manifest"]["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(packet["artifact_status"], "gated")
        self.assertEqual(packet["manifest_gate"]["status"], "gated")

    def test_input_alias_imports_offline_packet_directory(self):
        # tech-plan 验收命令使用 --input；它必须和 --artifact-root 进入同一条本地 intake 路径。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "packet"
            output = Path(tmpdir) / "manifest.json"
            make_complete_fixture(root)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_input_alias",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(packet["artifact_root"], str(root))
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["not_proven"])
        self.assertEqual(packet["input_manifest"]["status"], "not_found")

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

    def test_schema_mismatch_field_evidence_manifest_fails_closed(self):
        # field evidence 旧输出带错 schema 时仍必须 fail closed，避免消费者误读旧契约。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "packet"
            output = Path(tmpdir) / "generated.json"
            make_complete_fixture(root)
            write_existing_manifest(root / "field_evidence_manifest.json", schema="trashbot.field_evidence_manifest.v0")

            rc = manifest.main(["--mode", "local", "--input", str(root), "--output", str(output)])
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_existing_manifest_reuse")
        self.assertEqual(packet["blocked_reason"], "existing_manifest_schema_mismatch")
        self.assertEqual(packet["artifact_status"], "blocked")
        self.assertFalse(packet["delivery_success"])

    def test_route_source_manifest_schema_mismatch_is_upstream_evidence(self):
        # route/manifest.json 是路线采样 source manifest；vision_samples schema 不应阻断 field manifest 生成。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "generated.json"
            derived = Path(tmpdir) / "derived_replay.jsonl"
            make_real_bundle_fixture(root, include_route_bag=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--artifact-root",
                    str(root / "route"),
                    "--map-yaml",
                    str(root / "map" / "trashbot_dynamic_odom_tf_map.yaml"),
                    "--map-pgm",
                    str(root / "map" / "trashbot_dynamic_odom_tf_map.pgm"),
                    "--derive-replay-jsonl",
                    str(derived),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_route_source_manifest",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_missing")
        self.assertEqual(packet["blocked_reason"], "missing_required_artifact")
        self.assertEqual(packet["source_manifest"]["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(packet["source_manifest"]["sample_count"], 1)
        self.assertEqual(packet["input_manifest"]["status"], "not_found")
        self.assertTrue(packet["artifacts"]["map_yaml"]["path"].endswith("trashbot_dynamic_odom_tf_map.yaml"))
        self.assertTrue(packet["artifacts"]["map_pgm"]["path"].endswith("trashbot_dynamic_odom_tf_map.pgm"))
        self.assertTrue(packet["artifacts"]["route_csv"]["path"].endswith("route.csv"))
        self.assertTrue(packet["artifacts"]["source_manifest"]["path"].endswith("manifest.json"))
        self.assertTrue(packet["artifacts"]["keyframes"]["path"].endswith("keyframes"))
        self.assertTrue(packet["artifacts"]["rosbag"]["required"])
        self.assertFalse(packet["artifacts"]["rosbag"]["present"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["required"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertTrue(packet["not_proven"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])

    def test_unsafe_existing_manifest_claim_fails_closed(self):
        # 离线 packet 不能自带 delivery/control 成功声明；真实控制与送达必须由后续现场验收证明。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "packet"
            output = Path(tmpdir) / "generated.json"
            make_complete_fixture(root)
            write_existing_manifest(root / "field_evidence_manifest.json", delivery_success=True, safe_to_control=True)

            rc = manifest.main(["--mode", "local", "--input", str(root), "--output", str(output)])
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["blocked_reason"], "unsafe_existing_manifest_claim")
        self.assertEqual(packet["input_manifest"]["dangerous_true_fields"], ["delivery_success", "safe_to_control"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["primary_actions_enabled"])

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

    def test_real_bundle_layout_with_derived_replay_scans_generated_jsonl(self):
        # 真实 bundle 允许缺 replay 输入，但 derive 后应让 manifest 扫描到新文件。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "manifest.json"
            derived = Path(tmpdir) / "derived_replay.jsonl"
            make_real_bundle_fixture(root, include_route_bag=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--derive-replay-jsonl",
                    str(derived),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_real_bundle_derive",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))
            replay_text = derived.read_text(encoding="utf-8")
            replay_lines = [json.loads(line) for line in replay_text.splitlines() if line.strip()]

        self.assertEqual(rc, 0)
        self.assertTrue(packet["gate_pass"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertEqual(packet["artifacts"]["replay_jsonl"]["path"], str(derived))
        self.assertTrue(packet["derived_replay"]["generated"])
        self.assertEqual(packet["derived_replay"]["frame_count"], 3)
        self.assertEqual(len(replay_lines), 3)
        self.assertEqual(replay_lines[0]["schema"], "trashbot.fixed_route_replay.v1")
        self.assertEqual(replay_lines[0]["event"], "route_frame")
        self.assertEqual(replay_lines[0]["timestamp_ms"], 1781025357570)
        self.assertEqual(replay_lines[1]["frame_index"], 1)
        self.assertEqual(replay_lines[1]["source_route_csv"], "field_route://route.csv")
        self.assertEqual(replay_lines[1]["evidence_ref"], "field_route://route/keyframes/001.jpg")
        self.assertFalse(replay_lines[1]["evidence_ref"].startswith("/"))
        self.assertNotIn("/cmd_vel", replay_text)
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])

    def test_real_bundle_without_route_bag_stays_fail_closed_even_after_derive(self):
        # route_bag 缺失时必须 fail closed；derive replay 只能补 O7 回放材料，不能补 rosbag 证据。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "manifest.json"
            derived = Path(tmpdir) / "derived_replay.jsonl"
            make_real_bundle_fixture(root, include_route_bag=False)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--derive-replay-jsonl",
                    str(derived),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_real_bundle_missing_bag",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_missing")
        self.assertEqual(packet["blocked_reason"], "missing_required_artifact")
        self.assertTrue(packet["derived_replay"]["generated"])
        self.assertEqual(packet["derived_replay"]["frame_count"], 3)
        self.assertFalse(packet["artifacts"]["rosbag"]["present"])
        self.assertTrue(packet["artifacts"]["rosbag"]["required"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["primary_actions_enabled"])

    def test_real_bundle_without_replay_and_without_derive_stays_fail_closed(self):
        # 未启用 derive 且 bundle 内也没有 replay 文件时，replay_jsonl 必须继续作为必需材料阻断 gate。
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "bundle"
            output = Path(tmpdir) / "manifest.json"
            make_real_bundle_fixture(root, include_route_bag=True)

            rc = manifest.main(
                [
                    "--mode",
                    "local",
                    "--input",
                    str(root),
                    "--output",
                    str(output),
                    "--run-id",
                    "unit_real_bundle_missing_replay",
                ]
            )
            packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertFalse(packet["gate_pass"])
        self.assertEqual(packet["status"], "blocked_artifacts_missing")
        self.assertEqual(packet["blocked_reason"], "missing_required_artifact")
        self.assertTrue(packet["artifacts"]["rosbag"]["present"])
        self.assertTrue(packet["artifacts"]["rosbag"]["required"])
        self.assertFalse(packet["artifacts"]["replay_jsonl"]["present"])
        self.assertTrue(packet["artifacts"]["replay_jsonl"]["required"])
        self.assertFalse(packet["derived_replay"]["generated"])
        self.assertEqual(packet["derived_replay"]["blocked_reason"], "not_requested")


if __name__ == "__main__":
    unittest.main()

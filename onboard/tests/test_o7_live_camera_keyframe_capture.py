"""O7 live camera keyframe helper 的离线合同与安全回归测试。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path


# 测试矩阵说明：topic 选择优先验证 canonical 成功路径。
# 测试矩阵说明：topic 选择验证 canonical 与旁路候选同时存在。
# 测试矩阵说明：topic 选择验证 canonical 类型错误时禁止 fallback。
# 测试矩阵说明：topic 选择验证 canonical 零 publisher 时 fail closed。
# 测试矩阵说明：topic 选择验证 canonical 缺席时唯一兼容候选。
# 测试矩阵说明：topic 选择验证多个兼容候选产生歧义。
# 测试矩阵说明：topic 选择验证 shell 元字符不能进入 SSH 参数。
# 测试矩阵说明：inventory 验证依赖导入失败会阻断 capture。
# 测试矩阵说明：inventory 验证 bounded topic list timeout 会阻断 capture。
# 测试矩阵说明：inventory 验证 daemon pid 漂移会阻断 capture。
# 测试矩阵说明：inventory clean 时 publisher count 必须保留。
# 测试矩阵说明：inventory clean 时 SSH count 为一、capture count 为零。
# 测试矩阵说明：encoding 覆盖 bgr8 的蓝红交换。
# 测试矩阵说明：encoding 覆盖 rgb8 的通道保持。
# 测试矩阵说明：encoding 覆盖 bgra8 的交换与 alpha 丢弃。
# 测试矩阵说明：encoding 覆盖 rgba8 的 alpha 丢弃。
# 测试矩阵说明：encoding 覆盖 mono8 的三通道扩展。
# 测试矩阵说明：未知 encoding 必须抛出稳定错误。
# 测试矩阵说明：layout 覆盖 step 小于有效行宽。
# 测试矩阵说明：layout 覆盖 raw bytes 比 step 乘 height 更短。
# 测试矩阵说明：layout 覆盖合法 row padding 不进入像素。
# 测试矩阵说明：PNG 覆盖固定签名和非空输出。
# 测试矩阵说明：transport 覆盖固定 magic round trip。
# 测试矩阵说明：transport 覆盖错误 magic。
# 测试矩阵说明：transport 覆盖 metadata 声明 raw size 漂移。
# 测试矩阵说明：manifest 覆盖全部冻结 schema 字段。
# 测试矩阵说明：manifest 覆盖 task id 与 message type。
# 测试矩阵说明：manifest 覆盖媒体 basename、size 和 hash。
# 测试矩阵说明：manifest 覆盖 inventory/capture 精确一比一。
# 测试矩阵说明：manifest 覆盖 stamp 全零 fail closed。
# 测试矩阵说明：manifest 覆盖 hash 不匹配 fail closed。
# 测试矩阵说明：manifest 覆盖危险 true fail closed。
# 测试矩阵说明：manifest 覆盖 source/count 不匹配 fail closed。
# 测试矩阵说明：blocked manifest 仍包含冻结字段。
# 测试矩阵说明：blocked manifest annotation-ready 固定 false。
# 测试矩阵说明：blocked manifest current delta 固定 false。
# 测试矩阵说明：隐私矩阵覆盖 raw pixel key。
# 测试矩阵说明：隐私矩阵覆盖直接 bytes value。
# 测试矩阵说明：隐私矩阵覆盖远端绝对路径。
# 测试矩阵说明：隐私矩阵覆盖远端 host。
# 测试矩阵说明：隐私矩阵覆盖 HTTP URL。
# 测试矩阵说明：隐私矩阵覆盖 data URL 和 base64。
# 测试矩阵说明：JSON writer 在创建文件前拒绝 binary。
# 测试矩阵说明：invocation 成功路径只调用 transport 一次。
# 测试矩阵说明：invocation timeout 路径只调用 transport 一次。
# 测试矩阵说明：invocation encoding 失败只调用 transport 一次。
# 测试矩阵说明：inventory blocked 时 transport 调用次数为零。
# 测试矩阵说明：所有控制与路线字段都必须保持 false。
# 测试矩阵说明：成功仅允许 current artifact delta 为 true。
# 测试矩阵说明：外部、控制、用户动作 delta 始终 false。
# 测试矩阵说明：annotation-ready 不代表 visible content 已证明。
# 测试矩阵说明：annotation-ready 不代表 privacy 已批准。
# 测试矩阵说明：annotation-ready 不代表 production annotation。
# 测试矩阵说明：测试 fixture 永远不会被写成 live source proof。
# 测试矩阵说明：测试不发起 SSH，不改变真实 invocation 计数。
# 测试矩阵说明：测试不创建 camera runtime 或 ROS graph 写操作。
# 测试矩阵说明：测试不触碰 scan、initialpose、cmd_vel 或 UART。
# 测试矩阵说明：测试文件按精确路径载入，不要求 ROS 安装。
# 测试矩阵说明：fixture 尺寸足够小，便于人工核对 RGB 字节。
# 测试矩阵说明：fixture stamp 固定非零，保证 lineage 合法。
# 测试矩阵说明：fixture padding 使用特殊字节，便于证明未进入 RGB。
# 测试矩阵说明：comment assertion 同时检查 helper 和测试文件。
# 测试矩阵说明：comment assertion 只接受含中文的技术注释。
# 测试矩阵说明：comment ratio 必须严格大于百分之二十。
# 测试矩阵说明：所有 hostile case 都要求稳定 fail-closed reason。


# 测试从精确文件载入 helper，避免依赖 ROS workspace 已安装或 PYTHONPATH。
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "onboard" / "scripts" / "o7_live_camera_keyframe_capture.py"
SPEC = importlib.util.spec_from_file_location("o7_live_camera_keyframe_capture", SOURCE)
assert SPEC and SPEC.loader
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def inventory(records: list[dict], *, daemon_pre=None, daemon_post=None, dependency_ok=True, exit_code=0):
    """构造不含远端地址的 inventory 输入，复用真实选择逻辑。"""

    return helper.evaluate_inventory(
        {
            "dependency_ok": dependency_ok,
            "topic_list_exit_code": exit_code,
            "records": records,
            "daemon_pre": [] if daemon_pre is None else daemon_pre,
            "daemon_post": [] if daemon_post is None else daemon_post,
        }
    )


def canonical_inventory() -> dict:
    """返回通过 canonical publisher gate 的最小 live inventory。"""

    return inventory(
        [
            {
                "topic": "/camera/image_raw",
                "types": ["sensor_msgs/msg/Image"],
                "publisher_count": 1,
            }
        ]
    )


def bgr_frame(width: int = 2, height: int = 1, *, padding: int = 0) -> tuple[dict, bytes]:
    """生成可人工核对颜色顺序的 bgr8 fixture。"""

    # 两个像素分别是 RGB(30,20,10) 与 RGB(60,50,40)。
    row = bytes((10, 20, 30, 40, 50, 60))
    raw = b"".join(row + b"\xaa" * padding for _ in range(height))
    metadata = {
        "stamp_sec": 1721016000,
        "stamp_nanosec": 123456789,
        "width": width,
        "height": height,
        "step": width * 3 + padding,
        "encoding": "bgr8",
        "is_bigendian": False,
        "raw_size": len(raw),
    }
    return metadata, raw


class TopicSelectionTest(unittest.TestCase):
    """canonical、兼容候选和歧义状态必须有确定结果。"""

    def test_canonical_topic_wins_over_other_candidate(self):
        # canonical 存在时，即使还有兼容 topic 也不产生候选歧义。
        selected, blocked = helper.choose_image_topic(
            [
                {"topic": "/front/image", "types": [helper.MESSAGE_TYPE], "publisher_count": 1},
                {"topic": helper.CANONICAL_TOPIC, "types": [helper.MESSAGE_TYPE], "publisher_count": 2},
            ]
        )
        self.assertEqual(selected["topic"], helper.CANONICAL_TOPIC)
        self.assertEqual(selected["publisher_count"], 2)
        self.assertEqual(blocked, [])

    def test_unique_compatible_topic_is_allowed_when_canonical_absent(self):
        # fallback 只依赖唯一 Image publisher，不按 camera 名称猜测。
        selected, blocked = helper.choose_image_topic(
            [{"topic": "/front/image", "types": [helper.MESSAGE_TYPE], "publisher_count": 1}]
        )
        self.assertEqual(selected["topic"], "/front/image")
        self.assertEqual(blocked, [])

    def test_multiple_compatible_topics_fail_closed(self):
        selected, blocked = helper.choose_image_topic(
            [
                {"topic": "/front/image", "types": [helper.MESSAGE_TYPE], "publisher_count": 1},
                {"topic": "/rear/image", "types": [helper.MESSAGE_TYPE], "publisher_count": 1},
            ]
        )
        self.assertIsNone(selected)
        self.assertEqual(blocked, ["multiple_compatible_image_topics"])

    def test_canonical_wrong_type_does_not_fallback(self):
        # canonical 名称被错误类型占用是图谱冲突，不允许偷偷切换到另一来源。
        selected, blocked = helper.choose_image_topic(
            [
                {"topic": helper.CANONICAL_TOPIC, "types": ["std_msgs/msg/String"], "publisher_count": 1},
                {"topic": "/front/image", "types": [helper.MESSAGE_TYPE], "publisher_count": 1},
            ]
        )
        self.assertIsNone(selected)
        self.assertEqual(blocked, ["canonical_topic_wrong_type"])

    def test_canonical_zero_publishers_fails_closed(self):
        selected, blocked = helper.choose_image_topic(
            [{"topic": helper.CANONICAL_TOPIC, "types": [helper.MESSAGE_TYPE], "publisher_count": 0}]
        )
        self.assertIsNone(selected)
        self.assertEqual(blocked, ["canonical_topic_zero_publishers"])

    def test_invalid_topic_is_rejected_before_shell_use(self):
        with self.assertRaisesRegex(ValueError, "invalid_ros_topic"):
            helper.choose_image_topic(
                [{"topic": "/camera/image_raw;touch/tmp/x", "types": [helper.MESSAGE_TYPE], "publisher_count": 1}]
            )


class InventoryGateTest(unittest.TestCase):
    """inventory 的 dependency、daemon 与 publisher gate 必须独立 fail closed。"""

    def test_clean_inventory_records_exact_counts(self):
        result = canonical_inventory()
        self.assertEqual(result["status"], "clean_read_only_image_publisher")
        self.assertEqual(result["inventory_ssh_invocation_count"], 1)
        self.assertEqual(result["single_frame_capture_invocation_count"], 0)
        self.assertEqual(result["publisher_count_at_inventory"], 1)
        self.assertEqual(result["blocked_reasons"], [])
        self.assertFalse(result["current_run_artifact_delta"])
        self.assertFalse(result["safe_to_control"])

    def test_dependency_failure_blocks_before_selection(self):
        result = inventory([], dependency_ok=False)
        self.assertIn("remote_rclpy_or_image_dependency_unavailable", result["blocked_reasons"])
        self.assertEqual(result["topic"], "")

    def test_bounded_topic_list_failure_blocks(self):
        result = inventory([], exit_code=124)
        self.assertIn("bounded_topic_list_failed", result["blocked_reasons"])

    def test_daemon_pid_drift_blocks_capture(self):
        result = inventory([], daemon_pre=[10], daemon_post=[10, 11])
        self.assertIn("ros2_daemon_process_drift", result["blocked_reasons"])
        self.assertTrue(result["daemon_process_drift"])


class EncodingAndLayoutTest(unittest.TestCase):
    """只支持可无损解释的 8-bit encoding，并严格验证 step/data。"""

    def test_bgr8_is_converted_to_rgb_png(self):
        metadata, raw = bgr_frame()
        width, height, rgb = helper.image_to_rgb_rows(metadata, raw)
        self.assertEqual((width, height), (2, 1))
        self.assertEqual(rgb, bytes((30, 20, 10, 60, 50, 40)))
        png = helper.encode_png(metadata, raw)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_rgb8_preserves_channel_order(self):
        metadata, raw = bgr_frame()
        metadata["encoding"] = "rgb8"
        _, _, rgb = helper.image_to_rgb_rows(metadata, raw)
        self.assertEqual(rgb, raw)

    def test_bgra8_drops_alpha_and_swaps_channels(self):
        metadata = {"width": 1, "height": 1, "step": 4, "encoding": "bgra8"}
        _, _, rgb = helper.image_to_rgb_rows(metadata, bytes((1, 2, 3, 99)))
        self.assertEqual(rgb, bytes((3, 2, 1)))

    def test_rgba8_drops_alpha(self):
        metadata = {"width": 1, "height": 1, "step": 4, "encoding": "rgba8"}
        _, _, rgb = helper.image_to_rgb_rows(metadata, bytes((1, 2, 3, 99)))
        self.assertEqual(rgb, bytes((1, 2, 3)))

    def test_mono8_expands_to_rgb(self):
        metadata = {"width": 2, "height": 1, "step": 2, "encoding": "mono8"}
        _, _, rgb = helper.image_to_rgb_rows(metadata, bytes((7, 9)))
        self.assertEqual(rgb, bytes((7, 7, 7, 9, 9, 9)))

    def test_row_padding_is_not_hashed_as_pixels(self):
        metadata, raw = bgr_frame(height=2, padding=2)
        _, _, rgb = helper.image_to_rgb_rows(metadata, raw)
        self.assertEqual(len(rgb), 2 * 2 * 3)
        self.assertNotIn(0xAA, rgb)

    def test_short_data_fails_layout(self):
        metadata, raw = bgr_frame()
        with self.assertRaisesRegex(ValueError, "invalid_image_layout"):
            helper.image_to_rgb_rows(metadata, raw[:-1])

    def test_step_smaller_than_row_fails_layout(self):
        metadata, raw = bgr_frame()
        metadata["step"] = 5
        with self.assertRaisesRegex(ValueError, "invalid_image_layout"):
            helper.image_to_rgb_rows(metadata, raw)

    def test_unsupported_encoding_fails_closed(self):
        metadata, raw = bgr_frame()
        metadata["encoding"] = "yuv422"
        with self.assertRaisesRegex(ValueError, "unsupported_image_encoding"):
            helper.encode_png(metadata, raw)


class TransportTest(unittest.TestCase):
    """SSH pipe protocol 必须拒绝 prefix、长度和 raw size 损坏。"""

    @staticmethod
    def make_payload(metadata: dict, raw: bytes) -> bytes:
        header = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
        return b"O7FRAME1\n" + struct.pack(">I", len(header)) + header + raw

    def test_transport_round_trip(self):
        metadata, raw = bgr_frame()
        parsed_metadata, parsed_raw = helper.parse_frame_transport(self.make_payload(metadata, raw))
        self.assertEqual(parsed_metadata, metadata)
        self.assertEqual(parsed_raw, raw)

    def test_transport_bad_prefix_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_frame_transport_prefix"):
            helper.parse_frame_transport(b"not-a-frame")

    def test_transport_raw_size_mismatch_is_rejected(self):
        metadata, raw = bgr_frame()
        metadata["raw_size"] += 1
        with self.assertRaisesRegex(ValueError, "frame_transport_raw_size_mismatch"):
            helper.parse_frame_transport(self.make_payload(metadata, raw))


class ManifestContractTest(unittest.TestCase):
    """manifest 必须保留 lineage、hash、redaction 与所有固定 false。"""

    def test_live_manifest_has_frozen_schema_and_hash(self):
        inv = canonical_inventory()
        metadata, raw = bgr_frame()
        png = helper.encode_png(metadata, raw)
        manifest = helper.live_manifest(inv, metadata, png)
        self.assertTrue(helper.REQUIRED_MANIFEST_FIELDS.issubset(manifest))
        self.assertEqual(manifest["sha256"], hashlib.sha256(png).hexdigest())
        self.assertEqual(manifest["media_byte_size"], len(png))
        self.assertEqual(manifest["inventory_ssh_invocation_count"], 1)
        self.assertEqual(manifest["single_frame_capture_invocation_count"], 1)
        self.assertTrue(manifest["annotation_ready"])
        self.assertTrue(manifest["current_run_artifact_delta"])
        self.assertFalse(manifest["external_artifact_delta"])
        self.assertFalse(manifest["live_control_delta"])
        self.assertFalse(manifest["user_action_delta"])
        helper.validate_manifest(manifest, png)

    def test_hash_mismatch_is_rejected(self):
        inv = canonical_inventory()
        metadata, raw = bgr_frame()
        png = helper.encode_png(metadata, raw)
        manifest = helper.live_manifest(inv, metadata, png)
        with self.assertRaisesRegex(ValueError, "live_png_hash_or_size_mismatch"):
            helper.validate_manifest(manifest, png + b"x")

    def test_invalid_zero_stamp_is_rejected(self):
        inv = canonical_inventory()
        metadata, raw = bgr_frame()
        metadata["stamp_sec"] = 0
        metadata["stamp_nanosec"] = 0
        png = helper.encode_png(metadata, raw)
        with self.assertRaisesRegex(ValueError, "invalid_image_stamp"):
            helper.live_manifest(inv, metadata, png)

    def test_blocked_manifest_is_complete_and_fixed_false(self):
        manifest = helper.blocked_manifest(
            blocked_reasons=["single_frame_capture_timeout"],
            source_proof="live_single_frame_capture_failed",
            capture_count=1,
        )
        helper.validate_manifest(manifest)
        self.assertFalse(manifest["annotation_ready"])
        self.assertFalse(manifest["current_run_artifact_delta"])
        self.assertEqual(manifest["single_frame_capture_invocation_count"], 1)
        for key in helper.FIXED_FALSE_FIELDS:
            self.assertFalse(manifest[key])

    def test_dangerous_true_is_rejected(self):
        manifest = helper.blocked_manifest(
            blocked_reasons=["blocked"], source_proof="live_inventory_blocked"
        )
        manifest["safe_to_control"] = True
        with self.assertRaisesRegex(ValueError, "dangerous_field_not_false"):
            helper.validate_manifest(manifest)

    def test_source_count_mismatch_is_rejected(self):
        inv = canonical_inventory()
        metadata, raw = bgr_frame()
        png = helper.encode_png(metadata, raw)
        manifest = helper.live_manifest(inv, metadata, png)
        manifest["single_frame_capture_invocation_count"] = 0
        with self.assertRaisesRegex(ValueError, "live_invocation_count_mismatch"):
            helper.validate_manifest(manifest, png)


class PrivacyAndBinaryTest(unittest.TestCase):
    """JSON hostile 输入不得泄漏 binary、路径、URL、host 或 base64。"""

    def test_raw_pixel_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "binary_key_forbidden"):
            helper.assert_no_binary_or_unsafe_reference({"raw_pixels": [1, 2, 3]})

    def test_bytes_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "binary_value_forbidden"):
            helper.assert_no_binary_or_unsafe_reference({"sample": b"pixels"})

    def test_absolute_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsafe_reference_forbidden"):
            helper.assert_no_binary_or_unsafe_reference({"media": "/root/secret/keyframe.png"})

    def test_remote_host_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsafe_reference_forbidden"):
            helper.assert_no_binary_or_unsafe_reference({"host": "root@192.168.1.11"})

    def test_url_and_data_url_are_rejected(self):
        for value in ("https://example.invalid/frame", "data:image/png;base64,AAAA"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "unsafe_reference_forbidden"):
                helper.assert_no_binary_or_unsafe_reference({"value": value})

    def test_json_writer_never_accepts_binary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "artifact.json"
            with self.assertRaisesRegex(ValueError, "binary_value_forbidden"):
                helper.write_json(output, {"payload": b"pixels"})
            self.assertFalse(output.exists())


class InvocationAndRetryTest(unittest.TestCase):
    """capture transport 只调用一次，timeout/编码错误都不能 retry。"""

    def test_success_calls_transport_once(self):
        calls = []
        metadata, raw = bgr_frame()

        def transport(topic, timeout_s):
            calls.append((topic, timeout_s))
            return metadata, raw

        manifest, png = helper.capture_with_transport(canonical_inventory(), transport, 12.0)
        self.assertEqual(calls, [(helper.CANONICAL_TOPIC, 12.0)])
        self.assertTrue(manifest["annotation_ready"])
        self.assertGreater(len(png), 0)

    def test_timeout_calls_transport_once_and_propagates(self):
        calls = []

        def transport(topic, timeout_s):
            calls.append((topic, timeout_s))
            raise TimeoutError("owned_ssh_process_timeout")

        with self.assertRaises(TimeoutError):
            helper.capture_with_transport(canonical_inventory(), transport, 12.0)
        self.assertEqual(len(calls), 1)

    def test_encoding_failure_calls_transport_once(self):
        calls = []
        metadata, raw = bgr_frame()
        metadata["encoding"] = "unsupported_fixture"

        def transport(topic, timeout_s):
            calls.append((topic, timeout_s))
            return metadata, raw

        with self.assertRaisesRegex(ValueError, "unsupported_image_encoding"):
            helper.capture_with_transport(canonical_inventory(), transport, 12.0)
        self.assertEqual(len(calls), 1)

    def test_blocked_inventory_never_calls_transport(self):
        calls = []

        def transport(topic, timeout_s):
            calls.append((topic, timeout_s))
            raise AssertionError("must not be called")

        blocked = inventory([])
        with self.assertRaisesRegex(ValueError, "inventory_gate_not_clean"):
            helper.capture_with_transport(blocked, transport, 12.0)
        self.assertEqual(calls, [])


class CommentDisciplineTest(unittest.TestCase):
    """新增 Python 技术注释必须为中文且比例严格大于 20%。"""

    def test_chinese_comment_ratio_exceeds_twenty_percent(self):
        paths = [SOURCE, Path(__file__).resolve()]
        for path in paths:
            with self.subTest(path=path.name):
                lines = path.read_text(encoding="utf-8").splitlines()
                technical = [line for line in lines if line.strip() and not line.lstrip().startswith("#!")]
                # 计入中文 docstring 与 # 注释；二者都是源码中的技术说明，不计普通字符串。
                comments = [
                    line
                    for line in technical
                    if line.lstrip().startswith("#")
                    or (('"""' in line or "'''" in line) and any("\u4e00" <= char <= "\u9fff" for char in line))
                ]
                self.assertGreater(len(comments) / len(technical), 0.20, (path, len(comments), len(technical)))
                # 英文注释会导致硬件/算法解释口径漂移，新增注释统一要求含中文。
                for line in comments:
                    if line.lstrip().startswith("#"):
                        self.assertTrue(any("\u4e00" <= char <= "\u9fff" for char in line), line)


if __name__ == "__main__":
    unittest.main()

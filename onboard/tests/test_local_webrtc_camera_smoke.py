"""local_webrtc_camera_smoke 的 no-hardware 单元测试。

这些测试不打开真实摄像头、不读串口、不发送运动命令。
目标是锁住 8088 camera service 的只读诊断、auto 选源和 fail-closed offer。
"""

from __future__ import annotations

import importlib.util
import sys
import time
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_webrtc_camera_smoke.py"
SPEC = importlib.util.spec_from_file_location("local_webrtc_camera_smoke", MODULE_PATH)
camera = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
# dataclass 在 Python 3.13 会回查 sys.modules，所以路径加载必须先注册模块。
sys.modules[SPEC.name] = camera
SPEC.loader.exec_module(camera)


class LocalWebrtcCameraSmokeTests(unittest.TestCase):
    """覆盖 camera service 的安全边界和设备选择。"""

    def test_systemd_launcher_contract_stays_camera_only(self) -> None:
        """systemd 启动脚本必须可入仓复现，且只能启动 camera smoke。"""
        launcher = MODULE_PATH.with_suffix(".sh")
        text = launcher.read_text(encoding="utf-8")

        self.assertIn('HOST="${HOST:-0.0.0.0}"', text)
        self.assertIn('PORT="${PORT:-8088}"', text)
        self.assertIn('ROBER_CAMERA_SOURCE="${ROBER_CAMERA_SOURCE:-auto}"', text)
        self.assertIn("local_webrtc_camera_smoke.py", text)
        self.assertIn("--video-source", text)
        forbidden = ("ros2 ", "/api/base/manual", "cmd_vel", "nav2", "ttyS5", "motion_hil_unlocked")
        for token in forbidden:
            self.assertNotIn(token, text)

    def test_success_endpoint_schemas_match_historical_contracts(self) -> None:
        """成功响应 schema 要兼容历史真实服务 artifacts 和 PC catalog。"""
        self.assertEqual("trashbot.local_webrtc_camera_smoke.v1", camera.SCHEMA)
        self.assertEqual("trashbot.local_webrtc_camera_devices.v1", camera.DEVICES_SCHEMA)
        self.assertEqual("trashbot.local_webrtc_camera_offer.v1", camera.OFFER_SCHEMA)
        self.assertEqual("trashbot.local_webrtc_camera_close.v1", camera.CLOSE_SCHEMA)

    def test_api_camera_paths_alias_historical_root_paths(self) -> None:
        """8088 服务必须同时兼容历史根路径和上位机 `/api/camera/*` 合同。"""
        cases = {
            "/api/camera": "/",
            "/api/camera/health": "/health",
            "/api/camera/devices?fresh=1": "/devices",
            "/api/camera/mjpeg": "/mjpeg",
            "/api/camera/offer": "/offer",
            "/api/camera/peers/abc123/close": "/peers/abc123/close",
            "/health": "/health",
            "/mjpeg": "/mjpeg",
        }

        observed = {path: camera.normalize_camera_service_path(path) for path in cases}

        self.assertEqual(cases, observed)

    def test_auto_source_skips_cedrus_and_metadata_prefers_uvc_capture(self) -> None:
        """auto 必须选真实 UVC capture，不能落到 decoder 或 metadata。"""
        candidates = [
            {
                "path": "/dev/video0",
                "exists": True,
                "v4l2_name": "cedrus (platform:cedrus)",
                "sysfs_name": "cedrus",
                "is_video_capture": False,
                "is_uvc_or_usb": False,
                "is_decoder": True,
                "is_metadata": False,
            },
            {
                "path": "/dev/video1",
                "exists": True,
                "v4l2_name": "USB Composite Device: DV20 USB",
                "sysfs_name": "DV20 USB",
                "is_video_capture": True,
                "is_uvc_or_usb": True,
                "is_decoder": False,
                "is_metadata": False,
            },
            {
                "path": "/dev/video2",
                "exists": True,
                "v4l2_name": "USB Composite Device: DV20 USB",
                "sysfs_name": "metadata",
                "is_video_capture": False,
                "is_uvc_or_usb": True,
                "is_decoder": False,
                "is_metadata": True,
            },
        ]

        selection = camera.choose_auto_source(candidates)

        self.assertEqual("/dev/video1", selection["selected_path"])
        self.assertEqual("auto", selection["mode"])
        self.assertLess(
            next(item for item in selection["ranked"] if item["path"] == "/dev/video0")["score"],
            0,
        )
        self.assertLess(
            next(item for item in selection["ranked"] if item["path"] == "/dev/video2")["score"],
            0,
        )

    def test_auto_first_frame_sources_try_positive_capture_candidates_only(self) -> None:
        """首帧 fallback 只能尝试真实 capture，不能把 decoder/metadata 当备用画面。"""
        candidates = [
            {
                "path": "/dev/video0",
                "exists": True,
                "is_video_capture": False,
                "is_uvc_or_usb": False,
                "is_decoder": True,
                "is_metadata": False,
            },
            {
                "path": "/dev/video1",
                "exists": True,
                "is_video_capture": True,
                "is_uvc_or_usb": True,
                "is_decoder": False,
                "is_metadata": False,
            },
            {
                "path": "/dev/video3",
                "exists": True,
                "is_video_capture": True,
                "is_uvc_or_usb": True,
                "is_decoder": False,
                "is_metadata": False,
            },
            {
                "path": "/dev/video2",
                "exists": True,
                "is_video_capture": False,
                "is_uvc_or_usb": True,
                "is_decoder": False,
                "is_metadata": True,
            },
        ]

        selection = camera.choose_auto_source(candidates)
        paths = camera.auto_first_frame_source_paths(selection)

        self.assertEqual(["/dev/video1", "/dev/video3"], paths)
        self.assertNotIn("/dev/video0", paths)
        self.assertNotIn("/dev/video2", paths)

    def test_create_answer_auto_falls_back_to_second_frame_source(self) -> None:
        """auto 首选源无首帧时，应继续尝试下一个健康 capture 源，而不是直接让 PC 无图。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                },
                {
                    "path": "/dev/video3",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                },
            ]
        }
        calls: list[str] = []

        async def fake_create_answer(_offer: dict[str, object], source: str) -> tuple[int, dict[str, object]]:
            calls.append(source)
            if source == "/dev/video3":
                return 200, {"status": "answer_created", "video_source": source}
            return 503, camera.error_payload("first_frame_unreadable", "first_frame_total_timeout", video_source=source)

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            with mock.patch.object(camera, "import_state", return_value={"aiortc": True, "cv2": True, "av": True}):
                with mock.patch.object(state, "_create_answer_with_dependencies", side_effect=fake_create_answer):
                    status, payload = camera.asyncio.run(state.create_answer({"type": "offer", "sdp": "v=0\r\n"}))

        self.assertEqual(200, status)
        self.assertEqual(["/dev/video1", "/dev/video3"], calls)
        self.assertEqual("/dev/video3", payload["video_source"])
        self.assertTrue(payload["auto_source_fallback_attempted"])
        self.assertEqual("/dev/video1", payload["auto_source_primary_path"])

    def test_health_prefers_recent_frame_source_for_auto(self) -> None:
        """备用摄像头已经读到真实帧时，health 应展示 frame-proven 源，避免页面继续盯坏源。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        state.last_successful_frame = {
            "source": "/dev/video3",
            "channel": "mjpeg",
            "observed_at_ms": camera.now_ms(),
            "width": 640,
            "height": 480,
        }
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "v4l2_name": "DV20 USB",
                    "sysfs_name": "DV20 USB",
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "formats_summary": "MJPG@640x480@30",
                },
                {
                    "path": "/dev/video3",
                    "exists": True,
                    "v4l2_name": "Known Good UVC",
                    "sysfs_name": "Known Good UVC",
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "formats_summary": "MJPG@640x480@30",
                },
            ]
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            with mock.patch.object(camera, "collect_device_usage", return_value={"status": "not_in_use", "owner_count": 0, "other_owner_count": 0}):
                with mock.patch.object(camera, "collect_uvc_kernel_diagnostics", return_value={"status": "uvc_kernel_seen_without_recent_transport_errors"}):
                    with mock.patch.object(camera, "collect_uvc_usb_topology_diagnostics", return_value={"status": "uvc_video_usb_speed_loaded", "video_usb_speed": "480M"}):
                        with mock.patch.object(camera, "collect_cma_memory_diagnostics", return_value={"status": "cma_available_no_recent_failure"}):
                            health = state.health()

        self.assertEqual("ready", health["status"])
        self.assertEqual("first_frame_observed", health["source_readiness"])
        self.assertEqual("/dev/video3", health["current_selection"]["selected_path"])
        self.assertEqual("Known Good UVC", health["current_selection"]["selected_name"])

    def test_source_summary_exposes_uvc_sibling_metadata_node(self) -> None:
        """DV20 一类复合 UVC 要说明 video2 是兄弟 metadata 节点，不是备用画面源。"""
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "v4l2_name": "USB Composite Device: DV20 USB",
                    "sysfs_name": "USB Composite Device: DV20 USB",
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "formats_summary": "MJPG@640x480@30",
                },
                {
                    "path": "/dev/video2",
                    "exists": True,
                    "v4l2_name": "USB Composite Device: DV20 USB",
                    "sysfs_name": "USB Composite Device: DV20 USB",
                    "is_video_capture": False,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": True,
                    "formats_summary": "not_loaded",
                },
            ]
        }
        selection = {"mode": "auto", "requested_source": "auto", "selected_path": "/dev/video1", "ranked": []}

        summary = camera.source_candidates_summary(snapshot, selection)
        current = summary["current_selection"]

        self.assertEqual("single_shared_capture_for_multiple_clients", summary["shared_preview_contract"])
        self.assertEqual("video_capture", current["selected_role"])
        self.assertEqual(1, current["selected_sibling_video_node_count"])
        self.assertEqual("/dev/video2=metadata", current["selected_sibling_video_nodes_summary"])
        self.assertEqual("metadata", current["selected_sibling_video_nodes"][0]["role"])

    def test_explicit_source_is_respected_without_auto_rerank(self) -> None:
        """显式指定源时必须尊重 operator 输入，便于现场排查枚举漂移。"""
        selection = camera.resolve_video_source("/dev/video9")

        self.assertEqual("explicit", selection["mode"])
        self.assertEqual("/dev/video9", selection["selected_path"])
        self.assertEqual("/dev/video9", selection["requested_source"])

    def test_invalid_offer_fails_before_dependency_or_camera_access(self) -> None:
        """坏 offer 不应触发依赖 import 或 VideoCapture 打开。"""
        valid, reason = camera.validate_offer_payload({"type": "answer", "sdp": ""})

        self.assertFalse(valid)
        self.assertEqual("type_must_be_offer", reason)

    def test_mjpeg_part_encoder_wraps_only_real_jpeg_bytes(self) -> None:
        """MJPEG fallback 只能包装 OpenCV 编码出的真实 JPEG bytes，不能编造占位图。"""

        class FakeEncoded:
            def tobytes(self) -> bytes:
                return b"\xff\xd8real-jpeg\xff\xd9"

        class FakeCv2:
            def imencode(self, suffix: str, frame: object) -> tuple[bool, FakeEncoded]:
                self.suffix = suffix
                self.frame = frame
                return True, FakeEncoded()

        fake_cv2 = FakeCv2()
        frame = object()

        part = camera.encode_mjpeg_part(fake_cv2, frame)

        self.assertIsNotNone(part)
        assert part is not None
        self.assertIn(b"--roberframe", part)
        self.assertIn(b"Content-Type: image/jpeg", part)
        self.assertIn(b"\xff\xd8real-jpeg\xff\xd9", part)
        self.assertEqual(".jpg", fake_cv2.suffix)
        self.assertIs(frame, fake_cv2.frame)

    def test_camera_attempt_specs_include_real_dv20_discrete_modes(self) -> None:
        """首帧尝试矩阵必须贴合实板 DV20 枚举，避免一直用不支持的 15fps。"""
        specs = camera.camera_capture_attempt_specs(640, 480, 15)
        labels = [spec.label() for spec in specs]

        self.assertIn("MJPG@640x480@30", labels)
        self.assertIn("MJPG@1280x720@30", labels)
        self.assertIn("MJPG@480x320@30", labels)
        self.assertIn("MJPG@160x120@30", labels)
        self.assertIn("YUYV@640x480@22", labels)
        self.assertIn("YUYV@320x240@25", labels)
        self.assertIn("YUYV@320x240@20", labels)
        self.assertIn("YUYV@160x120@20", labels)
        self.assertEqual(len(labels), len(set(labels)))

    def test_mjpeg_attempt_specs_include_low_bandwidth_before_default(self) -> None:
        """共享预览要先试 native 和极低带宽真帧，不能等默认模式失败后才知道软件兜底没做。"""
        labels = [spec.label() for spec in camera.mjpeg_camera_capture_attempt_specs(640, 480, 15)]

        self.assertLess(labels.index("MJPG@1280x720@30"), labels.index("default@current"))
        self.assertLess(labels.index("MJPG@1280x720@30"), labels.index("MJPG@160x120@30"))
        self.assertLess(labels.index("MJPG@160x120@30"), labels.index("default@current"))
        self.assertLess(labels.index("YUYV@160x120@20"), labels.index("default@current"))
        self.assertLess(labels.index("MJPG@480x320@30"), labels.index("MJPG@160x120@30"))
        self.assertLess(labels.index("YUYV@320x240@25"), labels.index("YUYV@160x120@20"))
        self.assertEqual(len(labels), len(set(labels)))

    def test_mjpeg_first_frame_budget_keeps_total_window_but_shortens_each_attempt(self) -> None:
        """共享 MJPEG 总窗口要短到首屏可感知失败，但单次尝试仍能覆盖多个格式。"""
        self.assertLess(camera.MJPEG_FIRST_FRAME_TIMEOUT_S, camera.FIRST_FRAME_TIMEOUT_S)
        self.assertGreaterEqual(camera.MJPEG_FIRST_FRAME_TIMEOUT_S, 0.5)
        self.assertLessEqual(camera.MJPEG_FIRST_FRAME_TOTAL_TIMEOUT_S, 5.0)
        self.assertGreaterEqual(camera.MJPEG_FIRST_FRAME_TOTAL_TIMEOUT_S, camera.MJPEG_FIRST_FRAME_TIMEOUT_S)

    def test_opencv_open_candidates_can_try_index_and_v4l2_backend(self) -> None:
        """板端 OpenCV 可能 path 能 open 但无帧，MJPEG 共享预览要能继续试 index/backend。"""

        class FakeCv2:
            CAP_V4L2 = 200

        default_candidates = camera.opencv_capture_open_candidates(FakeCv2(), "/dev/video1")
        fallback_candidates = camera.opencv_capture_open_candidates(FakeCv2(), "/dev/video1", include_backend_fallbacks=True)

        self.assertEqual(
            [("/dev/video1", "default"), ("index:1", "default")],
            [(item["source_label"], item["backend_label"]) for item in default_candidates],
        )
        self.assertEqual(
            [("/dev/video1", "default"), ("/dev/video1", "CAP_V4L2"), ("index:1", "default"), ("index:1", "CAP_V4L2")],
            [(item["source_label"], item["backend_label"]) for item in fallback_candidates],
        )

    def test_mjpeg_first_frame_fallback_tries_numeric_index_after_path_read_false(self) -> None:
        """`/dev/video1` 打开但读不到帧时，MJPEG 首屏要继续尝试数字索引，降低 UVC 枚举差异影响。"""

        frame = object()

        class FallbackCapture:
            def __init__(self, source: str | int, backend: int | None) -> None:
                self.source = source
                self.backend = backend
                self.released = False

            def isOpened(self) -> bool:  # noqa: N802 - 模拟 OpenCV API。
                return True

            def set(self, _prop: int, _value: object) -> None:
                return None

            def read(self) -> tuple[bool, object | None]:
                if self.source == 1 and self.backend is None:
                    return True, frame
                return False, None

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_FOURCC = 6
            CAP_PROP_FRAME_WIDTH = 3
            CAP_PROP_FRAME_HEIGHT = 4
            CAP_PROP_FPS = 5
            CAP_V4L2 = 200

            def __init__(self) -> None:
                self.calls: list[tuple[str | int, int | None]] = []
                self.captures: list[FallbackCapture] = []

            def VideoWriter_fourcc(self, *_letters: str) -> int:  # noqa: N802 - 模拟 OpenCV API。
                return 100

            def VideoCapture(self, source: str | int, backend: int | None = None) -> FallbackCapture:  # noqa: N802 - 模拟 OpenCV API。
                self.calls.append((source, backend))
                capture = FallbackCapture(source, backend)
                self.captures.append(capture)
                return capture

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        fake_cv2 = FakeCv2()

        with mock.patch.object(camera, "FIRST_FRAME_WARMUP_INTERVAL_S", 0.001):
            shared, observed, attempts, error = state.acquire_first_frame_capture(
                "/dev/video1",
                fake_cv2,
                timeout_s=0.01,
                total_timeout_s=0.35,
                specs=[camera.CameraCaptureAttemptSpec("MJPG", 640, 480, 30)],
                include_open_source_fallbacks=True,
            )

        self.assertIsNone(error)
        self.assertIs(frame, observed)
        self.assertIsNotNone(shared)
        assert shared is not None
        self.assertEqual([("/dev/video1", None), ("/dev/video1", 200), (1, None)], fake_cv2.calls)
        self.assertEqual("index:1", shared.summary()["open_source"])
        self.assertEqual("default", shared.summary()["open_backend"])
        self.assertEqual(["/dev/video1", "/dev/video1", "index:1"], [item["open_source"] for item in attempts])
        self.assertEqual(["default", "CAP_V4L2", "default"], [item["open_backend"] for item in attempts])
        self.assertEqual("frame_read", attempts[-1]["status"])
        self.assertTrue(all(capture.released for capture in fake_cv2.captures[:2]))
        self.assertFalse(fake_cv2.captures[2].released)

    def test_missing_webrtc_dependencies_return_structured_fail_closed(self) -> None:
        """缺 aiortc/cv2/av 时 /offer 必须结构化失败，不能伪造图像。"""
        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        offer = {"type": "offer", "sdp": "v=0\r\n"}

        with mock.patch.object(camera, "import_state", return_value={"aiortc": False, "cv2": False, "av": False}):
            status, payload = camera.asyncio.run(state.create_answer(offer))

        self.assertEqual(503, status)
        self.assertEqual("dependency_missing", payload["error"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])

    def test_devices_enumeration_uses_readonly_v4l2_commands(self) -> None:
        """设备枚举只能调用只读 v4l2 命令，不写 controls。"""
        calls: list[list[str]] = []

        def fake_command(args: list[str], timeout_s: float = 0.0) -> dict[str, object]:
            calls.append(args)
            if args == ["v4l2-ctl", "--list-devices"]:
                return {
                    "available": True,
                    "stdout": "USB Composite Device: DV20 USB:\n\t/dev/video1\n",
                    "stderr": "",
                    "returncode": 0,
                }
            return {"available": True, "stdout": "Video Capture\nMJPG", "stderr": "", "returncode": 0}

        with mock.patch.object(camera.glob, "glob", return_value=["/dev/video1"]):
            with mock.patch.object(camera, "run_readonly_command", side_effect=fake_command):
                with mock.patch.object(camera, "read_sysfs_video_name", return_value="DV20 USB"):
                    snapshot = camera.collect_video_candidates()

        self.assertEqual(["/dev/video1"], snapshot["paths"])
        self.assertFalse(snapshot["writes_controls"])
        self.assertFalse(snapshot["opens_serial"])
        self.assertFalse(snapshot["sends_motion_commands"])
        flattened = " ".join(" ".join(call) for call in calls)
        self.assertIn("--list-devices", flattened)
        self.assertIn("--all", flattened)
        self.assertIn("--list-formats-ext", flattened)
        self.assertNotIn("--set-ctrl", flattened)

    def test_v4l2_formats_are_compacted_for_pc_readback(self) -> None:
        """PC 普通诊断需要一行看懂上车端实际支持哪些采集格式。"""
        text = "\n".join(
            [
                "[0]: 'MJPG' (Motion-JPEG, compressed)",
                "    Size: Discrete 640x480",
                "        Interval: Discrete 0.033s (30.000 fps)",
                "[1]: 'YUYV' (YUYV 4:2:2)",
                "    Size: Discrete 640x480",
                "        Interval: Discrete 0.045s (22.000 fps)",
                "    Size: Discrete 320x240",
                "        Interval: Discrete 0.050s (20.000 fps)",
            ]
        )

        summary = camera.summarize_v4l2_formats(text)

        self.assertEqual("MJPG@640x480@30；YUYV@640x480@22；YUYV@320x240@20", summary)

    def test_uvc_capture_with_metadata_capability_still_counts_as_video(self) -> None:
        """DV20 这类 UVC 复合设备会列出 metadata capability，但 /dev/video1 仍是图像节点。"""

        def fake_command(args: list[str], timeout_s: float = 0.0) -> dict[str, object]:
            if "--all" in args:
                return {
                    "available": True,
                    "stdout": "\n".join(
                        [
                            "Driver name      : uvcvideo",
                            "Card type        : USB Composite Device: DV20 USB",
                            "Capabilities     : Video Capture Metadata Capture Streaming",
                            "Device Caps      : Video Capture Streaming",
                            "Format Video Capture:",
                            "Pixel Format      : 'YUYV' (YUYV 4:2:2)",
                        ]
                    ),
                    "stderr": "",
                    "returncode": 0,
                }
            return {
                "available": True,
                "stdout": "\n".join(
                    [
                        "ioctl: VIDIOC_ENUM_FMT",
                        "Type: Video Capture",
                        "[0]: 'MJPG' (Motion-JPEG, compressed)",
                        "[1]: 'YUYV' (YUYV 4:2:2)",
                    ]
                ),
                "stderr": "",
                "returncode": 0,
            }

        with mock.patch.object(camera.os.path, "exists", return_value=True):
            with mock.patch.object(camera, "run_readonly_command", side_effect=fake_command):
                with mock.patch.object(camera, "read_sysfs_video_name", return_value="USB Composite Device: DV20 USB"):
                    candidate = camera.build_device_candidate("/dev/video1", "USB Composite Device: DV20 USB")

        self.assertTrue(candidate["is_video_capture"])
        self.assertFalse(candidate["is_metadata"])
        self.assertTrue(candidate["is_uvc_or_usb"])

    def test_devices_success_schema_uses_historical_contract(self) -> None:
        """`/devices` 成功响应保持历史 schema，不从 health schema 派生。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        snapshot = {
            "paths": ["/dev/video1"],
            "v4l2_list_devices": {"available": True},
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ],
            "writes_controls": False,
            "opens_serial": False,
            "sends_motion_commands": False,
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            payload = state.current_devices()

        self.assertEqual("trashbot.local_webrtc_camera_devices.v1", payload["schema"])
        self.assertEqual("/dev/video1", payload["video_source"])
        self.assertFalse(payload["safe_to_control"])

    def test_close_success_schema_uses_historical_contract(self) -> None:
        """`/peers/{peer_id}/close` 成功响应保持历史 close schema。"""
        class FakePc:
            async def close(self) -> None:
                self.closed = True

        class FakeTrack:
            def stop(self) -> None:
                self.stopped = True

        class FakeCapture:
            def release(self) -> None:
                self.released = True

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        peer = camera.PeerRecord(
            peer_id="abc123",
            pc=FakePc(),
            track=FakeTrack(),
            capture=FakeCapture(),
            source="/dev/video1",
        )
        peer.frames_read = 2
        state.peers[peer.peer_id] = peer

        status, payload = camera.asyncio.run(state.close_peer(peer.peer_id))

        self.assertEqual(200, status)
        self.assertEqual("trashbot.local_webrtc_camera_close.v1", payload["schema"])
        self.assertEqual("closed", payload["status"])
        self.assertEqual(0, payload["active_peer_count"])
        self.assertFalse(payload["safe_to_control"])

    def test_shared_capture_reuses_single_videocapture_for_same_source(self) -> None:
        """多客户端预览同一个 UVC 源时不能重复打开设备。"""

        class FakeRawCapture:
            def __init__(self) -> None:
                self.released = False
                self.set_calls: list[tuple[int, int]] = []

            def isOpened(self) -> bool:  # noqa: N802 - 模拟 OpenCV API。
                return True

            def set(self, key: int, value: int) -> None:
                self.set_calls.append((key, value))

            def read(self) -> tuple[bool, list[list[list[int]]]]:
                return True, [[[12, 34, 56]]]

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_FRAME_WIDTH = 3
            CAP_PROP_FRAME_HEIGHT = 4
            CAP_PROP_FPS = 5

            def __init__(self) -> None:
                self.captures: list[FakeRawCapture] = []

            def VideoCapture(self, source: str) -> FakeRawCapture:  # noqa: N802 - 模拟 OpenCV API。
                self.captures.append(FakeRawCapture())
                return self.captures[-1]

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        fake_cv2 = FakeCv2()

        first, first_error = state.acquire_shared_capture("/dev/video1", fake_cv2)
        second, second_error = state.acquire_shared_capture("/dev/video1", fake_cv2)

        self.assertIsNone(first_error)
        self.assertIsNone(second_error)
        self.assertIs(first, second)
        self.assertEqual(1, len(fake_cv2.captures))
        self.assertEqual(2, first.ref_count)
        self.assertFalse(first.release_ref())
        self.assertFalse(fake_cv2.captures[0].released)
        self.assertTrue(second.release_ref())
        self.assertTrue(fake_cv2.captures[0].released)

    def test_shared_capture_falls_back_to_numeric_index_for_dev_video_path(self) -> None:
        """部分 OpenCV/V4L2 组合能用索引打开但不能用路径打开，服务应自动兜底。"""

        class FakeRawCapture:
            def __init__(self, opened: bool) -> None:
                self.opened = opened
                self.released = False

            def isOpened(self) -> bool:  # noqa: N802 - 模拟 OpenCV API。
                return self.opened

            def set(self, _key: int, _value: object) -> None:
                return None

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            def __init__(self) -> None:
                self.sources: list[str | int] = []
                self.captures: list[FakeRawCapture] = []

            def VideoCapture(self, source: str | int) -> FakeRawCapture:  # noqa: N802 - 模拟 OpenCV API。
                self.sources.append(source)
                capture = FakeRawCapture(opened=source == 1)
                self.captures.append(capture)
                return capture

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        fake_cv2 = FakeCv2()

        shared, error = state.acquire_shared_capture("/dev/video1", fake_cv2, apply_settings=False)

        self.assertIsNone(error)
        self.assertIsNotNone(shared)
        assert shared is not None
        self.assertEqual(["/dev/video1", 1], fake_cv2.sources)
        self.assertTrue(fake_cv2.captures[0].released)
        self.assertFalse(fake_cv2.captures[1].released)
        self.assertEqual("index:1", shared.summary()["open_source"])

    def test_shared_capture_read_timeout_marks_source_failed_and_releases(self) -> None:
        """V4L2 read 卡住时必须快速失败，不能让 PC 画面一直显示等待。"""

        class BlockingRawCapture:
            def __init__(self) -> None:
                self.released = False

            def read(self) -> tuple[bool, None]:
                time.sleep(1.0)
                return False, None

            def release(self) -> None:
                self.released = True

        raw_capture = BlockingRawCapture()
        shared = camera.SharedCameraCapture(
            source="/dev/video1",
            capture=raw_capture,
            width=640,
            height=480,
            fps=15,
        )
        started = time.monotonic()

        ok, frame = shared.read_frame_with_timeout(0.05)

        self.assertFalse(ok)
        self.assertIsNone(frame)
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertEqual("capture_read_call_timeout", shared.last_error)
        self.assertTrue(shared.released)
        self.assertTrue(raw_capture.released)

    def test_shared_capture_first_frame_warmup_retries_false_reads(self) -> None:
        """UVC 刚打开时允许短暂 false 帧 warmup，但成功边界仍必须是真实帧。"""

        frame = object()

        class WarmupRawCapture:
            def __init__(self) -> None:
                self.read_count = 0
                self.released = False

            def read(self) -> tuple[bool, object | None]:
                self.read_count += 1
                if self.read_count < 3:
                    return False, None
                return True, frame

            def release(self) -> None:
                self.released = True

        raw_capture = WarmupRawCapture()
        shared = camera.SharedCameraCapture(
            source="/dev/video1",
            capture=raw_capture,
            width=640,
            height=480,
            fps=15,
        )

        ok, observed, attempts = shared.read_frame_until_success(0.5)

        self.assertTrue(ok)
        self.assertIs(frame, observed)
        self.assertEqual(3, attempts)
        self.assertEqual(1, shared.frames_read)
        self.assertEqual(2, shared.read_failures)
        self.assertFalse(shared.released)
        self.assertFalse(raw_capture.released)

    def test_first_frame_capture_falls_back_to_yuyv_after_mjpg_failure(self) -> None:
        """MJPG 首帧失败时应释放句柄再试 YUYV，避免一个格式失败挡住真实画面。"""

        frame = object()

        class FormatCapture:
            def __init__(self, name: str) -> None:
                self.name = name
                self.released = False
                self.fourcc_value: int | None = None
                self.fps_value: int | None = None

            def isOpened(self) -> bool:  # noqa: N802 - 模拟 OpenCV API。
                return True

            def set(self, prop: int, value: object) -> None:
                if prop == 6:
                    self.fourcc_value = int(value)
                if prop == 5:
                    self.fps_value = int(value)

            def read(self) -> tuple[bool, object | None]:
                if self.name == "mjpg" or self.fps_value != 22:
                    return False, None
                return True, frame

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_FOURCC = 6
            CAP_PROP_FRAME_WIDTH = 3
            CAP_PROP_FRAME_HEIGHT = 4
            CAP_PROP_FPS = 5

            def __init__(self) -> None:
                self.captures: list[FormatCapture] = []

            def VideoWriter_fourcc(self, *letters: str) -> int:  # noqa: N802 - 模拟 OpenCV API。
                return 100 if "".join(letters) == "MJPG" else 200

            def VideoCapture(self, _source: str) -> FormatCapture:  # noqa: N802 - 模拟 OpenCV API。
                capture = FormatCapture("mjpg" if len(self.captures) < 4 else "yuyv")
                self.captures.append(capture)
                return capture

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        fake_cv2 = FakeCv2()
        with mock.patch.object(camera, "FIRST_FRAME_TIMEOUT_S", 0.02):
            shared, observed, attempts, error = state.acquire_first_frame_capture("/dev/video1", fake_cv2)

        self.assertIsNone(error)
        self.assertIs(frame, observed)
        self.assertIsNotNone(shared)
        assert shared is not None
        self.assertEqual("YUYV", shared.fourcc)
        self.assertTrue(all(capture.released for capture in fake_cv2.captures[:5]))
        self.assertFalse(fake_cv2.captures[5].released)
        self.assertEqual(
            ["MJPG@640x480@15", "MJPG@640x480@30", "MJPG@1280x720@30", "MJPG@480x320@30", "YUYV@640x480@15", "YUYV@640x480@22"],
            [item["label"] for item in attempts],
        )
        self.assertEqual("first_frame_unreadable", attempts[0]["status"])
        self.assertEqual("frame_read", attempts[5]["status"])

    def test_first_frame_total_budget_stops_mjpeg_before_full_matrix(self) -> None:
        """共享 MJPEG 无帧时要及时返回诊断，不能让 PC 首屏等完整 9 格式矩阵。"""

        class NoFrameCapture:
            def __init__(self) -> None:
                self.released = False

            def isOpened(self) -> bool:  # noqa: N802 - 模拟 OpenCV API。
                return True

            def set(self, _prop: int, _value: object) -> None:
                return None

            def read(self) -> tuple[bool, None]:
                return False, None

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_FOURCC = 6
            CAP_PROP_FRAME_WIDTH = 3
            CAP_PROP_FRAME_HEIGHT = 4
            CAP_PROP_FPS = 5

            def __init__(self) -> None:
                self.captures: list[NoFrameCapture] = []

            def VideoWriter_fourcc(self, *_letters: str) -> int:  # noqa: N802 - 模拟 OpenCV API。
                return 100

            def VideoCapture(self, _source: str) -> NoFrameCapture:  # noqa: N802 - 模拟 OpenCV API。
                capture = NoFrameCapture()
                self.captures.append(capture)
                return capture

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        fake_cv2 = FakeCv2()

        with mock.patch.object(camera, "FIRST_FRAME_WARMUP_INTERVAL_S", 0.001):
            shared, observed, attempts, error = state.acquire_first_frame_capture(
                "/dev/video1",
                fake_cv2,
                timeout_s=0.02,
                total_timeout_s=0.055,
            )

        self.assertIsNone(shared)
        self.assertIsNone(observed)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertEqual("first_frame_total_timeout", error["failure_reason"])
        self.assertLess(len(attempts), len(camera.camera_capture_attempt_specs(640, 480, 15)))
        self.assertGreaterEqual(len(attempts), 1)
        self.assertTrue(all(capture.released for capture in fake_cv2.captures))
        self.assertEqual(attempts, error["first_frame_format_attempts"])

    def test_mjpeg_attempt_specs_cover_yuyv_and_default_before_extra_mjpg_modes(self) -> None:
        """共享预览短窗口内优先试 native 和低带宽离散模式，避免漏掉当前协商模式。"""
        specs = camera.mjpeg_camera_capture_attempt_specs(640, 480, 15)

        self.assertEqual(
            ["MJPG@640x480@30", "MJPG@1280x720@30", "MJPG@480x320@30", "YUYV@320x240@25", "MJPG@160x120@30", "YUYV@160x120@20"],
            [spec.label() for spec in specs[:6]],
        )
        self.assertIn("default@current", [spec.label() for spec in specs])
        self.assertEqual(len(specs), len({(spec.fourcc, spec.width, spec.height, spec.fps, spec.apply_settings) for spec in specs}))

    def test_mjpeg_attempt_budget_reaches_yuyv_and_default_modes(self) -> None:
        """MJPEG 每次尝试必须足够短，让现场 DV20 的小帧 YUYV/default 真正被执行到。"""
        critical_attempt_count = 6

        self.assertLess(camera.MJPEG_FIRST_FRAME_TIMEOUT_S, camera.FIRST_FRAME_TIMEOUT_S)
        self.assertLessEqual(
            camera.MJPEG_FIRST_FRAME_TIMEOUT_S * critical_attempt_count,
            camera.MJPEG_PRIMARY_SOURCE_TOTAL_TIMEOUT_S,
        )
        self.assertLessEqual(
            camera.MJPEG_PRIMARY_SOURCE_TOTAL_TIMEOUT_S + camera.MJPEG_OPEN_SOURCE_FALLBACK_TOTAL_TIMEOUT_S,
            camera.MJPEG_FIRST_FRAME_TOTAL_TIMEOUT_S,
        )

    def test_mjpeg_short_budget_tries_formats_before_open_source_fallbacks(self) -> None:
        """共享预览不能把短预算全花在同一格式的 path/index/backend fallback 上。"""

        class NoFrameCapture:
            def __init__(self) -> None:
                self.released = False

            def isOpened(self) -> bool:  # noqa: N802 - 模拟 OpenCV API。
                return True

            def set(self, _prop: int, _value: object) -> None:
                return None

            def read(self) -> tuple[bool, None]:
                return False, None

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_FOURCC = 6
            CAP_PROP_FRAME_WIDTH = 3
            CAP_PROP_FRAME_HEIGHT = 4
            CAP_PROP_FPS = 5
            CAP_V4L2 = 200

            def __init__(self) -> None:
                self.captures: list[NoFrameCapture] = []

            def VideoWriter_fourcc(self, *_letters: str) -> int:  # noqa: N802 - 模拟 OpenCV API。
                return 100

            def VideoCapture(self, _source: str | int, _backend: int | None = None) -> NoFrameCapture:  # noqa: N802 - 模拟 OpenCV API。
                capture = NoFrameCapture()
                self.captures.append(capture)
                return capture

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        fake_cv2 = FakeCv2()

        with mock.patch.object(camera, "FIRST_FRAME_WARMUP_INTERVAL_S", 0.001):
            _shared, _observed, attempts, error = state.acquire_first_frame_capture(
                "/dev/video1",
                fake_cv2,
                timeout_s=0.01,
                total_timeout_s=1.0,
                specs=camera.mjpeg_camera_capture_attempt_specs(640, 480, 15),
                include_open_source_fallbacks=False,
            )

        self.assertIsNotNone(error)
        self.assertGreaterEqual(len(attempts), 3)
        self.assertEqual(["MJPG@640x480@30", "MJPG@1280x720@30", "MJPG@480x320@30"], [item["label"] for item in attempts[:3]])
        self.assertIn("MJPG@160x120@30", [item["label"] for item in attempts])
        self.assertIn("YUYV@160x120@20", [item["label"] for item in attempts])
        self.assertEqual(["/dev/video1", "/dev/video1", "/dev/video1"], [item["open_source"] for item in attempts[:3]])
        self.assertEqual(["default", "default", "default"], [item["open_backend"] for item in attempts[:3]])
        self.assertTrue(all(capture.released for capture in fake_cv2.captures))

    def test_mjpeg_default_preview_retries_open_source_fallback_after_priority_formats(self) -> None:
        """默认 MJPEG 预览第一段先试低带宽格式，失败后再试 index/V4L2 打开兜底。"""

        frame = object()

        class FallbackCapture:
            def __init__(self, source: str | int, backend: int | None) -> None:
                self.source = source
                self.backend = backend
                self.released = False

            def isOpened(self) -> bool:  # noqa: N802 - 模拟 OpenCV API。
                return True

            def set(self, _prop: int, _value: object) -> None:
                return None

            def read(self) -> tuple[bool, object | None]:
                if self.source == 1 and self.backend is None:
                    return True, frame
                return False, None

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_FOURCC = 6
            CAP_PROP_FRAME_WIDTH = 3
            CAP_PROP_FRAME_HEIGHT = 4
            CAP_PROP_FPS = 5
            CAP_V4L2 = 200

            def __init__(self) -> None:
                self.calls: list[tuple[str | int, int | None]] = []
                self.captures: list[FallbackCapture] = []

            def VideoWriter_fourcc(self, *_letters: str) -> int:  # noqa: N802 - 模拟 OpenCV API。
                return 100

            def VideoCapture(self, source: str | int, backend: int | None = None) -> FallbackCapture:  # noqa: N802 - 模拟 OpenCV API。
                self.calls.append((source, backend))
                capture = FallbackCapture(source, backend)
                self.captures.append(capture)
                return capture

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        fake_cv2 = FakeCv2()

        def fake_first_frame_read(shared_capture: camera.SharedCameraCapture, _timeout_s: float) -> tuple[bool, object | None, int]:
            if shared_capture.open_source == 1 and shared_capture.open_backend == "default":
                return True, frame, 1
            shared_capture.last_error = "capture_read_returned_false"
            return False, None, 1

        with mock.patch.object(camera.SharedCameraCapture, "read_frame_until_success", fake_first_frame_read):
            shared, observed, attempts, error = state.acquire_mjpeg_first_frame_capture("/dev/video1", fake_cv2)

        self.assertIsNone(error)
        self.assertIs(frame, observed)
        self.assertIsNotNone(shared)
        assert shared is not None
        first_fallback_index = next(index for index, item in enumerate(attempts) if item["open_backend"] == "CAP_V4L2")
        self.assertEqual(
            ["MJPG@640x480@30", "MJPG@1280x720@30", "MJPG@480x320@30"],
            [item["label"] for item in attempts[:3]],
        )
        self.assertIn("MJPG@160x120@30", [item["label"] for item in attempts[:first_fallback_index]])
        self.assertIn("YUYV@160x120@20", [item["label"] for item in attempts[:first_fallback_index]])
        self.assertTrue(all(item["open_source"] == "/dev/video1" for item in attempts[:first_fallback_index]))
        self.assertTrue(all(item["open_backend"] == "default" for item in attempts[:first_fallback_index]))
        self.assertEqual(["/dev/video1", "index:1"], [item["open_source"] for item in attempts[-2:]])
        self.assertEqual(["CAP_V4L2", "default"], [item["open_backend"] for item in attempts[-2:]])
        self.assertEqual("frame_read", attempts[-1]["status"])
        self.assertIn(("/dev/video1", 200), fake_cv2.calls)
        self.assertEqual((1, None), fake_cv2.calls[-1])
        self.assertEqual("index:1", shared.summary()["open_source"])
        self.assertTrue(all(capture.released for capture in fake_cv2.captures[:-1]))
        self.assertFalse(fake_cv2.captures[-1].released)

    def test_stale_no_frame_peer_is_closed_before_new_offer(self) -> None:
        """卡在 new/0 帧的旧 peer 必须自动释放，避免长期占用 `/dev/video1`。"""

        class FakePc:
            async def close(self) -> None:
                self.closed = True

        class FakeTrack:
            def stop(self) -> None:
                self.stopped = True

        class FakeCapture:
            def __init__(self) -> None:
                self.released = False

            def release(self) -> None:
                self.released = True

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        capture = FakeCapture()
        peer = camera.PeerRecord(
            peer_id="stale123",
            pc=FakePc(),
            track=FakeTrack(),
            capture=capture,
            source="/dev/video1",
            created_ts_ms=camera.now_ms() - camera.STALE_PEER_NO_FRAME_MAX_AGE_MS - 1,
        )
        peer.connection_state = "new"
        peer.ice_connection_state = "new"
        state.peers[peer.peer_id] = peer

        closed = camera.asyncio.run(state.close_stale_peers())

        self.assertEqual([{"peer_id": "stale123", "http_status": 200, "status": "closed"}], closed)
        self.assertEqual({}, state.peers)
        self.assertTrue(capture.released)
        self.assertEqual("stale_no_frame_peer_replaced", state.last_closed_peer["cleanup"]["reason"])

    def test_health_exposes_required_safety_and_selection_fields(self) -> None:
        """health 必须能被 PC 诊断消费，同时保持控制字段关闭。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ]
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            payload = state.health()

        self.assertEqual(camera.SCHEMA, payload["schema"])
        self.assertEqual(camera.APP_NAME, payload["app"])
        self.assertEqual("source_not_probed", payload["status"])
        self.assertEqual("source_selected_not_probed", payload["source_readiness"])
        self.assertEqual("", payload["source_failure_reason"])
        self.assertEqual([], payload["last_first_frame_format_attempts"])
        self.assertEqual("/dev/video1", payload["video_source"])

    def test_health_exposes_last_first_frame_attempt_open_method(self) -> None:
        """MJPEG 首帧失败后，health 要保留打开方式矩阵，PC 不必重新开流也能复盘。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        state.last_offer_error = {
            "error": "first_frame_unreadable",
            "failure_reason": "first_frame_total_timeout",
            "video_source": "/dev/video1",
            "first_frame_format_attempts": [
                {
                    "label": "MJPG@640x480@30",
                    "open_source": "/dev/video1",
                    "open_backend": "CAP_V4L2",
                    "status": "first_frame_unreadable",
                }
            ],
        }
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ]
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            payload = state.health()

        self.assertEqual("source_first_frame_failed", payload["status"])
        self.assertEqual("first_frame_failed", payload["source_readiness"])
        self.assertEqual("first_frame_total_timeout", payload["source_failure_reason"])
        self.assertEqual("CAP_V4L2", payload["last_first_frame_format_attempts"][0]["open_backend"])
        self.assertEqual("/dev/video1", payload["last_first_frame_format_attempts"][0]["open_source"])
        self.assertEqual("auto", payload["video_source_mode"])
        self.assertEqual(0, payload["active_peer_count"])
        self.assertEqual(0, payload["active_frames_read"])
        self.assertEqual(0, payload["active_camera_read_failures"])
        self.assertIn("system_diagnostics", payload)
        self.assertIn("media_diagnostics", payload)
        self.assertIn("source_candidates_summary", payload)
        self.assertEqual("single_shared_capture_for_multiple_clients", payload["shared_preview_contract"])
        self.assertEqual("video_capture", payload["current_selection"]["selected_role"])
        self.assertEqual("none", payload["current_selection"]["selected_sibling_video_nodes_summary"])
        self.assertEqual("uvc_no_frame_not_exclusive", payload["source_diagnosis"]["status"])
        self.assertTrue(payload["source_diagnosis"]["not_exclusive"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])

    def test_health_marks_selected_source_failed_after_first_frame_offer_error(self) -> None:
        """最近 offer 已证明首帧失败时，health 不能继续把源说成 ready。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        state.last_offer_error = {
            "error": "first_frame_unreadable",
            "failure_reason": "capture_read_returned_false",
            "video_source": "/dev/video1",
        }
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ]
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            payload = state.health()

        self.assertEqual("source_first_frame_failed", payload["status"])
        self.assertEqual("first_frame_failed", payload["source_readiness"])
        self.assertEqual("capture_read_returned_false", payload["source_failure_reason"])
        self.assertEqual("uvc_no_frame_not_exclusive", payload["source_diagnosis"]["status"])
        self.assertIn("不是页面独占", payload["source_diagnosis"]["plain_hint"])
        self.assertEqual("check_usb_camera_input_power_or_known_good_uvc", payload["source_diagnosis"]["next_action"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])

    def test_health_keeps_self_owned_shared_capture_not_exclusive(self) -> None:
        """8088 自己短暂持有 shared capture 时，不能把无首帧误写成页面独占。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        state.last_offer_error = {
            "error": "first_frame_unreadable",
            "failure_reason": "first_frame_total_timeout",
            "video_source": "/dev/video1",
        }
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ]
        }
        usage = {
            "checked": True,
            "device": "/dev/video1",
            "status": "in_use_by_camera_service",
            "owner_count": 1,
            "other_owner_count": 0,
            "owners": [{"pid": 1234, "self": True, "command": "local_webrtc_camera_smoke.py"}],
            "opens_camera": False,
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            with mock.patch.object(camera, "collect_device_usage", return_value=usage):
                payload = state.health()

        self.assertEqual("uvc_no_frame_not_exclusive", payload["source_diagnosis"]["status"])
        self.assertTrue(payload["source_diagnosis"]["not_exclusive"])
        self.assertIn("不是页面独占", payload["source_diagnosis"]["plain_hint"])

    def test_uvc_kernel_diagnostics_scans_full_dmesg_for_old_transport_errors(self) -> None:
        """UVC 传输错误可能被后续日志挤出短 tail，但仍要进入 health 归因。"""
        old_error = "[695752.523424] uvcvideo 3-1:1.1: Failed to initialize the device (-5)."
        newer_error = "[777980.953405] usb 3-1: can't read configurations, error -71"
        filler = "\n".join(f"[800000.{index:06d}] unrelated service log" for index in range(700))
        dmesg_text = f"{old_error}\n{filler}\n{newer_error}\n"
        completed = camera.subprocess.CompletedProcess(["dmesg"], 0, stdout=dmesg_text, stderr="")
        candidate = {
            "path": "/dev/video1",
            "v4l2_name": "USB Composite Device: DV20 USB",
            "sysfs_name": "USB Composite Device: DV20 USB",
            "readonly_probe": {
                "v4l2_all": {
                    "stdout": "Driver Info:\n\tBus info         : usb-5310400.usb-1\n",
                },
            },
        }

        with mock.patch.object(camera.shutil, "which", return_value="/bin/dmesg"):
            with mock.patch.object(camera.subprocess, "run", return_value=completed):
                diagnostics = camera.collect_uvc_kernel_diagnostics("/dev/video1", candidate)

        self.assertEqual("uvc_usb_transport_errors_observed", diagnostics["status"])
        self.assertEqual(2, diagnostics["transport_error_count"])
        self.assertIn("can't read configurations", diagnostics["latest_transport_error"])
        self.assertIn("UVC/USB 传输错误", diagnostics["plain_hint"])
        self.assertFalse(diagnostics["opens_camera"])
        self.assertFalse(diagnostics["safe_to_control"])

    def test_uvc_usb_topology_marks_full_speed_video_device(self) -> None:
        """UVC 掉到 12M full-speed 时，health 要直接给现场可执行的换口/换线建议。"""
        topology = """/:  Bus 06.Port 1: Dev 1, Class=root_hub, Driver=ohci-platform/1p, 12M
    |__ Port 1: Dev 2, If 0, Class=Video, Driver=uvcvideo, 12M
    |__ Port 1: Dev 2, If 1, Class=Video, Driver=uvcvideo, 12M
/:  Bus 03.Port 1: Dev 1, Class=root_hub, Driver=ehci-platform/1p, 480M
"""
        completed = camera.subprocess.CompletedProcess(["lsusb", "-t"], 0, stdout=topology, stderr="")
        candidate = {
            "path": "/dev/video1",
            "v4l2_name": "USB Composite Device: DV20 USB",
            "sysfs_name": "USB Composite Device: DV20 USB",
            "readonly_probe": {
                "v4l2_all": {
                    "stdout": "Driver Info:\n\tBus info         : usb-5310400.usb-1\n",
                },
            },
        }

        with mock.patch.object(camera.shutil, "which", return_value="/usr/bin/lsusb"):
            with mock.patch.object(camera.subprocess, "run", return_value=completed):
                diagnostics = camera.collect_uvc_usb_topology_diagnostics("/dev/video1", candidate)

        self.assertEqual("uvc_video_on_full_speed_usb", diagnostics["status"])
        self.assertEqual("12M", diagnostics["video_usb_speed"])
        self.assertEqual("6-1", diagnostics["kernel_usb_address"])
        self.assertEqual("move_camera_to_high_speed_usb_port_or_powered_hub", diagnostics["next_action"])
        self.assertIn("full-speed", diagnostics["plain_hint"])
        self.assertFalse(diagnostics["opens_camera"])
        self.assertFalse(diagnostics["safe_to_control"])

    def test_uvc_kernel_diagnostics_keeps_stale_port_errors_out_of_current_root_cause(self) -> None:
        """换到新 USB 地址后，旧端口 UVC 错误只能作为残留证据，不能继续判当前传输错误。"""
        stale_error = "[777980.953405] usb 4-1: device descriptor read/all, error -71"
        current_seen = "[777990.953405] uvcvideo 3-1:1.0: Entity type for entity Camera 1 was not initialized!"
        completed = camera.subprocess.CompletedProcess(["dmesg"], 0, stdout=f"{stale_error}\n{current_seen}\n", stderr="")
        candidate = {
            "path": "/dev/video1",
            "v4l2_name": "USB Composite Device: DV20 USB",
            "sysfs_name": "USB Composite Device: DV20 USB",
            "readonly_probe": {
                "v4l2_all": {
                    "stdout": "Driver Info:\n\tBus info         : usb-5310400.usb-1\n",
                },
            },
        }

        with mock.patch.object(camera, "sysfs_usb_device_for_video", return_value="3-1"):
            with mock.patch.object(camera.shutil, "which", return_value="/bin/dmesg"):
                with mock.patch.object(camera.subprocess, "run", return_value=completed):
                    diagnostics = camera.collect_uvc_kernel_diagnostics("/dev/video1", candidate)

        self.assertEqual("uvc_kernel_seen_without_current_transport_errors", diagnostics["status"])
        self.assertEqual("3-1", diagnostics["current_usb_device"])
        self.assertEqual(0, diagnostics["transport_error_count"])
        self.assertEqual(1, diagnostics["stale_transport_error_count"])
        self.assertIn("usb 4-1", diagnostics["latest_stale_transport_error"])
        self.assertEqual("continue_first_frame_format_diagnostics", diagnostics["next_action"])

    def test_uvc_kernel_diagnostics_treats_same_usb_address_errors_before_reenumeration_as_stale(self) -> None:
        """同一个 `3-1` 地址被重用后，最近枚举前的旧错误不能继续压成当前传输错误。"""
        old_error = "[777992.581028] usb 3-1: device descriptor read/all, error -71"
        reenumerated = "[1003404.281463] usb 3-1: Found UVC 1.00 device USB Composite Device (4c4a:4a55)"
        current_seen = "[1003404.291463] usb 3-1: authorized to connect"
        completed = camera.subprocess.CompletedProcess(
            ["dmesg"],
            0,
            stdout=f"{old_error}\n{reenumerated}\n{current_seen}\n",
            stderr="",
        )
        candidate = {
            "path": "/dev/video1",
            "v4l2_name": "USB Composite Device: DV20 USB",
            "sysfs_name": "USB Composite Device: DV20 USB",
            "readonly_probe": {
                "v4l2_all": {
                    "stdout": "Driver Info:\n\tBus info         : usb-5310400.usb-1\n",
                },
            },
        }

        with mock.patch.object(camera, "sysfs_usb_device_for_video", return_value="3-1"):
            with mock.patch.object(camera.shutil, "which", return_value="/bin/dmesg"):
                with mock.patch.object(camera.subprocess, "run", return_value=completed):
                    diagnostics = camera.collect_uvc_kernel_diagnostics("/dev/video1", candidate)

        self.assertEqual("uvc_kernel_seen_without_current_transport_errors", diagnostics["status"])
        self.assertEqual(0, diagnostics["transport_error_count"])
        self.assertEqual(1, diagnostics["stale_transport_error_count"])
        self.assertEqual(1003404.291463, diagnostics["latest_current_enumeration_s"])
        self.assertIn("usb 3-1", diagnostics["latest_stale_transport_error"])

    def test_uvc_usb_topology_prefers_current_sysfs_device_over_other_full_speed_video(self) -> None:
        """同机存在其它 12M Video 设备时，当前摄像头 480M 不能被误判 full-speed。"""
        topology = """/:  Bus 06.Port 1: Dev 1, Class=root_hub, Driver=ohci-platform/1p, 12M
    |__ Port 1: Dev 2, If 0, Class=Video, Driver=uvcvideo, 12M
/:  Bus 03.Port 1: Dev 1, Class=root_hub, Driver=ehci-platform/1p, 480M
    |__ Port 1: Dev 19, If 0, Class=Video, Driver=uvcvideo, 480M
"""
        completed = camera.subprocess.CompletedProcess(["lsusb", "-t"], 0, stdout=topology, stderr="")
        candidate = {
            "path": "/dev/video1",
            "v4l2_name": "USB Composite Device: DV20 USB",
            "sysfs_name": "USB Composite Device: DV20 USB",
            "readonly_probe": {
                "v4l2_all": {
                    "stdout": "Driver Info:\n\tBus info         : usb-5310400.usb-1\n",
                },
            },
        }

        with mock.patch.object(camera, "sysfs_usb_device_for_video", return_value="3-1"):
            with mock.patch.object(camera.shutil, "which", return_value="/usr/bin/lsusb"):
                with mock.patch.object(camera.subprocess, "run", return_value=completed):
                    diagnostics = camera.collect_uvc_usb_topology_diagnostics("/dev/video1", candidate)

        self.assertEqual("uvc_video_usb_speed_loaded", diagnostics["status"])
        self.assertEqual("480M", diagnostics["video_usb_speed"])
        self.assertEqual("3-1", diagnostics["kernel_usb_address"])
        self.assertTrue(diagnostics["selected_by_sysfs_usb_device"])
        self.assertTrue(diagnostics["high_speed_observed"])
        self.assertEqual("continue_first_frame_format_diagnostics", diagnostics["next_action"])

    def test_source_diagnosis_prefers_kernel_transport_error_when_not_exclusive(self) -> None:
        """无首帧且无人占用时，如内核已有 -71/URB 错误，要指向 USB 链路。"""
        diagnosis = camera.build_source_diagnosis(
            "/dev/video1",
            source_failed=True,
            source_observed=False,
            source_usage={
                "status": "not_in_use",
                "owner_count": 0,
                "other_owner_count": 0,
            },
            selected_candidate={
                "v4l2_name": "USB Composite Device: DV20 USB",
                "is_uvc_or_usb": True,
            },
            last_offer_reason="first_frame_total_timeout",
            uvc_kernel_diagnostics={
                "status": "uvc_usb_transport_errors_observed",
            },
        )

        self.assertEqual("uvc_transport_error_not_exclusive", diagnosis["status"])
        self.assertEqual("check_usb_cable_port_power_or_known_good_uvc", diagnosis["next_action"])
        self.assertTrue(diagnosis["not_exclusive"])
        self.assertIn("不是页面独占", diagnosis["plain_hint"])
        self.assertIn("UVC/USB 传输错误", diagnosis["plain_hint"])

    def test_source_diagnosis_prefers_full_speed_usb_when_not_exclusive(self) -> None:
        """摄像头挂在 12M full-speed 时，比泛化传输错误更应该先提示换高速口/线。"""
        diagnosis = camera.build_source_diagnosis(
            "/dev/video1",
            source_failed=True,
            source_observed=False,
            source_usage={
                "status": "not_in_use",
                "owner_count": 0,
                "other_owner_count": 0,
            },
            selected_candidate={
                "v4l2_name": "USB Composite Device: DV20 USB",
                "is_uvc_or_usb": True,
            },
            last_offer_reason="first_frame_total_timeout",
            uvc_kernel_diagnostics={
                "status": "uvc_usb_transport_errors_observed",
            },
            uvc_usb_topology={
                "status": "uvc_video_on_full_speed_usb",
                "video_usb_speed": "12M",
            },
        )

        self.assertEqual("uvc_full_speed_usb_not_exclusive", diagnosis["status"])
        self.assertEqual("move_camera_to_high_speed_usb_port_or_powered_hub", diagnosis["next_action"])
        self.assertEqual("uvc_video_on_full_speed_usb", diagnosis["uvc_usb_topology_status"])
        self.assertEqual("12M", diagnosis["uvc_usb_topology_video_usb_speed"])
        self.assertIn("full-speed", diagnosis["plain_hint"])
        self.assertIn("不是页面独占", diagnosis["plain_hint"])

    def test_health_reports_selected_source_usage_without_opening_camera(self) -> None:
        """health 要能解释占用状态，但不能通过 OpenCV 或 V4L2 打开摄像头。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ]
        }
        usage = {
            "checked": True,
            "device": "/dev/video1",
            "status": "in_use_by_probe",
            "owner_count": 1,
            "other_owner_count": 1,
            "owners": [{"pid": 1234, "self": False, "command": "camera_first_frame_probe.py"}],
            "opens_camera": False,
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            with mock.patch.object(camera, "collect_device_usage", return_value=usage) as usage_mock:
                payload = state.health()

        usage_mock.assert_called_once_with("/dev/video1")
        self.assertEqual(usage, payload["source_usage"])
        self.assertEqual(usage, payload["media_diagnostics"]["source_usage"])
        self.assertFalse(payload["source_usage"]["opens_camera"])

    def test_health_marks_source_observed_only_after_real_frame(self) -> None:
        """只有真实读到帧后，health 才能把选中源升级为可用于建图的 ready。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        frame = mock.Mock()
        frame.shape = (480, 640, 3)
        state.mark_successful_frame("/dev/video1", frame, "webrtc_offer")
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ]
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            with mock.patch.object(camera, "collect_device_usage", return_value={"checked": True, "status": "not_in_use", "opens_camera": False}):
                payload = state.health()

        self.assertEqual("ready", payload["status"])
        self.assertEqual("first_frame_observed", payload["source_readiness"])
        self.assertEqual("/dev/video1", payload["last_successful_frame"]["source"])
        self.assertEqual("webrtc_offer", payload["last_successful_frame"]["channel"])
        self.assertEqual(640, payload["last_successful_frame"]["width"])


if __name__ == "__main__":
    unittest.main()

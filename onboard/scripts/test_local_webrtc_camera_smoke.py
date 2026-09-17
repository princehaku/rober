#!/usr/bin/env python3
"""local_webrtc_camera_smoke.py 的轻量资源释放测试。"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("local_webrtc_camera_smoke.py")


def load_smoke_module():
    """按文件路径导入脚本，避免测试依赖 ROS2 包安装或 PYTHONPATH。"""
    spec = importlib.util.spec_from_file_location("local_webrtc_camera_smoke", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_load:{SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTrack:
    """fake track 只记录 stop 次数，用来证明 close path 真的释放本地 track。"""

    kind = "video"

    def __init__(self) -> None:
        self.stop_calls = 0

    def stop(self) -> None:
        # 真实 CameraTrack.stop 会 release OpenCV cap；单测只验证调用语义。
        self.stop_calls += 1


class FakeSender:
    """aiortc sender 的最小替身，只暴露 cleanup helper 需要的 track 字段。"""

    def __init__(self, track: FakeTrack) -> None:
        self.track = track


class FakePeerConnection:
    """fake peer 避免引入 aiortc/cv2，让资源释放测试在普通 Python 环境可跑。"""

    def __init__(self, track: FakeTrack) -> None:
        self.track = track
        self.close_calls = 0

    def getSenders(self) -> list[FakeSender]:
        return [FakeSender(self.track)]

    async def close(self) -> None:
        self.close_calls += 1


class FakeCapture:
    """fake OpenCV capture 用于证明 auto source 会跳过不可读的视频节点。"""

    def __init__(self, source, outcomes) -> None:
        self.source = source
        self.outcomes = outcomes
        self.released = False

    def isOpened(self) -> bool:
        return bool(self.outcomes.get(self.source, {}).get("opened"))

    def read(self):
        outcome = self.outcomes.get(self.source, {})
        if not outcome.get("read_ok"):
            return False, None
        return True, object()

    def set(self, *_args) -> bool:
        return True

    def getBackendName(self) -> str:
        return "FAKE"

    def release(self) -> None:
        self.released = True


class FakeCv2:
    """fake cv2 只提供 auto source 选择需要的 VideoCapture 和常量。"""

    CAP_V4L2 = 200
    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4
    CAP_PROP_FPS = 5

    def __init__(self, outcomes) -> None:
        self.outcomes = outcomes
        self.opened_sources = []

    def VideoCapture(self, source, *_args):  # noqa: N802 - 模拟 OpenCV API 名称。
        self.opened_sources.append(source)
        return FakeCapture(source, self.outcomes)


class FakeCpuPsutil:
    """离线采样替身公开计数，性能探针可复用且不查询真实 CPU。"""

    def __init__(self) -> None:
        # 创建次数只统计 CPU 路径；内存诊断的独立 Process 不属于本探针。
        self.process_creations = 0
        self.process_sample_calls = 0
        self.system_sample_calls = 0
        self.intervals = []
        # 显式故障开关验证恢复过程，钩子用于构造确定性的采样争用。
        self.process_error = None
        self.system_error = None
        self.on_process_sample = None

    def Process(self, _pid):  # noqa: N802 - 保留 psutil 的公开工厂名称。
        # 工厂计数独立于读取计数，能够识别每请求重建对象的原始回归。
        self.process_creations += 1
        owner = self

        class ProcessSample:
            """每个实例的首个读数为零，用来捕获错误的反复重建。"""

            calls = 0

            def cpu_percent(self, interval=None):
                owner.process_sample_calls += 1
                owner.intervals.append(interval)
                # 钩子在采样锁内执行，其他线程应当立即返回不可用。
                if owner.on_process_sample is not None:
                    owner.on_process_sample()
                if owner.process_error is not None:
                    raise owner.process_error
                self.calls += 1
                return 0.0 if self.calls == 1 else 125.0

        return ProcessSample()

    def cpu_percent(self, interval=None):
        # 固定值只供路由验证；是否预热由待测采样器的线程窗口判断。
        self.system_sample_calls += 1
        self.intervals.append(interval)
        if self.system_error is not None:
            raise self.system_error
        return 25.0


class CpuPercentSamplerTest(unittest.TestCase):
    """差分窗口与并发协议用可控时钟验证，不依赖机器当时的负载。"""

    def setUp(self) -> None:
        # 每项测试拥有独立基线，避免执行顺序改变预热与故障断言。
        self.module = load_smoke_module()
        self.fake = FakeCpuPsutil()
        self.sampler = self.module.CpuPercentSampler()

    def sample_at(self, at):
        # 进程和系统读取都返回同一个时刻，让窗口断言保持确定性。
        with mock.patch.object(self.module.time, "monotonic", return_value=at):
            return self.sampler.sample(self.fake)

    def test_reuses_process_and_reports_warmup_and_window(self) -> None:
        """三个请求只创建一次对象，并提供两个可解释的差分窗口。"""
        first, second, third = [self.sample_at(at) for at in (1.0, 1.25, 1.75)]
        for name in ("process_cpu_percent", "system_cpu_percent"):
            # 首样本不能向使用者显示有效的 0% CPU。
            self.assertFalse(first[name]["available"])
            self.assertEqual(first[name]["reason"], "warming_up")
            self.assertNotIn("value", first[name])
            # 不等长的间隔能揭示固定窗口或沿用首样本时间的错误。
            self.assertEqual(second[name]["sample_window_ms"], 250.0)
            self.assertEqual(third[name]["sample_window_ms"], 500.0)
            self.assertTrue(second[name]["available"])
        # 多核进程占用允许超过 100%，不能按系统百分比截断。
        self.assertEqual(second["process_cpu_percent"]["value"], 125.0)
        # 同时约束查询次数，防止修复过程中引入隐藏的额外 CPU 读取。
        self.assertEqual(self.fake.process_creations, 1)
        self.assertEqual(self.fake.process_sample_calls, 3)
        self.assertEqual(self.fake.system_sample_calls, 3)
        self.assertTrue(all(interval is None for interval in self.fake.intervals))

    def test_zero_window_stays_unavailable(self) -> None:
        """同刻度读取属于预热状态，后续请求仍能继续采样。"""
        self.sample_at(1.0)
        sample = self.sample_at(1.0)
        # 连续请求碰到同一计时刻度时也不能宣称存在有效差分窗口。
        self.assertFalse(sample["process_cpu_percent"]["available"])
        self.assertEqual(sample["process_cpu_percent"]["sample_window_ms"], 0.0)

    def test_process_and_system_failures_rebuild_and_rewarm(self) -> None:
        """两种故障入口都恢复到新基线，避免只修复进程异常分支。"""
        for error_field in ("process_error", "system_error"):
            with self.subTest(error_field=error_field):
                self.fake = FakeCpuPsutil()
                self.sampler = self.module.CpuPercentSampler()
                self.sample_at(1.0)
                setattr(self.fake, error_field, RuntimeError("fake_cpu_read_failed"))
                failed = self.sample_at(2.0)
                # 部分读取失败后，恢复样本必须重新预热，不能沿用半更新基线。
                setattr(self.fake, error_field, None)
                warmup, valid = self.sample_at(3.0), self.sample_at(3.5)
                # 先核对故障原因，再核对恢复窗口，避免只证明异常被吞掉。
                for name in ("process_cpu_percent", "system_cpu_percent"):
                    self.assertEqual(failed[name]["reason"], "psutil_runtime_error")
                    self.assertEqual(warmup[name]["reason"], "warming_up")
                    self.assertTrue(valid[name]["available"])
                    self.assertEqual(valid[name]["sample_window_ms"], 500.0)
                self.assertEqual(self.fake.process_creations, 2)

    def test_dependency_absence_and_pid_change_reset_baselines(self) -> None:
        """依赖缺失会清理缓存，进程身份变化也触发相同的恢复路径。"""
        self.sample_at(1.0)
        absent = self.sampler.sample(None)
        self.assertEqual(absent["process_cpu_percent"]["reason"], "psutil_not_installed")
        # 依赖恢复或进程身份变化均需重建，防止将旧进程窗口带入新进程。
        self.assertEqual(self.sample_at(2.0)["process_cpu_percent"]["reason"], "warming_up")
        with mock.patch.object(self.module.os, "getpid", return_value=-1):
            self.assertEqual(self.sample_at(3.0)["process_cpu_percent"]["reason"], "warming_up")
        # 统计覆盖初次、依赖恢复、身份变化三个阶段，不依赖内部字段。
        self.assertEqual(self.fake.process_creations, 3)

    def test_system_warmup_is_independent_for_each_thread(self) -> None:
        """线程切换只影响系统 CPU 窗口，进程差分对象仍可安全共享。"""
        self.sample_at(1.0)
        samples = []
        worker = threading.Thread(target=lambda: samples.extend((self.sample_at(2.0), self.sample_at(2.5))))
        worker.start()
        worker.join(timeout=2.0)
        # 超时只负责暴露死锁，不作为 CPU 时延的性能测量结果。
        self.assertFalse(worker.is_alive())
        # 新线程共享进程对象，但 psutil 系统 CPU 的线程基线仍须单独预热。
        self.assertTrue(samples[0]["process_cpu_percent"]["available"])
        self.assertEqual(samples[0]["system_cpu_percent"]["reason"], "warming_up")
        self.assertTrue(samples[1]["system_cpu_percent"]["available"])
        # 回到原线程后，其窗口必须延续原线程的上次读数。
        self.assertEqual(self.sample_at(3.0)["system_cpu_percent"]["sample_window_ms"], 2000.0)
        self.assertEqual(self.fake.process_creations, 1)

    def test_concurrent_request_does_not_wait_for_sampler(self) -> None:
        """用事件顺序验证立即返回，避免使用机器速度相关的毫秒阈值。"""
        entered, release, returned = threading.Event(), threading.Event(), threading.Event()
        samples = []

        def hold_sample():
            # 第一线程停在 fake 内，竞争线程必须在 release 之前完成。
            entered.set()
            release.wait(timeout=3.0)

        def compete():
            samples.append(self.sampler.sample(self.fake))
            returned.set()

        self.fake.on_process_sample = hold_sample
        owner = threading.Thread(target=lambda: self.sampler.sample(self.fake))
        owner.start()
        contender = threading.Thread(target=compete)
        try:
            self.assertTrue(entered.wait(timeout=1.0))
            contender.start()
            self.assertTrue(returned.wait(timeout=1.0))
            self.assertEqual(samples[0]["process_cpu_percent"]["reason"], "sampling_in_progress")
            # 竞争者不能调用后端，否则仍可能交错修改 psutil 内部基线。
            self.assertEqual(self.fake.process_sample_calls, 1)
        finally:
            # 即使断言失败也释放工作线程，避免测试失败后拖住后续验收。
            release.set()
            owner.join(timeout=2.0)
            if contender.ident is not None:
                contender.join(timeout=2.0)
        self.assertFalse(owner.is_alive())

    def test_collector_reuses_service_sampler(self) -> None:
        """替换公开依赖并走 collector，覆盖服务接线与非阻塞采样契约。"""
        with (
            # 注入模块不要求本机安装 psutil，回归在离线环境保持可运行。
            mock.patch.dict(sys.modules, {"psutil": self.fake}),
            mock.patch.object(self.module.importlib.util, "find_spec", return_value=object()),
            mock.patch.object(self.module.time, "monotonic", side_effect=[1.0, 1.0, 1.5, 1.5]),
        ):
            first = self.module.collect_cpu_diagnostics()
            second = self.module.collect_cpu_diagnostics()
        # 验证实际 collector 复用服务级实例，避免仅测试了未接入的帮助类。
        self.assertEqual(first["process_cpu_percent"]["reason"], "warming_up")
        self.assertTrue(second["process_cpu_percent"]["available"])
        self.assertEqual(self.fake.process_creations, 1)


class LocalWebrtcCameraSmokeCleanupTest(unittest.TestCase):
    """资源释放测试必须可用 unittest 直接跑，贴合 sprint 验收命令。"""

    def test_auto_camera_source_selects_first_readable_video_node(self) -> None:
        """默认 auto 必须跳过 cedrus 等不可读节点，选择能读首帧的真实摄像头。"""
        module = load_smoke_module()
        fake_cv2 = FakeCv2(
            {
                "/dev/video0": {"opened": False, "read_ok": False},
                "/dev/video1": {"opened": True, "read_ok": True},
            }
        )

        source, diagnostics = module.resolve_camera_source(
            "auto",
            fake_cv2,
            ["/dev/video0", "/dev/video1"],
            width=640,
            height=480,
            fps=15,
        )

        self.assertEqual(source, "/dev/video1")
        self.assertEqual(fake_cv2.opened_sources, ["/dev/video0", "/dev/video1"])
        self.assertEqual(diagnostics["mode"], "auto")
        self.assertEqual(diagnostics["selected_source"], "/dev/video1")
        self.assertEqual(diagnostics["attempts"][0]["source"], "/dev/video0")
        self.assertFalse(diagnostics["attempts"][0]["opened"])
        self.assertTrue(diagnostics["attempts"][1]["read_ok"])

    def test_health_fail_open_without_psutil_or_temperature_files(self) -> None:
        """缺 psutil/温度 sysfs 时，/health 仍必须返回结构化诊断而不是抛异常。"""
        module = load_smoke_module()
        original_find_spec = module.importlib.util.find_spec

        def fake_find_spec(name: str):
            # 只模拟 psutil 缺失，避免把 aiohttp/aiortc/cv2/av 依赖状态改成测试假象。
            if name == "psutil":
                return None
            return original_find_spec(name)

        with (
            mock.patch.object(module.importlib.util, "find_spec", side_effect=fake_find_spec),
            mock.patch.object(module, "TEMPERATURE_GLOBS", ("/tmp/rober-missing-temp-*",)),
        ):
            payload = module.build_health(8088, "0")

        diagnostics = payload["system_diagnostics"]
        system_metrics = payload["system_metrics"]
        self.assertFalse(diagnostics["cpu"]["process_cpu_percent"]["available"])
        self.assertEqual(diagnostics["cpu"]["process_cpu_percent"]["reason"], "psutil_not_installed")
        self.assertIn(diagnostics["memory"]["available"], (True, False))
        self.assertFalse(diagnostics["temperature"]["available"])
        self.assertEqual(diagnostics["temperature"]["reason"], "temperature_files_not_found")
        self.assertIn("process_uptime_s", system_metrics)
        self.assertIn("temperature_unavailable_reason", system_metrics)
        self.assertEqual(system_metrics["temperature_unavailable_reason"], "temperature_files_not_found")
        self.assertIn("monotonic_s", diagnostics["sample"])
        self.assertGreaterEqual(diagnostics["sample"]["process_uptime_s"], 0)
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_commands"])
        self.assertFalse(payload["robot_control_executed"])

    def test_media_summary_keeps_stable_frame_fields(self) -> None:
        """PC 轮询需要稳定摘要，不应依赖 active_peers 里的原始内部字段名。"""
        module = load_smoke_module()
        stats = {
            "peer_id": "peer-1",
            "created_ts_ms": module.now_ms() - 1000,
            "frames_read": 15,
            "camera_read_failures": 1,
            "last_frame_ts_ms": module.now_ms() - 25,
            "last_frame_width": 640,
            "last_frame_height": 480,
            "connection_state": "connected",
            "ice_connection_state": "completed",
            "signaling_state": "stable",
            "track_stopped": False,
        }

        summary = module.build_media_summary({"peer-1": stats}, None)

        peer_summary = summary["active_peers"]["peer-1"]
        self.assertEqual(peer_summary["frames_read"], 15)
        self.assertEqual(peer_summary["camera_read_failures"], 1)
        self.assertEqual(peer_summary["last_frame_width"], 640)
        self.assertEqual(peer_summary["last_frame_height"], 480)
        self.assertGreater(peer_summary["fps_estimate"], 0)
        self.assertEqual(summary["totals"]["active_frames_read"], 15)

        stability_metrics = module.build_stability_metrics(
            1,
            {
                **summary,
                "last_closed_peer": {
                    "stats": {
                        "frames_read": 9,
                        "fps_estimate": 14.2,
                        "camera_read_failures": 0,
                        "track_stopped": True,
                    }
                },
            },
        )
        self.assertEqual(stability_metrics["active_peer_count"], 1)
        self.assertEqual(stability_metrics["active_frames_read"], 15)
        self.assertEqual(stability_metrics["active_camera_read_failures"], 1)
        self.assertEqual(stability_metrics["last_closed_frames_read"], 9)
        self.assertEqual(stability_metrics["last_closed_fps_estimate"], 14.2)
        self.assertTrue(stability_metrics["last_closed_track_stopped"])

    def test_close_peer_connection_stops_local_track(self) -> None:
        """close route/异常清理共用 helper 时，必须先 stop track 再 close peer。"""
        module = load_smoke_module()
        track = FakeTrack()
        pc = FakePeerConnection(track)
        pcs = {"peer-1": pc}

        result = asyncio.run(module.close_peer_connection("peer-1", pc, pcs))

        self.assertEqual(track.stop_calls, 1)
        self.assertEqual(pc.close_calls, 1)
        self.assertEqual(pcs, {})
        self.assertEqual(result["stopped_tracks"], ["video"])
        self.assertEqual(result["track_stop_errors"], [])
        self.assertIsNone(result["close_error"])

    def test_browser_page_closes_server_peer_on_page_exit(self) -> None:
        """浏览器刷新/关闭也要 POST peer close，避免 409 卡住下一轮 browser smoke。"""
        module = load_smoke_module()
        page = module.html_page(8088, "0")

        self.assertIn("let serverPeerId = null", page)
        self.assertIn("navigator.sendBeacon", page)
        self.assertIn("/peers/${serverPeerId}/close", page)
        self.assertIn("pagehide", page)
        self.assertIn("beforeunload", page)

    def test_browser_page_binds_streamless_track_to_video(self) -> None:
        """Chrome 收到 streamless track 时也必须给 video 设置 MediaStream。"""
        module = load_smoke_module()
        page = module.html_page(8088, "0")

        self.assertIn("new MediaStream([event.track])", page)
        self.assertIn("video.play().catch", page)

    def test_browser_page_waits_ice_gathering_before_offer(self) -> None:
        """无 trickle 信令时，浏览器必须等 ICE candidate 收齐再 POST /offer。"""
        module = load_smoke_module()
        page = module.html_page(8088, "0")

        self.assertIn("waitForIceGatheringComplete", page)
        self.assertIn("iceGatheringState === 'complete'", page)
        self.assertIn("await waitForIceGatheringComplete(pc)", page)


if __name__ == "__main__":
    unittest.main()

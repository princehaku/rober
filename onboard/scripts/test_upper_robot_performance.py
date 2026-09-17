"""只使用替身设备验证停止优先级、事件循环响应及状态缓存生命周期。"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import upper_robot_api as api


class BlockingSerial:
    """按 timeout 等待的 UART 替身；拒绝所有非测试路径。"""

    lock = threading.Lock()
    frames = []
    lines = []
    opened = 0
    max_opened = 0
    motion_started = threading.Event()
    feedback_started = threading.Event()

    @classmethod
    def reset(cls):
        # 每项测试独立记账，能发现线程并发打开同一设备的回归。
        cls.frames, cls.lines = [], []
        # 打开数归零用于 tearDown 检查泄漏，峰值计数用于检测重叠占用。
        cls.opened = cls.max_opened = 0
        cls.motion_started = threading.Event()
        cls.feedback_started = threading.Event()

    def __init__(self, port, baudrate, timeout):
        # 路径白名单是测试防线，避免替身接错时触碰真实串口。
        if port != "/dev/test-only":
            raise AssertionError("test attempted a non-fake serial path")
        self.timeout = timeout
        self.closed = False
        # Python 线程并发记账也需要锁，避免假阴性掩盖多 owner。
        with self.lock:
            type(self).opened += 1
            type(self).max_opened = max(self.max_opened, self.opened)

    def write(self, raw):
        # 保存解码后的命令与时间，断言顺序无需依赖线程名或日志文字。
        frame = json.loads(raw)
        with self.lock:
            self.frames.append((time.monotonic(), frame))
        # 两个事件为并发测试提供确定的注入点，无需猜测线程何时启动。
        if frame.get("T") == 130:
            self.feedback_started.set()
        elif frame.get("L") or frame.get("R"):
            self.motion_started.set()
        return len(raw)

    def readline(self):
        # 使用片段列表重现分片串口反馈，覆盖短 timeout 引入的解析边界。
        with self.lock:
            if self.lines:
                return self.lines.pop(0)
        # 真实 pyserial 也是阻塞读；此处只模拟等待，绝不访问设备。
        time.sleep(self.timeout)
        return b""

    def close(self):
        # 关闭幂等以适配 finally 和服务退出两条清理路径。
        with self.lock:
            if not self.closed:
                type(self).opened -= 1
                self.closed = True


class UpperRobotPerformanceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # aiohttp 缺失必须失败，HTTP 并发性能测试不能被静默跳过。
        from aiohttp.test_utils import TestClient, TestServer
        BlockingSerial.reset()
        self.serial_patch = mock.patch.object(api, "load_serial_module", return_value=(types.SimpleNamespace(Serial=BlockingSerial), None))
        self.serial_patch.start()
        # 统一 API 运行真实本地 HTTP 调度，只有硬件层被替换。
        self.robot = api.UpperRobotApi("http://127.0.0.1:1", "/dev/test-only", 115200, 0.12)
        self.client = TestClient(TestServer(api.create_app(self.robot)))
        await self.client.start_server()

    async def asyncTearDown(self):
        # cleanup 等待后台停车并关闭连接池，替身直到全部收口后才撤下。
        await self.client.close()
        self.serial_patch.stop()
        # 所有请求结束后仍有设备打开，说明取消或异常路径没有收口。
        self.assertEqual(BlockingSerial.opened, 0)
        # 峰值必须严格为单设备所有权；零表示该用例完全没有硬件层调用。
        self.assertLessEqual(BlockingSerial.max_opened, 1)

    async def wait_for(self, event):
        # 等待在默认线程池进行，不能让测试自身阻塞被测 HTTP 事件循环。
        self.assertTrue(await asyncio.to_thread(event.wait, 1.0))

    async def test_feedback_does_not_block_health_and_stop_preempts_read_window(self):
        # 先让真实 handler 进入无反馈读窗，再从另一个连接发送停止。
        feedback = asyncio.create_task(self.client.post("/api/base/feedback-request", json={"read_window_s": 1.2}))
        await self.wait_for(BlockingSerial.feedback_started)
        # health 响应证明非运动 HTTP 流量仍能被调度。
        started = time.monotonic()
        response = await self.client.get("/health")
        self.assertEqual(response.status, 200)
        # 此上限只用于 mock 调度回归，不能外推物理停车耗时。
        self.assertLess(time.monotonic() - started, 0.2)
        # Stop 不能等满 1.2s 窗口；容差涵盖共享 CI 主机调度抖动。
        started = time.monotonic()
        response = await self.client.post("/api/base/stop")
        self.assertLess(time.monotonic() - started, 0.25)
        # 返回结构必须反映实际停车写入，不能只观察 HTTP 成功。
        self.assertTrue((await response.json())["stop_result"]["ok"])
        payload = await (await feedback).json()
        # 抢占要在材料中可见，避免将缩短的采样窗解释为完整测量。
        self.assertTrue(payload["serial_read"]["interrupted"])

    async def test_stop_interrupts_pulse_and_no_old_motion_runs_after_stop(self):
        # 使用最大 pulse 放大错误实现的等待，Stop 应明显先于 800ms 返回。
        running = asyncio.create_task(self.client.post("/api/base/manual", json={"direction": "forward", "duration_ms": 800}))
        await self.wait_for(BlockingSerial.motion_started)
        # 并发方向请求直接拒绝，不允许存进队列再在 Stop 后出车。
        busy = await self.client.post("/api/base/manual", json={"direction": "back"})
        self.assertEqual(busy.status, 409)
        # 忙碌拒绝是公开兼容契约，PC 依赖该错误码提供可恢复反馈。
        self.assertEqual((await busy.json())["error"]["type"], "serial_busy")
        started = time.monotonic()
        stopped = await self.client.post("/api/base/stop")
        self.assertLess(time.monotonic() - started, 0.25)
        self.assertEqual(stopped.status, 200)
        payload = await (await running).json()
        # 被接受后再抢占应保留 accepted 语义，同时明确中断和停车结果。
        self.assertTrue(payload["preempted"])
        # preempted 与 auto_stop_executed 同时成立才证明中断后安全收口。
        self.assertTrue(payload["auto_stop_executed"])
        self.assertFalse(payload["feedback_after_stop_attempted"])
        # 统计运动帧能检出 Stop 后的旧排队请求，单看最后一帧无法发现此错误。
        moving = [frame for _, frame in BlockingSerial.frames if frame.get("L") or frame.get("R")]
        self.assertEqual(len(moving), 1)
        # 最后一条必须为停止，防止旧请求在显式 Stop 之后恢复执行。
        self.assertEqual(BlockingSerial.frames[-1][1], {"T": 1, "L": 0, "R": 0})

    async def test_cancelled_manual_request_still_stops_in_finally(self):
        # 直接取消任务重现断连后的协程取消，不依赖 aiohttp 的断连策略。
        running = asyncio.create_task(self.robot.manual_control({"direction": "forward", "duration_ms": 800}))
        await self.wait_for(BlockingSerial.motion_started)
        running.cancel()
        # 取消必须继续向调用方传播，同时不能撤回后台已接受动作的清理。
        with self.assertRaises(asyncio.CancelledError):
            await running
        # HTTP 协程取消后，后台停车已经完成，不能只取消一个 future 交差。
        self.assertEqual(BlockingSerial.frames[-1][1], {"T": 1, "L": 0, "R": 0})
        # 客户端已经离开，无需再占用完整反馈采集窗口。
        self.assertFalse(any(frame.get("T") == 130 for _, frame in BlockingSerial.frames))

    async def test_both_stop_entry_orders_keep_their_response_schema(self):
        # 同一个 future 被不同端点等待时，响应契约不能由发起顺序决定。
        for manual_first in (False, True):
            entered = threading.Event()
            release = threading.Event()
            real_stop = api.build_stop_payload

            def delayed_stop(port, baudrate):
                # 固定阻塞点让两个请求确定重叠，避免靠偶然线程调度覆盖竞争。
                entered.set()
                release.wait(1)
                return real_stop(port, baudrate)

            # 强制两个入口同时等待同一次 Stop，响应投影仍须符合各自契约。
            first_call = self.robot.manual_control({"direction": "stop"}) if manual_first else self.robot.base_stop()
            with mock.patch.object(api, "build_stop_payload", side_effect=delayed_stop):
                first = asyncio.create_task(first_call)
                await self.wait_for(entered)
                second_call = self.robot.base_stop() if manual_first else self.robot.manual_control({"direction": "stop"})
                second = asyncio.create_task(second_call)
                # 只让调度器运行一次以提交第二请求，不引入人为完成时延。
                await asyncio.sleep(0)
                release.set()
                first_result, second_result = await asyncio.gather(first, second)
            manual = first_result if manual_first else second_result
            stop = second_result if manual_first else first_result
            # manual-stop 要保留 accepted，独立 Stop 要保留自身 schema。
            self.assertEqual(manual["schema"], f"{api.SCHEMA}.base_manual_result")
            self.assertEqual(stop["schema"], f"{api.SCHEMA}.base_stop_result")
            # 保持不同消费者依赖的字段，不通过统一改 schema 掩盖并发错误。
            self.assertTrue(manual["accepted"])
            self.assertTrue(stop["stop_result"]["ok"])

    async def test_double_cancelled_stop_releases_reservation_after_actual_write(self):
        # 两次取消可打断取消处理器的等待，是共享 future 陈旧引用的回归点。
        entered = threading.Event()
        release = threading.Event()
        completed = threading.Event()
        real_stop = api.build_stop_payload

        def delayed_stop(port, baudrate):
            entered.set()
            release.wait(1)
            result = real_stop(port, baudrate)
            # 完成事件发生在实际写后，不能把请求排进线程池当停车完成。
            completed.set()
            return result

        # 第二次取消可中断等待 cleanup 的协程，预约仍由后台完成回调释放。
        with mock.patch.object(api, "build_stop_payload", side_effect=delayed_stop):
            stopping = asyncio.create_task(self.robot.base_stop())
            await self.wait_for(entered)
            stopping.cancel()
            await asyncio.sleep(0)
            # 第一次取消进入 shield 等待之后再取消，覆盖真实的重复取消路径。
            stopping.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await stopping
            release.set()
            await self.wait_for(completed)
        async with asyncio.timeout(1):
            # 等待后台 done callback，而非依赖已经被取消的 HTTP 请求清理。
            while self.robot._serial._stop_future is not None:
                await asyncio.sleep(0.001)
        count = len(BlockingSerial.frames)
        # 再次 Stop 应产生新写入，不能返回前一次取消请求留下的旧结果。
        await self.robot.base_stop()
        self.assertEqual(len(BlockingSerial.frames), count + 1)

    async def test_unexpected_motion_write_exception_still_attempts_stop(self):
        # 普通串口错误已有结构化处理，本例注入更外层的未预期异常。
        real_write = api.write_serial_json

        def fail_after_write(port, baudrate, command):
            result = real_write(port, baudrate, command)
            if command.get("L") or command.get("R"):
                # 先写再失败保证机器曾收到运动命令，停车断言才有意义。
                raise RuntimeError("injected failure after motion write")
            return result

        # 故障发生在方向已发出之后，测试必须证明 finally 真正发出停车。
        with mock.patch.object(api, "write_serial_json", side_effect=fail_after_write):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                await self.robot.manual_control({"direction": "left"})
        self.assertEqual(BlockingSerial.frames[-1][1], {"T": 1, "L": 0, "R": 0})


    async def test_feedback_joins_short_read_fragments_and_returns_on_target(self):
        # JSON 被切在数值和换行处，覆盖缩短 readline timeout 后的常见分片。
        BlockingSerial.lines = [b'{"T":', b'1001,"v":12}', b'\n']
        started = time.monotonic()
        payload = await self.robot.base_feedback_request({"read_window_s": 1.2})
        self.assertLess(time.monotonic() - started, 0.2)
        # 有效反馈必须避免读满默认 1.2 秒，同时保持零坏帧计数。
        self.assertEqual(payload["invalid_json_count"], 0)
        # 目标反馈仍只代表观察材料，实际 API 的 ACK/HIL 边界由旧回归共同覆盖。
        self.assertTrue(payload["feedback_ack"]["t1001_observed"])

    async def test_stop_marks_partial_samples_incomplete_and_persists_only_observations(self):
        # 第一帧可观察到反馈，剩余完整采样窗口仍应被 Stop 抢占。
        BlockingSerial.lines = [b'{"T":1001}\n']
        with tempfile.TemporaryDirectory() as tmp:
            # 持久化到临时目录，回归不污染现场 latest 材料。
            self.robot.feedback_samples_artifact_path = str(Path(tmp) / "feedback.json")
            samples = asyncio.create_task(self.robot.base_feedback_samples({"sample_count": 3, "read_window_s": 0.5}))
            await self.wait_for(BlockingSerial.feedback_started)
            await self.robot.base_stop()
            result = await samples
            # 部分成功材料可保留，但不能报告完整三帧都已验收。
            self.assertTrue(result["preempted"])
            self.assertLess(result["completed_sample_count"], 3)
            self.assertFalse(result["all_samples_observed_t1001"])
            # artifact 中也要留下同样边界，避免离线回放重新变成成功。
            saved = json.loads(Path(self.robot.feedback_samples_artifact_path).read_text())
            self.assertTrue(saved["preempted"])
            self.assertFalse(saved["all_samples_observed_t1001"])

    async def test_configured_subprocess_does_not_block_http(self):
        # 子进程调度与串口线程必须隔离，两者同时繁忙仍能响应 Stop。
        entered = threading.Event()
        release = threading.Event()

        def slow_command(_):
            entered.set()
            release.wait(1)
            return {"ok": True, "executed": True}

        # 不启动任何 ROS 或 shell，只注入一个阻塞操作检查 HTTP 调度。
        with mock.patch.object(api, "run_configured_command", side_effect=slow_command):
            request = asyncio.create_task(self.client.post("/api/radar/start"))
            await self.wait_for(entered)
            # 固定子进程保持阻塞，health/Stop 成功只能来自事件循环仍能运行。
            try:
                response = await asyncio.wait_for(self.client.get("/health"), 0.2)
                self.assertEqual(response.status, 200)
                stop = await asyncio.wait_for(self.client.post("/api/base/stop"), 0.2)
                self.assertTrue((await stop.json())["stop_result"]["ok"])
            finally:
                # 即使时延断言失败也解除替身阻塞，避免测试污染后续用例。
                release.set()
                await request

    async def test_slow_camera_is_singleflight_and_stale_is_visible(self):
        # 冷启动相机故意不完成，总状态应当立即提供保守快照。
        entered = asyncio.Event()
        release = asyncio.Event()
        calls = 0

        async def slow_camera():
            # 调用计数检查多个页面状态刷新是否放大相机健康请求。
            nonlocal calls
            calls += 1
            entered.set()
            await release.wait()
            return 200, {"status": "ready", "video_source": "fake"}

        self.robot.camera_health = slow_camera
        started = time.monotonic()
        first = await self.robot.unified_status()
        self.assertLess(time.monotonic() - started, 0.2)
        self.assertEqual(first["camera"]["status"], "unknown")
        await entered.wait()
        await self.robot.unified_status()
        self.assertEqual(calls, 1)
        # 放行后再观察缓存，区分 unknown 初态和真实采样成功。
        release.set()
        await self.robot._camera_refresh_task
        current = await self.robot.unified_status()
        self.assertEqual(current["camera"]["status"], "ready")
        sampled_at = current["camera"]["sampled_at_ms"]
        # 模拟缓存变旧，只改变样本年龄；生成新状态不能伪造新采样时间。
        code, value, stamp, mono = self.robot._camera_cache
        self.robot._camera_cache = (code, value, stamp, mono - 10)
        stale = self.robot._camera_snapshot()
        self.assertEqual(stale["sampled_at_ms"], sampled_at)
        # 旧成功状态必须转成 unknown，避免 UI 将历史健康当当前就绪。
        self.assertTrue(stale["stale"])
        self.assertEqual(stale["status"], "unknown")

    async def test_shared_camera_session_is_closed_with_app(self):
        # 使用本地 HTTP 相机替身，真实验证 session 复用和连接池释放。
        from aiohttp import web
        from aiohttp.test_utils import TestServer

        async def health(_):
            # 只提供健康 JSON，测试不需要视频设备或 WebRTC 编解码库。
            return web.json_response({"status": "ready"})

        camera_app = web.Application()
        camera_app.router.add_get("/health", health)
        camera = TestServer(camera_app)
        await camera.start_server()
        try:
            self.robot.camera_base_url = str(camera.make_url("/")).rstrip("/")
            await self.robot.camera_health()
            session = self.robot._camera_session
            # 第二次调用必须沿用同一对象，防止每个轮询重新创建连接池。
            await self.robot.camera_health()
            self.assertIs(session, self.robot._camera_session)
            await self.client.close()
            # 应用 cleanup 是生产与测试共用的资源退出边界。
            self.assertTrue(session.closed)
        finally:
            await camera.close()

    async def test_app_cleanup_cancels_camera_refresh(self):
        # 永不完成的网络请求重现相机服务卡住，退出不能留下后台任务。
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def never_finishes():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                # 协程 finally 执行证明任务已被取消并等待，只有 cancel() 调用不足。
                cancelled.set()

        self.robot.camera_health = never_finishes
        await self.robot.unified_status()
        await started.wait()
        await self.client.close()
        self.assertTrue(cancelled.is_set())


    async def test_repeated_artifact_is_read_once_per_snapshot_and_reloaded_next_time(self):
        # 既检查去重收益，也检查下次请求的文件变更不会被长期缓存隐藏。
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.json"
            path.write_text('{"schema":"one","proof":{}}', encoding="utf-8")
            self.robot.map_lifecycle_proof_artifact_path = str(path)
            real_read = Path.read_text
            reads = []

            def counted_read(candidate, *args, **kwargs):
                # 仅统计目标 map proof，其他设备元数据读取不影响断言。
                if candidate == path:
                    reads.append(candidate)
                return real_read(candidate, *args, **kwargs)

            # map 与 nav2 共用本次解析，下一次请求仍可看到文件变更。
            with mock.patch.object(Path, "read_text", counted_read):
                one = self.robot._status_snapshot({})
                # map 摘要和 nav2 readiness 共用一个已解析源。
                self.assertEqual(len(reads), 1)
                path.write_text('{"schema":"two","proof":{}}', encoding="utf-8")
                two = self.robot._status_snapshot({})
                # 新快照必须再次读盘，才能立即看见外部 collector 替换的材料。
                self.assertEqual(len(reads), 2)
            self.assertEqual(one["map"]["proof_latest"]["latest_result_schema"], "one")
            self.assertEqual(two["map"]["proof_latest"]["latest_result_schema"], "two")


if __name__ == "__main__":
    unittest.main()

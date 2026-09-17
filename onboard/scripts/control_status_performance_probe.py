#!/usr/bin/env python3
"""离线比较指定 Git 基线与工作区控制性能，所有时延均由同一套假设备实测。"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
from pathlib import Path
from unittest import mock

from test_local_webrtc_camera_smoke import FakeCpuPsutil


# 唯一允许的设备名称确保探针无法因环境变量误接真实串口。
FAKE_PORT = "/dev/performance-fake"
CAMERA_DELAY_S = 0.15
STOP_DELAY_S = 0.02
HEARTBEAT_S = 0.005
SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent.parent


def require(condition, message):
    """验证失败立即终止，避免输出带有成功标签的无效性能材料。"""
    if not condition:
        raise RuntimeError(message)


def git_output(*args):
    """基线直接读取本仓库 Git 对象，无网络、检出或工作区修改。"""
    return subprocess.check_output(["git", *args], cwd=REPO).decode("utf-8")


def load_module(name, source, path):
    """动态导入只执行模块定义，不触发脚本 main 或设备服务启动。"""
    module = types.ModuleType(name)
    # 显式文件名维持原脚本相对路径语义，模块名则确保不会进入 __main__。
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def distribution(values):
    """保留原始样本并用线性插值分位数，便于独立复核小样本结果。"""
    ordered = sorted(values)
    # 空序列意味着该阶段没有可验收观测，不能填零作为替代。
    require(bool(ordered), "missing_observed_samples")

    def percentile(fraction):
        # 采用连续排名插值；只有十次时 p99 主要反映本次最大观测值。
        rank = (len(ordered) - 1) * fraction
        lower = int(rank)
        upper = min(lower + 1, len(ordered) - 1)
        return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower), 6)

    return {
        "count": len(values), "unit": "ms", "samples": [round(value, 6) for value in values],
        "p50": percentile(0.50), "p95": percentile(0.95), "p99": percentile(0.99),
        "max": round(ordered[-1], 6),
    }


class FakeSerialBackend:
    """串口只模拟等待与 JSON 材料，绝不构造 pyserial 或打开设备节点。"""

    def __init__(self, feedback):
        # 每个样本都拥有独立后端，上一轮反馈与停车时间不会混入下一轮。
        self.feedback = feedback
        self.stop_times = []
        self.read_calls = 0
        self.open_count = 0
        # 新版通过后台线程调用，计数写入与读取必须有一致的并发边界。
        self._lock = threading.Lock()

    def Serial(self, *, port, baudrate, timeout):  # noqa: N802 - 匹配 pyserial 工厂。
        # 任何真实路径都拒绝；波特率只兼容调用参数，不模拟硬件时序。
        require(port == FAKE_PORT, "probe_refuses_real_serial_port")
        with self._lock:
            self.open_count += 1
        return FakeSerial(self, timeout)


class FakeSerial:
    """首个目标反馈固定延迟 1 ms；之后空读遵守调用方给出的 timeout。"""

    def __init__(self, owner, timeout):
        # timeout 保持可变，允许新版按剩余窗口缩短最后一个读片。
        self.owner, self.timeout = owner, timeout
        self.feedback_returned = False

    def write(self, frame):
        command = json.loads(frame.decode("utf-8"))
        # 探针仅准许查询和零轮速停车，意外的运动帧会使验收失败。
        require(command == {"T": 130} or command == {"T": 1, "L": 0, "R": 0}, "probe_refuses_motion_frame")
        if command.get("T") == 1:
            # 时间戳落在真正的 fake write 内，避免将 HTTP 协程恢复时间当写入时间。
            with self.owner._lock:
                self.owner.stop_times.append(time.perf_counter())
        return len(frame)

    def readline(self):
        # 查询次数额外证明新版在目标反馈之后结束读取，避免只看到耗时变化。
        with self.owner._lock:
            self.owner.read_calls += 1
        if self.owner.feedback and not self.feedback_returned:
            # 两版代码收到完全相同的首行；提前退出收益必须由运行结果体现。
            time.sleep(0.001)
            self.feedback_returned = True
            return b'{"T":1001,"L":0,"R":0}\n'
        time.sleep(self.timeout)
        # 空读消耗真实墙钟时间，基线窗口耗时来自实际执行而非公式计算。
        return b""

    def close(self):
        # 假串口没有系统资源；保留 close 入口以运行真实清理路径。
        pass


def new_robot(module, directory):
    """两版状态读取同一临时空材料集，避免宿主机历史文件改变样本。"""
    fields = (
        "feedback_samples_artifact_path", "lidar_scan_proof_artifact_path",
        "lidar_raw_packet_proof_artifact_path", "map_lifecycle_proof_artifact_path",
        "localization_artifact_path", "nav2_lifecycle_artifact_path",
        "elevator_status_artifact_path", "operator_report_artifact_path",
    )
    paths = {field: str(directory / (field + ".json")) for field in fields}
    # 仅传递 API 原默认值，不从宿主机环境读取任何真实设备配置。
    return module.UpperRobotApi(
        camera_base_url="http://performance-fake.invalid:8088", base_port=FAKE_PORT,
        base_baudrate=module.DEFAULT_BASE_BAUDRATE, max_speed=module.DEFAULT_MAX_SPEED,
        map_artifact_dir=str(directory / "maps"), **paths,
    )


async def close_robot(robot):
    """新版逐次关闭线程池与后台采样；基线无 close 方法时不调用。"""
    if hasattr(robot, "close"):
        await robot.close()


async def measure_feedback(module, directory, samples):
    """保留默认 1.2 秒窗口，测量目标反馈已经到达后的实际请求返回时间。"""
    durations, reads = [], []
    # 每轮构造 API，线程池初始化成本包含在被测请求的实际路径里。
    for _ in range(samples):
        backend = FakeSerialBackend(feedback=True)
        robot = new_robot(module, directory)
        # 连串口模块导入入口也替换，测试不依赖 pyserial 是否安装。
        with mock.patch.object(module, "load_serial_module", return_value=(backend, None)):
            try:
                started = time.perf_counter()
                result = await robot.base_feedback_request({})
                # 先停止请求计时，再做断言和清理，阶段总时间另行包含它们。
                durations.append((time.perf_counter() - started) * 1000)
                # 正确性先于时延：快速返回但未观察目标反馈的样本必须拒收。
                require(result.get("feedback_ack", {}).get("t1001_observed"), "fake_feedback_missing")
                reads.append(backend.read_calls)
            finally:
                await close_robot(robot)
    return {"request_ms": distribution(durations), "read_calls": reads}


async def measure_stop(module, directory, samples):
    """使用无目标反馈的读窗，观察预定 Stop 时刻至实际写入的完整等待。"""
    observed = {name: [] for name in (
        "planned_stop_to_write_ms", "stop_submission_lateness_ms", "submitted_stop_to_write_ms",
        "heartbeat_max_lag_ms", "feedback_request_ms",
    )}
    # 分开保留调度延迟与提交后的仲裁等待，避免改善一种时延掩盖另一种。
    for _ in range(samples):
        backend = FakeSerialBackend(feedback=False)
        robot = new_robot(module, directory)
        finished = asyncio.Event()
        heartbeat_lags = []

        async def heartbeat():
            # 每轮记录一次期望唤醒与实际唤醒差，阻塞造成的缺口不会被平均掉。
            while not finished.is_set():
                due = time.perf_counter() + HEARTBEAT_S
                await asyncio.sleep(HEARTBEAT_S)
                heartbeat_lags.append(max(0.0, time.perf_counter() - due) * 1000)

        async def stop_at(planned):
            # 即便事件循环已经堵过预定时刻，原计划时间仍不向后移动。
            await asyncio.sleep(max(0.0, planned - time.perf_counter()))
            submitted = time.perf_counter()
            # 保留基线同步写路径；新版通过其真实异步仲裁入口提交。
            if hasattr(robot, "base_stop"):
                result = await robot.base_stop()
            else:
                result = module.build_stop_payload(robot.base_port, robot.base_baudrate)
            require(result.get("stop_result", {}).get("ok"), "fake_stop_write_failed")
            return submitted

        with mock.patch.object(module, "load_serial_module", return_value=(backend, None)):
            pulse = asyncio.create_task(heartbeat())
            # 先让 heartbeat 注册计时器，再启动会阻塞旧事件循环的请求。
            await asyncio.sleep(0)
            started = time.perf_counter()
            # 两版都在请求开始后 20 ms 安排 Stop，保持外部事件条件一致。
            planned = started + STOP_DELAY_S
            stopper = asyncio.create_task(stop_at(planned))
            try:
                result = await robot.base_feedback_request({"read_window_s": 0.15, "read_timeout_s": 0.05})
                duration = (time.perf_counter() - started) * 1000
                submitted = await stopper
                require(not result.get("feedback_ack", {}).get("t1001_observed"), "unexpected_fake_feedback")
                require(len(backend.stop_times) == 1, "unexpected_stop_write_count")
                # 停车写入必须唯一，额外写入可能意味着样本清理或并发语义发生变化。
                written = backend.stop_times[0]
                # 计划提交时刻是外部事件意图；另列真正提交延迟，避免掩盖事件循环堵塞。
                observed["planned_stop_to_write_ms"].append((written - planned) * 1000)
                observed["stop_submission_lateness_ms"].append((submitted - planned) * 1000)
                observed["submitted_stop_to_write_ms"].append((written - submitted) * 1000)
                observed["feedback_request_ms"].append(duration)
            finally:
                # 完整等待任务和后台 owner，防止某个样本泄漏到下一轮。
                await asyncio.gather(stopper, return_exceptions=True)
                finished.set()
                await pulse
                await close_robot(robot)
            observed["heartbeat_max_lag_ms"].append(max(heartbeat_lags))
    # 分位数针对每轮最大 heartbeat lag，单轮内的高频样本不会稀释长停顿。
    return {name: distribution(values) for name, values in observed.items()}


async def measure_camera(module, directory, samples):
    """分别记录冷启动、缓存预热和复用 API 的稳态请求，初始化成本不能隐藏。"""
    robot = None
    backend = FakeSerialBackend(feedback=False)
    # 启动、完成和取消分别计数，后台工作尚未结束时不能记成已经取到健康状态。
    fetches = {"started": 0, "completed": 0, "cancelled": 0}
    sessions = set()

    async def fake_fetch(_url, *args, **kwargs):
        fetches["started"] += 1
        # 只统计明确传入的 session，基线 helper 被替换后的连接数不作推断。
        if kwargs.get("session") is not None:
            sessions.add(id(kwargs["session"]))
        # 只返回内存中的假健康数据，绝不创建相机或发起 HTTP 请求。
        try:
            await asyncio.sleep(CAMERA_DELAY_S)
        except asyncio.CancelledError:
            # 收集取消路径以发现冷请求之后直接丢弃后台任务的测量失真。
            fetches["cancelled"] += 1
            raise
        fetches["completed"] += 1
        return 200, {"status": "ok", "video_source": "performance-fake"}

    async def status_samples(count, cold=False):
        durations, camera_states = [], []
        # 每组计数取差量，同时在最终结果保存总数用于核对请求来源。
        before = dict(fetches)
        for _ in range(count):
            started = time.perf_counter()
            result = await robot.unified_status()
            durations.append((time.perf_counter() - started) * 1000)
            camera_states.append(result["camera"]["status"])
            require(result.get("safe_to_control") is False, "status_safety_boundary_changed")
            # 冷缓存 unknown 与预热后的 ok 分别核对，不能把旧成功材料充当冷返回。
            expected = "unknown" if cold and hasattr(robot, "_camera_snapshot") else "ok"
            require(result["camera"]["status"] == expected, "unexpected_camera_state")
            require(backend.open_count == 0, "status_opened_fake_serial")
        return {
            "status_request_ms": distribution(durations), "camera_states": camera_states,
            "fake_fetch": {key: fetches[key] - before[key] for key in fetches},
        }

    async def cold_start():
        nonlocal robot
        # 唯一冷样本包含对象构造、首次 aiohttp 导入和 session 初始化，单独保留。
        robot = new_robot(module, directory)
        return await status_samples(1, cold=True)

    async def cache_warmup():
        before = dict(fetches)
        # 基线冷请求已经等待相机；新版等待先前发出的同一个后台请求完成。
        refresh = getattr(robot, "_camera_refresh_task", None)
        if refresh is not None:
            await refresh
        return {"fake_fetch": {key: fetches[key] - before[key] for key in fetches}}

    with (
        mock.patch.object(module, "fetch_json", side_effect=fake_fetch),
        mock.patch.object(module, "load_serial_module", return_value=(backend, None)),
    ):
        try:
            cold = await timed_phase(cold_start)
            # 冷启动延迟不混入稳态分位数；预热本身的 CPU 与墙钟成本另列。
            warmup = await timed_phase(cache_warmup)
            session = getattr(robot, "_camera_session", None)
            # 稳态连续请求复用同一 API；新版缓存窗口内不额外发起相机请求。
            steady = await timed_phase(lambda: status_samples(samples))
            reused_session = session is not None and session is getattr(robot, "_camera_session", None)
            # 相同对象身份只证明连接池复用，实际 TCP 连接未在本探针中建立。
            require(fetches["started"] > 0, "camera_fetch_injection_not_exercised")
            return {
                "cold_start": cold, "cache_warmup": warmup, "steady_state": steady,
                "fake_fetch_total": dict(fetches), "passed_session_count": len(sessions),
                "after_session_reused_in_steady_state": reused_session if hasattr(robot, "_camera_session") else None,
                "cache_ttl_s": getattr(module, "CAMERA_CACHE_TTL_S", None),
                "transport_boundary": "fetch_json is mocked; no TCP/connect timing or baseline session creation measured",
            }
        finally:
            # 结束后才关闭同一个 API，整个稳态过程不重新建线程池或连接池。
            if robot is not None:
                await close_robot(robot)


def measure_cpu(module, samples):
    """实际执行两版 collector；旧版错误的有效零读数单独计数。"""
    fake = FakeCpuPsutil()
    # 每个指标各用一个时刻；同轮二者同值，跨轮差分恒为 250 ms。
    times = [1.0 + index * 0.25 for index in range(samples) for _ in range(2)]
    # 注入间隔只给差分窗口，不参与真实时延或 process_time 的测量。
    with (
        mock.patch.dict(sys.modules, {"psutil": fake}),
        mock.patch.object(module.importlib.util, "find_spec", return_value=object()),
        mock.patch.object(module.time, "monotonic", side_effect=times),
    ):
        results = [module.collect_cpu_diagnostics()["process_cpu_percent"] for _ in range(samples)]
    # 基线可能错误地报告 available=true，因此有效窗口计数必须独立呈现。
    return {
        "process_creations": fake.process_creations, "process_sample_calls": fake.process_sample_calls,
        "system_sample_calls": fake.system_sample_calls,
        "warmup_count": sum(item.get("reason") == "warming_up" for item in results),
        "reported_available_count": sum(item["available"] for item in results),
        "reported_zero_count": sum(item.get("value") == 0 for item in results),
        "valid_window_count": sum(item["available"] and item.get("sample_window_ms", 0) > 0 for item in results),
        "samples": results, "all_intervals_none": all(value is None for value in fake.intervals),
    }


async def timed_phase(operation):
    """记录整个阶段消耗，包括初始化清理；单请求时延在阶段内部另测。"""
    wall, cpu = time.perf_counter(), time.process_time()
    # process_time 包含本进程工作线程；注入的等待只增加 wall，不伪装成计算负载。
    result = await operation()
    return {"wall_ms": (time.perf_counter() - wall) * 1000, "process_cpu_ms": (time.process_time() - cpu) * 1000, **result}


async def run(samples, baseline_ref):
    """同进程顺序执行基线和工作区；运行环境与源码散列随结果留存。"""
    # 先验证引用能解析成提交，非法输入在任何性能阶段开始前失败。
    baseline_sha = git_output("rev-parse", "--verify", "--end-of-options", f"{baseline_ref}^{{commit}}").strip()
    # 先读取全部模块再执行，各轮使用固定源码，避免中途文件编辑改变测量对象。
    modules, provenance = {}, {}
    for label in ("baseline", "after"):
        modules[label], provenance[label] = {}, {}
        for short in ("upper_robot_api", "local_webrtc_camera_smoke"):
            relative = f"onboard/scripts/{short}.py"
            # 两份旧源都使用已解析 SHA，后续提交或分支切换不会改变本轮基线。
            source = git_output("show", f"{baseline_sha}:{relative}") if label == "baseline" else (REPO / relative).read_text(encoding="utf-8")
            modules[label][short] = load_module(f"performance_{label}_{short}", source, REPO / relative)
            provenance[label][relative] = hashlib.sha256(source.encode("utf-8")).hexdigest()
    # 仲裁器属于新版依赖，额外保存散列以识别同名 API 的依赖变更。
    provenance["after"]["onboard/scripts/upper_robot_io.py"] = hashlib.sha256((SCRIPTS / "upper_robot_io.py").read_bytes()).hexdigest()
    result = {
        "schema": "rober.control_status_performance.v2", "evidence_boundary": "software_mock_only",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "baseline_ref": baseline_ref, "baseline_git_sha": baseline_sha, "source_sha256": provenance,
        # 探针自身也保存指纹，后续调整方法时仍能区分历史材料。
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        # 运行环境只记录解释时延所需的平台信息，避免采集本机凭据或网络配置。
        "environment": {"python": sys.version, "platform": platform.platform(), "processor": platform.processor()},
        # 输入条件与观测结果分区存储，配置中的 1.2 秒不属于实测数据。
        "method": {"samples_per_phase": samples, "baseline_source": "git show <resolved SHA>:<path>",
                   # 冷启动仅有一个观测点，稳态与其余请求阶段才使用指定样本数。
                   "percentiles": "linear interpolation of ordered observed samples",
                   "timings": "direct API method calls; no HTTP transport; perf_counter wall / process_time CPU",
                   "feedback": {"default_read_window_s": 1.2, "fake_first_target_delay_s": 0.001},
                   "stop": {"read_window_s": 0.15, "read_timeout_s": 0.05, "planned_submission_s": STOP_DELAY_S, "heartbeat_s": HEARTBEAT_S},
                   "camera": {"fake_fetch_delay_s": CAMERA_DELAY_S, "cold_start_samples": 1,
                              "cache": "cold start plus completed warmup; steady state reuses one API and its session"},
                   "reproduce_command": f"python3 onboard/scripts/control_status_performance_probe.py --baseline-ref {baseline_sha} --samples {samples} --output sprints/2026.09.17_00-01_control-status-performance-epic/evidence/robot-performance.json"},
        # 方法调用未经过 HTTP 传输，结果仅覆盖当前 API 内部调度和 fake I/O。
        "limitations": ["No real serial, camera, network, ROS runtime, phone CPU or HIL evidence.",
                        "CPU time measures this synthetic probe, not video CPU savings.",
                        "Ten samples describe this run; p99 is not a production tail guarantee.",
                        "Explicit --baseline-ref SHA keeps future reruns comparable after commits.",
                        "Camera cold_start has one sample; no tail reliability is claimed for its percentiles."],
    }
    with tempfile.TemporaryDirectory(prefix="rober-performance-") as directory:
        # 临时目录生命周期覆盖两版全部状态样本，退出后清理空材料集。
        for label in ("baseline", "after"):
            api, camera = modules[label]["upper_robot_api"], modules[label]["local_webrtc_camera_smoke"]
            # 配置仅描述输入；下面每个数值都来自执行后的观测。
            require(api.DEFAULT_FEEDBACK_READ_WINDOW_S == 1.2, "unexpected_default_read_window")
            phases = {}
            for name, operation in (("feedback", measure_feedback), ("stop", measure_stop), ("camera", measure_camera)):
                phases[name] = await timed_phase(lambda operation=operation: operation(api, Path(directory), samples))
                print(f"{label}.{name}: done", file=sys.stderr, flush=True)

            async def cpu_phase():
                # CPU 结构性计数和实际阶段 CPU 时间同时保留，避免混淆口径。
                return measure_cpu(camera, samples)

            phases["cpu_sampling"] = await timed_phase(cpu_phase)
            result[label] = phases
    return result


def main():
    """仅写用户指定的证据路径；样本不足十次时拒绝启动。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10)
    # 默认便于本地使用；正式证据命令必须传固定提交 SHA，以便提交后复跑。
    parser.add_argument("--baseline-ref", default="HEAD")
    args = parser.parse_args()
    # 最小样本数是命令契约，不能用一次运行结果冒充尾部分布。
    if args.samples < 10:
        parser.error("--samples must be >= 10")
    # 即使后续代码意外绕过 fake fetch，解析域名或建立连接也会立即失败。
    with (
        mock.patch.object(socket, "getaddrinfo", side_effect=RuntimeError("probe_network_forbidden")),
        mock.patch.object(socket.socket, "connect", side_effect=RuntimeError("probe_network_forbidden")),
    ):
        result = asyncio.run(run(args.samples, args.baseline_ref))
    # 所有阶段成功后才落盘，任何失败都保留非零退出码供验收定位。
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "baseline_git_sha": result["baseline_git_sha"]}))


if __name__ == "__main__":
    main()

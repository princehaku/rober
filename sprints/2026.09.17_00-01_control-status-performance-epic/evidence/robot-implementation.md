# Robot 控制与状态性能实现证据

- 日期：2026-09-18（sprint 使用 2026-09-17 启动名）。
- 分支：`codex/control-status-performance`。
- 状态：实现、回归、性能探针与触点集成核对完成。
- 边界：`software_mock_only`，未打开真实串口/相机，未控车、未远端部署。

## 实际文件

生产实现：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/upper_robot_io.py`（新增）
- `onboard/scripts/local_webrtc_camera_smoke.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`（仅静态白名单新增 `diagnostics.js`）

测试与探针：

- `onboard/scripts/test_upper_robot_api.py`
- `onboard/scripts/test_upper_robot_performance.py`（新增）
- `onboard/scripts/test_local_webrtc_camera_smoke.py`
- `onboard/scripts/control_status_performance_probe.py`（新增）
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`（仅静态托管入口覆盖）

文档与证据：

- `docs/interfaces/o7_upper_robot_api.md`
- `docs/interfaces/o1_upper_robot_api_base_feedback.md`
- `docs/interfaces/o7_local_webrtc_camera_smoke.md`
- 本目录 `robot-cpu-sampling.md`、`robot-performance.json`、`robot-implementation.md`

## 实现与精简收益

串口仲裁使用单实例专用线程。普通请求先预约，忙时 HTTP 409 `accepted=false/error.type=serial_busy`，不积压旧运动。完整方向写、可中断 pulse、finally 停车、反馈均在同一 owner 中执行。Stop 可打断 pulse/读窗，HTTP 取消与未预期异常仍停车；多次取消由实际 future 完成回调释放预约。兼容 manual-stop 与独立 Stop 共用底层结果、分别投影响应 schema。50 ms 短读片与 200 ms 写 timeout 均为配置上限，未外推物理停止时延。

普通反馈收到 `T=1001` 立即结束，跨读片 JSON 会累计到换行再解析。显式 samples 保留整窗观察，抢占产生 `preempted=true`，未完成批次不会报告 `all_samples_observed_t1001=true`。批次落盘离开串口占用区。

配置型子进程移到默认线程池并 single-flight，专用串口线程保持独立。总状态立即读取 camera 缓存；相机后台单飞采样，共享 HTTP session，正常 cleanup 取消并等待后台任务、关闭 session。冷态或过期状态为 unknown，保留实际 `sampled_at_ms/sample_age_ms/stale/refreshing`。同次状态请求的重复 artifact 读取和 JSON 解析去重，下一次请求重新读取；根路径直接返回静态 routes。

CPU 采样复用 Process 对象，区分预热、有效窗口与异常恢复。未改摄像头编码、分辨率或硬件配置。新增仲裁/生命周期代码带来少量线程和调度成本；本轮优先减少端到端等待并保证 Stop，未追求净代码行数下降。原始反馈/控制响应字段与安全边界保留。

硬件资料依据：`docs/vendor/VENDOR_INDEX.md`、`waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`、`waveshare_wave_rover/ugv_rpi/base_ctrl.py`。未改 vendor 波特率、命令或速度映射。

## 验证命令与结果

Docker CLI 存在，Engine 的 `dockerDesktopLinuxEngine` pipe 不存在。Windows Python 3.13 首轮 39 tests：3 failures 为既有 POSIX 路径/命令假设，4 HTTP tests 因缺 aiohttp 跳过，未作为验收通过依据。Ubuntu 22.04 缺 pip/ensurepip；改用已安装的 Ubuntu 24.04 Python 3.12.3，在 `/tmp/rober-control-performance-deps` 安装隔离 aiohttp 依赖，无仓库依赖文件改动。

最终实际 Linux/WSL 命令：

```powershell
wsl -d Ubuntu-24.04 -- bash -lc 'cd /mnt/e/rober && PYTHONPATH=/tmp/rober-control-performance-deps python3 -m unittest onboard.scripts.test_upper_robot_api onboard.scripts.test_local_webrtc_camera_smoke onboard.scripts.test_upper_robot_performance'
```

该次运行 65 tests OK；随后增加部分 samples 抢占回归并执行完整目录：

```powershell
wsl -d Ubuntu-24.04 -- bash -lc 'cd /mnt/e/rober && PYTHONPATH=/tmp/rober-control-performance-deps python3 -m unittest discover -s onboard/scripts -p "test_*.py"'
```

最终输出：

```text
Ran 108 tests in 4.497s
OK
```

无 skip。新增性能/并发回归共 13 项，覆盖：

- 慢反馈读窗中的 HTTP health/Stop 响应；所有测试最大并发串口打开数 <= 1。
- 最大 pulse 中的 Stop 抢占、busy 拒绝、Stop 后无旧排队运动。
- 请求取消与方向写后未预期异常仍在 finally 停车。
- 两种 Stop 入口的两种发起顺序保持 schema；双取消后新 Stop 产生新写入。
- 短读分片 JSON、有效反馈早返回、部分 samples 抢占和落盘边界。
- 慢配置命令下 health/Stop 可响应。
- camera 单飞/过期可见、连接池复用及 cleanup 取消等待。
- 同次 artifact 读取一次，下一次请求能看到文件变化。

静态托管实际 HTTP 测试（非 DOM mock）：

```powershell
wsl -d Ubuntu-24.04 -- bash -lc 'cd /mnt/e/rober/onboard/src/ros2_trashbot_behavior/test && PYTHONPATH=/tmp/rober-control-performance-deps python3 -m unittest test_remote_cloud_relay.RemoteCloudRelayHttpTest.test_cloud_relay_serves_mobile_web_shell_without_auth test_remote_cloud_relay.RemoteCloudRelayHttpTest.test_mobile_web_static_does_not_cover_api_or_probe_routes test_remote_cloud_relay.RemoteCloudRelayHttpTest.test_mobile_web_missing_static_and_traversal_are_phone_safe'
```

```text
Ran 3 tests in 1.889s
OK
```

确认 `/diagnostics.js` HTTP 200、JavaScript MIME、正确脚本内容；API/probe 路由与路径穿越防线保持。

## 性能实测

复跑使用固定 Git 基线，不随后续提交移动：

```powershell
wsl -d Ubuntu-24.04 -- bash -lc 'cd /mnt/e/rober && PYTHONPATH=/tmp/rober-control-performance-deps python3 onboard/scripts/control_status_performance_probe.py --baseline-ref 869dfe5aaf95bcd1759583752a1a433b9ff1e83c --output sprints/2026.09.17_00-01_control-status-performance-epic/evidence/robot-performance.json'
```

此命令已对最终代码重跑成功。`robot-performance.json` 保存原始样本、p50/p95/p99、墙钟与进程 CPU 时间、注入条件、固定基线 SHA 及源码/探针 hash。hash 按读取后 UTF-8 文本（换行归一化）计算，已与最终三份生产源码和 probe 核对一致。

每组 10 次；p50 单位 ms：

| 指标 | baseline 实测 | after 实测 |
| --- | ---: | ---: |
| 普通有效反馈请求 | 1202.019 | 1.388 |
| 计划 Stop 时刻到实际写入 | 130.615 | 30.474 |
| 每轮最大 heartbeat 调度延迟 | 145.642 | 0.419 |
| 预热、同实例总状态请求 | 150.909 | 0.510 |

停止组使用 150 ms 无反馈读窗，20 ms 后计划 Stop；旧代码在事件循环内读完整窗口，因而 Stop 的提交本身被推迟。上表使用“计划 Stop 到写入”，JSON 同时保留“实际提交到写入”与提交迟到量，避免将不同起点混为物理停止时延。探针直接调用 API，不包含 HTTP 传输；HTTP 调度由上述回归独立验证。

camera cold_start/cache_warmup/steady_state 分组保留：本次 after 冷首请求 88.029 ms、CPU 59.307 ms，包含 aiohttp 首次导入/创建 session；等待后台初次采样 150.330 ms。预热后复用同一实例与 session 连续请求，after fake fetch 仅 1 次，baseline 每次都等待 150 ms 相机。没有删除冷样本或以稳态替代初始化成本。

CPU 不作总体下降声明。反馈组累计进程 CPU 7.066 -> 8.028 ms，Stop 组 7.755 -> 16.191 ms，线程与抢占引入额外调度；camera 稳态 7.285 -> 5.519 ms，但这个短 mock 窗口不足以外推真实板端 CPU 百分比。结构性证据：CPU 采样的 Process 创建数 10 -> 1，after 1 次预热、9 次有效窗口；baseline 10 次返回 available=true/0.0 却没有有效差分窗口。

## 集成与完成前自检

已读取触点 owner 的 `ui-performance.json`、`ui-implementation.md` 并核对接口：PC 映射 `accepted/preempted/error` 为 `upper_accepted/preempted/upper_error`，409 与中断响应不丢失；Stop 独立分发，旧响应不能覆盖 Stop 文案。directUpper camera 摘要采用 `camera.status`，unknown 不会被残留 HTTP 200 提升成 ready；当前 cameraSmoke 独立健康路径未由本次缓存改变。

手机诊断懒加载文件已获实际托管 HTTP 覆盖。Full-stack 的 PC 110 tests/build/lint、聚合 probe 7 PC + 9 mobile 通过；手机历史 415 项中 10 个既存错误已由该 owner 对基线复现，不属于本轮 Robot 回归结果。

无范围外产品修改；历史未跟踪 `2026.06.12_00-01_o10-amcl-nav2-bringup-epic` 未改。没有新增未处理 TODO。新增/修改 Python 技术注释均中文；按新增非空行保守统计，API 20.2%、仲裁 20.9%、性能测试 20.5%、CPU 实现 22.2%、CPU 测试 20.6%、probe 20.1%，均超过 20%。Robot 范围 `git diff --check` 通过，触点 owner 已清理其 HTML 尾空格。

## 剩余风险与计划偏差

- 单实例仲裁无法约束外部 `esp32_bridge`/其他进程；真实部署仍需保证 UART 独占。
- 50 ms 读片、200 ms 写 timeout 不等于物理停车时延；驱动异常、进程强制终止、设备掉线/硬件看门狗均未由 mock 验收。
- 不含真实相机编码、浏览器端到端视频、4G、ROS runtime/HIL 或现场送达；不得抬高产品 Objective 完成度。
- CPU 的本地采样正确性已修复，持续板端负载与真实手机 CPU 需后续实机测量。
- Windows 静态/单测平台差异未通过改产品路径掩盖；最终以 WSL Linux mock 回归验收。
- 按主节点最新实施令使用 `control_status_performance_probe.py` 和精确 `MOBILE_WEB_STATIC_FILES` 名称；旧计划草稿中的名称已经要求 Product 同步。

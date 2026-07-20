# Tech Plan

## 元数据

- `sprint_type: epic`
- 状态：`planning_complete_pending_engineer_dispatch`
- 主责/集成 owner：`full-stack-software-engineer`（Full-Stack）
- 并行事实与条件式现场测量 owner：`rober-hardware-engineer`（Hardware）
- 当前 live authorization：`none`；`ceo_20260721_0154_minimal_wheel_jog_v6` 已在前序 micro 中 exactly-once 消费
- 目标：把 browser keydown 到 wheel onset 拆成可信 waterfall，优先消除 warm hot path 的可避免等待，同时保持 stop/watchdog 安全合同。

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低 Objective 是 O5（约 `85%`）。O5 provider/runtime blocker 已连续消费 `2/2` 并暂停，本 sprint 不再开 provider、preflight、tunnel、readback 或 wrapper。用户本轮明确指定“按键到轮子动”的 O1/O7 体验问题，且它是可行动的新 lane；因此转向 O1 人工控制 latency，O7 负责用户触点。O6/O7 各约 `93%`、O1 约 `94%`，planning 阶段全部 flat，KR `不归档`。

## 当前基线假设与先量后改

当前源码显示：

- Vue 首次 keydown 直接调用 `sendKeyboardManualPulse()`；后续 pulse 等前一 HTTP 回包后自调度，默认 interval `260ms`、duration `240ms`。
- PC Node 收到固定 proxy 请求后同步校验/clamp，再 `await` forward 到 `/api/base/manual`。
- Upper `rclpy` context 是 lazy init；hold refresh 调用进程内 `/cmd_vel` burst 前最多等待 subscription `150ms`，全局默认 discovery 常量为 `1.2s`。这只是候选瓶颈，必须由 trace 证实后再调整。
- bridge `_cmd_vel_callback` 在 build command 后调用 `_send_json()`，transport write 在 debug append 前；现有 log 只有 wall time，不能直接与 browser/upper monotonic 相减。
- vendor UART 参考以 newline JSON 为命令边界；现场 bridge 当前默认用 ESP32 HTTP `/js` 规避 UART TX 断点。两种 transport 都只能证明 host write，之后到 wheel onset 仍是物理未知段。

第一阶段先在当前代码上跑相同 software/mock fixture 形成 baseline，再做实现并复跑。不得用不同 fixture、不同 sample count 或混合 cold/warm 样本制造改善。

## 执行拓扑与 owner 边界

```text
Full-Stack baseline + trace contract + hot-path optimization + integration tests
          |
          +---- browser -> Node -> Upper -> /cmd_vel -> bridge/fake serial
          |
Hardware vendor facts + independent observer/probe + artifact review
          |
          +---- no shared core edits; fresh authorization 才执行 physical sampling
```

- Full-Stack 是唯一产品代码集成 owner。由于接口强耦合，Vue、Node、Upper 和 bridge timing hook 由同一 owner 串行完成并统一回归，避免多个 agent 双写 trace schema。
- Hardware 可并行只读 vendor/runtime 事实，或新增独立 probe/observer 与自己 artifact；不得修改 Full-Stack、Upper 或 bridge 核心文件，不得发送 nonzero/control。
- Product 只验收文档与证据，不写产品代码、测试或运行 live 命令。

## 文件范围

### Full-Stack 可写

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- 可新增 `pc-tools/workstation/src/server/robotControlLatency.ts`
- 可新增 `pc-tools/workstation/test/robotControlLatency.test.ts`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
- `docs/product/pc_free_roam_mapping_design.md`
- `docs/interfaces/ros_runtime_contracts.md`
- `sprints/2026.07.21_03-50_o1_keyboard_to_wheel_latency/artifacts/full-stack/`
- 最终由主责创建 `sprints/2026.07.21_03-50_o1_keyboard_to_wheel_latency/tech-done.md`

不为制造 diff 而修改所有候选文件；实际无需触碰的文件保持不动。不得修改 vendor source、速度/PWM/PID/串口默认配置、Nav2、O5/O6、`OKR.md`、其他 sprint 或 Product 后续收口文档。

### Hardware 可写且不得与 Full-Stack 重叠

- 可新增 `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/keyboard_wheel_latency_probe.py`
- 可新增 `onboard/src/ros2_trashbot_hardware/test/test_keyboard_wheel_latency_probe.py`
- `sprints/2026.07.21_03-50_o1_keyboard_to_wheel_latency/artifacts/hardware/`

Hardware probe 默认 `software/mock/read-only`，不得自动打开真实 UART、发布 `/cmd_vel`、调用 manual/Nav2 或发送 nonzero。只有 future fresh authorization 明确允许时，才可消费 Full-Stack 已冻结的 trace 与外部 observer 记录；仍不改 Vue/Node/Upper/bridge core。

## 工作区冲突隔离

当前 `onboard/scripts/upper_robot_api.py`、`onboard/tests/test_upper_robot_api.py`、`docs/interfaces/ros_runtime_contracts.md` 已有 `2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission` 的未提交 Nav2 改动。

1. Full-Stack 开工前记录 `git status --short`、目标文件 blob/hash、`git diff --binary -- <shared files>` 和现有 hunk 摘要，写入本 sprint artifact。
2. 优先等待 Nav2 owner 冻结/提交，再从包含其改动的基线开 latency 分支/worktree；不得从旧 HEAD 创建“干净”副本后覆盖当前文件。
3. 如必须在同一脏树工作，只允许小范围 additive patch；禁止整文件 formatter、checkout、reset、rebase、stash pop 或回滚。修改后逐 hunk 对比，证明既有 Nav2 hunks仍在。
4. 共享测试必须同时跑 Nav2 既有 targeted suite 与 latency suite；若语义冲突，停止实现并让主节点协调 owner，不自行裁掉另一 sprint 合同。
5. `pc_free_roam_mapping_design.md` 已较大，只追加精确 latency 合同段，不重排历史；`ros_runtime_contracts.md` 若仍被占用则延后到 owner handoff 后更新。

## Trace 接口字段

请求保持既有 direction/speed/duration/command/hold 字段，并仅增加可选诊断 envelope：

```json
{
  "latency_trace": {
    "schema": "trashbot.keyboard_wheel_latency_trace.v1",
    "latency_trace_id": "opaque-uuid",
    "client_keydown_perf_ms": 1234.5,
    "client_time_origin_ms": 1784570000000,
    "hold_session_id": "opaque-session",
    "hold_sequence": 1,
    "sample_kind": "warm"
  }
}
```

- PC response/diagnostic artifact追加：`pc_receive_mono_ns`、`pc_validation_done_mono_ns`、`pc_forward_start_mono_ns`、`pc_upstream_headers_mono_ns`、`pc_response_done_mono_ns`。
- Upper 追加：`upper_receive_mono_ns`、`manual_gate_done_mono_ns`、`rclpy_context_status`、`rclpy_ready_mono_ns`、`cmd_vel_first_publish_mono_ns`、`cmd_vel_publish_done_mono_ns`、`upper_response_ready_mono_ns`。
- bridge 追加：`bridge_callback_mono_ns`、`vendor_command_built_mono_ns`、`transport_write_start_mono_ns`、`transport_write_end_mono_ns`、`transport_write_returned`、`command_transport`，并按实际 transport 分出 `http_write_returned` / `serial_write_returned`。
- observer 追加：`wheel_onset_observer_kind`、`wheel_onset_timestamp`、`observer_clock_id`、`observer_sample_period_ms`、`observer_uncertainty_ms`。
- 所有 monotonic 值只在其 `clock_id/host_id/process_boot_id` 作用域内相减。对外 summary 优先返回已经计算的 local span，不要求 UI 自己算裸 timestamp。
- trace id、session id 做长度/字符白名单；未知字段忽略或 fail closed，不回显 base URL、token、UART path、raw body 或 traceback。

## 时钟与时间戳策略

1. Browser 使用 `performance.now()`；记录 `performance.timeOrigin` 仅用于关联，不把它当无误差跨机 monotonic。
2. Node 使用 `process.hrtime.bigint()`；Python Upper/bridge 使用 `time.monotonic_ns()`。同一 OS 主机不同进程的 monotonic 是否同源也必须通过 `clock_id/boot_id` 明确，不凭字段名假设。
3. Browser↔Node、PC↔upper 先做轻量 ping/echo calibration，至少 9 轮，取最小 RTT 样本估 offset，并记录 median/min RTT、offset 与 uncertainty；calibration 过期或 uncertainty `>10ms` 时，不输出合成 keydown-to-UART 精确值。
4. 不直接做 `client_perf - upper_monotonic`、`PC monotonic - upper monotonic` 或 host wall-clock 相减。跨机默认报告各段 + network RTT envelope。
5. 物理主指标优先用同一 observer clock捕获 keydown marker 与 wheel onset。若用视频，帧周期计入 uncertainty；若用 T1001，必须记录 feedback rate/采样周期且 L/R 非零，IMU-only 不能命名为 wheel onset。

## 实现阶段

### Phase 1：baseline 与 instrumentation

- 建立 deterministic fake clock、loopback upstream、fake rclpy publisher/subscription，以及 fake HTTP 与 fake serial transport。
- 当前代码 warm/cold 各独立采样；warm 至少 `100`，保留 raw JSONL，计算 p50/p95/max 与 dropped/error counts。
- 先让 trace continuity、clock scopes、negative/unknown case 测试通过；尚不改变控制节奏。

### Phase 2：浏览器与 PC proxy hot path

- keydown handler 第一行附近打点，保持 editable/armed/owner/safety gate；repeat 仍由 hold loop接管。
- fetch 立即 dispatch，Node 复用 keep-alive；不在 forward 前刷新 summary/readback。
- stop request拥有独立高优先级，不被 manual response pending gate无限阻塞；保持旧接口兼容。

### Phase 3：Upper `/cmd_vel` 首帧

- service startup/readiness 预热 rclpy import/node/publisher/DDS match；readiness 未通过时 manual fail closed，不在首次 keydown 临时承担秒级冷启动。
- 已 warm/matched 时，安全校验后立即发首帧，再完成剩余 burst；不得在首帧前 sleep。
- 将非关键 debug scan/evidence packaging 移出首帧关键路径；response 若先返回 receipt，必须明确 evidence pending，不能标 complete。
- CLI fallback 不作为正常键盘 hot path；仅在结构化 failure 时使用，并不得悄悄把秒级 CLI latency算入达标样本。

### Phase 4：bridge transport 与日志

- callback/build/write 分段打点，transport write 继续早于 debug append。
- 调试日志如异步化，必须 bounded queue、stop priority、flush/丢弃计数和 shutdown 语义；不得因日志线程丢失安全错误。
- 保持当前 live `command_transport=http` 与 ESP32 `/js` 路径，不以降延迟为由切到 serial；serial 配置仍通过现有 encoder生成 UTF-8 单行 JSON + `\n`。不改 T=1/T=11/T=13 映射或 motor参数。

### Phase 5：优化后 software/mock 与回归

- 同 fixture 重跑 `>=100` warm samples；cold 单列。
- 目标 `keydown -> fake configured transport write` p50 `<=35ms`、p95 `<=60ms`、max `<=100ms`，HTTP/serial fixture 分账，且 baseline p95 改善目标 `>=30%`。
- 各 local segment p95 必须可读；任何单段 p95 `>25ms` 或 sample `>=50ms` 给出 root cause。
- `keyup/blur/page hidden/button/watchdog -> fake stop write` 保持全覆盖，p95 不比 baseline 退化 `>10ms`。

### Phase 6：条件式 live physical

本阶段默认 `NOT_AUTHORIZED`。只有 CEO 提供新的 fresh bounded authorization 后才由 Hardware 与 Full-Stack 串行执行；不能复用 v6。

授权至少冻结：authorization id、operator present、路线清空、物理限位、direction、`speed<=0.08m/s`、`duration<=300ms`、sample count（候选 `10`）、间隔、pre/post stop、watchdog、紧急停止、observer、abort 条件。每个 nonzero 都计数，任何失败不自动 retry。

有授权时，依次 pre-stop -> calibrated trace sample -> post-stop；command-path 与 physical observer 分账。目标 physical p50 `<=100ms`、p95 `<=150ms`、max `<=200ms`、相对有效 baseline p95 改善 `>=30%`。sample 不足、clock uncertainty 过大、observer 不可信或 T1001 L/R 仍为 0 时写 `physical_latency_not_measured`，不得用 HTTP/UART/IMU 替代。

## 安全不变量与测试矩阵

- keydown 只在 armed、owner、非 editable、safety confirmed 下发送；key repeat 不重复开启 session。
- keyup/all release、direction change、pointer end/cancel/leave、window blur、page hidden、stop button、unmount、network error、request timeout、watchdog expiry 都能触发 stop/收口。
- stop 高优先级；in-flight motion response、deferred evidence 或日志 queue 不得阻塞。
- hold session/sequence 乱序、重复、过期 fail closed；旧 watchdog 不得停止新 session，也不得被旧请求续期。
- lost PC、lost upper、lost DDS subscriber、fake serial error、partial write、log queue full 均产生结构化失败且不声称 wheel moved。
- cold rclpy unavailable/prewarm fail 时 manual blocked；不能静默走更慢且不可控路径后仍报 latency pass。
- trace payload hostile/oversized/invalid clock value 被拒绝或裁剪，不反射敏感信息。

## 验收命令

所有实现、测试、修复命令由对应 Engineer 执行；Product 不运行工程命令。

```bash
set -euo pipefail

cd pc-tools/workstation
npm test -- robotControlLatency.test.ts
npm test -- catalog.test.ts -t "keyboard|manual|stop|watchdog|latency"
npm test
npm run build
npm run lint
cd ../..

python3 -m py_compile onboard/scripts/upper_robot_api.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py
python3 -m unittest onboard/tests/test_upper_robot_api.py
python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py
python3 -m unittest onboard/tests/test_upper_robot_api.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  onboard/tests/test_o11_nav2_lifecycle_script.py

bash onboard/scripts/docker_humble_build.sh

python3 -m json.tool \
  sprints/2026.07.21_03-50_o1_keyboard_to_wheel_latency/artifacts/full-stack/software_latency_summary.json \
  >/dev/null
jq -e '
  .sample_kind == "warm" and
  .valid_sample_count >= 100 and
  .keydown_to_fake_transport_write_ms.p95 <= 60 and
  .keydown_to_fake_transport_write_ms.max <= 100 and
  .stop_latency_regression_ms.p95 <= 10 and
  .live_nonzero_request_count == 0
' sprints/2026.07.21_03-50_o1_keyboard_to_wheel_latency/artifacts/full-stack/software_latency_summary.json

git diff --check -- \
  pc-tools/workstation \
  onboard/scripts/upper_robot_api.py \
  onboard/tests/test_upper_robot_api.py \
  onboard/src/ros2_trashbot_hardware \
  docs/product/pc_free_roam_mapping_design.md \
  docs/interfaces/ros_runtime_contracts.md \
  sprints/2026.07.21_03-50_o1_keyboard_to_wheel_latency
```

若没有新增 `robotControlLatency.test.ts` 或 Hardware probe，主责应把 targeted 命令换成实际文件并在 `tech-done.md` 记录，不得用不存在文件的失败冒充产品失败。live 命令不写入默认验收脚本，防止误执行。

## 失败重试与修复策略

- 单测/构建/lint/Docker 失败：读错误，限定在 owner 文件范围修复，先重跑 targeted，再跑 full；不得把首次失败直接交差。
- latency 阈值失败：保留失败 raw，不删 outlier；按 browser/PC/network/upper/DDS/bridge/transport/observer 分段定位，每次只改一个主假设并用同 fixture A/B。最多两轮优化同一 root cause，第三轮必须上报 Product 决定换抓手。
- trace 断链或 clock uncertainty 超限：修复测量，不做性能结论；禁止拿 response latency补位。
- stop/watchdog 任一回归：P0 fail，立即回滚本 sprint 自己的相关 latency hunk并由 Full-Stack 重做；不得回滚他人 Nav2 改动。
- worktree/shared hunk 冲突：停止共享文件写入，保存自己 patch，交主节点协调现 owner；禁止自行选择一方覆盖。
- future live sample 失败：立即 post-stop/abort，冻结证据；是否允许下一样本必须由 frozen authorization 的计数/abort contract决定，默认不自动 retry。

## 工程质量与中文注释

- 新增/修改的所有技术注释必须使用中文，解释时钟边界、首帧优先、stop 优先和 fail-closed 原因。
- 每个 owner 对自己修改的代码统计“有意义中文注释行 / 代码行”，比例严格 `>20%`；结果与统计命令写入 `tech-done.md`。
- 不允许靠重复、无意义注释凑比例；测试中的关键 timing/safety fixture 也需中文说明原因。
- 功能、接口或架构变更必须同步 `docs/product/pc_free_roam_mapping_design.md` 与 `docs/interfaces/ros_runtime_contracts.md`；vendor 文件只读不改。

## Artifact 与最终验收合同

- Full-Stack：baseline/optimized raw JSONL、summary、trace continuity、clock calibration、segment histogram、stop regression、test/build/lint/Docker logs、共享文件 hunk preservation audit。
- Hardware：vendor source list、probe calibration/observer uncertainty、只读 artifact review；无 fresh authorization 时明确 `live_nonzero_request_count=0`、`physical_latency_not_measured`。
- `tech-done.md` 必须记录实际文件、所有命令结果、失败定位/修复、baseline 对比、阈值、注释比例、docs 同步与剩余风险。
- 只有 Product closeout 才创建 `side2side_check.md`、`final.md` 并更新 OKR/progress；software/mock 达标不能把 `hil_pass`、`safe_to_control`、route 或 delivery 写 true。

## 剩余风险与停止条件

- 软件 p95 达标仍可能被 Wi-Fi、DDS discovery、firmware loop 或电机死区主导；无 physical observer 不宣称用户问题已关闭。
- T1001 feedback cadence 可能低于真实 wheel onset 分辨率；L/R=0 与现有 IMU-only 证据要求外部 observer。
- 预热 publisher 必须处理 upper restart、DDS subscriber重启与 ROS domain变化，不能缓存永久假 ready。
- 任何优化需要放宽速度、延长 pulse、禁用 stop/watchdog、绕过固定 proxy、直连 `/cmd_vel`/UART，立即停止该方案。
- 当前 v6 authorization 已消费；在新 authorization 前，所有 live nonzero/control 为硬停止条件。

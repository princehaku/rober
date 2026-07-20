# PRD

## 元数据与产品决定

- `sprint_type: epic`
- 状态：`planning_complete_pending_engineer_dispatch`
- 主责：`full-stack-software-engineer`（Full-Stack）
- 并行事实/条件式现场 owner：`rober-hardware-engineer`（Hardware）
- 用户价值：按键后轮子尽快开始动，松键或失去操作上下文时仍立即进入可靠停车链路。
- 产品决定：先建立可归因的 keydown-to-wheel latency waterfall，再优化 warm hot path；response latency 与 wheel-motion latency 永远分账。

## OKR 映射与 KR

- O1 约 `94%`：本轮直面可信底盘控制层的人工操控响应与 current live HIL 缺口，但只有物理 wheel onset 证据才可能改变 live latency 判断。
- O7 约 `93%`：Vue/Node 用户触点提供按键入口、trace identity 与分段可观测性；UI/loopback 单独不能提升 O1 HIL 结论。
- O5 约 `85%` 仍是最低 Objective，但 provider/runtime blocker 已消费 `2/2` 并暂停；本轮不再消费同一 blocker。
- planning 阶段所有百分比 flat、KR `不归档`；当前没有可移入历史区的完成项。

## 问题定义

当前控制链有多个潜在延迟源：浏览器 gate 与请求创建、Node 转发、PC 到 upper 网络、upper 首次 rclpy 初始化/DDS discovery、首帧发布前 subscription wait、burst 内 sleep、同步回包证据聚合、bridge callback/transport lock/日志，以及 firmware 收到换行 JSON 后到电机输出的物理延迟。

前序 micro sprint `sprints/2026.07.21_01-54_o1_minimal_wheel_jog/` 的 `ceo_20260721_0154_minimal_wheel_jog_v6` first-jog 只证明一次 bounded command 已转发、raw nonzero 与 IMU delta 可见；授权已经消费，且 artifact 不含 keydown-to-wheel timestamps，所以它既不是 baseline，也不能支持重试。必须先在 software/mock 路径完成 trace 与优化，再凭新的 bounded authorization 获取物理证据。

## 指标定义

每个样本以唯一 `latency_trace_id` 关联，至少报告：

| 指标 | 起点 | 终点 | 结论边界 |
|---|---|---|---|
| `browser_dispatch_ms` | browser keydown handler entry | fetch/request dispatch | 仅浏览器热路径 |
| `pc_proxy_queue_ms` | Node receive | upstream fetch start | PC 校验/排队 |
| `pc_to_upper_ms` | PC forward start | upper receive | 跨机网络，需校时或用 RTT 分账 |
| `upper_to_cmd_vel_first_publish_ms` | upper receive | 首帧 publisher call | Upper 热路径 |
| `cmd_vel_to_transport_write_ms` | bridge callback entry | configured HTTP/serial write return | ROS/DDS + bridge + transport host write，不是轮子运动 |
| `keydown_to_transport_write_ms` | browser keydown | configured transport write return | 仅在时钟可关联时报告，否则报告区间/unknown |
| `keydown_to_wheel_onset_ms` | browser keydown | 外部/可信反馈检测到首次轮动 | 唯一物理用户体验主指标 |
| `keyup_to_stop_onset_ms` | keyup/blur/page hidden/stop | 轮子开始减速或归零 | 安全性能，不得因启动优化退化 |

所有分位数必须同时给出 sample count、cold/warm 分类、丢样/异常数量和测量 uncertainty。HTTP `200` 或 response complete 不能替代任一 wheel onset 指标。

## 功能需求

### R1：端到端 trace contract

- 浏览器在 `keydown` handler 入口立即生成或继承 `latency_trace_id`，记录 `performance.now()`、`performance.timeOrigin`、direction、hold session/sequence 与 cold/warm 标签。
- PC Node 在 receive、validation complete、forward start、upstream headers/end 记录本机 monotonic 时间；只返回/落盘白名单 timing，不暴露 token、任意 URL 或大 body。
- Upper 在 request receive、manual gate complete、rclpy context ready、首帧 publish、response ready 记录本机 monotonic 时间。
- `esp32_bridge` 在 callback entry、command built、transport write start/end 记录 monotonic 时间与 transport result；当前 live 默认 HTTP `/js` 不变，serial fixture/配置仍验证一行 UTF-8 JSON + newline。
- trace 字段是诊断元数据，不改变 direction/speed/duration/command mode，不得成为运动授权。

### R2：时钟与跨机口径

- 同一进程/同一主机内以 monotonic clock 计算 span：浏览器用 `performance.now()`，Node 用 `process.hrtime.bigint()`，Python 用 `time.monotonic_ns()`。
- browser 与 Node、PC 与 upper、upper 与 ESP32/外部 observer 之间禁止直接相减裸 monotonic 值。
- 跨机指标优先拆成各 host span + request RTT；如必须合成，先执行 offset/RTT calibration，记录 offset、uncertainty、round count 与有效期，uncertainty 超阈值则 end-to-end 值为 `unknown`。
- 物理 wheel onset 优先用同一高帧率画面同时捕获可识别的 keydown marker 与轮子，或使用有明确采样周期/时钟标定的外部传感器；仅凭人眼或 HTTP response 不验收。

### R3：低延迟 warm hot path

- Upper rclpy node/publisher 与 DDS subscription readiness 应在 service readiness/prewarm 阶段完成，首次按键不得承担可避免的 import、node create 或完整 discovery wait。
- 首个非零 `/cmd_vel` frame 应在安全校验通过后立即发布；burst 的持续帧与证据聚合不能阻塞首帧。
- PC Node 复用 HTTP keep-alive/连接池；方向白名单、clamp 和 safety fields 保持同步轻量，不在 forward 前拉 summary/readback。
- Upper response 中体积大、只读证据扫描或反馈汇总应与运动首帧解耦；但错误与 stop 状态仍须 fail closed。若改为 deferred evidence，接口必须显式返回 receipt/evidence pending 状态，不能伪造 complete。
- bridge transport write 必须优先于调试落盘；日志写入不能阻塞下一控制 callback。任何队列化都必须有有界容量、丢弃策略和 stop 优先级。
- 不允许浏览器直连 upper、直接发布 `/cmd_vel` 或直接写 UART 来绕过固定代理和安全 gate。

### R4：安全停止不回归

- `keyup`、所有方向键释放、组合键变化、pointer up/leave/cancel、window blur、page hidden、stop button 保持统一 stop 路径。
- `realtime_hold` 的 `hold_session_id`、递增 `hold_sequence`、`hold_watchdog_ms` 与 upper watchdog 必须保持；断网、丢 pulse、页面崩溃后 watchdog 仍停车。
- stop 优先级高于 pending motion/evidence；不得因 in-flight manual response 阻塞 stop。重复/乱序 hold sequence 必须 fail closed，旧请求不能延长新 session。
- 启动 latency 优化后，software/mock 的 `keyup -> fake stop write` p95 不得比优化前退化超过 `10ms`；live physical stop 阈值由新的 bounded authorization 单独冻结。

### R5：software/mock 验收

- 使用 fake clock、loopback PC/upper、fake rclpy publisher/subscriber 与 fake serial；不得访问真实机器人 endpoint、`/cmd_vel` 或 `/dev/tty*`。
- warm path 至少 `100` 个有效样本；cold-start 另列，不混入 warm 分位数。
- `keydown -> fake configured transport write`：p50 `<=35ms`、p95 `<=60ms`、max `<=100ms`；HTTP 与 serial fixture 分开报告。
- browser dispatch、PC receive-to-forward、upper receive-to-first-publish、bridge callback-to-write 各段必须有独立 histogram；任何单段 p95 `>25ms` 或单样本 `>=50ms` 必须给出原因。
- 与代码改动前相同 fixture baseline 对比，warm p95 至少降低 `30%`；若基线本已低于 `60ms`，则以不回归及消除用户所见 live 主瓶颈为准，不能制造虚假百分比。

### R6：live command-path 与 physical 验收

- 当前 v6 exactly-one authorization 已消费，live nonzero invocation 必须为 `0`。
- 新 physical run 必须先取得 fresh bounded authorization，并冻结 direction、`speed<=0.08m/s`、单次 `duration<=300ms`、sample count、间隔、operator、物理限制、pre/post stop、紧急停止和 abort 条件；计划中的默认候选是 `10` 个有效样本，但没有 CEO 明确授权不得执行。
- live command-path 必须记录 browser/PC/upper/publish/bridge/UART write；它只能证明 command path latency。
- live physical 必须新增可信 wheel onset。目标为 p50 `<=100ms`、p95 `<=150ms`、max `<=200ms`，且相对同配置有效 baseline p95 降低至少 `30%`。
- 若 T1001 `L/R` 仍为 `0/0`，IMU delta 可证明动作迹象但不能当 encoder wheel onset；改用外部观察或写 `physical_latency_not_measured`。

## 非目标

- 不修 Nav2 readiness、route execution、camera、LiDAR、云端或 delivery。
- 不调整速度/PWM、firmware PID、电气、机械、UART 设备/波特率默认值来“压低延迟”。
- 不删除安全确认、stop、watchdog 或 feedback proof boundary。
- 不把现有 first-jog、software/mock、HTTP response、UART write 或 IMU delta升级成 HIL/safe-to-control/route/delivery 完成。

## 优先级与验收

| 优先级 | 验收项 | 必须满足 |
|---|---|---|
| P0 | 测量可信 | trace 全链路、monotonic 分段、跨机 uncertainty、wheel onset 与 HTTP 分账 |
| P0 | 启动响应 | software/mock warm p95 `<=60ms` 且 baseline p95 改善目标 `>=30%` |
| P0 | 停止安全 | keyup/blur/page hidden/button/watchdog 全保留，stop latency 不显著回归 |
| P0 | 授权边界 | v6 已消费，当前实现阶段 live nonzero=`0`；新 physical run 先获 fresh authorization |
| P1 | 实车体验 | 有授权时 physical p50/p95/max 达标，不能测则诚实标 unknown |
| P1 | 工程质量 | targeted/full tests、build/lint、Docker/ROS 相关验证通过，中文技术注释严格 `>20%` |

## 风险与剩余证据

- 最高概率瓶颈是首次 rclpy/DDS readiness 与 request-response 自调度，不应在没有 trace 前凭直觉删除逻辑。
- 跨主机 clock drift 会制造负延迟或虚假改善；未校时只能报告各段与 RTT。
- bridge 的 HTTP/`serial.write()` 返回只表示 transport 接受，不表示 firmware 已解析或轮子已转动。
- 大型 debug log 同步扫描/写入可能拖慢后续 pulse；优化时必须保持 evidence 可追溯和 stop 优先。
- 当前没有可信 physical baseline，live SLO 仍待 fresh authorization 下验证；未验证前 `safe_to_control=false`、`hil_pass=false` 保持。

## 后续留档

当前只完成前置三文档。Full-Stack/HW 完成实现与验证后才允许创建 `tech-done.md`；Product 再按证据创建 `side2side_check.md`、`final.md` 并决定 OKR/docs 更新。

# Sprint 2026.05.13_07-08 Mobile Operation Log Gate - Pre Start

## Sprint Type

- `sprint_type: epic`
- 本轮是跨 owner 的 Objective 4 手机用户体验 sprint planning，预计后续由 full-stack-software-engineer 与 robot-software-engineer 并行执行。
- 当前阶段只创建 planning docs：`pre_start.md`、`prd.md`、`tech-plan.md`。本阶段不改产品代码、测试代码、`OKR.md` 或 `docs/product/` 正文。

## 启动依据

- `OKR.md` 4.1 最新快照更新时间：2026-05-13 06:47 Asia/Shanghai。
- 当前最低 Objective：Objective 4 手机用户体验与低成本量产边界，约 58%。
- Objective 5 云中转约 59%，Objective 1/2/3 分别约 75%/77%/77%。
- 最新 sprint `sprints/2026.05.13_06-07_cloud-external-probe-bundle-gate/final.md` 建议下一轮按 live OKR 选择最低且可推进 Objective；O4 已低于 O5。
- 本机环境为 Docker-only，无真实硬件、真实手机设备、真实云/4G 或 HIL 证据。

## 上轮未完成项

- Objective 5 上轮完成 `software_proof_docker_cloud_external_probe_bundle_gate`，但仍缺真实云、真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL、Nav2/fixed-route、WAVE ROVER 或真实送达。
- Objective 4 最近完成 `software_proof_docker_mobile_web_entrypoint_gate` 和 `software_proof_docker_mobile_task_start_confirmation_gate`，但仍缺 production app、真实手机浏览器/设备验收、真实 PWA install prompt，以及用户从"查看状态"到"处理异常"的手机端闭环。
- `mobile/README.md` 路线图把真实手机浏览器/设备验收、安装提示、弱网体验和操作日志面板列为下一阶段方向；当前 Docker-only 条件下先推进可落地的软件证明。

## 本轮目标

建立 `software_proof_docker_mobile_operation_log_gate`：

- 手机端展示 phone-safe 操作/状态事件日志，让普通用户能看到最近发生了什么、下一步该做什么。
- 异常状态提供恢复提示，不暴露 raw JSON、ROS topic、`/cmd_vel`、串口、波特率、WAVE ROVER 参数、凭证、路径或完整 artifact。
- 提供支持交接摘要入口，帮助用户把当前状态、阻塞原因和下一步安全地交给家人、售后或工程支持。
- 通过 robot compatibility fence 确认 operation-log metadata 不触发 robot action、不 POST ACK、不推进或持久化 cursor，也不改变 `trashbot.remote.v1` command/status/ack 语义。

## 用户价值和产品北极星

用户价值：普通手机用户在任务阻塞、等待 ACK、离线恢复或需要人工接管时，不需要看 raw diagnostics，也能理解"刚才发生了什么、现在卡在哪里、下一步怎么处理"。

产品北极星：rober 的手机端必须成为普通用户唯一可理解入口；软件证明阶段也要把 ACK、状态、异常和支持交接用 phone-safe 语言解释清楚，而不是把内部机器人协议暴露给用户。

## OKR 映射

- Objective 4 KR1：补齐"查看状态 -> 处理异常"这一段手机最小流程。
- Objective 4 KR4：把远程诊断最小数据包的一部分转成用户可读、可交接的事件日志与摘要入口。
- Objective 4 KR5：用户不接触命令行、ROS2、串口或硬件调试，也能理解失败或阻塞状态。
- Objective 4 KR7：继续完善手机端主路径、中文优先文案、按钮安全状态和 support handoff。
- Objective 2/5 guardrail：operation-log metadata 只能是状态解释与支持信息，不得触发机器人动作、ACK 或 cursor 变化。

## 范围边界

本轮后续工程允许范围：

- full-stack-software-engineer：
  - `mobile/web/`
  - `mobile/fixtures/`
  - `mobile/test_mobile_web_entrypoint.py`
  - `mobile/README.md`
  - `docs/product/mobile_user_flow.md`
- robot-software-engineer：
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `docs/interfaces/ros_contracts.md`
  - `docs/product/remote_4g_mvp.md`
- Product owner 后续收口：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - 本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`

本 planning 阶段只允许创建：

- `sprints/2026.05.13_07-08_mobile-operation-log-gate/pre_start.md`
- `sprints/2026.05.13_07-08_mobile-operation-log-gate/prd.md`
- `sprints/2026.05.13_07-08_mobile-operation-log-gate/tech-plan.md`

## 阻塞与风险

- 无真实手机设备/浏览器：本轮不能证明 iPhone/Android 真机、真实 PWA install prompt 或 production app。
- 无真实云/4G/OSS/CDN：本轮不能证明公网、TLS、SIM、CDN live traffic 或生产数据链路。
- 无真实机器人硬件：本轮不能证明 WAVE ROVER、真实串口、Nav2/fixed-route、HIL 或真实送达。
- ACK 仍只能说明 command accepted/processing evidence，不能说明 delivery success。
- 操作日志如果设计过宽，可能泄露内部字段或被误解为 robot action proof；robot fence 必须覆盖 metadata-only 安全边界。

## 需要创建或更新的 sprint 文档

- 已创建/待填写：`pre_start.md`
- 已创建/待填写：`prd.md`
- 已创建/待填写：`tech-plan.md`
- 后续执行后必须补齐：`tech-done.md`
- 后续验收后必须补齐：`side2side_check.md`
- 后续收口后必须补齐：`final.md`

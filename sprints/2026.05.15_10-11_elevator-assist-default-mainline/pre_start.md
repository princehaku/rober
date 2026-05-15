# Sprint 2026.05.15_10-11 Elevator Assist Default Mainline - Pre Start

sprint_type: epic

## 1. 开工依据

用户要求“开始下一轮迭代，根据近期 PR 和评审，建议下一步应深入的OKR；用team继续完成OKR，重新在功能往前走；别测试代码一堆，测试只围栏；优先推进OKR完成度低；本机没有真实硬件，只有docker；最后提交并推送”。

当前 `OKR.md` 4.1 显示最低 Objective 是 Objective 5（约 66%），但同一节和最近两轮 final 均明确：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料时，不应继续堆 O5 本地 metadata。最新 sprint `sprints/2026.05.15_09-10_route-task-field-run-material-validation/final.md` 建议转向 Objective 2 / Objective 3 的真实路线/任务现场材料回填。

本机仍只有 Docker、无真实硬件，因此本轮不承诺真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实电梯、真实喇叭/TTS 或 delivery success。为了让功能继续往前走，本轮选择 Objective 2 的 KR7 明确差距：跨楼层任务默认启用电梯状态链，但只读证据显示 `task_orchestrator.py` 中 `declare_parameter("elevator_assist_enabled", False)`，`autonomous.launch.py` 中 `elevator_assist_enabled` 默认 `false`。

## 2. 用户价值和产品北极星

产品北极星：普通手机用户把垃圾交给小车后，小车能以可解释、可复盘、可安全降级的方式沿固定路线完成投递；跨楼层场景必须把电梯 assisted delivery 放进主任务链，而不是隐藏在默认关闭的 feature flag 后面。

本轮用户价值：把“跨楼层送垃圾需要电梯状态链”从可选 dry-run 推进成默认主链路的软件行为。普通用户和运维同学应能在手机只读状态中理解：当前默认进入电梯 assisted delivery dry-run，系统会记录等待开门、进入电梯、请求人工按楼层、等待目标楼层、出电梯、继续送达等状态；失败时解释人工接管原因。该价值只限 Docker/local 软件证据，不证明真实电梯、真实语音播报、真实导航或真实送达。

## 3. OKR 映射

- Objective 2：主目标。聚焦 KR6 / KR7，把电梯 assisted delivery 状态链从默认关闭推进为默认启用的安全 dry-run 主链路，并要求 task record / diagnostics 落盘 mode、状态链、失败原因、人工接管原因和 evidence_ref。
- Objective 4：支撑目标。手机端只读解释默认电梯 assisted delivery 状态，不放行危险操作，不暴露 raw ROS topic 或硬件细节。
- Objective 5：当前数值最低但本轮不推进。理由是缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 等外部材料；继续本地 O5 metadata 会重复消费同一 blocker。

## 4. KR 拆解或更新

- O2 KR7：`elevator_assist_enabled` 默认从关闭变为开启，但 `elevator_assist_mode` 保持 `dry_run`，并且所有输出必须标注 `not real` / `不证明`。
- O2 KR6：电梯状态链仍是 assisted delivery dry-run，不做真实门识别、楼层识别、TTS 播放、Nav2/fixed-route 驶入驶出或 WAVE ROVER 控制。
- O4 KR6：手机端只读展示电梯 assisted delivery 状态与人工接管原因，不让 Start/Confirm/Cancel 因该 dry-run 自动放行。

## 5. 本轮核心抓手

交付 `software_proof_docker_elevator_assist_default_mainline_gate`：默认启用电梯 assisted delivery dry-run 主链路，并让 Robot diagnostics 与 `mobile/web` 只读面板能解释该状态。验收口径必须明确：这是 software proof only，不是真实电梯、真实喇叭/TTS、真实 Nav2/fixed-route、HIL 或 delivery success。

## 6. 需要做什么

- Robot Platform Engineer：修改 behavior / launch 默认值与 task record / diagnostics 输出，使 `elevator_assist_enabled` 默认启用，mode 保持 `dry_run`，失败或禁用时有明确告警和恢复建议。
- User Touchpoint Full-Stack Engineer：修改手机只读状态展示，解释默认电梯 assisted delivery dry-run 的阶段、人工协助请求和失败原因；不暴露 raw JSON / ROS topic，不改变主操作安全 gating。
- Product Manager / OKR Owner：工程完成后补齐 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和必要产品文档同步核对。

## 7. 优先级和验收口径

P0：Robot 默认启用 `elevator_assist_enabled`，保持 `dry_run` 安全边界，测试覆盖默认主链路与显式降级关闭。
P0：手机端只读解释电梯 assisted delivery 默认状态，且仍明确 `not real` / `不证明` delivery success。
P1：diagnostics / task record 中保留 schema、mode、evidence_ref、failure_code / takeover reason 和 rerun guidance。
P2：文档同步更新 `docs/product/mobile_user_flow.md` 与接口/状态文档，避免产品文档滞后。

## 8. 风险、阻塞和证据链缺口

- 当前没有真实硬件、真实电梯、真实楼层识别、真实 TTS/喇叭、真实 Nav2/fixed-route 或 WAVE ROVER 串口，因此本轮只允许产出 Docker/local 软件证据。
- `elevator_assist_enabled` 默认启用可能让旧测试或旧手机文案误解为真实电梯能力完成；工程实现必须用边界字段和文案阻断该误读。
- 若后续要提升到真实场景，必须补同一 `evidence_ref` 下的门状态、楼层证据、真实路线运行、人工协助记录、task completion 和失败恢复材料。

## 9. 需要创建或更新的 sprint 文档

本阶段创建：

- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/pre_start.md`
- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/prd.md`
- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/tech-plan.md`

工程实现后必须更新：

- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/tech-done.md`
- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/side2side_check.md`
- `sprints/2026.05.15_10-11_elevator-assist-default-mainline/final.md`
- `OKR.md`
- 与实际改动相关的 `docs/` 文档。

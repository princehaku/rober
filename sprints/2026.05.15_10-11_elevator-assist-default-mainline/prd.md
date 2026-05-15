# Sprint 2026.05.15_10-11 Elevator Assist Default Mainline - PRD

sprint_type: epic

## 1. 背景

Objective 2 要求送垃圾任务覆盖电梯 assisted delivery 必达闭环。当前 `OKR.md` 明确 KR7：跨楼层任务默认启用电梯状态链，若降级关闭必须给出明确告警与恢复建议。只读证据显示当前实现仍是默认关闭：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`：`declare_parameter("elevator_assist_enabled", False)`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`：`elevator_assist_enabled` 默认 `false`

最新 sprint 已完成路线/任务现场材料校验，但仍不证明真实 route/task field run、真实 Nav2/fixed-route、真实送达或 Objective 5 external proof。由于本机没有真实硬件，下一步应把 Objective 2 的可软件推进差距收敛：把电梯 assisted delivery 从“可选 dry-run”推进到“默认启用但仍安全 dry-run、可被手机只读解释”。

## 2. 用户价值和北极星

北极星：普通手机用户不需要懂 ROS2、串口、地图或电梯实现细节，也能知道小车跨楼层送垃圾时正在等待开门、请求人工按楼层、等待目标楼层、准备驶出或需要人工接管。

用户价值：

- 对用户：跨楼层任务默认进入可解释流程，不再因为 feature flag 默认关闭而让手机端看不到电梯 assisted delivery 主链路。
- 对运维：Docker/local 证据能确认默认配置、状态落盘、diagnostics 与手机只读文案一致，为下一次真实楼宇受控测试减少配置遗漏。
- 对产品：推进 Objective 2 KR7 的“默认启用电梯状态链”，但保持严谨边界，不把 dry-run 写成真实电梯或 delivery success。

## 3. 范围

### In Scope

- 默认 `elevator_assist_enabled=true`，`elevator_assist_mode=dry_run`。
- Behavior / launch 默认值、task record、diagnostics 的电梯 assisted delivery 状态与失败原因。
- `mobile/web` 只读解释：当前为 software proof / dry-run，不证明真实电梯、真实楼层、真实语音、真实导航或真实送达。
- 相关 `docs/` 文档同步。
- 围栏验证：py_compile、目标 unittest、mobile entrypoint test、`node --check`、required `rg`、scoped `git diff --check`。

### Out of Scope

- 真实电梯开关门识别、真实楼层识别、真实 TTS/喇叭播放。
- 真实 Nav2/fixed-route 驶入/驶出电梯、真实 WAVE ROVER 底盘运动、真实串口/UART、HIL。
- 真实手机设备/browser 验收、production app、真实 PWA prompt/user choice。
- Objective 5 外部 proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 4. 需求

### R1 默认主链路

跨楼层任务默认启用电梯 assisted delivery 状态链。默认模式必须仍是 `dry_run`，并在输出中包含 `software_proof_docker_elevator_assist_default_mainline_gate` 或等价 schema/boundary 字段，避免把默认启用误读成真实能力。

### R2 安全降级

允许显式关闭 `elevator_assist_enabled=false`，但关闭时 task record / diagnostics / phone copy 必须给出明确告警、关闭原因和恢复建议。降级关闭不得静默通过。

### R3 可复盘输出

task record / diagnostics 至少应表达：

- `elevator_assist_enabled`
- `mode=dry_run`
- `target_floor`
- 状态链或事件摘要
- `evidence_ref`
- 失败原因 / `failure_code`
- `requires_human_help` 或人工接管原因
- `not real` / `不证明` 边界

### R4 手机只读解释

手机端必须把电梯 assisted delivery 状态解释成人能理解的中文文案：等待开门、进入电梯、请求人工按目标楼层、等待目标楼层、开门后驶出、继续送达或需要人工接管。手机端不应暴露 raw ROS topic、raw JSON、`cmd_vel` 或硬件协议细节。

### R5 操作安全

本轮不得因为电梯 dry-run 默认启用而放行 Start/Confirm/Cancel 之外的新动作，也不得将 ACK、artifact pass、dry-run complete 写成 delivery success。

## 5. OKR 映射

- Objective 2 KR6：状态机覆盖电梯 assisted delivery 完整状态链；本轮推进 Docker/local dry-run 默认主链路。
- Objective 2 KR7：跨楼层任务默认启用电梯状态链；本轮直接修正 `elevator_assist_enabled` 默认关闭的差距。
- Objective 4 KR6：手机/语音体验需要解释电梯 assisted delivery 失败原因；本轮做手机只读解释支撑。
- Objective 5：不推进。当前最低但外部 evidence 缺失，重复本地 metadata 不应提升 O5。

## 6. 优先级

- P0 Robot：默认启用 + dry-run 边界 + explicit disable warning。
- P0 Full-stack：手机只读解释 + forbidden success wording fence。
- P1 Docs：同步 `docs/product/mobile_user_flow.md` 与接口/diagnostics 文档。
- P1 Product closeout：工程完成后更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 7. 验收口径

通过后只能声明：`software_proof_docker_elevator_assist_default_mainline_gate` 已证明默认电梯 assisted delivery dry-run 主链路、diagnostics/task record metadata 和手机只读解释在 Docker/local 软件环境可验证。

不得声明：

- 真实电梯完成
- 真实喇叭/TTS 播放完成
- 真实 Nav2/fixed-route 驶入/驶出
- HIL 或 WAVE ROVER 实机通过
- 真实 dropoff/cancel completion
- delivery success
- Objective 5 external proof

## 8. 责任 Engineer

- Robot Platform Engineer：主责 behavior / launch / task record / diagnostics。
- User Touchpoint Full-Stack Engineer：主责 `mobile/web` 只读解释和 mobile validation。
- Product Manager / OKR Owner：负责阶段验收、OKR/KR closeout 和 sprint 留档。
- Hardware Infra Engineer：本轮不改硬件；如文案或状态涉及真实 WAVE ROVER / UART 事实，必须先查 `docs/vendor/VENDOR_INDEX.md`。
- Autonomy Algorithm Engineer：本轮不改 Nav2/fixed-route；如后续涉及真实路线运行，再单独规划。

## 9. 风险和补证链

- Docker/local 只能证明默认配置、状态链、文案和软件围栏，不证明真实场景。
- 默认启用可能引发产品误读；必须保留 `not real` / `不证明` 边界和 fail-closed wording。
- 下一层真实证据需要受控楼宇路线、真实门状态、楼层证据、人工协助记录、Nav2/fixed-route runtime log、WAVE ROVER/HIL 和同一 `evidence_ref` 的 task completion。

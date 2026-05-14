# Sprint 2026.05.14_23-24 PC Route Debug Console - PRD

sprint_type: epic

## 用户价值和产品北极星

产品北极星：PC 端开发者/操作员能独立打开一个只读 route debug console，查看 fixed-route 当前状态、关键帧预检、route/task 对账摘要和最近任务状态；页面明确标注 `not_proven`，避免把 Docker/local software proof 误读成 HIL、真实路线实跑或 delivery success。

本轮用户价值不是“又生成一份复盘 artifact”，而是把上一轮 operator review 之后的下一步变成可操作界面：操作员可以从 PC 页面判断是补 keyframe/route status、修 task_record mismatch，还是准备同一 `evidence_ref` 的真实上车复账。

## OKR 映射

- Objective 3：对应 KR5。PC 的关键帧调试页面展示当前位置、目标点、匹配状态、失败原因和最近一次任务状态。
- Objective 2：复用 recent task/task_record 摘要，让送垃圾任务闭环的失败原因、终态和证据引用能被固定路线 debug console 消费。
- Objective 5：不提升。`OKR.md` 4.1/6 明确 O5 只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据才继续推进；本机只有 Docker。
- Objective 1：不提升。本机无真实硬件/串口/WAVE ROVER/HIL。

## KR 拆解或更新

本轮不直接修改 `OKR.md`，但按以下验收准备后续 OKR 更新：

- Objective 3 KR5：若 PC route debug console 可独立运行、JSON API 可消费 fixed_route debug status、`route_progress`、`keyframe_preflight` 和 recent task/task_record 摘要，且围栏验证通过，可作为 `software_proof_docker_pc_route_debug_console_gate` 记录。
- Objective 2 KR5：若最近任务状态、失败原因、task/task_record 摘要能与 route debug summary 合并展示，可作为任务复盘可用性的小幅软件证据。
- Objective 5/O1：即使本轮通过，也不得上调，除非额外获得真实外部云材料或真实硬件/HIL 材料。

## 范围

### In Scope

- `pc-tools/route/route_debug_web.py`：dependency-free 或最小标准库优先的 PC route debug console，读取本地 JSON status/task 文件，提供只读 HTML 和 JSON API。
- `pc-tools/route/README.md` 与 `pc-tools/README.md`：写清运行方式、输入契约、证据边界和不得声明的事项。
- `docs/navigation/fixed_route_workflow.md`：补充 PC route debug console 工作流，强调它不读取硬件、serial/UART 或 Nav2 runtime。
- `operator_gateway_diagnostics.py`：metadata-only 暴露 `pc_route_debug_console` 或 route_debug summary。
- `mobile/web`：只读展示 PC route debug console availability/summary，不能新增控制授权。
- `docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`：同步 metadata-only、phone/support-safe、`not_proven` 和控制边界。

### Out of Scope

- 不读取或控制 WAVE ROVER、serial/UART、Orange Pi 硬件、Nav2 runtime、ROS graph 或 `/cmd_vel`。
- 不把 PC debug console 接入手机主控制流程，不改变 Start/Confirm/Cancel 授权。
- 不声明真实 Nav2/fixed-route 实跑、真实路线采集、HIL、dropoff/cancel completion 或 delivery success。
- 不推进 Objective 5 external proof，不引入公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 伪证据。

## 本轮核心抓手

`software_proof_docker_pc_route_debug_console_gate` 的产品验收含义：

- PC 工具能独立运行，消费文件而不是 onboard ROS2 import。
- 页面和 JSON API 展示：当前位置/当前 checkpoint、目标点、匹配状态、失败原因、`keyframe_preflight`、`route_progress`、recent task/task_record 摘要、`not_proven`。
- diagnostics/mobile 只展示 availability/summary，不触发 robot action、ACK、cursor、terminal ACK 或控制授权。
- 所有 copy 必须避免 “delivery success” 误读，明确 `delivery_success=false` 或等价边界。

## 需要做什么

1. Task A Autonomy 建立 `pc-tools/route/` 独立 route debug console 和 JSON API，并补文档。
2. Task B Robot 在 diagnostics 输出 metadata-only `pc_route_debug_console` 或 route_debug summary，并用测试证明它不触发控制动作。
3. Task C Full-stack 在 `mobile/web` 首屏或诊断区域只读展示 PC route debug console availability/summary，并保持所有控制按钮 gating 不变。

## 优先级和验收口径

P0：

- Task A 能独立从固定 JSON fixture 启动 console/API，不依赖 ROS2 安装。
- 页面/API 必须展示 Objective 3 KR5 所需字段：当前位置/当前 checkpoint、目标点、匹配状态、失败原因、最近一次任务状态。
- 输出必须包含 `not_proven`，并明确不证明 HIL、真实 fixed-route、dropoff/cancel completion 或 delivery success。

P1：

- diagnostics 暴露 phone/support-safe summary；mobile 只读展示 availability/summary。
- 文档同步到 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。

P2：

- UI copy 可读、字段命名稳定、异常输入降级为 blocked/not_proven。

## 对应责任 Engineer

- `autonomy-engineer`：Task A，PC route debug console/JSON API。
- `robot-software-engineer`：Task B，operator gateway diagnostics metadata-only exposure。
- `full-stack-software-engineer`：Task C，mobile/web 只读展示与 fixture/test。

## 风险、阻塞和需要补齐的证据链

- `pc-tools/route/` 独立运行可能暴露现有 onboard `route_debug_web.py` 仍依赖 ROS2 packaging 的耦合；解决方向是 PC 端只读 JSON consumer，而不是搬入 ROS2 runtime。
- 最近 task/task_record 输入可能不存在；页面/API 必须显示 `not_proven` 或 `blocked_missing_task_record`，不能伪造最近任务状态。
- 手机展示可能被误解为可控制机器人；必须使用 metadata-only copy，不能新增控制入口或授权。
- 剩余证据链仍缺：真实路线采集、真实 Nav2/fixed-route 实跑、同一 `evidence_ref` 上车复账、WAVE ROVER/HIL、真实串口、真实云/4G/OSS/CDN/DB/queue。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后更新：`tech-done.md`。
- 验收与收口更新：`side2side_check.md`、`final.md`，并最终更新 `OKR.md`。

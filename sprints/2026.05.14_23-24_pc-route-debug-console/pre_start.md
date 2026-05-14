# Sprint 2026.05.14_23-24 PC Route Debug Console - Pre Start

sprint_type: epic

## 启动结论

本轮启动 fresh Epic sprint：`2026.05.14_23-24_pc-route-debug-console`。

核心抓手：`software_proof_docker_pc_route_debug_console_gate`。

本轮目标不是继续包装上一轮 route/task rehearsal artifact，而是把 PC 端 route debug console 从 onboard 调试入口推进到 `pc-tools/route/` 的独立开发者/操作员工具。它应消费 fixed_route debug status、`route_progress`、`keyframe_preflight`、recent task/task_record 摘要，并输出只读 HTML 页面与 JSON API。证据边界保持 Docker/local software proof；不读取硬件、serial/UART 或 Nav2 runtime，不声明 HIL、真实 fixed-route、dropoff/cancel completion 或 delivery success。

## 用户价值和产品北极星

产品北极星：现场操作员和开发者不用 SSH 到 onboard、也不用理解 ROS2 runtime，就能在 PC 上查看固定路线当前 checkpoint、目标点、匹配状态、失败原因和最近一次任务状态，并清楚知道哪些材料仍是 `not_proven`。

用户价值：

- 操作员能用 PC 只读页面定位固定路线失败原因，减少 raw JSON 和 onboard ROS 命令依赖。
- Autonomy 能把 `route_progress`、`keyframe_preflight` 和 task_record 摘要放到同一视图，为下一轮真实路线/任务材料或同一 `evidence_ref` 上车复账做准备。
- Robot diagnostics 与 mobile/web 只消费 metadata-only 可用性摘要，不把 PC debug 工具误变成手机控制入口。

## 证据来源

- `OKR.md` 4.1：Objective 5 当前约 68%，仍是数字最低；Objective 1 约 75%；Objective 2 与 Objective 3 均约 81%。
- `OKR.md` 6：只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据时，才继续推进 Objective 5；本机只有 Docker，缺真实外部材料。
- 最新 closed sprint `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/final.md`：若外部 O5 材料仍不可用，下一轮 O2/O3 应从 operator review 走向真实路线/任务材料或同一 `evidence_ref` 上车复账，不能继续叠加本地包装层。
- `pc-tools/README.md`：`pc-tools/route/` 仍未落地，`route_debug_web.py` 和 `route_csv_to_yaml.py` 仍位于 onboard。
- `OKR.md` Objective 3 KR5：PC 的关键帧调试页面必须展示当前位置、目标点、匹配状态、失败原因和最近一次任务状态。

## OKR 映射

- Objective 3：主目标。补齐 KR5 的 PC 关键帧调试页面，从 onboard ROS2 debug 入口推进到 PC 工作站可独立运行的 debug console。
- Objective 2：支撑目标。把最近 task/task_record 摘要接入 route debug console，让任务闭环复盘能围绕同一 `evidence_ref` 查看。
- Objective 5：不推进完成度。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据。
- Objective 1：不推进完成度。本机无真实硬件、串口、WAVE ROVER 或 HIL，不能提升真实硬件完成度。

## 本轮核心抓手

`software_proof_docker_pc_route_debug_console_gate`：

- Autonomy：建立 `pc-tools/route/` 独立工具入口，提供只读 HTML 页面与 JSON API。
- Robot：在 diagnostics 暴露 `pc_route_debug_console` 或 route_debug summary，metadata-only，不触发控制动作。
- Full-stack：在 `mobile/web` 只读展示 PC route debug console availability/summary，不新增控制授权，不改变 Start/Confirm/Cancel gating。

## 责任 Engineer

- Task A：`autonomy-engineer`，负责 PC route debug console/JSON API。
- Task B：`robot-software-engineer`，负责 diagnostics metadata-only summary。
- Task C：`full-stack-software-engineer`，负责 mobile/web 只读可用性摘要。

## 风险、阻塞和证据链缺口

- 本轮不访问真实硬件、serial/UART、WAVE ROVER、Nav2 runtime、ROS graph 或 `/cmd_vel`。
- 本轮不声明真实 route run、真实路线采集、dropoff/cancel completion、delivery success、HIL 或 Objective 5 外部云证明。
- 关键证据链缺口仍是：真实 Nav2/fixed-route 实跑、同一 `evidence_ref` 上车复账、真实路线采集、真实 WAVE ROVER/HIL、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 和 production DB/queue。
- 若工程实现发现 `pc-tools/route/` 无法在无 ROS2 环境独立运行，应降级为 dependency-free JSON file consumer，而不是引入 onboard ROS2 import。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后必须更新：`tech-done.md`。
- Epic 收口时必须更新：`side2side_check.md`、`final.md`，并由 Product Owner 更新 `OKR.md` 进展。

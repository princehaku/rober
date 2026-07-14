# Pre Start - O7 Delivery Result Intake

- sprint_type: epic
- Sprint: `sprints/2026.07.13_17-17_o7_delivery_result_intake/`
- Started at: 2026-07-13 17:17 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`

## 上轮未完成项

- O5 仍是最低 Objective，约 `85%`，但最新 O5 CDN/TLS 外部探针收口在 `blocked_http_status_not_success_class`，重复探测同一 4xx endpoint 会连续消费 blocker。
- O1/O3 仍需要 explicit operator-approved current live HIL/current route execution evidence，当前自动化不能自行触碰真实 `/api/base/stop`、`/api/base/manual`、`/cmd_vel`、NavigateToPose 或 WAVE ROVER UART。
- O7/O6 上两轮已经完成 selected-task `inference/request` 与 `events/append`，本轮不得重复 query/readback wrapper 或同类 mission event append。

## 本轮目标

在 PC/O7 consumer-read 选中任务视图中新增一个 local/mock `delivery result intake` action-write 路径，让 operator 能把同一 `task_id` 的 delivery result evidence 写入 O6 现有归档链，并立刻得到 fail-closed receipt。

目标证据边界：

- 接受为 `software_proof_o7_o6_consumer_delivery_result_intake_only`。
- 只证明 PC/O7 selected-task request、adapter guardrail、O6 local/mock delivery result evidence intake/readback receipt。
- 不证明 production cloud、真实 DB/queue、OSS/CDN、4G/SIM、真实手机/browser、route execution、delivery/operator acceptance、HIL、safe-to-control、`/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。

## Owner 和范围

- 主责 owner：`full-stack-software-engineer`
- 允许实现范围：PC workstation O7 consumer-read adapter/API/UI/contracts/tests、相关 O7/O6 interface/product docs、本 sprint `tech-done.md`。
- O6 后端只允许复用现有 `/api/o6/archive/field-evidence` 或现有 consumer detail 合同；如必须改 O6，只能做 delivery result evidence receipt 的窄修补并补对应 unittest。

## 阻塞与切换理由

- 不继续 O5：当前最低 O5 的最近外部证据是 HTTP `4xx`，在 endpoint 未预期返回 success class 前重复跑 CDN/TLS probe 只会重复消费同一 blocker。
- 不继续 O1/O3：当前 live HIL/route execution 需要 operator safety window，自动化不能越权真实控制。
- 转向 O7/O6：delivery result 是任务闭环关键材料，且当前环境可用 local/mock O6 archive 与 PC tests 产生可验证软件结果。

## 验收口径

- O7 新 endpoint 固定为 selected-task path，浏览器不能传任意 O6 endpoint。
- Adapter 只允许 local-loopback `baseUrl`，path/body `task_id` 必须一致。
- Request 必须使用 delivery result evidence 白名单字段，并拒绝 unsafe refs、危险 true fields、raw path、token/header、控制/串口/ROS topic 文案。
- Receipt 必须保留 fixed false fields：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`。
- `tech-done.md` 必须记录实际改动、验证命令输出和剩余风险。

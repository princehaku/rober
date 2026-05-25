# Cloud Phone Command API Mainline Side-by-side Check

## 对照结论

本轮目标是推进 Objective 5 最低项，避免继续新增只读 metadata wrapper。实际结果符合目标：

- 之前：`mobile/web` 主要消费只读 status/diagnostics panel，主动作 endpoint 仍是旧 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 占位。
- 现在：relay 提供 bearer-gated `/api/commands/collect`、`/api/commands/confirm-dropoff`、`/api/commands/cancel`，并把手机任务级请求写入现有 command queue。
- 现在：`mobile/web` 主动作 endpoint 已切到 `/api/commands/*`，提交 `cloud_phone_command_api` envelope，并渲染 queued receipt。

## 安全边界核对

- 没有暴露 `/cmd_vel`、ROS topic、serial/UART、WAVE ROVER、baudrate、Authorization、bearer token、OSS secret、本地路径或 complete artifact。
- Receipt 固定显示 `ack_semantics=queued_not_delivery_success`。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 未被改成 true。
- Robot polling、status、ACK 既有 contract 未被破坏。

## 验收状态

- Robot focused validation：通过。
- Mobile focused validation：通过。
- Scoped whitespace validation：通过。
- 未运行 Docker/Humble build、真实公网、真实 4G/SIM、production DB/queue、真实手机/browser、HIL 或真实路线/送达验证；这些不属于本轮软件主链路 proof 范围。

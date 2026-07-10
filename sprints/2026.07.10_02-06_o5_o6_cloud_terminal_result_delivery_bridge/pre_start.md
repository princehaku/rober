# O5/O6 Cloud Terminal Result Delivery Bridge Pre-Start

## Sprint 类型

sprint_type: epic

## 本轮目标

把 O5 `trashbot.cloud_command_terminal_result.v1` 软件终态结果，安全桥接到 O6/O7 已有 `delivery_result_evidence` 与 route delivery closure 链路中。目标不是新增 summary wrapper，而是让云端 command/result 主路径可以成为同一 `task_id` 的送达结果证据来源。

## OKR 和最低优先级

- `OKR.md` 4.1 当前最低 active Objective：O5、O6、O7 并列约 80%；O1 约 85%。
- `OKR.md` 第 5 节提示：O6/O7 下一步应优先 production cloud、真实或准现场 live route execution、delivery record / operator confirmation，而不是继续做 summary wrapper。
- 本轮选择：O5 -> O6/O7 交界的 cloud terminal result delivery bridge。
- 选择理由：最近多轮已连续推进 O6/O7 local/mock route evidence 与 closure packet；O5 同为最低且较久未推进。本轮把已有 O5 robot-facing terminal result 主路径接入 O6 delivery result evidence，能够同时推进 cloud command/result 与 delivery closure 证据链。

## 最近两轮 blocker 核对

- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/final.md`：完成，未 blocked；建议下一轮转向真实/准现场 live Nav2 result、delivery record/operator confirmation 或 production cloud。
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/final.md`：完成，未 blocked；明确下一轮优先 production cloud、真实或准现场 live route execution、delivery record/operator confirmation，而不是继续做 summary wrapper。

结论：没有连续 blocked 的同一根因；但若继续补 wrapper/decoder 会违反方向提醒。本轮转到 cloud terminal result -> delivery result evidence 桥接。

## Owner

- `robot-algorithm-engineer`：在 field route evidence manifest 中接收并转换 O5 cloud terminal result。
- `robot-software-engineer`：确保 O6 readback/consumer 对该来源保持白名单、fail-closed 与测试覆盖。

## 验收口径

- `cloud_command_terminal_result` 输入必须转成标准 `delivery_result_evidence`，并嵌入 manifest 顶层与 `field_motion_evidence_packet`。
- O6 consumer detail 能回读 `source_schema=trashbot.cloud_command_terminal_result.v1` 的 delivery result evidence。
- 全链路必须保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 危险字段、路径、token、raw/base64、credential URL 必须 fail-closed，不能回显原始敏感内容。

## 边界

本轮只能证明 local/mock software bridge：云端终态结果记录可作为 O6/O7 只读 delivery result evidence 来源。不证明真实 production cloud、真实 4G/TLS、production DB/queue、真实 live Nav2、真实 delivery success、真实 operator media、真实 robot motion 或完整路线长期验收。

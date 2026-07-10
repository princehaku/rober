# O5 Reconciliation Same-Task Archive Smoke PRD

## 用户价值

运营人员需要确认云端命令终态和路线/送达材料是否属于同一任务。现在 gate 已存在，但 terminal material 仍主要来自手写 fixture。本轮把 relay reconciliation v2 作为输入，降低“云端结果已记录但没有进入任务证据链”的人工对照成本。

## 产品范围

本轮做：

- 接受 O5 reconciliation v2 JSON 作为 `--cloud-terminal-result-json` 输入来源。
- 从 reconciliation 的 nested `terminal_result` 提取安全白名单字段。
- 运行本地可复跑 smoke，证明 O5 relay write/read material 可生成 manifest，并被 O6 archive/readback 同 task 消费。
- 保持所有 safety flags 为 false。

本轮不做：

- 不连接真实 production cloud、OSS/CDN、4G/SIM 或 TLS 域名。
- 不发送 `/cmd_vel`，不启动 Nav2，不控制 WAVE ROVER，不改硬件参数。
- 不把 gate ready 宣称为 delivery success。

## 验收口径

- reconciliation v2 recorded 时，manifest 中 `delivery_result_evidence.source_schema` 仍为 `trashbot.cloud_command_terminal_result.v1`，并记录 reconciliation 来源边界。
- reconciliation pending/missing/unsafe 时，manifest fail-closed，不能输出 ready gate。
- smoke 输出中必须读回 `same_task_mission_gate_ready_not_success_proof`，同时 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- O6 consumer detail 必须能通过 `include=same_task_mission_evidence_gate` 读回同 task gate。

## OKR 映射

- O5/KR1：云中转 command/status/result 主链路进一步进入 mission evidence gate。
- O6/KR2/KR6：archive/consumer readback 可消费 O5 reconciliation-derived terminal material。
- O7/KR3：既有 O7 consumer detail 可继续读取该 O6 task；本轮若不改 O7 UI，不上调 O7 主进度。

## 风险

- 仍是 local/mock software proof，不等于 production cloud。
- 若实现只新增总结字段而没有 relay -> archive smoke，则不得作为主线 OKR 提升。
- 若 smoke 依赖真实硬件或外部网络，本轮应降级为本地 mock 并保留切换入口。

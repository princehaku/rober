# PRD - O5 Command Lifecycle CLI Export Refresh

## 用户价值

普通手机用户和现场支持同学需要看到云命令生命周期的安全验收包边界：ACK 只代表 relay 接收或处理，不代表机器人执行、送达成功或可控制。当前最低 Objective 仍是 O5，但真实 production/cloud 材料缺失，所以本轮选择刷新一个现有但非最近消费的 O5 CLI export artifact，作为后续 field-owner review 的当前材料。

## OKR 对齐

- Objective 5 当前约 `85%`，仍是最低进度项。
- 本轮针对 O5，但只生成软件 proof，不可上调百分比。
- 选择理由：最近 O5 support-only packet/gate 已被连续消费；本轮不重复那些 blocker，而是刷新 command lifecycle CLI export 这一独立安全导出边界。

## 需求

1. 生成 sprint-scoped artifact：`artifacts/o5_command_lifecycle_cli_export.json`。
2. Artifact schema 必须是 `trashbot.cloud_command_lifecycle_replay_acceptance_packet_cli_export.v1`。
3. Evidence boundary 必须是 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`。
4. Artifact 必须包含 `accepted_processing_only_not_delivery_success`、`terminal_result_pending`、field owner handoff、next required evidence 和 not-proven list。
5. 固定 false 字段必须保留：`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`ack_post_allowed=false`、`command_replay_allowed=false`、`command_resubmit_allowed=false`、`robot_command_side_effects_allowed=false`、`nav2_triggered=false`、`hil_pass=false`。
6. Artifact 和日志不得泄露 token、Authorization、URL、raw command、cursor/checksum、local path、serial/UART、WAVE ROVER、ROS topic、`/cmd_vel` 或 traceback。

## 验收口径

- 接受：fresh CLI export artifact 可以被生成、JSON 校验通过、结构断言通过、相关单测通过、sprint `tech-done.md` 记录实际改动/验证/剩余风险。
- 拒绝：任何 production ready、delivery success、safe-to-control、robot control、route execution、HIL 或真实外部云/手机证据 claim。

# 2026.05.26 37-38 Operator Gateway Payload Reviewer ACK Source Cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 引入 `first_dict_value`。
  - 仅将 4 个 `field_evidence_material_resolution_reviewer_ack_*_preserved_source` 旧三元链改为显式候选 resolver：
    - `field_evidence_material_resolution_reviewer_ack_intake_preserved_source`
    - `field_evidence_material_resolution_reviewer_ack_review_decision_preserved_source`
    - `field_evidence_material_resolution_reviewer_ack_review_handoff_preserved_source`
    - `field_evidence_material_resolution_reviewer_ack_followup_escalation_status_preserved_source`
  - 保留旧候选顺序：`latest_status` robot summary、`latest_status` plain summary、`diagnostics_source` robot summary、`diagnostics_source` plain summary、`latest_status` raw key、`diagnostics_source` raw key，默认值仍为 `{}`。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 reviewer ACK material-resolution preserved-source 已改用显式 `first_dict_value` 候选列表，并明确该调整不改变 payload key、fallback 默认值、safe-copy、`not_proven`、ROS2、launch 或硬件行为。
- 流程修复
  - 将 sprint 类型声明调整为项目要求的 `## sprint_type: micro`。
  - 对 `operator_gateway_diagnostics_payload_sources.py` 执行 `git add -N`，让 `git diff --check` 覆盖该 intent-to-add 新文件内容。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.244s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无错误输出。
- `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_37-38_operator-gateway-payload-reviewer-ack-source-cleanup/tech-done.md`
  - 结果：通过，无 whitespace 错误输出；`operator_gateway_diagnostics_payload_sources.py` 已通过 `git add -N` 纳入本次 diff check 覆盖。
- 额外核对：`rg` 确认 4 个目标 `field_evidence_material_resolution_reviewer_ack_*_preserved_source` 变量均调用 `first_dict_value`。

## 剩余风险

- 本轮是 payload source resolver 的结构性清理，不包含真实 ROS2 节点启动、Docker/Humble 全量构建、HIL、真实串口、WAVE ROVER feedback 或硬件验证。
- 未修改硬件/vendor/launch/UART/serial 行为。

# Operator Gateway Payload Field Evidence Rerun Acceptance Followup Status Source Cleanup

## sprint_type: micro

## 实际改动

- 将 `operator_gateway_diagnostics_payload.py` 中三条 handoff-intake 后续 status source 选择链改为复用 `first_status_dict(...)`：
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_status_source`
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_status_source`
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_status_source`
- 保留原候选顺序：latest robot summary -> latest plain summary -> latest raw artifact -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}`。
- 未新增 `diagnostics_source["summary"]` 或 `diagnostics_source["diagnostics_summary"]` 兜底，后续 ref/env 覆盖逻辑未改动。
- 同步更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录本轮分片继续保持字段级证据边界，不引入 aggregate summary。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.510s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无 stdout/stderr，退出码 0。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_56-57_operator-gateway-payload-field-evidence-rerun-acceptance-followup-status-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_56-57_operator-gateway-payload-field-evidence-rerun-acceptance-followup-status-source-cleanup/tech-done.md`
  - 关键输出：命令无 whitespace error 输出，退出码 0。

## 剩余风险

- 本轮仅做软件侧 payload source cleanup，未改硬件参数、launch、接口字段语义，也未做真实 ROS2 节点联调或硬件在环验证。

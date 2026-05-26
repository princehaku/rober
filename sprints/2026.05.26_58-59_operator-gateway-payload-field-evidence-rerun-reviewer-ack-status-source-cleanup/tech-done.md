# Operator Gateway Payload Field Evidence Rerun Reviewer ACK Status Source Cleanup

## sprint_type: micro

## 实际改动

- 在 `operator_gateway_diagnostics_payload_sources.py` 新增 `first_non_empty_dict_value(*candidates, default=None)`，只返回第一个非空 `dict`，用于保留旧链路“非空 preserved_source 才优先”的语义。
- 在 `operator_gateway_diagnostics_payload.py` 将三条 reviewer ACK owner-response status source 长 fallback 链改为调用 `first_non_empty_dict_value`：
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_status_source`
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_status_source`
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_status_source`
- 三条链均保持候选顺序：非空 `preserved_source` -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}`。
- 同步更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录本轮只收敛字段级 source resolver，不新增 latest-status、generic diagnostics summary、ref/env、ROS2、launch、硬件或 UART 行为变化。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.210s` / `OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_58-59_operator-gateway-payload-field-evidence-rerun-reviewer-ack-status-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_58-59_operator-gateway-payload-field-evidence-rerun-reviewer-ack-status-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace error 输出。

## 剩余风险

- 本轮未做硬件、串口、launch、HIL 或真实机器人验证，因为改动仅限 operator gateway diagnostics payload 选择逻辑。

# Operator Gateway Payload Field Evidence Rerun Result Status Source Cleanup

## sprint_type: micro

## 实际改动

- 将 `field_evidence_rerun_execution_result_intake_status_source`、`field_evidence_rerun_execution_result_review_decision_status_source`、`field_evidence_rerun_execution_result_review_handoff_status_source` 的长 `isinstance(..., dict)` 三元链替换为 `first_status_dict(...)`。
- 保留原字段级候选顺序：latest robot summary -> latest plain summary -> latest raw artifact -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}`。
- 未新增 `diagnostics_source["summary"]` 或 `diagnostics_source["diagnostics_summary"]` 兜底；后续 ref/env 覆盖逻辑保持不变。
- 同步更新 `docs/interfaces/operator_gateway_diagnostics.md`，说明本分片保持字段级证据边界，不引入 aggregate summary。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.123s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_53-54_operator-gateway-payload-field-evidence-rerun-result-status-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_53-54_operator-gateway-payload-field-evidence-rerun-result-status-source-cleanup/tech-done.md`
  - 结果：通过，无空白错误输出。

## 剩余风险

- 本轮只做软件单元测试、Python 编译检查和 diff 空白检查；未触碰硬件参数、launch、ROS2 topic/action/service 契约，也未进行真实机器人或串口 HIL 验证。

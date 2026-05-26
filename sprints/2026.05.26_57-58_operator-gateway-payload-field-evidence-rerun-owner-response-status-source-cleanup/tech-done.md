# Operator Gateway payload field evidence rerun owner-response status source cleanup

## sprint_type: micro

## 实际改动

- 收敛 `operator_gateway_diagnostics_payload.py` 中三条 owner-response 后续 status source 选择链：
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_status_source` 改用 `first_status_dict`，保留 latest robot summary -> latest plain summary -> latest raw artifact -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}` 顺序。
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_status_source` 改用 `first_dict_value`，保留 preserved source -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}` 顺序。
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_status_source` 改用 `first_dict_value`，保留 preserved source -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}` 顺序。
- 对 preserved source 优先级补充中文注释，明确字段级证据边界和空 dict 仍按 `isinstance(..., dict)` 命中，不新增 truthy 条件。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录本轮分片只收敛 dict status source 选择，不新增 generic diagnostics summary fallback，不改变 env/ref 覆盖顺序。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.234s`，`OK`。
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无编译错误输出。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_57-58_operator-gateway-payload-field-evidence-rerun-owner-response-status-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_57-58_operator-gateway-payload-field-evidence-rerun-owner-response-status-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace error 输出。

## 剩余风险

- 本轮不改硬件参数、launch、ROS2 接口字段语义或后续 env/ref 覆盖逻辑；验证范围以单元测试、Python 编译和 diff 空白检查为准。
- 未做真实机器人、串口、WAVE ROVER、手机端或 HIL 验证；本次改动不涉及这些硬件路径。

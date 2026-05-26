# Operator Gateway payload field evidence rerun acceptance handoff status source cleanup

## sprint_type: micro

## 实际改动

- 在 `operator_gateway_diagnostics_payload.py` 中，将三条 field evidence rerun execution-result acceptance handoff status-source 长 `isinstance(..., dict)` 三元链替换为 `first_status_dict(...)`：
  - `field_evidence_rerun_execution_result_acceptance_review_handoff_status_source`
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_status_source`
  - `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_status_source`
- 三条链均保留原候选顺序：latest robot summary -> latest plain summary -> latest raw artifact -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}`。
- 没有新增 `diagnostics_source["summary"]` 或 `diagnostics_source["diagnostics_summary"]` 兜底；后续 ref/env 覆盖逻辑保持不变。
- 补充中文注释，说明 handoff status source 仍保持字段级证据边界，不引入 aggregate summary。
- 在 `docs/interfaces/operator_gateway_diagnostics.md` 同步记录本分片的 resolver 边界和兼容性不变项。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.185s`、`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_55-56_operator-gateway-payload-field-evidence-rerun-acceptance-handoff-status-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_55-56_operator-gateway-payload-field-evidence-rerun-acceptance-handoff-status-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace 错误输出。

## 剩余风险

- 本轮只做 Python 单测、compileall 和 diff whitespace 检查；未运行 ROS2 `colcon build`、真实机器人、串口、WAVE ROVER 或 HIL 验证。
- 未改硬件参数、launch、接口字段语义或 summarizer 的 env/ref 覆盖路径；硬件运行时风险不在本 micro sprint 覆盖范围内。

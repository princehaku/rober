# operator gateway payload field evidence rerun acceptance status source cleanup

## sprint_type: micro

## 实际改动

- 将 `field_evidence_rerun_execution_result_acceptance_packet_status_source`、`field_evidence_rerun_execution_result_acceptance_backfill_status_source`、`field_evidence_rerun_execution_result_acceptance_backfill_review_decision_status_source` 的长 `isinstance(..., dict)` 三元 fallback 链收敛为 `first_status_dict(...)`。
- 三条链路保留原字段级候选顺序：latest robot summary -> latest plain summary -> latest raw artifact -> diagnostics robot summary -> diagnostics plain summary -> diagnostics raw artifact -> `{}`。
- 未新增 `diagnostics_source["summary"]` 或 `diagnostics_source["diagnostics_summary"]` 兜底，后续 ref/env 覆盖逻辑保持不变。
- 同步更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 acceptance status source 仍保持字段级证据边界，不引入 aggregate summary。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.127s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无输出，退出码 0。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_54-55_operator-gateway-payload-field-evidence-rerun-acceptance-status-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_54-55_operator-gateway-payload-field-evidence-rerun-acceptance-status-source-cleanup/tech-done.md`
  - 关键输出：命令无输出，退出码 0。

## 剩余风险

- 本轮仅做 payload source selection cleanup，不改变 ROS2 接口、launch、硬件参数或 UART/serial 行为。
- 未覆盖真实机器人、真实串口、WAVE ROVER feedback、手机/Web 端到端验收；本 sprint 验证边界是 Python 单测、compileall 和 diff 静态检查。

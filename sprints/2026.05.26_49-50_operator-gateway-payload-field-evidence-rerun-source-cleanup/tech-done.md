# operator gateway payload field evidence rerun source cleanup

## sprint_type: micro

## 实际改动

- 在 `operator_gateway_diagnostics_payload.py` 中仅收敛三条 field evidence rerun source fallback 链：
  - `field_evidence_rerun_callback_review_decision_source`
  - `field_evidence_rerun_callback_review_handoff_source`
  - `field_evidence_rerun_handoff_intake_source`
- 使用已有 `first_dict_value` helper 替换长 `a if isinstance(a, dict) else ...` 链，保持原候选顺序不变。
- 保留 `diagnostics_source["summary"]` 和 `diagnostics_source["diagnostics_summary"]` 旧快照兜底，未新增接口字段语义，未改硬件参数或 launch。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.259s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出，退出码 0。
- `cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_49-50_operator-gateway-payload-field-evidence-rerun-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_49-50_operator-gateway-payload-field-evidence-rerun-source-cleanup/tech-done.md`
  - 结果：通过，无输出，退出码 0。

## 剩余风险

- 本轮是 payload 内部可读性收敛，验证范围覆盖 Python 单测、语法编译和 diff whitespace 检查；未运行 ROS2 Docker `colcon build`。
- 未做 HIL、真实串口或 WAVE ROVER 验证；本次未涉及硬件参数、底盘运动、串口、传感器或机械假设。

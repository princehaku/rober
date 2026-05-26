# Operator Gateway payload real material owner ACK source cleanup

## sprint_type: micro

## 实际改动

- 将 `field_evidence_real_material_followup_escalation_status_source` 的初始 dict source 选择收敛到 `first_status_dict`，并保持旧顺序：raw artifact -> plain summary -> robot diagnostics summary。
- 将 `field_evidence_real_material_owner_ack_intake_preserved_source` 与 `field_evidence_real_material_owner_ack_review_decision_preserved_source` 收敛到 `first_status_dict`，并保持旧顺序：robot diagnostics summary -> plain summary -> raw artifact。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，说明本轮 resolver 顺序、不新增 `diagnostics_source["summary"]` / `diagnostics_source["diagnostics_summary"]` 兜底，以及后续 ref/env 覆盖链保持不变。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.262s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `cd /mnt/e/rober && git add -N sprints/2026.05.26_60-61_operator-gateway-payload-real-material-owner-ack-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_60-61_operator-gateway-payload-real-material-owner-ack-source-cleanup/tech-done.md`
  - 结果：通过，无输出。

## 剩余风险

- 本轮未修改硬件参数、launch、接口字段语义或后续 ref/env 覆盖逻辑。
- 当前验证覆盖 payload 单元测试、Python 编译检查和限定范围 whitespace 检查；未覆盖真实 ROS2 运行时与硬件联调。

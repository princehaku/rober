# Operator Gateway Payload Real Material Status Source Cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload_sources.py` 新增 `first_non_empty_dict_then_first_dict()`，用于保留 preserved_source 只有非空 dict 才优先的语义，同时让后续 fallback 继续按旧链路接受空 dict。
- `operator_gateway_diagnostics_payload.py` 将 `field_evidence_real_material_request_dispatch_status_source` 收敛为 `first_status_dict(...)`，候选顺序保持 latest robot summary、latest plain summary、latest raw artifact、diagnostics robot summary、diagnostics plain summary、diagnostics raw artifact、`{}`。
- `operator_gateway_diagnostics_payload.py` 将 `field_evidence_real_material_response_intake_status_source`、`field_evidence_real_material_response_review_decision_status_source`、`field_evidence_real_material_response_review_handoff_status_source` 改为复用新 helper；review decision 和 review handoff 未新增 latest_status 候选，也未新增 `diagnostics_source["summary"]` 或 `diagnostics_source["diagnostics_summary"]` 兜底。
- `docs/interfaces/operator_gateway_diagnostics.md` 补充本轮 real material status-source cleanup 的 resolver 顺序、preserved-source 空 dict 兼容语义，以及不改变 env/ref、ROS2、launch、硬件或 UART 行为的边界。
- 本轮未改硬件参数、launch、接口字段语义，也未改后续 env/ref 覆盖逻辑。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.202s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，命令无输出，退出码 0。
- `cd /mnt/e/rober && git add -N ... && git diff --check -- ...`
  - 结果：通过，命令无输出，退出码 0。

## 剩余风险

- 本轮验证覆盖 Python 单测、语法编译和 diff 空白检查；未运行 ROS2 容器级 `colcon build`，也未做真实机器人/HIL 验证。
- 变更只影响 operator gateway diagnostics payload 的 dict source 选择，不涉及硬件链路；无 Product、Hardware、Autonomy 或 Full-Stack 协同需求。

# Operator Gateway Payload Mobile Field Material Source Cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py` 将
  `mobile_field_material_review_decision_source` 和
  `mobile_field_material_retest_request_source` 的长 `isinstance(..., dict)`
  三元 fallback 链替换为 `first_status_dict`。
- 两条链保留旧顺序：latest raw artifact -> latest plain summary ->
  diagnostics raw artifact -> diagnostics plain summary -> `{}`。
- 未新增 `robot_diagnostics_*_summary`、`diagnostics_source["summary"]` 或
  `diagnostics_source["diagnostics_summary"]` fallback；后续 ref/env 覆盖和
  summarizer 调用位置未改。
- `docs/interfaces/operator_gateway_diagnostics.md` 补充本轮 resolver 顺序和
  不变项说明。

## 验证结果

- 通过：
  `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.296s`，`OK`。
- 通过：
  `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：
  `cd /mnt/e/rober && git add -N sprints/2026.05.26_64-65_operator-gateway-payload-mobile-field-material-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_64-65_operator-gateway-payload-mobile-field-material-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace 错误输出。

## 剩余风险

- 当前改动是 resolver 可读性收敛，不包含真实手机/浏览器、ROS2 运行态或硬件/HIL 验证。

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py` 中
  `route_task_field_retest_execution_pack_source`、
  `route_task_field_retest_session_handoff_source`、
  `route_task_field_retest_result_intake_source` 改为显式
  `first_dict_value` 候选列表。
- 保留原有候选顺序、默认 `{}`、空 dict 命中语义、generic
  `diagnostics_source["summary"]` / `diagnostics_source["diagnostics_summary"]`
  fallback 相对顺序，以及后续 env/ref 覆盖和 summarizer 调用。
- `docs/interfaces/operator_gateway_diagnostics.md` 补充三条 route field
  retest source 的 helper 化说明和顺序保持边界。

## 验证结果

- 通过：
  `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  输出关键结果：`Ran 326 tests in 7.579s`，`OK`。
- 通过：
  `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  命令返回 0，无错误输出。
- 通过：
  `cd /mnt/e/rober && git add -N sprints/2026.05.26_66-67_operator-gateway-payload-route-field-retest-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_66-67_operator-gateway-payload-route-field-retest-source-cleanup/tech-done.md`
  命令返回 0，无 whitespace 错误。

## 剩余风险

- 本轮是结构清理，不覆盖真实 ROS2 运行、硬件串口、WAVE ROVER 或 HIL
  验证。

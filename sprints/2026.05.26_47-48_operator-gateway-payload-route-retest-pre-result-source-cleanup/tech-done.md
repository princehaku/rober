# Operator Gateway Payload Route Retest Pre-Result Source Cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 清理 `route_task_field_retest_evidence_dispatch_source`、`route_task_field_retest_callback_intake_source`、`route_task_field_retest_callback_review_decision_source`、`route_task_field_retest_review_result_handoff_source` 四个重复三元链。
  - 改为显式调用 `first_dict_value(...)`，候选顺序保持为 `latest_status` raw key、`latest_status` plain summary、`diagnostics_source` raw key、`diagnostics_source` plain summary、`diagnostics_source["summary"]`、`diagnostics_source["diagnostics_summary"]`、默认 `{}`。
  - 增加中文注释说明这四个 pre-result source 有 legacy generic summary fallback，不能和普通字段级 resolver 混为一谈。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 route task field retest pre-result source 已改用显式 resolver，并说明保留 `summary` / `diagnostics_summary` fallback。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键结果：`Ran 326 tests in 7.114s`，`OK`。
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键结果：命令退出码 0，无输出。
- 通过：`rg -n -C 2 "route_task_field_retest_(evidence_dispatch|callback_intake|callback_review_decision|review_result_handoff)_source = first_dict_value|diagnostics_source\\.get\\(\\\"summary\\\"\\)|diagnostics_source\\.get\\(\\\"diagnostics_summary\\\"\\)" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 关键结果：四个目标 source 均命中 `first_dict_value`，且四个候选列表均保留 `diagnostics_source.get("summary")` 和 `diagnostics_source.get("diagnostics_summary")`。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_47-48_operator-gateway-payload-route-retest-pre-result-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_47-48_operator-gateway-payload-route-retest-pre-result-source-cleanup/tech-done.md`
  - 关键结果：命令退出码 0，无输出。

## 剩余风险

- 本轮未改变 ROS2 接口、launch、硬件配置、UART/serial 行为，也未执行真实机器人或硬件在环验证。
- 本轮只覆盖 route task field retest pre-result 四个 source；result_acceptance、field_evidence_rerun、hardware、mobile 及其他 payload 区域保持原状。

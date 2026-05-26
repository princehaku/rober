# route retest acceptance/backfill source cleanup tech done

日期：2026-05-26

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `route_task_field_retest_result_acceptance_packet_source`、`route_task_field_retest_result_acceptance_backfill_source`、`route_task_field_retest_result_backfill_review_decision_source` 的手写三元 fallback 链改为显式 `first_dict_value(...)` 候选列表。
  - 保持原候选顺序：`latest_status` raw key、`latest_status` plain `*_summary`、`diagnostics_source` raw key、`diagnostics_source` plain `*_summary`、`diagnostics_source["summary"]`、`diagnostics_source["diagnostics_summary"]`、默认 `{}`。
  - 增加中文注释，说明这三个 acceptance/backfill source 需要兼容旧路由复测整包 summary artifact，不能用普通字段级 resolver 替代。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 route task field retest result acceptance/backfill source 已改用 explicit resolver，并明确保留 `summary` / `diagnostics_summary` fallback。
- `sprints/2026.05.26_48-49_operator-gateway-payload-route-retest-acceptance-source-cleanup/tech-done.md`
  - 按项目 micro sprint 格式要求，将类型声明从裸行修正为 `## sprint_type: micro`。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键结果：`Ran 326 tests in 7.177s`，`OK`。
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键结果：命令退出码 0，无输出。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_48-49_operator-gateway-payload-route-retest-acceptance-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_48-49_operator-gateway-payload-route-retest-acceptance-source-cleanup/tech-done.md`
  - 关键结果：命令退出码 0，无输出。
- 额外核对：`rg` 确认三个目标 source 均已改为 `first_dict_value(...)`，且候选列表仍保留 `diagnostics_source.get("summary")` 与 `diagnostics_source.get("diagnostics_summary")`。

## 剩余风险

- 本轮只清理指定三个 source 查找，不触碰 review dispatch/intake/decision/handoff、callback、field_evidence_rerun、hardware、mobile 或其他 payload 区域。
- 本轮不涉及 WAVE ROVER、ESP32、Orange Pi、UART、serial、launch 或硬件配置；硬件 HIL 与真实 ROS2 bringup 不在验证范围内。

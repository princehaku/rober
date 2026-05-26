## sprint_type: micro

## 实际改动

- 将 `operator_gateway_diagnostics_payload.py` 中
  `route_task_field_retest_result_reconciliation_source`、
  `route_task_field_retest_material_pack_source`、
  `route_task_field_retest_material_callback_packet_source` 三条重复三元链
  改为显式 `first_dict_value(..., default={})` 候选列表。
- 保持旧 source key、候选顺序和空 dict 命中语义不变；未修改后续 env/ref
  覆盖、summarizer、payload key、ROS2 接口、launch、硬件、UART/serial 或测试断言。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录三条 source 的
  helper 化范围、顺序保持和结构清理边界。

## 验证结果

- 通过：
  `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.305s`，`OK`
- 通过：
  `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：
  `cd /mnt/e/rober && git add -N sprints/2026.05.26_67-68_operator-gateway-payload-route-field-retest-material-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_67-68_operator-gateway-payload-route-field-retest-material-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace/error 输出。

## 剩余风险

- 本轮是非硬件 payload source 结构清理，未触碰硬件、vendor、launch、
  UART/serial、WAVE ROVER 或 ROS2 接口；风险主要剩余在真实运行时上游数据组合
  未做硬件在环验证。

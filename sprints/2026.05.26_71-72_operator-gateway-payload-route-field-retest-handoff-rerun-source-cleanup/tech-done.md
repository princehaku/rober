## sprint_type: micro

## 实际改动

- 将 `operator_gateway_diagnostics_payload.py` 中
  `route_task_field_retest_acceptance_execution_handoff_intake_source` 的长三元
  fallback 链改为显式 `first_dict_value(..., default={})` 候选列表。
- 将 `route_task_field_retest_acceptance_execution_rerun_queue_source` 的长三元
  fallback 链改为显式 `first_dict_value(..., default={})` 候选列表。
- 两条 source 链保持各自旧顺序；handoff-intake 仍按 latest raw -> latest
  plain summary -> latest robot diagnostics summary -> diagnostics raw ->
  diagnostics plain summary -> diagnostics robot diagnostics summary ->
  diagnostics `summary` -> diagnostics `diagnostics_summary` -> `{}`。
- rerun-queue 仍按 latest robot diagnostics summary -> latest plain summary ->
  latest raw -> diagnostics robot diagnostics summary -> diagnostics plain
  summary -> diagnostics raw -> diagnostics `summary` -> diagnostics
  `diagnostics_summary` -> `{}`。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录两条链已 helper
  化，且两条链的候选顺序不同，不能归一化。

## 验证结果

- 通过：
  `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 10.214s`，`OK`。
- 通过：
  `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：
  `cd /mnt/e/rober && git add -N sprints/2026.05.26_71-72_operator-gateway-payload-route-field-retest-handoff-rerun-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_71-72_operator-gateway-payload-route-field-retest-handoff-rerun-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace error。

## 剩余风险

- 本轮只做结构清理，不修改 payload key、summarizer、env/ref 覆盖、ROS2
  接口、launch、硬件、UART/serial 或测试断言语义。
- 未做真实机器人、真实 ROS2 graph 或硬件串口验证；本轮不涉及硬件链路。

# Operator Gateway Payload Cloud Guard Source Cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `cloud_guard_source`、`poll_backoff_source`、`ack_lookup_pending_source`、`ack_accepted_result_pending_source`、`terminal_result_verification_source`、`cancel_pending_source` 的长 `isinstance(..., dict)` 三元链收敛为 `first_dict_value(..., default={})`。
  - 保持 malformed-response guard 与 poll-backoff guard 的窄候选顺序：latest `remote_readiness` -> diagnostics `remote_readiness` -> latest raw guard -> latest robot summary -> `{}`，未新增 diagnostics guard fallback。
  - 保持 ACK lookup、ACK accepted-result、terminal result verification、cancel pending 的旧候选顺序：latest `remote_readiness` -> diagnostics `remote_readiness` -> latest raw guard -> latest robot summary -> diagnostics raw guard -> diagnostics robot summary -> `{}`。
  - 未改 `_remote_readiness_for_*` 后续写回 `latest_status["remote_readiness"]` 的逻辑。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 补充本轮 cloud guard resolver 顺序、不变项，以及不新增 generic diagnostics summary fallback 的边界。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，关键输出 `Ran 326 tests in 7.147s` / `OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，命令无输出，退出码 0。
- `cd /mnt/e/rober && git add -N sprints/2026.05.26_62-63_operator-gateway-payload-cloud-guard-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_62-63_operator-gateway-payload-cloud-guard-source-cleanup/tech-done.md`
  - 结果：通过，命令无输出，退出码 0。

## 剩余风险

- 本轮为 payload source resolver 结构清理，未接入真实云端、ROS2 runtime、硬件、UART 或 WAVE ROVER HIL；验证边界以单元测试、Python 编译检查和 diff whitespace 检查为准。

# 2026.05.26 40-41 operator gateway payload owner-response reviewer ACK source cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 verified-terminal owner-response reviewer ACK intake、review decision、review handoff、follow-up escalation status 四个 preserved-source 旧三元链改为 `first_status_dict(...)`。
  - 为四个变量分别定义字段级 keys tuple，保留旧 alias 优先级：`latest_status` 的 robot summary、plain summary、raw key，再到 `diagnostics_source` 的同组三个字段级 alias。
  - 不启用 `fallback_to_diagnostics_source=True`，缺失字段级 alias 时仍默认 `{}`，避免扩大 owner response ACK 证据边界。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 verified-terminal owner-response reviewer ACK preserved-source 已迁移到 resolver，且只允许字段级 alias。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.274s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无输出，退出码 0。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_40-41_operator-gateway-payload-owner-response-reviewer-ack-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_40-41_operator-gateway-payload-owner-response-reviewer-ack-source-cleanup/tech-done.md`
  - 关键输出：命令无输出，退出码 0。
- 额外核对：`cd /mnt/e/rober/onboard && rg -n "verified_terminal_result_material_owner_response_reviewer_ack_(intake|review_decision|review_handoff|followup_escalation_status)_(keys|preserved_source)|fallback_to_diagnostics_source=True" src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 关键结果：四个 reviewer ACK preserved-source 变量均使用 keys tuple + resolver；`fallback_to_diagnostics_source=True` 只出现在既有 generic material intake/review/review-handoff 区块，不在本轮 reviewer ACK 区块。

## 剩余风险

- 本轮不改变 ROS2 接口、launch、硬件配置、UART/serial 行为，未做 HIL 或真实机器人验证。
- 本轮只清理四个指定 reviewer ACK preserved-source 变量，其他 payload 区域保持现状。

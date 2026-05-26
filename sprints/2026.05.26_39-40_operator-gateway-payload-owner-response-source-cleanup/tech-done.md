# 2026-05-26 39-40 operator gateway payload owner-response source cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py`：仅清理 3 个
  `verified_terminal_result_material_owner_response_*_preserved_source` 变量，
  把重复三元链改为字段级 keys tuple 加 `first_status_dict` resolver 调用。
- `docs/interfaces/operator_gateway_diagnostics.md`：记录 owner-response
  preserved-source 已改用 resolver，并明确只允许字段级 alias，不允许把整个
  `diagnostics_source` 当作 owner response 证据。
- 未修改 `reviewer_ack_*` preserved-source、payload key、summary 变量名、
  alias 优先级、fallback 默认值、safe-copy 内容、`not_proven` 内容、ROS2 接口、
  launch、硬件配置或 UART/serial 行为。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键结果：`Ran 326 tests in 7.417s`，`OK`。
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键结果：命令退出码 0，无输出。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_39-40_operator-gateway-payload-owner-response-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_39-40_operator-gateway-payload-owner-response-source-cleanup/tech-done.md`
  - 关键结果：命令退出码 0，无 whitespace/error 输出。
- 额外核对：`rg` 确认 3 个目标 owner-response preserved-source 变量均已改为
  keys tuple 加 `first_status_dict` resolver 调用，并且没有设置
  `fallback_to_diagnostics_source=True`。

## 剩余风险

- 当前为结构性清理，主要风险是 alias 顺序或 fallback 边界误改；本轮通过单测、
  compileall、diff whitespace 检查和窄范围 `rg` 核对收口。
- 本轮不覆盖硬件 HIL、真实串口、WAVE ROVER feedback、Nav2 运行或上车验证。

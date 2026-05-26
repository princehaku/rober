# 2026-05-26 38-39 operator gateway payload verified-terminal source cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py`：仅清理 4 个
  `verified_terminal_result_material_*_preserved_source` 变量，把重复三元链改为
  `first_status_dict` 调用。
- `docs/interfaces/operator_gateway_diagnostics.md`：记录 verified-terminal
  preserved-source 已改用 resolver，并明确 `diagnostics_source` 兜底边界。
- 未修改 ROS2 接口、launch、硬件配置、UART/serial 行为，也未扩展到
  owner_response / reviewer_ack preserved-source 块。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键结果：`Ran 326 tests in 7.254s`，`OK`。
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键结果：命令退出码 0，无输出。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_38-39_operator-gateway-payload-verified-terminal-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_38-39_operator-gateway-payload-verified-terminal-source-cleanup/tech-done.md`
  - 关键结果：命令退出码 0，无 whitespace/error 输出。
- 额外核对：`rg` 确认 4 个目标 preserved-source 变量均已改为
  `first_status_dict` resolver 调用，前三个保留
  `fallback_to_diagnostics_source=True`，followup 保持字段级兜底。

## 剩余风险

- 当前为结构性清理，风险集中在 alias 顺序或 fallback 语义误改；本轮通过单测、
  compileall 和 diff whitespace 检查收口。
- 本轮不覆盖硬件 HIL、真实串口、WAVE ROVER feedback、Nav2 运行或上车验证。

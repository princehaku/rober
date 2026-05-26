# Micro Sprint Tech Done

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source` 从旧三元链改为显式 keys tuple + `first_status_dict(...)`。
  - 保留旧候选顺序：`latest_status` raw key、summary key、`robot_diagnostics_*_summary`，再到 `diagnostics_source` 的同三类字段，默认 `{}`。
  - 未启用 `fallback_to_diagnostics_source=True`，继续只接受字段级 alias，避免把整包 diagnostics 当作手机实机验收 review-handoff 证据。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 mobile field-trial tail execution handoff review-handoff source 已改用 resolver，且不改变 payload、ROS2、launch、硬件、UART/serial 或用户可见状态语义。

## 用户旅程变化和触点收益

手机/Web 端 payload 字段、状态说明、失败解释和控制可用性不变；收益是最后一个 mobile real-device field-trial acceptance tail source 的来源解析也收敛到统一 resolver，后续排查真实手机验收交接来源时可以直接审查 keys tuple 和字段级 alias 边界。

## 接口影响

- 不新增、不删除、不重命名 payload key。
- 不改变 summary 变量名、alias 优先级、默认 `{}` fallback、`not_proven` 或 safe-copy 内容。
- 不改变 ROS2 接口、launch、硬件配置、UART/serial 行为。
- 不改 UI，不新增 mock，不改变用户可见状态语义。

## 验证结果

已执行：

1. `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
   - 结果：通过，`Ran 326 tests in 7.156s`，`OK`。
2. `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
   - 结果：通过，无错误输出。
3. `cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_45-46_operator-gateway-payload-mobile-field-trial-tail-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_45-46_operator-gateway-payload-mobile-field-trial-tail-source-cleanup/tech-done.md`
   - 结果：通过，无 whitespace/error 输出。

额外核对：

- `rg -n "execution_handoff_review_handoff_source(_keys)?|first_status_dict" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 结果：确认 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source_keys` 已定义，且 tail source 通过 `first_status_dict(...)` 解析。

## 失败定位

无失败。

## 剩余风险

本轮是结构性软件清理，只覆盖单元测试、Python 编译、diff whitespace 检查和窄 `rg` 核对；不证明真实手机浏览器、真实 ROS2 runtime、真实 4G 链路、真实 WAVE ROVER/UART/HIL 或现场 field-trial 验收。

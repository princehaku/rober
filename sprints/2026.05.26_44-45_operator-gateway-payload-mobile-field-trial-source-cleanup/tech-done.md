# Micro Sprint Tech Done

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将七个 mobile real-device field-trial acceptance source 查找从重复三元链改为显式 keys tuple + `first_status_dict(...)`。
  - 保留旧候选顺序：`latest_status` raw key、summary key、`robot_diagnostics_*_summary`，再到 `diagnostics_source` 的同三类字段，默认 `{}`。
  - 未改 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source`，也未启用 `fallback_to_diagnostics_source=True`，避免把整包 diagnostics 当作手机真实验收状态。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 mobile real-device field-trial acceptance source 已使用 resolver，且只允许字段级 alias。
- 未修改 `operator_gateway_diagnostics_payload_sources.py`，现有 resolver 语义已经满足本轮任务。

## 用户旅程变化和触点收益

手机/Web 端看到的 diagnostics payload 字段名、状态语义和失败解释不变；收益是 source 解析结构更集中，后续排查 mobile real-device field-trial acceptance 状态来源时，可以直接审查 keys tuple 和 resolver 调用，减少重复三元链带来的维护风险。

## 接口影响

- 不新增、不删除、不重命名 payload key。
- 不改变 summary 变量名、alias 优先级、`not_proven` / safe-copy 内容或默认 `{}` fallback。
- 不改变 ROS2 接口、launch、硬件配置、UART/serial 行为。
- 不改 UI，不新增 mock，不改变用户可见状态语义。

## 验证结果

已执行：

1. `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
   - 结果：通过，`Ran 326 tests in 7.237s`，`OK`。
2. `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
   - 结果：通过，无错误输出。
3. `cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_44-45_operator-gateway-payload-mobile-field-trial-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_44-45_operator-gateway-payload-mobile-field-trial-source-cleanup/tech-done.md`
   - 结果：通过，无 whitespace/error 输出。

额外核对：

- `rg` 确认本轮七个 mobile real-device field-trial acceptance source 已改为 keys tuple + `first_status_dict`；既有 `execution_handoff_review_handoff_source` 保持原逻辑，未纳入本轮范围。

## 失败定位

无失败。

## 剩余风险

本轮是结构性清理，只覆盖软件单测、编译和 diff whitespace 检查；不证明真实手机浏览器、真实 ROS2 runtime、真实 4G 链路、真实 WAVE ROVER/UART/HIL 或现场 field-trial 验收。

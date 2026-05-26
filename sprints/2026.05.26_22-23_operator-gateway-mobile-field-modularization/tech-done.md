# Operator Gateway Mobile Field Modularization Tech Done

## Sprint Type

sprint_type: micro

## 实际改动

- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_mobile_field.py`，承接 mobile route/elevator field-device precheck、mobile field material intake/review/retest、mobile real-device field-trial acceptance 相关常量、默认 blocked summary、`not_proven` helper、source contract helper、unsafe-field helper 和 summarize 函数。
- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，保留 public compatibility facade，从新模块 re-export 原有常量、helper 和 summarize 函数；`build_diagnostics_payload` 的调用点和测试导入路径保持不变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，补充 mobile field diagnostics 模块边界、兼容导入和 metadata-only / not_proven 证据边界说明。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过。
  - 关键输出：`Ran 326 tests in 7.024s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_mobile_field.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_22-23_operator-gateway-mobile-field-modularization/tech-done.md`
  - 结果：通过，无输出。

## 失败定位

- 首轮 `python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 失败，根因是新模块漏引 `_safe_pc_route_debug_value`，`summarize_mobile_field_material_retest_request` 在构造 `source_review_decision` 时触发 `NameError`。
- 修复方式：在 `operator_gateway_diagnostics_mobile_field.py` 从 `operator_gateway_diagnostics_route_rehearsal` 补充导入 `_safe_pc_route_debug_value`，随后全量诊断单测通过。

## 剩余风险

- 本轮是结构拆分，不改变 payload/schema/gate/alias/safe copy/not_proven 判定口径，也不证明真实手机浏览器、production app/PWA、真实 route/elevator field pass、Nav2/fixed-route 实跑、WAVE ROVER 运动、真实串口/UART、HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 当前工作树存在前序 dirty / untracked sprint 和诊断模块文件，本轮未清理、未回滚、未重命名无关文件。

## 用户旅程与接口影响

- 用户旅程变化：无新增 UI 流程；手机/Web 仍通过既有 diagnostics payload 读取 mobile field 和 real-device acceptance 只读摘要。
- 触点收益：facade 体积下降，mobile field / real-device acceptance 诊断逻辑集中到独立模块，后续维护手机现场验收状态、失败解释和只读材料摘要时更容易定位，不改变普通用户可见字段。
- 接口影响：无公开接口破坏；`operator_gateway_diagnostics.py` 继续 re-export 原有名称，`/api/status` / `/api/diagnostics` payload key、schema、gate、alias、默认值、错误语义保持兼容。
- 前后端/ROS2 联调说明：本轮未触发 ROS2 topic/action/service 或真实硬件联调；验证范围为 Python 单元测试、模块编译和 diff 静态检查。

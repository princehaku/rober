# 2026.05.26 26-27 operator gateway PR5 material modularization

sprint_type: micro

## 实际改动

- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_pr5_material.py`，承接 PR5 review/material metadata-only diagnostics 的常量、required/status tuple、`not_proven` helper、default blocked summary、source contract、unsafe guard、false-state guard 和 `summarize_pr5_*` 函数。
- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，移除已迁移的 PR5 review/material 实现，并从新模块显式 re-export 原有 `PR5_*` 常量、`summarize_pr5_*` 函数和原有私有 helper 名称；`build_diagnostics_payload` 调用点和 payload alias 未变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，补充 PR5 review/material diagnostics 的模块边界说明，声明本次拆分仅为结构迁移。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过。
  - 关键输出：`Ran 326 tests in 7.151s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无错误输出。
- `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_pr5_material.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_26-27_operator-gateway-pr5-material-modularization/tech-done.md`
  - 结果：通过，无错误输出。

## 剩余风险

- 本轮采用硬件资料入口 `docs/vendor/VENDOR_INDEX.md` 作为边界确认来源，但只迁移 PR5 review/material diagnostics metadata，不新增或修改 UART、波特率、电压、引脚、底盘协议、固件、机械尺寸、传感器选型或真实硬件验收结论。
- 验证范围为 Python 单测、模块编译和 whitespace 检查；未运行 Docker/ROS2 colcon、真实串口、WAVE ROVER feedback、HIL 或实车验证，因为本次改动不触碰运行时硬件链路。

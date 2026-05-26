# operator gateway payload builder modularization tech done

## sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_payload.py`，承载 `_drop_safe_alias_inputs`、`build_diagnostics_payload`、`diagnostics_payload` 与 payload 组装直接依赖的 import。
- 收窄 `operator_gateway_diagnostics.py` 为兼容 facade：从 common re-export `_task_terminal_field_material_intake_copy_is_unsafe`，并显式 re-export payload 模块中的入口函数。
- 将 `_task_terminal_field_material_intake_copy_is_unsafe` 的单一 canonical 实现迁入 `operator_gateway_diagnostics_common.py`，payload 模块直接使用 common helper，避免 facade/payload 双定义。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，说明 payload assembly 已迁入内部模块，facade 继续保持兼容导出。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.205s`、`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：`cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_common.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_35-36_operator-gateway-payload-builder-modularization/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace 错误。
- 通过：`rg -n "^def _task_terminal_field_material_intake_copy_is_unsafe|_task_terminal_field_material_intake_copy_is_unsafe" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_common.py`
  - 关键输出：只有 `operator_gateway_diagnostics_common.py` 存在 `def _task_terminal_field_material_intake_copy_is_unsafe`；facade 与 payload 仅 import/re-export。

## 剩余风险

- 未跑真实机器人、Docker/Humble 全量构建、硬件串口或 WAVE ROVER HIL；本轮仅做 payload builder 结构迁移，不涉及硬件配置或 ROS2 launch 行为。

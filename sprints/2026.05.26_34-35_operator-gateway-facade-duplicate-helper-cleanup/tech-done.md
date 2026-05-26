# Operator Gateway Facade Duplicate Helper Cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics.py` 删除已经迁移到 canonical 模块的重复 default-summary helper 函数体。
- `operator_gateway_diagnostics.py` 从 `operator_gateway_diagnostics_cloud_worker.py` 和 `operator_gateway_diagnostics_route_field_run.py` 显式导入对应 `_default_*` helper；route field artifacts、route terminal、task terminal 的 `_default_*` helper 已有显式导入并继续作为 facade 兼容导出。
- `_task_terminal_field_material_intake_copy_is_unsafe` 暂留在 facade。原因是 `operator_gateway_diagnostics_field_evidence_material.py` 等材料模块当前通过 facade 延迟解析该 helper，贸然迁移会扩大导入图调整范围并引入循环导入风险。
- `docs/interfaces/operator_gateway_diagnostics.md` 记录 facade 现在复用 canonical default helper，重复实现已移除，接口与 payload 语义不变。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键结果：`Ran 326 tests in 7.146s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键结果：命令退出码 0，无错误输出。
- 通过：`cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_common.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_field_evidence_material.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_34-35_operator-gateway-facade-duplicate-helper-cleanup/tech-done.md`
  - 关键结果：命令退出码 0，无 whitespace 错误输出。

## 剩余风险

- 本轮未做硬件、HIL、真实串口、WAVE ROVER feedback、Nav2 runtime 或手机端联调验证；改动仅限 Python import/export 结构、接口文档与 sprint 留档。
- `_task_terminal_field_material_intake_copy_is_unsafe` 仍是 facade 暂留兼容 helper，后续如果要迁入 common 或材料模块，需要先拆除材料模块对 facade helper bridge 的延迟依赖并单独验证导入图。

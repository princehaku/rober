# operator gateway field evidence rerun modularization

sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_field_evidence_rerun.py`，承接 field evidence rerun 诊断域的 schema/gate/status 常量、not_proven helper、default summary helper、source contract/unsafe field helper、execution callback review handoff 字段映射 helper，以及 `summarize_field_evidence_rerun_*` 函数。
- `operator_gateway_diagnostics.py` 保持兼容 facade，从新模块显式 re-export 原有 public import/API 表面；现有测试和调用点无需改 import。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 field evidence rerun 诊断域已迁入独立内部模块，且 payload、schema、gate、alias、safe copy、命令可用性和 metadata-only 边界不变。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 第二轮通过：`Ran 326 tests in 7.058s`，`OK`。
  - 第一轮失败定位：迁移 execution callback review handoff bridge helper 时删除范围过宽，误把 route-task field retest source-contract helper 从 facade 移走，触发 `_route_task_field_retest_execution_pack_source_contract` `NameError`；已恢复非 rerun helper 到 facade 后重跑通过。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 通过，无输出。
- `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_field_evidence_rerun.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_19-20_operator-gateway-field-evidence-rerun-modularization/tech-done.md`
  - 通过，无输出。

## 剩余风险

- 本轮是 metadata-only software proof，只做 Python 单测、compileall 和 diff whitespace 检查；未覆盖 HIL、真实串口、WAVE ROVER feedback、ESP32、Orange Pi、Nav2 runtime、真实手机浏览器或现场投递闭环。
- 未改硬件配置、launch 参数、串口、波特率、速度映射或机械参数；本轮不需要 Product、Hardware、Autonomy 或 Full-Stack 协同。

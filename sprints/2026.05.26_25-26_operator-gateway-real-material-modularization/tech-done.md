# operator-gateway real material modularization

sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_real_material.py`，承接 real material metadata 诊断域的 schema/gate 常量、required `not_proven` tuple、默认 blocked summary、source contract、unsafe `evidence_ref` guard、manifest template safe helper、not_proven helper 和 summarize 函数。
- `operator_gateway_diagnostics.py` 保持兼容 facade，通过显式 import/re-export 暴露原有名称；`build_diagnostics_payload` 调用点和测试导入路径保持不变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 real material 诊断域已迁移到内部模块且行为语义不变。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.041s`，`OK`。
  - 首轮失败定位：机械搬移时 `_real_material_followup_escalation_status_not_proven` 少了最终 `return values`，导致 `summary["not_proven"]` 为 `None`；已补回并复跑通过。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_real_material.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_25-26_operator-gateway-real-material-modularization/tech-done.md`
  - 结果：通过，无输出。

## 剩余风险

- 本轮仅迁移 diagnostics metadata 代码，不新增或修改 UART、波特率、电压、引脚、底盘协议、固件、机械尺寸或真实硬件验收结论。
- 硬件资料边界采用 `docs/vendor/VENDOR_INDEX.md` 作为入口来源；该入口指向 Orange Pi Zero 3 手册/原理图和 WAVE ROVER vendor 资料。本轮未触碰硬件事实，未进行 HIL、真实串口、WAVE ROVER feedback 或真实材料验收。

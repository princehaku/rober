# Tech Done

## sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_payload_sources.py`，提供
  `first_dict_value` 与 `first_status_dict` 两个内部 preserved-source
  resolver。
- 在 `operator_gateway_diagnostics_payload.py` 中只重构
  `field_evidence_material_resolution_intake` 到
  `field_evidence_material_resolution_owner_response_review_handoff` 这组
  alias 顺序一致的 preserved-source 查找逻辑。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 payload source
  resolver 的模块边界和本轮未迁移 reviewer ACK 块的原因。

## 验证结果

- 通过：
  `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.121s` / `OK`
- 通过：
  `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无输出，退出码 0。
- 通过：
  `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_36-37_operator-gateway-payload-source-resolver/tech-done.md`
  - 关键输出：命令无输出，退出码 0。
- 只读核对：
  `rg -n "first_status_dict|first_dict_value|payload source resolver|field_evidence_material_resolution_intake_preserved_source" ...`
  - 关键结果：helper 定义位于 `operator_gateway_diagnostics_payload_sources.py`，
    payload builder 仅有 7 个 `first_status_dict` 调用，均在本轮 material
    resolution preserved-source 组内。

## 剩余风险

- 本轮是软件结构重构，没有触碰 launch、硬件配置、UART/serial、WAVE
  ROVER 或真实 HIL 路径；验证范围不覆盖真实机器人运行。
- `reviewer_ack_*` preserved-source 块保留旧实现，因为其 legacy alias
  fallback 顺序不同，后续若迁移需要单独做兼容性核对。

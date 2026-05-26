# operator gateway payload field evidence rerun intake source cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `field_evidence_rerun_material_dispatch_source` 与 `field_evidence_rerun_callback_intake_source` 从长 `isinstance(..., dict)` 三元链收敛为 `first_dict_value(...)` 显式候选列表。
  - 保留既有候选顺序：latest robot summary -> latest summary -> latest raw -> diagnostics robot summary -> diagnostics summary -> diagnostics raw -> `diagnostics_source["summary"]` -> `diagnostics_source["diagnostics_summary"]` -> `{}`。
  - 扩展相邻中文注释，说明这一组 field evidence rerun source 保留旧快照 summary 兜底是为了兼容历史诊断 payload 回放。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 同步记录本轮分片已把 material dispatch 与 callback intake source 纳入 `first_dict_value` resolver 边界，且不改变 payload 字段、接口、launch、硬件或 UART 行为。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.139s`，`OK`。
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无输出，退出码 0。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_50-51_operator-gateway-payload-field-evidence-rerun-intake-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_50-51_operator-gateway-payload-field-evidence-rerun-intake-source-cleanup/tech-done.md`
  - 关键输出：命令无输出，退出码 0。

## 剩余风险

- 本轮只做 payload source resolver 等价收敛，未运行真实 ROS2 节点、HIL、串口、WAVE ROVER feedback 或硬件 smoke。
- 工作区已有大量本轮范围外未提交改动，本轮未回滚、未整理，也未验证这些范围外改动。

# Operator Gateway Payload Material Blocker Source Cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py` 中
  `field_evidence_material_blocker_escalation_pack_preserved_source` 改为使用
  `first_status_dict`，候选 key 顺序保持为 robot diagnostics summary、plain
  summary、raw artifact，并继续按 `latest_status` 后 `diagnostics_source`
  解析，默认 `{}`。
- `docs/interfaces/operator_gateway_diagnostics.md` 补充本轮 resolver 边界：
  不新增 `diagnostics_source["summary"]` 或
  `diagnostics_source["diagnostics_summary"]` 兜底，不改变后续 ref/env 覆盖
  路径，不改变 ROS2、launch、硬件、UART 或 WAVE ROVER 行为。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，关键输出 `Ran 326 tests in 7.185s` / `OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，命令无输出。
- `cd /mnt/e/rober && git add -N sprints/2026.05.26_61-62_operator-gateway-payload-material-blocker-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_61-62_operator-gateway-payload-material-blocker-source-cleanup/tech-done.md`
  - 结果：通过，命令无输出。

## 剩余风险

- 本轮只做软件层 resolver 写法收敛，未触碰硬件参数、launch、接口字段语义或真实机器人运行链路；未覆盖 HIL、真实串口、WAVE ROVER feedback、Nav2 实机路径。

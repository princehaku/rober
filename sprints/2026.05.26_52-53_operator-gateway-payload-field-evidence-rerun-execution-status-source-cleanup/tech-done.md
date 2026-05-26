# Operator Gateway Payload Field Evidence Rerun Execution Status Source Cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py` 将 field evidence rerun queue、execution callback review decision、execution callback review handoff 的 status-source 长 fallback 链收敛为 `first_status_dict`，显式保留 robot summary、plain summary、raw artifact 的 key 顺序，并保持 `latest_status` 优先于 `diagnostics_source`。
- `operator_gateway_diagnostics_payload.py` 将 field evidence rerun execution pack、execution callback intake 的 diagnostics-only 长 fallback 链收敛为 `first_dict_value`，只包住原 diagnostics candidates，没有新增 `latest_status` 候选。
- `operator_gateway_diagnostics_payload.py` 增加中文注释，说明本组 status source 不引入 `diagnostics_source["summary"]` / `diagnostics_source["diagnostics_summary"]` aggregate 兜底，避免扩大证据来源；后续 ref/env 覆盖逻辑未改。
- `docs/interfaces/operator_gateway_diagnostics.md` 同步记录本轮分片的 resolver 边界、key 顺序和 aggregate summary 非兜底约束。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.260s` / `OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：`cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_52-53_operator-gateway-payload-field-evidence-rerun-execution-status-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_52-53_operator-gateway-payload-field-evidence-rerun-execution-status-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无 whitespace error 输出。

## 剩余风险

- 本轮只做 payload status-source resolver 收敛，验证范围覆盖单元测试、Python 编译和 diff 空白检查。
- 未做真实机器人、HIL、串口或 WAVE ROVER 验证；本轮未改硬件参数、launch、ROS2 接口字段语义，硬件运行风险不应扩大。

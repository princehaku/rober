# Operator Gateway Payload Cloud Lifecycle Source Cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `cloud_support_handoff_safe_export_source` 的长 `isinstance(..., dict)` 三元链收敛为 `first_status_dict`，保持 latest raw -> latest plain summary -> latest robot summary -> diagnostics raw -> diagnostics plain summary -> diagnostics robot summary -> `{}`。
  - 将 `cloud_command_lifecycle_audit_export_source` 收敛为 `first_status_dict`，未命中 dict 时才调用原有 `build_cloud_command_lifecycle_audit_export(...)` 默认 builder，避免默认参数提前求值改变旧语义。
  - 将两条 replay acceptance packet reviewer ACK source 链收敛为 `first_status_dict`：follow-up 未命中时仍默认 `{}`，owner-response intake bridge 未命中时仍默认上一阶 generated follow-up summary。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 补充本轮 resolver 顺序与默认值说明，明确未新增 `diagnostics_source["summary"]` 或 `diagnostics_source["diagnostics_summary"]` 兜底。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 通过，关键输出：`Ran 326 tests in 7.208s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 通过，命令返回 0，无语法错误输出。
- `cd /mnt/e/rober && git add -N sprints/2026.05.26_63-64_operator-gateway-payload-cloud-lifecycle-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_63-64_operator-gateway-payload-cloud-lifecycle-source-cleanup/tech-done.md`
  - 通过，命令返回 0，无 whitespace/error 输出。

## 剩余风险

- 本轮仅做 payload source resolver 结构收敛，不改变 builder/summarizer 输出字段，不覆盖真实手机、云端、Nav2、WAVE ROVER、UART 或 HIL 运行时验证。
- 未发现失败项；验证范围限定为 operator gateway diagnostics 单元测试、Python 编译检查和本轮三文件 diff 格式检查。

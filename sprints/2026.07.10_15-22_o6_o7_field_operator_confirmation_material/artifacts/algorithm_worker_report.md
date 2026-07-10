# Algorithm Worker Report

## 自主能力目标和本轮抓手

- 目标：实现 Algorithm producer `trashbot.field_operator_confirmation_material.v1`。
- 抓手：在 `field_route_evidence_manifest.py` 新增 `--field-operator-confirmation-json`，安全消费真实上位机 operator report/latest result 或准现场 summary，并同时输出 manifest 顶层与 `field_motion_evidence_packet.field_operator_confirmation_material`。
- 证据边界：`software_proof_field_operator_confirmation_material_only`，只证明 operator confirmation material 被白名单摘要消费，不证明真实送达、真实控制、HIL 或 production cloud。

## 实际改动文件

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/algorithm_worker_report.md`

## 实现内容和接口影响

- 新增 CLI：`--field-operator-confirmation-json <operator_report_or_summary.json>`。
- 新增 additive schema：`trashbot.field_operator_confirmation_material.v1`。
- 新增固定 proof scope/evidence boundary：`software_proof_field_operator_confirmation_material_only`。
- 新增 ready status：`field_operator_confirmation_material_ready_not_delivery_proof`。
- 新增字段：`schema`、`proof_scope`、`evidence_boundary`、`status`、`task_id`、`task_id_source`、`source`、`operator_report_present`、`operator_report_status`、`operator_confirmation_present`、`operator_confirmation_status`、`operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`、`observed_motion`、`observed_stop`、`reported_at`、`same_task_id_consumed`、`linked_route_material_present`、`linked_delivery_material_present`、`operator_material_consumed`、`support_only_reason`、`blocked_reasons`、`next_required_evidence`、`material_summaries`。
- 固定 false 字段：`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。
- fail-closed 条件：缺输入、坏 JSON、root 非 object、task mismatch、operator identity/material id 缺失、危险 true、raw/body/path/token/URL/base64/traceback/credential 类字段或文本污染，均只让本 section `blocked_not_proven`，不回显原文。

## 验证结果

运行时间：2026-07-10 15:39:42 CST。

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

结果：

```text
Ran 73 tests in 0.543s
OK
```

```bash
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
```

结果：通过，无输出。

## 失败定位

- 本轮指定验收命令均通过，没有未修复失败。

## 数据、样本或调试输出变化

- 新增 ready fixture 覆盖同 task operator report：顶层与 `field_motion_evidence_packet.field_operator_confirmation_material` 完全一致，status 为 `field_operator_confirmation_material_ready_not_delivery_proof`，且不回显 operator id/material id。
- 新增 hostile fixture 覆盖 task mismatch、`safe_to_control=true`、`raw_body`、绝对路径和 token 文本：section-local `blocked_not_proven`，只输出 blocked reasons、危险字段名和 unsafe 计数，不回显 raw/body/path/token 原文。

## 剩余风险和下一步建议

- 当前仍是 `software_proof_field_operator_confirmation_material_only`，不证明真实 delivery success、真实 HIL、真实 production cloud 或真实 live Nav2 route execution。
- 下一步应由 O6/O7 owner 接入 archive/readback/UI consumer，并继续保持只读展示和 fixed false safety flags。

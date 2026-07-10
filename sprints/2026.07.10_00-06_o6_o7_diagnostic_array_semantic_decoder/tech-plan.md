# O6/O7 DiagnosticArray Semantic Decoder Tech Plan

## OKR 最低优先级核对

`OKR.md` 4.1 当前 active Objective 完成度最低的是：

- O6：约 76%。
- O7：约 76%。

本 sprint 直接针对最低 Objective。选择 DiagnosticArray 的原因是上一轮 final/report 明确指出 full semantic decode matrix 仍有 unsupported topic type，且 `diagnostic_msgs/msg/DiagnosticArray` 与路线诊断、运行健康和后续现场复盘直接相关。本轮不消费硬件 blocker，也不把 local/mock wrapper 当成进展。

## 技术方案

1. Algorithm 在 `onboard/scripts/field_route_evidence_manifest.py` 中增加 `diagnostic_msgs/msg/DiagnosticArray` 安全 decoder。
   - 只输出诊断 status 数量、最高 level、level 分布、status name/hardware_id 短样本、key/value pair 计数。
   - 不输出 raw values、message 原文、payload、路径、URL、token 或控制 topic。
2. Algorithm 更新 route bag semantic replay 聚合与 full semantic decode matrix decoder map。
3. O6 更新 field evidence archive/readback fixture，证明 DiagnosticArray decoded matrix item 可通过 detail/include 安全保留。
4. O7 更新 consumer fixture、shared contract 或 UI 测试，证明 DiagnosticArray decoded coverage 可见且仍 fail-closed。
5. 更新相关 docs 和 sprint `tech-done.md`。

## 文件范围

Algorithm owner 可改：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/algorithm_worker_report.md`

O6 owner 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/o6_worker_report.md`

O7 owner 可改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/artifacts/o7_worker_report.md`

主节点仅更新本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`、`side2side_check.md`、`final.md` 和必要汇总记忆。

## 验收命令

Algorithm：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

O6：

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

O7：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

收口：

```bash
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/navigation/field_route_evidence_manifest.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder
```

## 风险边界

- DiagnosticArray decoder 只能作为安全摘要，不可输出完整 diagnostic message 或敏感文本。
- 如果真实 DB3 中没有 DiagnosticArray，本轮用 fixture/mock DB3 证明软件链路；这不等于现场 route bag 已包含诊断证据。
- O6/O7 ready 语义仍只能是 `ready_not_route_execution_proof`，不能外推为路线执行成功或 delivery success。

# O6/O7 Route Execution Credit Material Tech Done

## sprint_type

epic

## 实际改动

本轮在上一轮 `same_task_route_execution_material_packet` 基础上补齐可计分材料字段，而不是新增独立 wrapper。三条 owner 线均已落地并同步文档。

Algorithm 改动：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/artifacts/algorithm_worker_report.md`

Algorithm 新增 `live_or_field_command_evidence_present`、`delivery_or_operator_material_consumed`、`route_execution_credit_candidate`、`credit_support_only_reason`、`credit_required_evidence`。`route_execution_credit_candidate=true` 只在同一 `task_id` 同时具备 route execution material、live/field command evidence 和 delivery/operator material 时成立；固定 false 的 delivery/control/safety flags 不变。

O6 改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/artifacts/o6_worker_report.md`

O6 archive/readback 对同一 packet 保留 credit-aware 字段，并对缺字段、字段类型错误、credit candidate 与来源布尔不一致、unsafe text/path/token/raw/base64/dangerous true 做 section-local fail-closed。即使 credit candidate 成立，也不放开 `delivery_success`、`safe_to_control`、`primary_actions_enabled` 或 `robot_control_executed`。

O7 改动：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/artifacts/o7_worker_report.md`

O7 consumer/UI 消费并展示 credit-aware 字段，明确 support-only/blocked 语义。主节点验收发现 O7 初版与 O6 合同存在两个问题：第一，`route_execution_credit_candidate=true` 时 O6 合法输出空 `credit_support_only_reason`，O7 初版会误判缺字段；第二，缺字段 fail-closed 路径需要保留 selected task id。O7 已返工，补齐 candidate-true 空 reason 兼容和 task id preservation 回归。

Sprint/OKR 留档改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/tech-done.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/side2side_check.md`
- `sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/final.md`

## 验证结果

Algorithm worker 验证：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
# exit 0

python3 -m unittest onboard.tests.test_field_route_evidence_manifest
# Ran 67 tests in 0.499s
# OK

git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
# exit 0
```

O6 worker 验证：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# exit 0

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
# Ran 171 tests in 68.289s
# OK

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
# exit 0
```

O7 worker 验证：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
# Tests 486 passed (486)
# vite build passed with existing chunk-size warning
# eslint . passed

git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material
# exit 0
```

主节点验收：

```bash
rg -n "route_execution_credit_candidate|credit_support_only_reason|live_or_field_command_evidence_present|delivery_or_operator_material_consumed|credit_required_evidence|o6_o7_route_execution_credit_material" onboard pc-tools docs sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material OKR.md
# 关键字段已贯通 Algorithm、O6、O7、文档和 sprint 留档

git diff --check
# exit 0
```

## 偏差与修复

- Role-specific subagent 启动失败于运行时模型解析，已按 AGENTS.md fallback 规则改用 `worker` 并在 prompt 中明确角色与文件范围。
- O7 初版把 candidate-true 的空 `credit_support_only_reason` 误判为缺字段；返工后改为 candidate true 可为空、candidate false 必须非空。
- O7 缺字段 fail-closed 路径补充 selected task id 保留断言，避免错误 reason 被当成 task id。

## 剩余风险

- 本轮是 `software_proof_o6_o7_route_execution_credit_material_only`，不证明真实 production cloud、production DB/queue、OSS/CDN、4G/TLS、真实 live Nav2、真实机器人运动、真实 delivery record、真实 operator confirmation、真实 delivery success 或 hardware safety/HIL。
- `route_execution_credit_candidate=true` 只表示同一 `task_id` 的材料形态具备 OKR credit candidate，不等于 delivery success，也不允许解锁控制。
- O5 仍缺真实生产云/DB/queue/live endpoint 证据；O1 仍缺真实 WAVE ROVER nonzero L/R、轮向、operator report 与 HIL acceptance。

# O6/O7 Field Operator Confirmation Material Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 O5，约 `85%`；次低是 O1，约 `86%`；O6/O7 约 `90%`。
2. 本 sprint 不直接针对最低 O5，也不直接针对次低 O1。
3. 理由：O5 当前缺真实 production cloud、production DB-queue、4G、TLS、live endpoint、OSS/CDN 或真实手机/browser 材料；recent gate 已禁止 local/mock probe、readback-only、checklist-only 或 support-only surface 继续计 O5 主进度。O1 上一轮刚完成 `wave_rover_nonzero_feedback_hil_gate`，下一步必须是真实同 run `feedback_T1001.log`、motion command、operator report 和 HIL acceptance，不能再消费同一软件 gate。为避免重复 blocker，本轮转向 O6/O7，消费新的准现场 `field_operator_confirmation_material`。

## 接口设计

- Algorithm schema：`trashbot.field_operator_confirmation_material.v1`。
- O6 schema：`trashbot.o6.field_operator_confirmation_material.v1`。
- O7 schema：`trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1`。
- Proof boundary：`software_proof_field_operator_confirmation_material_only`。

建议字段：

- `task_id`
- `source_schema`
- `proof_boundary`
- `status`
- `operator_report_id`
- `operator_report_present`
- `operator_confirmation_present`
- `operator_confirmation_status`
- `operator_confirmed_at`
- `confirmation_source`
- `same_task_id_consumed`
- `linked_route_material_present`
- `linked_delivery_material_present`
- `operator_notes_summary`
- `blocked_reasons`
- `next_required_evidence`
- `support_only_reason`
- fixed false fields: `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`

## 安全和 Fail-closed 要求

- 只保留安全摘要，不回显 raw report、base64、绝对路径、URL、token、credential、response body、traceback 或完整人工备注。
- `task_id` mismatch、proof boundary mismatch、dangerous true、缺少 operator material identity、缺少 confirmation source、unsafe text、字段类型错误时，section-local 降级为 `blocked_not_proven`。
- O7 只读展示，不新增按钮，不开启控制，不把 operator material ready 渲染成 delivery success。

## 文件范围

Algorithm owner `robot-algorithm-engineer` 可改：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/algorithm_worker_report.md`

Robot Software/O6 owner `robot-software-engineer` 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/o6_worker_report.md`

Full-stack/O7 owner `full-stack-software-engineer` 可改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/artifacts/o7_worker_report.md`

Product closeout 后续可改：

- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/tech-done.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/side2side_check.md`
- `sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

本轮计划阶段禁止改动上述 Product closeout 文件，也禁止改动代码、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## Worker 分工和验收命令

### Algorithm owner：`robot-algorithm-engineer`

目标：新增 `trashbot.field_operator_confirmation_material.v1` 生产入口，并在 manifest 顶层及适当的 field/material packet 下输出安全摘要。建议文件：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
```

### Robot Software/O6 owner：`robot-software-engineer`

目标：新增 O6 archive/readback/include `trashbot.o6.field_operator_confirmation_material.v1`，覆盖 field evidence、artifact bundle、archive detail、consumer detail 与 `include=field_operator_confirmation_material`。建议文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
```

### Full-stack/O7 owner：`full-stack-software-engineer`

目标：新增 O7 consumer/default include/UI summary `trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1`，让 workstation 只读展示 operator material summary。建议文件：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
```

## 集成验收

后续实现阶段完成后，主节点只做验收、留档和必要返工派单。集成验收至少检查：

```bash
rg -n "field_operator_confirmation_material|software_proof_field_operator_confirmation_material_only|trashbot.field_operator_confirmation_material.v1|trashbot.o6.field_operator_confirmation_material.v1|trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1" onboard docs pc-tools sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
git diff --check
```

计划阶段验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|field_operator_confirmation_material|software_proof_field_operator_confirmation_material_only|robot-algorithm-engineer|robot-software-engineer|full-stack-software-engineer" sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
git diff --check -- sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material
```

## 证据边界

本轮 proof boundary 是 `software_proof_field_operator_confirmation_material_only`。它只证明 operator report / operator confirmation material 可以被安全摘要化、归档、回读和展示；不证明 production cloud、live Nav2 execution、robot motion、delivery success 或 HIL pass。


# O5/O6/O7 Same Task Mission Gate Tech Done

## Sprint 类型

sprint_type: epic

收口时间：2026-07-10 03:37 CST。

## 实际改动

Algorithm 新增 `trashbot.same_task_mission_evidence_gate.v1`，在 manifest 顶层和 `field_motion_evidence_packet.same_task_mission_evidence_gate` 写入同一 `task_id` mission gate。Gate 只读消费已有 additive summary，要求 O5 `trashbot.cloud_command_terminal_result.v1` source、Nav2 goal evidence、route execution readiness、route delivery closure packet 和 pose progress replay 同 task 后才输出 `same_task_mission_gate_ready_not_success_proof`。

O6 新增 `trashbot.o6.same_task_mission_evidence_gate.v1` archive/readback/include 支持，覆盖 field evidence、artifact bundle、field motion packet、archive detail、consumer detail 与 `include=same_task_mission_evidence_gate`。缺失、schema mismatch、proof scope mismatch、task mismatch、unsafe text/raw/base64/绝对路径/credential URL/token、dangerous true 均 fail closed。

O7 workstation 新增 `same_task_mission_evidence_gate` consumer/display 支持，默认请求该 include，并展示 O5 terminal/cloud source、source schema、terminal result status、route execution material status、linked flags、blocked reasons 和 next required evidence。UI 文案保持 ready-not-success-proof，不把 gate ready 当作真实送达成功。

Product/OKR closeout 更新 `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md`、`side2side_check.md`、`final.md` 和 `artifacts/product_worker_report.md`。

## 实际改动文件

- Algorithm：`onboard/scripts/field_route_evidence_manifest.py`
- Algorithm：`onboard/tests/test_field_route_evidence_manifest.py`
- Algorithm：`docs/navigation/field_route_evidence_manifest.md`
- O6：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- O6：`onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- O6：`docs/interfaces/o6_cloud_archive_api.md`
- O7：`pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- O7：`pc-tools/workstation/src/shared/contracts.ts`
- O7：`pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- O7：`pc-tools/workstation/test/catalog.test.ts`
- O7：`pc-tools/workstation/test/App.test.ts`
- O7：`docs/interfaces/o7_realtime_operator_console.md`
- O7：`docs/product/pc_tools_workstation.md`
- O7：`pc-tools/README.md`
- Sprint artifacts：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/algorithm_worker_report.md`
- Sprint artifacts：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/o6_worker_report.md`
- Sprint artifacts：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/o7_worker_report.md`
- Product closeout：`OKR.md`
- Product closeout：`docs/process/okr_progress_log.md`
- Product closeout：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/tech-done.md`
- Product closeout：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/side2side_check.md`
- Product closeout：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/final.md`
- Product closeout：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/product_worker_report.md`

## 验证结果

Algorithm：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
# passed, no output

python3 -m unittest onboard.tests.test_field_route_evidence_manifest
Ran 55 tests in 0.291s
OK
```

O6：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# passed, no output

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 166 tests in 63.477s
OK
```

O7：

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint
Test Files  3 passed (3)
Tests  484 passed (484)
build passed
lint passed
```

Product closeout 验收命令已执行并记录在 `artifacts/product_worker_report.md`。

## 失败定位

- Algorithm：无验证失败。
- O6：首轮完整 unittest 暴露 `NameError: name 'task_origin' is not defined`，原因是 artifact bundle alias helper 中误用了不存在的局部变量；已修复为固定 `task_origin="artifact_bundle"` 并复验通过。
- O7：首次 `npm run test` 因 App/catalog gate fixture 缺少 `proof_boundary` 导致 render `TypeError`；已补齐 fixture 并复验通过。
- Product closeout：无已知失败，最终验收以 `artifacts/product_worker_report.md` 为准。

## 剩余风险

证据边界为 `software_proof_same_task_mission_evidence_gate_only`。本轮 not production cloud，not delivery success；不证明真实 4G/TLS、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 annotation API/export、真实 dataset export、真实手机/browser 验收或完整路线长期验收。

下一轮必须消费真实或准现场同一 `task_id` mission materials，优先 production cloud、live route execution、delivery record/operator confirmation，而不是继续 wrapper、decoder、handoff 或 review surface。

# O5/O6/O7 Same Task Mission Gate Tech Plan

## 范围

新增 additive evidence schema：`trashbot.same_task_mission_evidence_gate.v1`，O6 规范化为 `trashbot.o6.same_task_mission_evidence_gate.v1`。proof scope 固定为 `software_proof_same_task_mission_evidence_gate_only`。

ready 状态建议：`same_task_mission_gate_ready_not_success_proof`。blocked 状态：`blocked_not_proven`。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O5 约 81%，O7 约 81%。
- 本 sprint 是否针对该最低 Objective：是，同时覆盖 O6 约 82%。
- 理由：上一轮 O5 terminal result bridge 已完成，但 final 要求下一轮消费真实或准现场 same-task terminal result + live route execution / production cloud evidence。本轮实现同 task gate，为真实材料到位后的验收建立软件可验证入口，避免继续 wrapper/decoder lane。
- final.md 收口需复核：本轮是否真的把 O5 terminal source 与 route execution materials 做同 task gate，而不是只新增展示包装。

## Task A：Algorithm Gate

Owner：`robot-algorithm-engineer`

允许改动：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/algorithm_worker_report.md`

实现要求：

- 在 manifest 顶层和 `field_motion_evidence_packet.same_task_mission_evidence_gate` 写入新 gate。
- Gate 只消费当前 manifest 已生成的 linked additive，不读取 raw cloud/route payload。
- Ready 条件至少包括：
  - `delivery_result_evidence.status=ready_not_delivery_proof`
  - `delivery_result_evidence.source_schema=trashbot.cloud_command_terminal_result.v1`
  - `route_execution_result_delivery_readiness.status=route_execution_result_delivery_readiness_ready_not_delivery_proof`
  - `route_delivery_closure_packet.status=route_delivery_closure_ready_not_success_proof`
  - `route_bag_pose_progress_replay.nonzero_pose_progress_observed=true`
  - 所有 linked `task_id` 与 packet `task_id` 一致
  - 无 dangerous true、unsafe 文本、unsafe 计数、schema mismatch
- 输出必须包含 blocked reasons、next required evidence、terminal refs、linked readiness flags、`mission_artifact_delta`，并固定所有安全控制字段为 false。

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

## Task B：O6 Archive/Readback

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/o6_worker_report.md`

实现要求：

- 支持 artifact bundle、field evidence、archive detail、consumer detail 与 `include=same_task_mission_evidence_gate`。
- O6 summary schema 使用 `trashbot.o6.same_task_mission_evidence_gate.v1`，proof scope 不变。
- 缺失、schema mismatch、proof scope mismatch、task mismatch、unsafe text、dangerous true 都必须 blocked。
- 不回显 raw/base64、绝对路径、credential URL、token。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

## Task C：O7 Consumer/Workstation

Owner：`full-stack-software-engineer`

允许改动：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/o7_worker_report.md`

实现要求：

- Consumer detail 暴露 `same_task_mission_evidence_gate`。
- Artifact bundle readiness 汇总该 gate 的 status、linked flags、blocked reasons、next required evidence。
- UI/fixture preview 展示 gate 状态和 terminal/cloud source，不把 ready 显示为真实送达成功。
- API 请求 include 列表增加 `same_task_mission_evidence_gate`。

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

## Task D：Product Closeout

Owner：`product-okr-owner`

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/tech-done.md`
- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/side2side_check.md`
- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/final.md`
- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/artifacts/product_worker_report.md`

验收命令：

```bash
test -f sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/pre_start.md
test -f sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/prd.md
test -f sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/tech-plan.md
test -f sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/tech-done.md
test -f sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/side2side_check.md
test -f sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/final.md
rg -n "same_task_mission_evidence_gate|software_proof_same_task_mission_evidence_gate_only|O5|O6|O7|not.*production cloud|not.*delivery success" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate
```

## 风险

- 本轮仍是 local/mock software proof，不是 production cloud 或真实 route execution。
- 现有工作树已有多轮未提交改动；各 owner 不得回滚或覆盖非本任务文件。
- O6/O7 合同文件较大，新增字段必须尽量沿用现有 pattern，避免重构。

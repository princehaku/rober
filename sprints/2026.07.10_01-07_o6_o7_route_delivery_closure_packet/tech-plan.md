# O6/O7 Route Delivery Closure Packet Tech Plan

## OKR 最低优先级核对

`OKR.md` 4.1 当前 active Objective 完成度最低的是：

- O6：约 78%。
- O7：约 78%。

本 sprint 直接针对最低 Objective。选择 `route_delivery_closure_packet` 的原因是最近两轮已连续推进 decoder，最新 `final.md` 与 `OKR.md` 均建议转向真实/准现场 live Nav2 result、delivery record/operator confirmation 或 production cloud。本轮用本地/准现场 fixture 把这些结果链收束成软件可验证闭合包，避免继续消费 decoder blocker。

## 技术方案

1. Algorithm 新增 `trashbot.route_delivery_closure_packet.v1`。
   - 从 `nav2_goal_execution_evidence`、`delivery_result_evidence`、`route_execution_result_delivery_readiness`、`route_bag_pose_progress_replay` 派生。
   - ready 仅表示同一 `task_id` 的软件证据闭合，状态建议为 `route_delivery_closure_ready_not_success_proof`。
   - 固定输出 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`。
2. O6 新增 `trashbot.o6.route_delivery_closure_packet.v1` 安全摘要。
   - 支持 field evidence manifest、artifact bundle、archive detail、consumer detail 和 `include=route_delivery_closure_packet`。
   - 坏 schema、危险 true、unsafe 文本、缺关键字段均降级为 `blocked_not_proven`。
3. O7 新增 consumer summary 与 UI preview。
   - 复用 O6 summary，只展示 closure status、linked evidence flags、blocked reasons、next required evidence 和 false safety flags。
   - 加入 default include，fixture 和 blocked/fail-closed 测试覆盖。
4. 文档同步更新。

## 文件范围

Algorithm owner 可改：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/artifacts/algorithm_worker_report.md`

O6 owner 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/artifacts/o6_worker_report.md`

O7 owner 可改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/artifacts/o7_worker_report.md`

Product closeout 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/tech-done.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/side2side_check.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/final.md`
- `sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/artifacts/product_worker_report.md`

## 接口影响

- 新增 additive 字段：`route_delivery_closure_packet`。
- 不删除、不改名现有 `route_execution_result_delivery_readiness`、`delivery_result_evidence` 或 `nav2_goal_execution_evidence` 字段。
- 所有新增字段必须保持 summary-only；不得输出绝对路径、raw payload、base64、token、credential-bearing URL 或控制动作。

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
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/navigation/field_route_evidence_manifest.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md pc-tools/README.md OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet
```

## 风险边界

- 本轮仍是 local/offline software proof，不证明真实 production cloud 或真实 delivery success。
- 若上游 fixture 只有 ready_not_delivery_proof，本轮 closure ready 也只能是 `ready_not_success_proof`。
- 如果 worker 发现当前工作树已有同名字段或冲突，必须保留他人改动并收窄实现，不得回滚。

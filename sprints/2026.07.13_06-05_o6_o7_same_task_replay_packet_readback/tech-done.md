# Tech Done - O6/O7 Same-task Replay Packet Readback

## Sprint 类型

- sprint_type: epic
- 完成时间：2026-07-13 06:53:48 CST
- owner: full-stack-software-engineer

## 实际改动

本轮把 05:02 accepted 的 O3/O1 same-task replay packet 作为只读材料安全消费到 O6 local/mock archive/readback 与 O7 PC consumer detail，新增独立 section `same_task_replay_packet_readback`，避免与 `same_task_route_execution_material_packet` 混淆。

改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/tech-done.md`

## 用户旅程变化和触点收益

- O6 archive / consumer read 现在可以在同一 `task_id` 下接收并回读 05:02 O3 replay packet 的 exact identity、三类 28 count、basename refs、hash prefix 与 fail-closed blocked reasons。
- O7 PC consumer detail 默认 include 新增 `same_task_replay_packet_readback`，operator 在 O7 Previews 的 consumer primary path 里能直接看到 packet identity/readback 是否 ready，以及为什么仍不是路线执行、送达、HIL 或控制证据。
- UI 新增 “Same task replay packet readback” 只读块，明确展示 fixed false fields，避免把 replay packet readback 误读成可执行路线或可控制状态。

## O6/O7 接口影响

- O6 新增回读 schema：`trashbot.o6.same_task_replay_packet_readback.v1`。
- O7 新增 summary schema：`trashbot.pc_tools_workstation.o7_same_task_replay_packet_readback.v1`。
- `GET /api/o6/consumer/tasks/<task_id>?include=same_task_replay_packet_readback` 可单独读取该 section。
- O7 `GET /api/o7/consumer-read/tasks/<task_id>` 默认把该 section 纳入 detail include，并在 `artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness` 和 detail 顶层保持同一摘要。
- 保持 source identity 精确不变：
  - `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
  - `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
  - `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
  - `route_csv_row_count=28`
  - `replay_jsonl_event_count=28`
  - `path_structured_pose_count=28`
  - `same_task_replay_packet_ready=true`

## 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

结果：

```text
Ran 185 tests in 81.295s
OK
```

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

结果：

```text
Test Files  3 passed (3)
Tests  491 passed (491)

vite v7.3.3 building client environment for production...
✓ 34 modules transformed.
✓ built in 1.92s

eslint .
```

说明：Vite 继续输出既有 chunk size warning，但 build exit code 为 0，lint exit code 为 0。

```bash
git diff --check -- \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/interfaces/o6_cloud_archive_api.md \
  pc-tools/workstation \
  docs/product/pc_tools_workstation.md \
  sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback
```

结果：无输出，exit code 0。

## 失败定位和修复记录

- 实现中先遇到 O6 全局 unsafe gate 把 `same_task_replay_packet_readback.publishes_cmd_vel=false` 这类安全 false 字段误判为危险字段。修复方式：在全局 gate 前移除该 readback 原始 section，只对该 section 使用专门白名单摘要，并把 `publishes_cmd_vel` 纳入 false-only 保留字段。
- O7 fixture 侧先出现 task id/source schema 不一致导致的 fail-closed 预期偏差。修复方式：让 catalog fixture 的 `same_task_replay_packet_readback` 与当前测试 task id 对齐，并用专门断言覆盖 exact identity、28/28/28 counts、basename refs、sha256 prefix 和 fixed false fields。

## 剩余风险和边界

- 当前证明边界固定为 `software_proof_o6_o7_same_task_replay_packet_readback_only`。
- 这不是 route execution、delivery、HIL、safe-to-control、NavigateToPose/controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或 O5 production/external evidence。
- 固定 false 字段保持为 false：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`primary_actions_enabled=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`connects_cloud_production=false`。
- 后续若要提升 OKR credit，需要机器人侧或云侧提供新的 same-task route execution / delivery / HIL / production evidence；本轮只完成 O6/O7 安全读回和 PC 展示。

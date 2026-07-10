# O6/O7 Same-Task Field Material Packet Tech Plan

## 目标

将已有准现场 route materials 接入同一 `task_id` 的 Algorithm -> O6 -> O7 证据链，形成 `same_task_field_material_packet`。该 packet 是 mission artifact delta 的可消费材料包，不是 delivery success proof。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective：O1、O5、O6、O7 均约 `85%`，并列最低。
2. 本 sprint 针对并列最低中的 O6/O7，同时支撑 O5/O6/O7 后续 same-task mission evidence gate。
3. 不选择 O1 的原因：本轮没有真实 WAVE ROVER 非零 L/R raw feedback、轮速方向或 HIL 材料，继续模拟底盘只会重复消费硬件 blocker。
4. 不选择 O5 production cloud 的原因：当前没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic 或凭证；继续 local probe/readback 会重复消费上轮 hard gate 已禁止的 support-only blocker。
5. 选择 O6/O7 的原因：仓库内已有准现场 `route.csv`、keyframes、route bag / rosbag、replay JSONL，可在当前环境下消费为 same-task mission materials，并避免继续做 wrapper-only 进展。

## 技术方案

### Robot Algorithm Engineer

- 在 `onboard/scripts/field_route_evidence_manifest.py` 新增 `trashbot.same_task_field_material_packet.v1`。
- Packet 字段建议包含：
  - `task_id`、`task_id_source`
  - `status`: `ready_not_delivery_proof` 或 `blocked_not_proven`
  - `present_materials` / `missing_materials`
  - `route_csv_present`、`keyframes_present`、`route_bag_or_rosbag_present`、`replay_jsonl_present`
  - safe counts、basename、size、sha256 prefix、sample refs
  - `same_task_id_consumed=true` 当 task_id 有效且材料来自同一 manifest root
  - `live_or_field_material_consumed=true` 当至少两类准现场材料存在且安全通过
  - false safety fields: `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`
- 将 packet 挂到 manifest 顶层和 `field_motion_evidence_packet.same_task_field_material_packet`。
- 更新 `same_task_mission_gate_artifact_delta`：当 gate ready 且 packet ready 时，允许 `mission_artifact_delta` 记录 `same_task_field_material_consumed=true`；如没有 live command 仍不得宣称 delivery success。
- 单测覆盖 ready、缺 map 但消费 route/keyframe/replay/rosbag、unsafe path/token/raw fail-closed。

### Robot Software Engineer / O6

- 在 `remote_cloud_relay.py` 新增 `trashbot.o6.same_task_field_material_packet.v1` summarizer。
- 支持 field evidence ingest、artifact bundle、archive detail、consumer detail 和 `include=same_task_field_material_packet` 回读。
- 只保留安全摘要字段；unsafe text、absolute path、credential URL、raw/base64、dangerous true 均降级当前 section。
- 更新 O6 docs。

### Full-Stack / O7

- 在 workstation contracts 与 consumer adapter 中新增 `same_task_field_material_packet` summary。
- 将 `DEFAULT_DETAIL_INCLUDE` 增加该 section。
- UI 邻近 `same_task_mission_evidence_gate` / material checklist 展示 packet status、present materials、sample refs、blocked reasons 和 next evidence。
- Checklist 增加或复用 material item，使 operator 能看到 route material packet 是否已消费。
- 更新 O7 docs。

## 文件范围

### Algorithm

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/artifacts/algorithm_worker_report.md`

### O6

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/artifacts/o6_worker_report.md`

### O7

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/artifacts/o7_worker_report.md`

### Product / Main 汇总

- `sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/tech-done.md`
- `sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/side2side_check.md`
- `sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验收命令

Algorithm worker:

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet
```

O6 worker:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet
```

O7 worker:

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet
```

Product / main acceptance:

```bash
rg -n "same_task_field_material_packet|field_material|okr_credit_allowed|same_task_field_material_consumed" OKR.md docs/process/okr_progress_log.md docs/interfaces docs/navigation docs/product pc-tools/workstation onboard sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet
git diff --check
```

## 风险边界

- 本轮证明准现场材料已进入 same-task readback/consumer 主路径；不证明真实 production cloud、真实 live Nav2 execution、真实机器人运动、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 如果 worker 无法在 O6/O7 完成全链路接入，必须至少保留 Algorithm packet 与阻塞原因，不得把不完整链路记为 OKR 百分比提升。

# O6/O7 Same-Task Field Material Packet Tech Done

## Sprint Type

sprint_type: epic

## 实际改动

### Robot Algorithm Engineer

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `trashbot.same_task_field_material_packet.v1`，同时写入 manifest 顶层与 `field_motion_evidence_packet.same_task_field_material_packet`。
  - Packet 只读消费同一 `artifact_root` 的 `map.yaml`、`route.csv`、keyframes、route bag / rosbag、replay JSONL。
  - 输出 `present_materials`、`missing_materials`、`material_summaries`、top-level `sample_refs`、blocked/next evidence 和固定 false safety fields。
  - `map.yaml` 缺失只记录 `same_task_field_material_map_yaml_missing_optional`，不阻止 route/keyframe/route bag/replay 材料消费。
  - `same_task_mission_gate_artifact_delta` 新增 `same_task_field_material_consumed`，但仍不放开 `okr_credit_allowed` 或 delivery success。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 覆盖缺 `map.yaml` 仍 ready、hostile source manifest fail-closed、mission artifact delta 消费字段。
- `docs/navigation/field_route_evidence_manifest.md`
  - 记录新 packet 的 schema、proof scope、字段和证据边界。

### Robot Software Engineer / O6

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `trashbot.o6.same_task_field_material_packet.v1` summarizer、placeholder、request 提取、pre-scan 剥离和 consumer readback。
  - 支持 field evidence、artifact bundle、archive detail、consumer detail 顶层 alias 与 `include=same_task_field_material_packet`。
  - 返工对齐 Algorithm 实际 shape：读取 `material_summaries`，接受 `map_yaml` optional material，输出 list-shaped top-level `sample_refs` 和 per-material `material_sample_refs`。
  - unsafe text、绝对路径、credential URL、token、raw/base64、dangerous true 只降级当前 section。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖 O6 readback、explicit include、unsafe section 降级、Algorithm actual shape。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 记录 O6 packet readback contract 和 shape compatibility。

### Full-Stack / O7

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `O7ConsumerSameTaskFieldMaterialPacketSummary`，接入 consumer detail / artifact bundle readiness contract。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - `DEFAULT_DETAIL_INCLUDE` 增加 `same_task_field_material_packet`。
  - 从 O6 top-level、field evidence、field motion、artifact bundle / ingest / readiness 白名单路径读取 packet。
  - 返工兼容 Algorithm/O6 shape：top-level `sample_refs` list、`material_summaries`、`material_sample_refs`、`sample_ref_summaries` 和旧 dict-shaped `sample_refs`。
  - `map_yaml` 缺失只展示 optional gap，不阻断 route/keyframe/route bag/replay 消费展示。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 邻近 same-task gate / checklist 增加 `same_task_field_material_packet` 展示区。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 packet include、UI 文本、O6 actual readback shape、checklist 第 9 项。
- `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`
  - 更新 O7 consumer include、packet 展示规则、shape compatibility 和 proof boundary。

## 验证结果

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py` 通过；`python3 -m unittest onboard.tests.test_field_route_evidence_manifest` 输出 `Ran 62 tests in 0.347s OK`；scoped `git diff --check` 通过。
- O6 初轮：`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 169 tests in 66.620s OK`。
- O6 返工后：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 通过；`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 170 tests in 67.261s OK`；scoped `git diff --check` 通过。
- O7 初轮：`cd pc-tools/workstation && npm run test` 输出 `Tests 484 passed (484)`；`npm run build`、`npm run lint` 通过。
- O7 返工后：`cd pc-tools/workstation && npm run test` 输出 `Tests 485 passed (485)`；`npm run build` 通过但保留既有 Vite chunk-size warning；`npm run lint` 通过；scoped `git diff --check` 通过。
- 主会话验收：核对 O6 已读取 `material_summaries` 并输出 list-shaped `sample_refs`；核对 O7 已兼容 `material_summaries` / `material_sample_refs` / `sample_ref_summaries` / legacy dict sample refs；`git diff --check` 通过。

## 返工与定位

- 主会话验收发现 O6 初版只读取 dict-shaped `sample_refs`，与 Algorithm 实际 `material_summaries` + list-shaped `sample_refs` 不一致，会导致真实 packet 被降级。已派回 O6 修复并复验到 `170 tests OK`。
- 主会话验收发现 O7 初版要求 `sample_refs` 必须是 list 且未展示 per-material summary；返工后兼容新旧 shape，并修复一次 TypeScript `null` vs `undefined` 类型错误和一处误把 optional map gap 当 hard fail 的断言。

## 证据边界

本轮 proof boundary 为 `software_proof_same_task_field_material_packet_only`。

本轮证明：同一 `task_id` 的准现场 route materials 可以从 Algorithm manifest 进入 O6 archive/readback，再被 O7 workstation 安全展示和纳入 operator checklist。

本轮不证明：真实 production cloud、production DB/queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 live Nav2 route execution、真实机器人运动、真实 delivery record、真实 operator confirmation、真实 delivery success 或 hardware safety。

## 剩余风险

- `map_yaml` 当前按 optional gap 处理；后续真实路线验收仍需要补齐地图上下文。
- `same_task_field_material_consumed=true` 只表示材料消费，不等于 `okr_credit_allowed=true`；credit gate 仍要求 live/field command execution 或更强真实任务材料。
- O7 build 仍有既有 Vite chunk-size warning，本轮未处理拆包。

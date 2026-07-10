# O7 Worker Report

## 实际改动文件

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/artifacts/o7_worker_report.md`

## 实现摘要

- 新增 O7 `same_task_field_material_packet` shared contract，并把该 section 接入 consumer detail、artifact bundle readiness 和 operator checklist。
- `DEFAULT_DETAIL_INCLUDE` 增加 `same_task_field_material_packet`，adapter 现在会从 O6 top-level、field evidence、field motion、artifact bundle / ingest / readiness 白名单路径读取 packet。
- 对 schema mismatch、task mismatch、dangerous true、unsafe text/list、proof scope mismatch 做 fail-closed；只保留材料布尔位、present/missing materials、top-level sample refs、per-material basename/size/hash/count/sample refs、blocked reasons 和 next required evidence。
- O7 adapter 兼容三类上游 shape：Algorithm 实际 `material_summaries`、O6 修正后的 `material_summaries` / `material_sample_refs` / `sample_ref_summaries`，以及旧 O6 dict-shaped `sample_refs`。旧 shape 会降级为 per-material summary，不再把整个 detail fail-closed。
- `map_yaml` 现在作为可展示材料保留在 packet 中；缺失时只显示 optional gap，不阻断 route CSV、keyframes、route bag / rosbag、replay JSONL 的消费展示。
- UI 在 `same_task_mission_evidence_gate` / checklist 邻近新增 `Same task field material packet` 展示区，并显式展示 per-material summary 行和 `optional_map_gap`；checklist 维持 9 项，显式显示 `same_task_field_material_packet` 的 ready/blocked 状态。
- 文档同步更新 include 列表、consumer detail 来源路径、packet shape 兼容规则和 checklist 项定义。

## 验证结果

### 1. 测试

```bash
cd pc-tools/workstation && npm run test
```

结果：`Test Files 3 passed (3)`，`Tests 485 passed (485)`。

### 2. 构建

```bash
cd pc-tools/workstation && npm run build
```

结果：通过。Vite 仍有既有 `chunk size` warning（`dist/assets/index-BBs43sg6.js` 约 1.50 MB），但不阻塞本轮验收。

### 3. 静态检查

```bash
cd pc-tools/workstation && npm run lint
```

结果：通过。

### 4. diff 检查

```bash
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet
```

结果：通过。

## Proof Boundary

- 本轮证据边界是 `software_proof_same_task_field_material_packet_only` 与其 O7 consumer/UI 消费链。
- 证明内容仅限：同一 `task_id` 的准现场 route material packet 可以被 O7 按真实/旧版 O6 shape 安全读取、fail-closed 展示，并进入 operator checklist。
- **不证明**：真实 production cloud、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实机器人运动、真实硬件安全、真实 delivery success。

## 剩余风险

- 当前 O7 对 packet 的 ready 仍然是 software proof only；上游若继续新增未兼容的 summary alias、material key 或 proof scope，会直接 fail-closed。
- checklist 已显式展示 `same_task_field_material_packet`，但是否可计 O5/O6/O7 主进度，仍受 O6 gate 的 `okr_credit_allowed` 约束。
- build 继续有前端 bundle size warning，本轮未处理代码拆包。

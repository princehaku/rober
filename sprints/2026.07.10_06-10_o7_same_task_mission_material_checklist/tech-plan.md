# O7 Same-Task Mission Material Checklist Tech Plan

## Sprint 类型

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节 active Objective 进度：O7 约 83%，O5 约 84%，O6 约 84%，O1 约 85%。
2. 当前最低可推进 Objective：O7。O5 虽在最高优先级列表中靠前，但最近 `2026.07.10_05-10_o5_sqlite_shadow_same_task_gate` 已明确不能再用 local shadow/smoke 提升；O6 也不应继续 wrapper/decoder。
3. 本 sprint 是否针对最低 Objective：是，直接针对 O7 的 consumer detail 主路径和 operator checklist。
4. 如不继续 O5/O6 的具体理由：O5 需要真实 production cloud、production DB/queue external probe 或 live endpoint evidence；O6 需要真实隧道、生产 DB/queue、OSS、真实机器人数据或现场长期数据回灌。当前可在本地推进的最高价值工作，是让 O7 消费 O6 `same_task_mission_evidence_gate` 并输出 operator 可执行 material checklist。
5. final.md 收口时必须复核：本轮是否真的形成 `same_task_mission_material_checklist`，且 UI 能指导 operator 补 mission material，而不是只新增 summary wrapper。

## 最近两轮 final 核对

- `sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/final.md`：本地 relay reconciliation material 进入 same-task gate 和 O6 archive/readback，但不证明 production cloud、live Nav2、delivery record、operator confirmation 或 delivery success。
- `sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/final.md`：SQLite shadow restart/readback 已完成；下一轮若没有真实外部材料，应转向 O7 same-task mission material checklist。

结论：本轮不重复消费 local smoke blocker，不继续 wrapper/decoder lane。

## 技术方案

### Task A - O7 Consumer Detail Checklist

Owner：`full-stack-software-engineer`

目标：在 `pc-tools/workstation` O7 consumer detail 主路径中派生 `same_task_mission_material_checklist` 或等价清单数据结构。

建议实现点：

- 在 `o7ConsumerReadAdapter.ts` 中新增 derivation helper，例如 `deriveSameTaskMissionMaterialChecklist(...)`。
- Source 优先级应沿用现有 O7 consumer detail 主路径：
  - top-level `same_task_mission_evidence_gate`
  - O6 `field_evidence` / artifact bundle / consumer detail alias 中的同名 gate
  - legacy fallback 仅用于兼容，不得覆盖主路径安全判断
- Checklist schema 建议为 `trashbot.pc_tools_workstation.o7_same_task_mission_material_checklist.v1`。
- 每个 item 至少包含：
  - `id`
  - `label`
  - `material_status`
  - `source_summary`
  - `blocked_reasons`
  - `next_required_evidence`
  - `owner_hint`
- 总体状态建议：
  - `blocked_not_proven`
  - `materials_ready_not_success_proof`
  - `fail_closed`

必须固定的安全字段：

- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

Fail-closed 输入条件：

- O6 gate 缺失。
- `task_id` 不一致。
- schema 不属于 `trashbot.o6.same_task_mission_evidence_gate.v1` 或 `trashbot.same_task_mission_evidence_gate.v1`。
- `blocked_reasons` / `next_required_evidence` 类型不安全。
- 任何 dangerous true 字段出现。
- source ref 含绝对路径、raw/base64、token、credential-bearing URL、串口或控制 topic。

允许改动范围：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/artifacts/o7_worker_report.md`

### Task B - O7 UI Checklist Display

Owner：`full-stack-software-engineer`

目标：在 O7 UI consumer detail 主路径展示 operator 可执行清单。

展示要求：

- Checklist 必须和现有 `same_task_mission_evidence_gate` 摘要相邻，便于 operator 对照。
- Item 按 mission material 分组展示：
  - same task identity
  - terminal/cloud result
  - route execution material
  - delivery record
  - operator confirmation
  - route pose progress
  - production cloud readback
  - safety invariants
- 每个 item 展示 material status、blocked reasons 和 next required evidence。
- UI 不得提供 send、run、control、navigate、submit、TTS、stop、cancel、production cloud connect 操作。
- 如需本地交互，只允许展开/折叠或复制非敏感 evidence key，不触发后端写入或机器人命令。

允许改动范围：

- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/artifacts/o7_worker_report.md`

### Task C - Docs Sync

Owner：`full-stack-software-engineer`

目标：同步更新 O7 接口文档。

必须更新：

- `docs/interfaces/o7_realtime_operator_console.md`

文档必须写清：

- `same_task_mission_material_checklist` 来源于 O6 consumer detail 主路径的 `same_task_mission_evidence_gate`。
- 它是 operator material checklist，不是 success proof。
- 固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 不连接真实公网云、不发送控制命令、不证明 production cloud、live route execution、delivery record、operator confirmation 或 delivery success。

允许改动范围：

- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/artifacts/o7_worker_report.md`

## 文件范围汇总

后续实现 owner 可改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/artifacts/o7_worker_report.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/tech-done.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/side2side_check.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/final.md`

本规划任务实际允许改动且已创建的文件仅为：

- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/pre_start.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/prd.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/tech-plan.md`

## 接口影响

- 新增 additive O7 consumer detail 字段：`same_task_mission_material_checklist` 或等价字段。
- 不删除、不改名现有 `same_task_mission_evidence_gate`、`artifact_bundle_readiness`、`route_replay_mvp` 或 `labeling_mvp`。
- 不要求 O6 新增 API；只消费 O6 existing consumer detail readback。
- 不改变真实 control、cloud、annotation、voice、route replay API 的启用状态。

## 验收命令

后续实现验收：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check
rg -n "same_task_mission_material_checklist|same_task_mission_evidence_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|robot_control_executed=false" pc-tools/workstation docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist
```

本规划任务验收：

```bash
test -f sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/pre_start.md
test -f sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/prd.md
test -f sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|same_task_mission_material_checklist|npm run test && npm run build && npm run lint|git diff --check" sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist
```

## 风险边界

- 本轮规划和后续实现均不证明真实 production cloud、真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 annotation API/export、真实 dataset export、真实手机/browser 或真实 delivery success。
- Checklist ready 只能表示材料清单在软件 readback 上 ready-not-success-proof，不能解锁控制。
- 如果 O6 gate 形状漂移，O7 必须 fail-closed 并报告 schema mismatch，不得推断成功。
- 如果实现只新增视觉 summary 而未提供 item-level next required evidence，Product 收口时不得计为 O7 主线增量。


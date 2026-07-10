# O7 Same-Task Mission Material Checklist Tech Done

## Sprint 类型

sprint_type: epic

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `O7ConsumerSameTaskMissionMaterialChecklist` 和 checklist item contract。
  - 在 O7 consumer detail、artifact bundle readiness、artifact bundle summary 和 consumer ingest summary 中增加 additive 字段 `same_task_mission_material_checklist`。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 新增 schema `trashbot.pc_tools_workstation.o7_same_task_mission_material_checklist.v1`。
  - 从现有 O6 `same_task_mission_evidence_gate` 派生 operator 材料清单，覆盖 `same_task_identity`、`terminal_cloud_result`、`route_execution_material`、`delivery_record`、`operator_confirmation`、`route_pose_progress`、`production_cloud_readback`、`safety_invariants`。
  - 固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，不启用 submit/TTS/nav/control。
  - 收紧 same-task gate 输入：schema mismatch、task mismatch、危险 true、unsafe ref/path/token/base64、blocked/next 列表类型不安全时 fail-closed。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 在现有 `same_task_mission_evidence_gate` 区块旁新增 checklist 展示。
  - UI 展示每个 material item 的 `material_status`、`source_summary`、`blocked_reasons`、`next_required_evidence` 和 `owner_hint`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 ready-not-success checklist、8 个 item、production cloud readback 缺口、固定 false 字段。
  - 覆盖 task mismatch 和 unsafe blocked list fail-closed。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 O7 UI 渲染 checklist schema、status、8 个 item、production cloud 下一步材料和四个固定 false 字段。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 同步新增 checklist contract、item 字段、fail-closed 条件和证明边界。

## 用户旅程变化和触点收益

PC operator 现在不只看到 O6 same-task gate 的原始摘要，还能在同一 consumer detail 主路径中看到材料清单：哪些材料已可读、哪些仍 blocked、下一步该补哪份证据、应由哪个 owner 配合。该 UI 仍是 observe-only，不提供控制、提交、TTS、Nav2 或生产云连接动作。

## 接口影响

- Additive 新增字段：`same_task_mission_material_checklist`。
- 新 schema：`trashbot.pc_tools_workstation.o7_same_task_mission_material_checklist.v1`。
- 不删除或改名既有 `same_task_mission_evidence_gate`、`artifact_bundle_readiness`、route replay、labeling 或 O6 API 字段。
- 不连接真实公网云，不读取硬件，不发送机器人控制命令。

## 验证结果

已复验：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

关键结果：

- Vitest：`Test Files 3 passed (3)`，`Tests 484 passed (484)`。
- Build：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；Vite 仅提示 chunk size warning。
- Lint：`eslint .` 通过，退出码 0。

第一轮验证失败定位和修复：

- `tsc` 首次失败于 `o7ConsumerReadAdapter.ts` 的 `unsafeList[0]` 可能为 `undefined`、重复 `proof_status` spread、route pose progress ready 字面量不匹配，以及 `App.test.ts` fixture 重复 `proof_status`。
- 已修复为 fallback reason、删除重复 `proof_status`、使用现有 contract 字面量 `ready_not_live_nav2_proof`，随后完整复验通过。

```bash
git diff --check
```

关键结果：通过，无 whitespace error。

```bash
rg -n "same_task_mission_material_checklist|same_task_mission_evidence_gate|delivery_success=false|safe_to_control=false|primary_actions_enabled=false|robot_control_executed=false" pc-tools/workstation docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist
```

关键结果：通过，命中 `same_task_mission_material_checklist` schema/adapter/UI/test/docs/sprint 留档、既有 `same_task_mission_evidence_gate` 主路径和四个固定 false 字段。

## 剩余风险

- 当前证明边界仍是 local/mock software proof，不证明真实 production cloud、production DB/queue、live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实 robot motion 或 delivery success。
- `materials_ready_not_success_proof` 只表示材料清单在软件 readback 上可读，不允许解锁 primary actions。

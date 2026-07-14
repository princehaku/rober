# Tech Done：O7 Mission Bundle Terminal Material Export

## Sprint Type

- `sprint_type: epic`
- Owner：`full-stack-software-engineer`
- 完成时间：2026-07-14 03:39 CST

## 实际改动

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 在 `missionEvidenceBundleSectionSummaries` 稳定 section 顺序中加入 `bounded_route_execution_gate_material` 和 `bounded_route_terminal_result_material`。
  - 在 mission evidence bundle export 的 material section 分类集合中加入上述两个 section，使 `counts.material_section_count` 从旧 material 分类扩展到最新 gate/terminal material。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展 `O7 mission evidence bundle export summarizes selected O6 detail without raw export claims` fixture，复用 `sampleBoundedRouteGateMaterial` 和 `sampleBoundedRouteTerminalResultMaterial`。
  - 增加 `section_summaries` 包含两个新 section 的断言，并把 `material_section_count` 精确断言为 `12`。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 同步 O7 consumer detail 默认 include 和 export 聚合说明，明确两个 bounded route material 会进入 selected-task bundle summary/material count。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC workstation 产品文档，明确 export 只聚合 `bounded_route_execution_gate_material` / `bounded_route_terminal_result_material` 的安全摘要，不证明真实 route execution、delivery、HIL、production cloud 或 safe-to-control。

## 用户旅程变化和触点收益

- Operator 在同一 selected task 上执行 mission evidence bundle export 时，可以在 `section_summaries` 和 `counts.material_section_count` 中看到 bounded route gate 与 terminal result material 已被纳入 material 类汇总。
- UI/API 仍只返回 local/mock receipt 摘要，不暴露 raw artifact body、真实路径、完整 URL、token 或真实 dataset。
- 固定 false fields 继续保持：`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`robot_control_executed=false`、`connects_cloud_production=false`、`real_cloud_db_connected=false`、`real_oss_connected=false`。

## 前后端 / ROS2 联调结果

- 本轮未新增 endpoint，未连接 production cloud，未访问真实 UART/WAVE ROVER，未触发 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或机器人运动。
- 联调边界为 O7 workstation 本机 loopback adapter 重新读取 O6 selected-task consumer detail 的 local/mock software proof。
- Proof boundary 继续是 `software_proof_o7_o6_mission_evidence_bundle_export_only`。

## 验证结果

```text
cd pc-tools/workstation && npm run test -- test/catalog.test.ts -t "O7 mission evidence bundle export"
Test Files  1 passed (1)
Tests  3 passed | 241 skipped (244)
```

```text
cd pc-tools/workstation && npm run test
Test Files  3 passed (3)
Tests  513 passed (513)
```

```text
cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 2.09s
```

- `npm run build` 仍有既有 Vite large chunk warning，未阻塞构建。

```text
cd pc-tools/workstation && npm run lint
eslint .
```

- `rg -n "bounded_route_terminal_result_material|bounded_route_execution_gate_material|material_section_count|software_proof_o7_o6_mission_evidence_bundle_export_only|route_execution_success=false|delivery_success=false|hil_pass=false" ...`：exit 0，命中 code/test/docs/sprint 锚点。
- `git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.14_03-29_o7_mission_bundle_terminal_material_export`：exit 0，无输出。

## 失败定位

- 无失败需要修复。targeted test、全量 workstation test、build、lint、anchor rg 和 scoped diff check 均通过。

## 剩余风险

- 本轮只证明 O7/O6 selected-task mission evidence bundle export 的 material 汇总一致性，不证明真实 route execution、delivery success、operator acceptance、HIL、safe-to-control、production cloud、real cloud DB、real OSS 或 real dataset export。
- 工作区开工前已有大量未提交改动；本轮只在允许范围内叠加窄改，未回滚或改写范围外文件。

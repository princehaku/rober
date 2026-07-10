# O7 Worker Report - Nav2 Goal Evidence Consumer

运行时间：2026-07-09 15:25:10 CST

## 用户旅程变化和触点收益

- O7 consumer detail 现在会消费 O6 回读的 `nav2_goal_execution_evidence`，并在 PC 工作站里展示同一 `task_id` 的 Nav2 goal/result/base command 只读摘要。
- UI 新增 `Nav2 goal execution evidence` 区块，展示 schema/status/proof_scope、goal requested/sent/accepted/result received、result status/code、base command/feedback 摘要、blocked reasons、next required evidence 和固定 false safety fields。
- 页面继续不打开真实控制，不把 `goal_result_status=succeeded` 解释为真实送达成功。

## 实际改动文件

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/artifacts/o7_worker_report.md`

## 接口影响

- `DEFAULT_DETAIL_INCLUDE` 新增 `nav2_goal_execution_evidence`。
- 新增 O7 summary 类型 `O7ConsumerNav2GoalExecutionEvidenceSummary`，并挂到 `O7ConsumerTaskDetailResponse` 与 `O7ConsumerArtifactBundleReadiness`。
- Adapter 白名单读取来源包括 top-level `nav2_goal_execution_evidence`、`field_evidence.nav2_goal_execution_evidence`、`field_motion_evidence_packet.nav2_goal_execution_evidence`、field evidence ingest、artifact bundle、artifact bundle consumer ingest 和 readiness wrapper。
- 只接受 schema `trashbot.nav2_goal_execution_evidence.v1` 与 proof scope `software_proof_nav2_goal_execution_evidence_only`；schema mismatch、proof scope mismatch、缺字段、dangerous true、unsafe text 均 fail-closed。

## 验证命令输出结果

```text
cd pc-tools/workstation && npm run test
Test Files  3 passed (3)
Tests       477 passed (477)
Duration    48.90s
```

```text
cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ 34 modules transformed.
✓ built in 1.73s
```

```text
cd pc-tools/workstation && npm run lint
eslint .
exit code 0
```

```text
rg -n "nav2_goal_execution_evidence|Nav2 goal|software_proof_nav2_goal_execution_evidence_only" ...
关键命中：adapter、shared contract、Vue 展示、catalog/App tests、产品文档均已覆盖。
```

## 失败定位和修复

- 首次 `npm run build` 失败于 `src/server/o7ConsumerReadAdapter.ts` 的 TS2783：`connects_cloud_production` / `robot_control_executed` 在 Nav2 summary 中显式写入后又被 `fixedFalseFields()` 覆盖。
- 已删除重复显式字段，保留统一 false helper；重跑 build 通过。

## 剩余风险

- 本轮是 O7 consumer read / UI 展示层软件证据，只证明 PC 工作站能消费 O6 回读摘要。
- 不证明真实 production cloud、真实 live Nav2 run、真实 route_bag、真实底盘运动、真实送达成功、真实 OSS/CDN 或真实 annotation API/export。
- 需要 O6/Algorithm 继续保证同一 `task_id` 下的 `nav2_goal_execution_evidence` 来源脱敏、字段稳定，并保持安全旗标为 false。

# O7 Worker Report

## 实际改动

- 在 [`/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts) 新增 `O7ConsumerCleanBaselineNav2PathMaterialSummary`，并把 `clean_baseline_nav2_path_material` 加入 O7 consumer detail contract。
- 在 [`/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts) 把 `clean_baseline_nav2_path_material` 加入默认 detail include，新增 top-level / field / bundle / readiness 白名单来源查找、fail-closed 归一化和 detail 返回。
- 在 [`/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`](/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue) 新增 clean-baseline 只读面板，展示 status、first failure、retry success、`path_point_count`、cleanup、blocked reasons、next required evidence 和固定 false flags。
- 在 [`/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts) 与 [`/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts) 增加 fixture、query include 断言和 clean-baseline summary 断言。
- 在 [`/Users/m1/apps/rober/docs/interfaces/o7_realtime_operator_console.md`](/Users/m1/apps/rober/docs/interfaces/o7_realtime_operator_console.md) 与 [`/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`](/Users/m1/apps/rober/docs/product/pc_tools_workstation.md) 同步 O7 consumer 主路径和产品边界文档。

## 用户旅程变化和触点收益

- O7 operator 不再需要回翻旧 sprint artifacts 才能知道 clean-baseline Nav2 preflight 的 first failure、retry success、31 点路径和 cleanup 结果。
- 同一 consumer detail 现在能把 `current_field_evidence_material`、`clean_baseline_nav2_path_material` 和 `same_task_route_execution_material_packet` 连续展示，方便区分 preflight 材料、support-only 当前材料和 route execution credit 材料。
- 页面继续保持 fail-closed：没有解锁任何控制、delivery 成功或 primary action 文案。

## 验证结果

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

- `npm run test`：`Tests 486 passed (486)`
- `npm run build`：通过；保留既有 Vite chunk size warning，不是本轮新增失败
- `npm run lint`：通过

```bash
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/o7_worker_report.md
```

- scoped `git diff --check`：通过，无输出

## 联调口径

- 本轮联调对象是 O6 consumer read detail contract，不是 live ROS2、不是 production cloud。
- O7 只消费 `trashbot.o6.clean_baseline_nav2_path_material.v1` / `trashbot.clean_baseline_nav2_path_material.v1` 的安全摘要。
- 证明边界固定为 `software_proof_clean_baseline_nav2_path_material_only`，并继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`hil_pass=false`、`connects_cloud_production=false`。

## 剩余风险

- 当前验证是 contract/UI/test 级软件证明，不证明真实 Nav2 route execution、真实 delivery result、真实 operator confirmation 或 HIL。
- build 仍有既有前端 chunk size warning；本轮没有扩展到 code split。

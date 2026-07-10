# O7 Worker Report

## sprint_type: micro

### 实际改动
- 在 [`pc-tools/workstation/src/shared/contracts.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts) 新增 `O7ConsumerRouteBagPoseProgressReplaySummary` 及其 frame/pose 子类型，并把 `route_bag_pose_progress_replay` 接到 task detail、artifact bundle、artifact bundle consumer ingest、artifact bundle readiness 的共享合同里。
- 在 [`pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts) 增加 pose progress replay 的多入口归一化、blocked summary、next evidence 合并和 fail-closed 逻辑。
- 在 [`pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`](/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue) 增加只读 pose progress 区块，展示 sample/decode counts、topic types、frame pairs、起止位姿、位移和 false fields。
- 在 [`pc-tools/workstation/test/catalog.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts) 与 [`pc-tools/workstation/test/App.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts) 更新 include 列表、blocked summary 断言和 pose progress 读回断言。
- 更新 [`docs/product/pc_tools_workstation.md`](/Users/m1/apps/rober/docs/product/pc_tools_workstation.md) 与 [`pc-tools/README.md`](/Users/m1/apps/rober/pc-tools/README.md) 的 O7 consumer 说明。

### 验证结果
- 执行 `cd pc-tools/workstation && npm run test && npm run build && npm run lint`
- 结果：`479` 个测试全部通过，`vite build` 通过，`eslint` 通过。
- 构建期间只有 Vite 的 chunk size warning，没有阻塞性错误。

### 失败定位
- 过程中先后遇到过 include 列表、blocked summary 断言和 TypeScript 类型导入/重复字段问题。
- 已修正为当前 fail-closed 行为，最终验证通过。

### 剩余风险
- `route_bag_pose_progress_replay` 目前仍按读模型和 blocked summary 暴露，不会解锁 Play/Submit/Control。
- 该能力仍依赖上游 O6 detail 提供足够的 pose progress 证据；缺字段时会继续 fail closed。
- 前端打包体积仍有 Vite 的 chunk size warning，暂不影响验证，但后续可再做拆包优化。

### 运行时间
- 2026-07-09 20:44:40 CST

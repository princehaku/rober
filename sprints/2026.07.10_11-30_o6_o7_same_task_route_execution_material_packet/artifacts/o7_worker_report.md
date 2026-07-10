# O7 Worker Report

- role: full-stack-software-engineer
- run_time: 2026-07-10 11:50:02 CST
- sprint_type: epic
- scope: O7 consumer/UI only

## 用户旅程变化

O7 consumer detail 默认 include `same_task_route_execution_material_packet`，PC workstation 现在能在同一任务详情页直接看到 O6 顶层 packet status、same-task identity、route execution materials、route execution result summary、pose progress/replay timeline summary、blocked reasons、next required evidence 和固定 false flags。

Checklist 仍可引用 packet，但验收不再只有 checklist；UI 有独立 `Same task route execution material packet` 区块，不会从 child readiness 推导 `delivery_success=true`、`safe_to_control=true` 或 primary action enabled。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`: 增加 O7 same-task route execution material packet 类型，并挂到 artifact bundle summary、consumer ingest、readiness 和 task detail。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`: 默认 include 新 packet；从 O6 top-level、field evidence、field motion、artifact bundle、consumer ingest 和 readiness 读取；补 schema/task/proof/unsafe/dangerous fail-closed；把 packet 纳入 readiness 和 checklist 依赖。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`: 新增独立 packet 展示区和 readiness 状态摘要，展示材料摘要、route result、pose timeline、blockers、next evidence、false flags。
- `pc-tools/workstation/test/App.test.ts`: 增加 UI fixture 和 DOM 断言，覆盖新 packet 可见摘要。
- `pc-tools/workstation/test/catalog.test.ts`: 增加 adapter fixture、default include、packet summary、fail-closed unsafe/mismatch 覆盖。
- `docs/product/pc_tools_workstation.md`: 更新 workstation adapter 默认 include 和 packet 产品语义。
- `docs/interfaces/o7_realtime_operator_console.md`: 更新 O7 console 接口说明和安全边界。

## 验证结果

```text
cd pc-tools/workstation && npm run test && npm run build && npm run lint

Test Files  3 passed (3)
Tests  486 passed (486)
vite v7.3.3 building client environment for production...
✓ built in 1.80s
eslint .
exit code 0
```

```text
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet

exit code 0
```

## 失败定位

第一轮 `npm run test` 暴露 4 个 catalog fixture 断言/数据问题：

- default include 断言未包含 `same_task_route_execution_material_packet`。
- legacy same-task field material packet fixture 切换 task id 后，缺少同 task 的 route execution material packet，导致新 gate 先 fail-closed。
- same-task mission gate fail-closed fixtures 缺少同 task route execution material packet，导致先命中 packet task mismatch。
- artifact readiness source 断言仍按旧预期要求 nested bundle source；当前 adapter 优先显示 top-level O6 packet source。

已修复 fixture 和断言后复验通过。

## 剩余风险

- 本轮验证是本地软件/Mock O7 consumer proof；不等于真实 O6 producer 已在同一 task_id 下持续产出该 packet。
- O6/Algorithm 并行 lane 若调整 packet 字段名或 material alias，O7 需要按最终 O6 contract 再跑一次联调 smoke。
- 所有控制、送达、primary action flag 仍固定 false；这符合当前只读证据消费边界。

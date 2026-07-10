# O7 Worker Report

## 用户旅程变化和触点收益

- O7 consumer detail 现在会稳定消费 `trashbot.o6.route_delivery_closure_packet.v1`，用户在 PC workstation 上可以直接看到 route delivery closure 的闭环状态，而不需要再去读原始 O6 payload。
- UI 只展示 `closure_status`、linked evidence flags、`blocked_reasons`、`next_required_evidence` 和固定 false safety flags，避免把本地/mock 证据误读成可提交、可发车、可控制或 delivery success。
- `route_delivery_closure_packet` 已加入默认 O6 consumer detail include，常见来源路径 `direct`、`field_evidence`、`field_motion_evidence_packet`、`artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness` 都会被统一折叠成 O7 安全摘要。

## 实际改动文件

- `/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`
- `/Users/m1/apps/rober/pc-tools/workstation/test/App.test.ts`
- `/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`
- `/Users/m1/apps/rober/pc-tools/README.md`
- `/Users/m1/apps/rober/sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/artifacts/o7_worker_report.md`

## 改动文件和接口影响

- `o7ConsumerReadAdapter.ts`
  - 把 `route_delivery_closure_packet` 加入默认 detail include。
  - 新增 O6 closure packet 的多来源读取与 fail-closed 收敛逻辑。
  - 把 closure packet 摘要接入 top-level detail、artifact bundle、artifact bundle consumer ingest 和 artifact bundle readiness。
- `contracts.ts`
  - 新增 `O7ConsumerRouteDeliveryClosurePacketSummary`。
  - 给 detail / artifact bundle / readiness 相关合同补齐 `route_delivery_closure_packet` 字段。
- `O7FixturePreviewPanel.vue`
  - 新增 route delivery closure packet 面板。
  - 只展示 closure status、linked evidence flags、blockers、next evidence 和 false safety flags。
- `catalog.test.ts` / `App.test.ts`
  - 覆盖 ready、blocked、schema mismatch、dangerous true、unsafe text 的 fail-closed 路径。
  - 断言 include 列表和 UI 文案都带上 `route_delivery_closure_packet`。
- `docs/product/pc_tools_workstation.md` / `pc-tools/README.md`
  - 同步 workstation O7 consumer read 主路径、include 列表、closure packet 摘要边界和来源说明。

## 前后端/ROS2 联调结果

- 本轮仅完成 PC workstation 对 O6 consumer read 合同的本地/mock 联调。
- 已验证 O7 adapter 能从 O6 consumer detail 的常见来源路径读出 `route_delivery_closure_packet` 并折叠成只读安全摘要。
- 本轮没有接入真实云、真实机器人、真实 ROS2 控制链，也没有声明 delivery success。

## 验证命令输出结果

执行命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

关键结果：

```text
Test Files  3 passed (3)
Tests  483 passed (483)
Duration  37.05s

vite build: ✓ built in 1.75s
lint: eslint . 退出码 0
```

## 失败定位

- 中途出现一次 TypeScript 构建失败：`O7ConsumerArtifactBundleReadiness` 缺少 `route_delivery_closure_packet` 字段定义，导致 adapter object literal 和测试访问该字段时报错。
- 已在 `contracts.ts` 补齐该字段后复验通过。

## 剩余风险

- 当前仍是本地/mock/O6-shaped contract 证明，不等于真实云、真实 ROS2、真实送达闭环或 production connected。
- UI 故意固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，后续若要接真实 lane，需要机器人侧和 O6 lane 继续提供更强现场/任务证据。
- 本轮只覆盖了 workstation O7 读路径，没有新增提交、控制或发车动作。

# O7 Worker Report

## 实际改动文件

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`

## 用户旅程变化和触点收益

- O7 consumer detail 现在会随默认 include 一起请求并读取 `route_execution_result_delivery_readiness`。
- PC UI 新增统一结果链只读摘要区，运营可以在同一 `task_id` 下同时看到 route execution、delivery readiness、operator confirmation readiness 的状态、来源、blocked reasons 和 next evidence。
- artifact bundle readiness 同步带出 `route_execution_result_delivery_readiness_status`，保持 bundle 主路径和 detail 主路径口径一致。

## 接口影响

- 新增 O7 消费字段：`route_execution_result_delivery_readiness`
- 新增 include：`route_execution_result_delivery_readiness`
- adapter 只接受：
  - schema `trashbot.o6.route_execution_result_delivery_readiness.v1`
  - proof scope `software_proof_route_execution_result_delivery_readiness_only`
- fail-closed 条件：
  - schema/proof scope mismatch
  - dangerous true
  - unsafe text/path/url/token
  - 必填字段缺失

## 前后端联调结果

- 本轮以 O7 fixture / mock O6 consumer detail 联调。
- adapter 会从 top-level、`field_evidence`、`field_motion_evidence_packet`、`artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness` 白名单位置读取统一结果链摘要。
- O7 不自行推导 delivery success；UI 固定保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 验证结果

执行通过：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

关键日志片段：

- `Tests 480 passed (480)`
- `vite v7.3.3 building client environment for production...`
- `built in 1.71s`
- `eslint .`

## 失败定位

- 初次 `npm run test` 失败在旧 include 断言未包含 `route_execution_result_delivery_readiness`；补齐测试期望后通过。
- 初次 `npm run build` 失败在：
  - `O7ConsumerDeliveryResultEvidenceSummary` import 未被直接使用
  - 测试 fixture 重复声明 `proof_status`
- 已改为直接类型引用并去掉重复字段，build 通过。

## 剩余风险

- 仍然只证明 `software_proof_route_execution_result_delivery_readiness_only`。
- 不证明真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 production cloud、真实 OSS/CDN。
- O7 当前只消费 O6 摘要；若 O6 上游字段命名继续变化，需要同步更新 adapter 白名单位置和 fail-closed 测试。

## 返工说明（fail-closed 语义）

- 返工原因：`buildRouteExecutionResultDeliveryReadinessSummary()` 曾把 `nav2_goal_execution_ready` / `delivery_result_ready` / `operator_confirmation_ready` 参与顶层 ready 聚合，导致 O6 顶层 `status=blocked_not_proven` 时仍可能被 O7 显示成 ready。
- 修复后口径：O7 顶层 `summary.status` 只信任 O6 顶层 `status==="route_execution_result_delivery_readiness_ready_not_delivery_proof"`；子字段 readiness 继续展示，但不再把整体 blocked 推成 ready。
- 新增回归覆盖：
  - catalog: O6 顶层 blocked，但 delivery/operator 子 readiness 为 ready 时，O7 detail 与 artifact bundle readiness 仍返回 `blocked_not_proven`。
  - App: 预览 UI 显示 `route_execution_result_delivery_readiness_status=blocked_not_proven`，同时保留 `delivery_result_ready=true`、`operator_confirmation_ready=true`。

## 返工验证结果

- 返工后再次执行：
  - `cd pc-tools/workstation && npm run test`
  - `cd pc-tools/workstation && npm run build`
  - `cd pc-tools/workstation && npm run lint`
- 实际关键日志：
  - `Tests 482 passed (482)`
  - `vite v7.3.3 building client environment for production...`
  - `✓ built in 1.81s`
  - `eslint .`

# O7 worker report: route bag full semantic decode matrix

- run_time: 2026-07-09 22:34:40 CST
- owner: full-stack-software-engineer
- scope: O7 consumer read adapter, workstation readonly UI, tests, docs
- proof_scope: `software_proof_route_bag_full_semantic_decode_matrix_only`

## 用户旅程变化和触点收益

- O7 consumer detail 现在会请求并展示 `route_bag_full_semantic_decode_matrix`，operator 可以在 artifact bundle readiness 与 O7 fixture preview 中只读看到 decoded / unsupported / failed topic type counts、coverage ratio、限量 sample topic/type、blocked reasons、next evidence 和固定 false safety fields。
- `ready_not_route_execution_proof` 只表示本地/离线 semantic coverage 可读；UI 和 readiness 文案继续明确不代表 route execution success、delivery success 或真实 robot motion。
- matrix 被纳入 artifact bundle readiness gating；缺失 matrix 时 readiness 保持 `derived_blocked_not_proven` 并提示需要 `route_bag_full_semantic_decode_matrix_for_selected_task`。

## 实际改动文件和接口影响

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `O7ConsumerRouteBagFullSemanticDecodeMatrixSummary` 与 topic/type sample summary contract。
  - 将 matrix summary 挂到 consumer task detail、artifact bundle summary、artifact bundle consumer ingest 与 artifact bundle readiness。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - detail include 增加 `route_bag_full_semantic_decode_matrix`。
  - 支持 schema `trashbot.route_bag_full_semantic_decode_matrix.v1` 与 `trashbot.o6.route_bag_full_semantic_decode_matrix.v1`。
  - 从 direct、`field_evidence`、`field_motion_evidence_packet`、`artifact_bundle`、`artifact_bundle_consumer_ingest`、`field_evidence_consumer_ingest`、`artifact_bundle_readiness` 候选源读取。
  - 只保留 coverage counts、sample topic/type、blocked reasons、next evidence、false safety fields；坏 schema、proof scope mismatch、危险 true、unsafe 文本、控制 topic、unsafe topic/type、坏计数和非法 coverage ratio 均 fail-closed。
  - 同时兼容 O6 原始 `topic_type_matrix` 与 readiness 已适配的 `sample_topic_type_matrix`。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 在 O7 preview 中新增 “Route bag full semantic decode matrix” 只读区块，并在 artifact bundle readiness 摘要中显示 matrix status / coverage / counts。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 adapter 合同断言、readiness 派生断言、控制 topic fail-closed 断言。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 UI fixture 和 DOM 断言，覆盖 matrix section、coverage/counts/sample/blocker/next evidence 展示。
- `docs/product/pc_tools_workstation.md`
  - 更新 O7/O6 consumer read 集成说明，加入 matrix include、候选源、proof scope、fail-closed 与 ready 边界。
- `pc-tools/README.md`
  - 更新 workstation O7 Previews 说明，加入 matrix readonly summary 与 artifact bundle readiness 消费边界。

## 前后端 / ROS2 联调结果

- 本轮没有接真实 ROS2 graph、真实 route bag、真实 robot runtime 或生产云；验证边界是 workstation 本地 adapter + UI software proof。
- Adapter 按 O6/Algorithm 已脱敏 summary contract 消费 matrix，不读取 DB3 原始文件、raw ROS payload、本地路径、token 或控制 topic。
- UI 只读展示同一 `task_id` 的 matrix coverage，不发控制请求、不打开 submit/export/control 能力。

## 测试和手动验收证据

执行命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

最终结果：

```text
Test Files  3 passed (3)
Tests  482 passed (482)

vite v7.3.3 building client environment for production...
✓ 34 modules transformed.
✓ built in 1.74s

> rober-pc-tools-workstation@0.1.0 lint
> eslint .

exit code 0
```

第一轮验证失败定位与修复：

- 初次 `npm run test` 失败 8 项，根因是新 matrix fixture 使用 `/camera/image_raw`，命中既有 topic safety guard；同时 `artifact_bundle_readiness` 候选源可能给出已适配的 `sample_topic_type_matrix`。
- 修复：matrix fixture 改用安全 sample topic `/camera/image`，并让 adapter 同时接受 `topic_type_matrix` 与 `sample_topic_type_matrix`。随后完整 test/build/lint 通过。

## 剩余风险和机器人侧配合事项

- 仍是 `software_proof_route_bag_full_semantic_decode_matrix_only`；未证明真实 route bag 解码来自实车、未证明 route execution success、delivery success 或 HIL。
- O6/Algorithm 需要继续产出同 task 的安全 matrix summary，尤其是 unsupported / failed topic type 的后续 decoder evidence 与 decode failure repro。
- 若未来要展示更多 topic/type 或原始解码内容，需要先扩展 O6 脱敏 contract；O7 UI 不应绕过 adapter 直接展示 raw payload。

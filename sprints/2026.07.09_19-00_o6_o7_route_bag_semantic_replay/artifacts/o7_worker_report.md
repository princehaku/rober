# O7 Worker Report

- 角色：full-stack-software-engineer
- sprint：`2026.07.09_19-00_o6_o7_route_bag_semantic_replay`
- 运行时间：2026-07-09 19:52 CST
- 证据边界：`software_proof_route_bag_semantic_replay_only`

## 实际改动的文件列表

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 补齐 `route_bag_semantic_replay` 的 consumer detail 主路径接入。
  - 从 O6 top-level、`field_evidence`、`field_motion_evidence_packet`、`artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness` 归一读取 semantic replay。
  - 把 semantic replay 的 blocked reasons / next required evidence 合并进 `artifact_bundle_readiness`。
  - 修正 fail-closed detail、TypeScript 类型和 readiness 空值兜底，保证缺 `labeling.review_items` 时仍 fail-closed。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 新增 semantic replay 只读 panel、decode summary、LaserScan/Image/TF 摘要、blocked reasons、next evidence 和 false fields 展示。
  - 在 labeling summary / artifact bundle readiness summary 中加入 `route_bag_semantic_replay_status`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补 semantic replay fixture、include 断言和 adapter/readiness 断言。
- `pc-tools/workstation/test/App.test.ts`
  - 补 semantic replay fixture、DOM 文案和主路径 summary 断言。
- `docs/product/pc_tools_workstation.md`
  - 更新 O7 consumer adapter / include / artifact bundle readiness 文档，补 `route_bag_semantic_replay` 只读合同说明。
- `pc-tools/README.md`
  - 更新 O7 consumer read primary path 与 field evidence consumer ingest 文档，补 semantic replay 消费口径。
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/o7_worker_report.md`
  - 本次执行记录。

## 验证命令输出结果

```bash
cd pc-tools/workstation && npm run test
```

输出摘要：

```text
Test Files  3 passed (3)
Tests  479 passed (479)
Duration  41.04s
```

```bash
cd pc-tools/workstation && npm run build
```

输出摘要：

```text
vite v7.3.3 building client environment for production...
✓ built in 1.74s
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json 通过
```

```bash
cd pc-tools/workstation && npm run lint
```

输出摘要：

```text
eslint . 通过
```

补充校验：

```bash
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/o7_worker_report.md
```

输出：通过，无空白错误。

## 失败定位

- 首轮 `npm run test` 失败：
  - `artifactBundleReadinessRefs()` 直接读取 `labeling.review_items.sample`，在若干 fail-closed catalog case 中触发空值异常。
  - `buildO7ConsumerTaskDetail()` 已开始使用 `route_bag_semantic_replay`，但遗漏了 candidate/build/fail-closed 接线和 top-level detail 返回字段。
- 首轮 `npm run build` 失败：
  - adapter 缺少 `O7ConsumerRouteBagSemanticReplaySummary` 类型导入。
  - `failClosedDetail()` 缺少 `route_bag_semantic_replay` 字段，且 `blockedArtifactBundleReadiness()` 参数顺序未跟 semantic replay 新签名同步。
  - semantic replay sanitizer 里对 `laser_scan_summary` / `image_summary` / `tf_summary` 的空值保护不完整，TypeScript 拒绝编译。
- 处理：
  - 增加 semantic replay 主路径接线、fail-closed 字段和类型导入。
  - 对 readiness / sanitizer 补空值兜底。
  - 同步修正 catalog / App fixture 与 include 断言。

## 剩余风险

- 当前仍只是 `software_proof_route_bag_semantic_replay_only`；不证明真实 production cloud、真实 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- O7 只展示白名单语义统计，不展示 raw payload、base64、媒体内容、绝对路径、token 或控制字段；若后续 Algorithm/O6 扩充 schema，O7 仍需要显式更新白名单。

# tech-done

- sprint_type: epic
- round: 2026.07.09_09-57_o7_artifact_bundle_consumer_readiness
- status: done
- current_run_time: 2026-07-09 10:44 CST

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts` 新增 `O7ConsumerArtifactBundleSummary`、`O7ConsumerArtifactBundleConsumerIngestSummary`、`O7ConsumerArtifactBundleReadiness`，并把 consumer detail 扩展为可返回 `artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness`。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts` 现在会优先从 O6 顶层 `artifact_bundle` / `artifact_bundle_consumer_ingest` / wrapper 内 bundle 读取同一 `task_id` 的 route/replay/keyframe/evidence refs，生成 readiness counts / refs / blocked reasons / next required evidence，并在危险 bundle ref、危险 true 字段或 schema mismatch 时 fail closed。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 已把 consumer-detail 主路径改成显式展示 `artifact_bundle_readiness`、bundle source、bundle refs、blocked reasons 和 next evidence，并把 route replay / labeling 仍保留为只读消费面。
- `pc-tools/workstation/test/catalog.test.ts` 增加了 bundle/readiness happy path 断言和 unsafe ref fail-closed 断言。
- `pc-tools/workstation/test/App.test.ts` 补齐了 O7 Previews 的 consumer detail fixture，让 UI 能实际渲染 readiness 文案与 bundle 摘要。
- `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`、`pc-tools/README.md` 已同步说明 bundle readiness 主路径与兼容 fallback 边界。

## 验证结果

- `npm run test -- --runInBand` 失败，原因是当前 Vitest 不支持 `--runInBand`。
- 退回执行 `npm run test` 成功，结果为 `3 passed`、`470 passed`。
- `npm run build` 成功。
- `npm run lint` 成功。
- `git diff --check` 成功。

## 剩余风险

- 这轮只验证了 workstation 端的 software-proof / mock 链路，没有真实串口、真实 O6/O7 生产云、真实媒体、真实机器人运动或 HIL 证据。
- readiness 依赖上游 O6 detail 仍保持 bundle / ingest / wrapper 结构稳定；如果 O6 字段再改，consumer detail 的 fallback 口径需要同步调整。

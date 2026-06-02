# 2026.06.02 09-10 Real Material Runbook

## sprint_type

micro

## Owner

full-stack-software-engineer

## 实际改动

- 扩展 `GET /api/real-material/acceptance` 合同：每条 O5/O6/O7 queue item 新增 `collection_runbook` 和 `artifact_freshness`。
- `collection_runbook` 给 operator 展示采集目标、建议命令、必需 env/artifact、期望输出、成功判定、失败处理和安全说明；API 只返回 recipe，不执行命令。
- `artifact_freshness` 对 env 指向或默认 runtime artifact 做只读 `stat`，输出 `fresh/stale/missing`、mtime、age 和 stale 阈值；响应不暴露绝对路径。
- `RealMaterialAcceptancePanel.vue` 展示每条 item 的 freshness、runbook 摘要、建议命令和成功判定，让下一步采集更明确。
- 同步更新 workstation 产品边界和 real-material acceptance queue 接口文档。

## 验证结果

已执行并通过：

- `cd pc-tools/workstation && npm run test`
  - `Test Files  2 passed (2)`
  - `Tests  57 passed (57)`
- `cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - `✓ 35 modules transformed.`
  - `✓ built in 2.50s`
- `cd pc-tools/workstation && npm run lint`
  - `eslint .`
  - exit code 0
- `git diff --check -- pc-tools/workstation/src/server/realMaterialAcceptance.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/RealMaterialAcceptancePanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md docs/interfaces/real_material_acceptance_queue.md sprints/2026.06.02_09-10_real-material-runbook/tech-done.md`
  - exit code 0

## 剩余风险

- 当前改动只让 operator 看见 runbook 和 artifact 新鲜度，不新增真实公网 TLS、真实 4G/SIM、production DB/queue、真实 OSS/CDN、真实 180s browser artifact 或真实机器人控制证据。
- Freshness 只证明文件 mtime 是否新，不证明 artifact 内容通过验收；内容判定仍由 item `status` 和 `blocking_reason` 表达。
- O5/O6/O7 的真实材料仍需要 operator 按 runbook 在准备好 env、云端和浏览器环境后手动采集。

## 运行时间

- 初稿记录：2026-06-02 09:18:35 CST
- 验证完成：2026-06-02 09:24:40 CST

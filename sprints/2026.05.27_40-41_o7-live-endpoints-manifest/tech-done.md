# O7 Live Endpoints Manifest Micro Sprint

sprint_type: micro

## 实际改动

- 新增 `GET /api/o7/live-endpoints/manifest`，由 `pc-tools/workstation/src/server/o7LiveEndpointsManifest.ts` 只读构建 O7-KR1..KR6 future live API readiness manifest。
- manifest 只读取环境变量，URL 只展示 `protocol://host/path`，token 只展示 `present` / `absent`；含 credentials、query 或 hash 的 URL 会 `blocked` 且不采用。
- O7 Previews UI 新增手动加载面板，展示 endpoint configured/not_configured/blocked、token present/absent、全局安全 false flags、required live evidence 和 remaining real capability gaps。
- 更新共享契约、client API、Express route、单测、README、产品边界文档和接口文档。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，Vite 输出 `✓ built in 707ms`。
- `cd pc-tools/workstation && npm run test`：通过，输出 `Test Files  2 passed (2)`、`Tests  39 passed (39)`、`Duration  11.89s`。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无报错输出，退出码 0。
- `git diff --check -- pc-tools/workstation/src/server/o7LiveEndpointsManifest.ts pc-tools/workstation/src/server/catalog.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts pc-tools/README.md docs/product/pc_tools_workstation.md docs/interfaces/o7_live_endpoints_manifest_api.md sprints/2026.05.27_40-41_o7-live-endpoints-manifest/tech-done.md`：通过，无输出，退出码 0。

## 剩余风险

- 本轮只建立 env-only readiness manifest，不执行网络探测、不连接生产、不验证 endpoint reachable/auth、不证明真实 RTC/视频、云归档、标注、ASR/TTS、safe command、robot ACK 或硬件安全。
- 真实能力仍需要 O6/O7 后续提供 live API contract、鉴权策略、端到端审计日志、robot ACK、受控现场和硬件安全证据。

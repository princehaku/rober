# PC 开发入口避开 Node 7001 冲突

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-26 10:30 CST

## 实际改动

- `pc-tools/workstation/vite.config.ts`：Vite 热更新开发页默认端口从 `7001` 调整为 `7002`，`/api` 默认代理到本机 Node 工作站 `http://127.0.0.1:7001`。这样正式 Node/Express 入口继续固定 `0.0.0.0:7001`，开发页不再和它抢端口，也不会误把 `/api/robot-control/*` 打到上位机服务。
- `pc-tools/workstation/package.json`：`npm run dev:public` 同步改为 `HOST=0.0.0.0 PORT=7002 vite`。
- `pc-tools/workstation/src/shared/workstationDefaults.ts`：新增 Node/Vite 端口常量，避免 server、Vite config 和测试各自写一套端口口径。
- `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/test/catalog.test.ts`：server 改读共享 Node 端口常量；新增回归，锁定 Node 工作站默认 `0.0.0.0:7001`，Vite dev 默认 `0.0.0.0:7002`，且 `/api` 代理到 `127.0.0.1:7001`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步说明正式现场访问仍用 Node/Express `7001`；开发热更新页使用 `7002 -> 7001` 代理链路。未修改 Clash 或系统代理配置。

## 验证结果

- 首次定向测试失败：直接在 `catalog.test.ts` import `vite.config.ts` 触发 Vite/esbuild 在当前 jsdom 环境的 `TextEncoder().encode("") instanceof Uint8Array` invariant failure。已改为共享轻量端口常量，避免测试直接加载 Vite config。
- 通过：`npm test -- -t "defaults workstation Node API|keeps Vite dev defaults"`，2 passed。
- 通过：`npm run lint`。
- 通过：`npm run build`。仅保留既有 Vite chunk size warning。
- 通过：`npm test`，204 passed。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，`node` 监听 `*:7001`。

## 剩余风险

- 本轮只修 PC 开发入口配置，不改变真实上车端 Robot API、Nav2、manual、delivery 或键盘控制行为。Vite dev 需要与 `npm run api` 同时使用：7002 的热更新页代理到 7001 的 Node 工作站。

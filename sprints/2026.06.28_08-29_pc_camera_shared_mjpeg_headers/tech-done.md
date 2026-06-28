# tech-done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：PC 共享 MJPEG multipart 响应新增 `X-Robber-Camera-Shared-Capture: single_shared_capture_for_multiple_clients` 与 `X-Robber-Camera-Exclusive-Claim: false`。这样首个页面、并发页面和后进页面都能从响应头直接确认这是同一条只读共享上游，不是每个浏览器独占摄像头。
- `pc-tools/workstation/test/catalog.test.ts`：扩展 MJPEG relay 测试，覆盖首个、后进和并发客户端都拿到共享只读 header，且仍只产生 1 次上游 `/api/camera/mjpeg` 请求。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 2026-06-28 08:29 CST 的共享预览 contract。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation camera MJPEG proxy forwards only fixed readonly multipart stream"`：通过，`1 passed | 147 skipped`。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "does not close wheel raw L/R from static nonzero base feedback samples"`：通过，`1 passed | 203 skipped`。全量第一次跑到该用例时捕到一次 `/api/robot-control/base/manual` 时序串扰，单测复跑通过后继续全量复跑。
- `cd pc-tools/workstation && npm test`：第二次全量复跑通过，`352 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；保留 Vite 既有 chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只强化 PC 7001 共享 MJPEG relay 的可机读 contract，未做真实 UVC 首帧、供电、USB 带宽或上车端 `/api/camera/mjpeg` HIL 复测。
- 改动不调用 manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel`，也不修改 Clash 或系统代理配置。

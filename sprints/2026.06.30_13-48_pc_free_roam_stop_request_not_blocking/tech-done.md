# PC Free Roam Stop Request Not Blocking Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 自由移动 summary、latest response 和 action card evidence 增加 `start_clears_stop_request_not_blocking`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.free_roam` 和 `free_move` action card 输出“停止请求可由 start 自动清除且不阻塞启动”的结构化字段。
  - 将普通文案从容易误解的“当前有停止请求”调整为“停止请求会在开始自由移动时自动解除，不作为启动阻塞”。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/free-roam/autonomy/latest` 同步同一字段和文案，避免 latest 详情与 summary 漂移。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-action-status-card-free_move`、`plain-free-roam-motion-gauge` 和自由移动主按钮暴露 `data-start-clears-stop-request-not-blocking`。
  - 自由移动仪表文案改为“停止请求会自动解除，不阻塞启动”。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 锁定新字段和新文案。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步 stop request 不阻塞自由移动启动的产品合同。

## 验证结果

- `npm test -- test/App.test.ts -t "labels free-roam start as clearing a pending stop request before moving"`：通过，1 个目标测试通过。
- `npm test -- test/catalog.test.ts -t "free-roam autonomy latest"`：通过，3 个目标测试通过。
- `npm test -- test/catalog.test.ts -t "does not treat stale runtime scan"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 个 error；保留既有 4 个 Vue warning。
- `npm run build`：通过，生成 `dist/assets/index-351GdzWe.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `git diff --check`：通过。
- 7001 live 验证：
  - 已停止旧 `node` PID `72466`，新 `node` PID `75811` 监听 `*:7001`。
  - `curl http://127.0.0.1:7001/` 返回新资产 `/assets/index-351GdzWe.js` 和 `/assets/index-DCA8Xtd4.css`。
  - `GET /api/robot-control/summary` 显示 `readback_summary.free_roam.start_clears_stop_request_not_blocking=true`，`plain` 事实写成“停止请求会在开始时自动解除，不作为启动阻塞”。
  - `free_move` action card evidence 显示 `start_clears_stop_request_not_blocking=true`，`next_action_plain` 不再残留“当前处于停止请求”。

## 剩余风险

- 本轮只补 PC Web/Node 只读 summary、DOM 和文案合同，不自动清除 stop、不启动自由移动、不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- 真车是否实际移动仍需要现场勾选安全确认后显式点击自由移动 start，并用停止兜底和轮速/位姿证据复验。

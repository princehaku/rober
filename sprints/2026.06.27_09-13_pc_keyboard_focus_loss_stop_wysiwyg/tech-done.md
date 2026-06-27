# PC keyboard focus-loss stop WYSIWYG

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/test/App.test.ts` 新增 PC 键盘连续手控回归：按住键盘方向后，`window blur` 和 `document visibilitychange(hidden)` 都必须通过固定 `/api/robot-control/base/stop` 收口，并在普通首屏保留对应停止原因。
- 在 `docs/product/pc_tools_workstation.md` 同步记录普通用户口径：窗口失焦/切页面会停，只验证 PC 前端事件兜底和固定 stop 代理，不调用 Nav2、delivery、free-roam motion 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "stops continuous keyboard control when the window loses focus or the page is hidden"`，结果 `1 passed | 280 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍有既有 chunk size warning，不影响产物生成。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`、`281 passed (281)`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，结果 `node` 监听 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsS http://127.0.0.1:7001/api/health` 返回 `trashbot.pc_tools_workstation.health.v1`。

## 剩余风险

- 本轮只做 PC 前端 mock 回归和本机 7001 健康检查，没有发真实键盘 pulse、Nav2、free-roam 或 `/cmd_vel`；真实车动仍需要 operator 现场安全确认后再测。

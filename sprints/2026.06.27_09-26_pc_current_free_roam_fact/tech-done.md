# PC current free-roam fact

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的普通首屏 `当前事实` 增加自由移动事实行，只读展示上车 runtime 当前是否已经发布运动。
- 在 `pc-tools/workstation/test/App.test.ts` 覆盖三种事实：默认未发布运动、live/start-ready 但 artifact-only、运动发布已解锁。
- 在 `docs/product/pc_tools_workstation.md` 同步记录该 WYSIWYG 口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "renders Robot Control V1|free-roam autonomy|free movement"`，结果 `15 passed | 267 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍有既有 chunk size warning，不影响产物生成。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`、`282 passed (282)`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，结果 `node` 监听 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsS http://127.0.0.1:7001/api/health` 返回 `trashbot.pc_tools_workstation.health.v1`。

## 剩余风险

- 本轮只改 PC 首屏只读事实行和 mock 回归，没有触发真实 free-roam start/stop、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。

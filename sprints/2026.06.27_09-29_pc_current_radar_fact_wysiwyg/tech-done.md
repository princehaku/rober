# PC current radar fact WYSIWYG

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 增加 `plainCurrentRadarFactText()`，让普通首屏 `当前事实` 的雷达行同步展示运行/待刷新状态、压缩雷达点数和最近障碍距离。
- 在 `pc-tools/workstation/test/App.test.ts` 更新默认当前事实期望，并为 live 形状 `latest_proof_incomplete_while_lifecycle_running + scan_preview_point_count=72 + 最近障碍 0.04m` 增加当前事实断言。
- 在 `docs/product/pc_tools_workstation.md` 同步记录雷达当前事实 WYSIWYG 口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "current-facts|renders Robot Control V1|radar"`，结果 `30 passed | 252 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍有既有 chunk size warning，不影响产物生成。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`、`282 passed (282)`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，结果 `node` 监听 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsS http://127.0.0.1:7001/api/health` 返回 `trashbot.pc_tools_workstation.health.v1`。

## 剩余风险

- 本轮只改 PC 首屏只读事实行和 mock 回归，没有启动/刷新真实雷达，没有发真实 manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel`。

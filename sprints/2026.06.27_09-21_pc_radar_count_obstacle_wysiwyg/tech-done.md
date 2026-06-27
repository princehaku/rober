# PC radar count and obstacle WYSIWYG

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 调整地图雷达 marker 和口径行：当雷达只有压缩点数、没有点数组，同时自动扫图门禁提供最近障碍距离时，普通首屏同时显示 `待刷新雷达点 N 个` 和 `最近障碍 Xm`。
- 在 `pc-tools/workstation/test/App.test.ts` 更新既有雷达 marker 期望，并新增 live 形状回归：`latest_proof_incomplete_while_lifecycle_running`、`scan_preview_point_count=72`、`最近障碍 0.04m` 时，地图 marker、aria、雷达点口径和坐标口径都必须同时展示点数与最近障碍。
- 在 `docs/product/pc_tools_workstation.md` 同步记录该所见即所得规则。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "radar"`，结果 `29 passed | 253 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- -t "radar|renders Robot Control V1|surfaces generated trip readback|localization reset failure|draws the latest Nav2 goal|marks stale path preview|draws no-motion route markers"`，结果 `35 passed | 247 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍有既有 chunk size warning，不影响产物生成。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`、`282 passed (282)`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，结果 `node` 监听 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsS http://127.0.0.1:7001/api/health` 返回 `trashbot.pc_tools_workstation.health.v1`。

## 剩余风险

- 本轮只改 PC 前端显示和 mock 回归，没有启动/刷新真实雷达，没有发真实 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`；live 雷达 proof 不完整仍需继续查 LiDAR 数据链路。

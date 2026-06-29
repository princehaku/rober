# PC 雷达旧点不贴图保护语

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通地图/雷达下一步在 `start_radar_then_refresh_map_preview` 时，即使后端已经给了简短 `next_action_plain`，也补充“旧雷达点不会贴到当前地图”。
- `pc-tools/workstation/test/App.test.ts`：把 not-current 雷达测试改成 live 形态，确认后端有简短 next_action_plain 时，前端仍保留旧点不贴图保护语。
- `docs/product/pc_tools_workstation.md`：同步普通首屏雷达旧点保护语。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "not-current map radar overlay"`，结果 `1 passed | 216 skipped`。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "radar"`，结果 `33 passed | 184 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed` test files，`382 passed` tests。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提示，不影响本轮雷达文案。
- 通过：`git diff --check`。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读检查 live `/api/robot-control/summary`，雷达仍为 `radar_stopped`，地图雷达层仍为 `not_current`，blocked reasons 为 `runtime_scan_stale_for_map_radar_overlay,radar_lifecycle_not_running_for_map_radar_overlay`；本轮未启动雷达。

## 剩余风险

- 本轮只改普通页面文案，不启动雷达、不刷新地图、不发送 manual/Nav2/free-roam/stop 或 `/cmd_vel`。
- 真正让雷达点贴到地图仍需现场点击启动雷达，等待新扫描，再刷新地图画面确认。

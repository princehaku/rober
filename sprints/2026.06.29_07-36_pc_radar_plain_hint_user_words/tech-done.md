# PC radar plain hint user words

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`readback_summary.radar.plain_hint` 改成普通用户口径，使用“地图雷达点 / 新扫描 / 同轮地图预览”，并把下一步动作合入总事实。
- `pc-tools/workstation/src/server/index.ts`：独立 `/api/robot-control/radar/status` 顶层 `plain_hint`、`radar_status_plain`、`radar_next_action_plain` 与 summary 使用同一普通口径。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`、`pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：同步本地 fallback、fixture 和 radar/status 断言，锁定总事实不再暴露 `marker/overlay`。
- `docs/product/pc_tools_workstation.md`：同步记录 radar plain hint 普通用户口径和只读边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "radar status|Robot Control summary"`，`1 passed`，`39 passed | 121 skipped`。
- 已通过：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 均成功；仅保留既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`，`2 passed`，`375 passed`。
- 已通过：重启 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID `57726` 监听 `TCP *:7001`。
- 已通过：只读请求 `GET /api/robot-control/summary`，live `readback_summary.radar.plain_hint` 返回 `雷达未运行或扫描已停；地图雷达点当前显示 0 个，旧来源点 81 个只作诊断。下一步：先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`。
- 已通过：只读请求 `GET /api/robot-control/radar/status`，live 顶层 `plain_hint` 返回 `雷达未运行或扫描已停；旧雷达来源点不能当作当前地图雷达点。下一步：先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`。

## 剩余风险

- 本轮只改善雷达 summary/status 的普通用户表达，不启动雷达、不刷新地图、不发送任何运动命令。
- live 雷达仍未运行；需要现场显式启动雷达并刷新地图画面后，才能证明地图雷达点真正显示。

# 2026.06.26 04:24 PC 雷达启动后刷新 pending WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 雷达 start 已返回 ok 且自动 scan proof refresh 仍 pending 时，雷达卡片 hint 改为 `雷达启动已返回，正在刷新新雷达点。`
  - 地图雷达点口径在同一状态下显示 `雷达启动已返回，正在刷新新点位。`
  - 地图 marker 继续使用已有 `雷达已启动，位置未读到/等待刷新确认` 语义，避免退回旧的未运行状态。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 `auto-refreshes radar proof after plain radar start reports ok`：悬挂 `/api/robot-control/radar/scan-proof/refresh`，验证刷新未返回期间的普通首屏、地图 marker 和点位口径；释放刷新后再验证最终切到 `雷达已运行`。
- `docs/product/pc_tools_workstation.md`
  - 记录雷达启动 ok 后自动刷新 proof 的 pending WYSIWYG 口径和控制边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- -t "auto-refreshes radar proof"`
  - 结果：1 passed，190 skipped。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
- 已通过：`cd pc-tools/workstation && npm test`
  - 结果：2 files passed，191 tests passed。
- 已通过：`git diff --check`
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有做真实雷达 HIL。
- 没有触发真实上位机雷达、manual、Nav2、delivery 或 `/cmd_vel`；真实场地仍需 HIL 验证雷达启动后的自动 proof 刷新时序。

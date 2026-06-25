# 2026.06.26 01:42 PC 雷达启动失败地图 Marker WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `启动雷达` 返回失败时，把本次 radar lifecycle proxy 的 `failure_reason` 同步到地图雷达 marker。
  - 地图 marker 状态改为 `data-state=雷达启动失败`，ARIA 补充地图位置是否读到。
  - 雷达 freshness 文案在失败态明确显示 `雷达点口径：雷达启动失败，未显示新点位。`，避免 operator 误以为已出现新 scan。
  - 失败态不显示扫描范围占位；这是因为 start 未成功时不应暗示 LiDAR 正在等待确认。
- `pc-tools/workstation/test/App.test.ts`
  - 在既有 `shows plain radar start only when the readback says lidar is stopped` 用例中补充地图 marker、`data-state`、ARIA、扫描范围隐藏和 freshness 断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏雷达启动失败的地图 WYSIWYG 口径和不触发控制动作的边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows plain radar start only when the readback says lidar is stopped"`
  - 结果：`1 passed | 178 skipped (179)`
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `cd pc-tools/workstation && npm test`
  - 结果：通过，`2 passed (2)`，`179 passed (179)`。
- `git diff --check`
  - 结果：通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 验证副作用处理

- 全量 Vitest 运行后会刷新两份旧 DOM smoke artifact 的 `checked_at` 字段；本轮已将
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  和
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
  的时间戳恢复到原值，避免把旧证据误记为本轮产物。

## 剩余风险

- 本轮只做 PC DOM/mock 验证，未连接真实上位机触发 `/api/radar/start`，因此不构成真实 LiDAR lifecycle HIL 通过。
- 改动不自动重试、不自动刷新 proof，不发送 manual、keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。

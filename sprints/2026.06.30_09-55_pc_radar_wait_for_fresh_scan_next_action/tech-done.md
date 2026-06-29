# PC 雷达地图下一步等待新扫描

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：当地图雷达 overlay 为 `not_current` 且原因包含雷达 lifecycle 未运行时，`radar_overlay_wysiwyg_next_action_plain` 和 `radar_overlay_next_action_plain` 从“先启动雷达，再刷新地图画面”改为“先启动雷达并等待新扫描，再刷新地图画面确认雷达点”。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：同步普通地图卡、雷达卡、雷达点 evidence 兜底和建图 readiness suffix，避免普通用户把旧雷达来源点误判成当前地图点。
- `pc-tools/workstation/src/server/index.ts`：移除 7001 启动前的短生命周期端口 probe，避免 `tsx` 启动链路下出现实际已监听但日志残留 `address already in use` 的误导。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补齐回归断言，锁定 summary、map preview 和首屏 UI 都使用“等待新扫描”的下一步。
- `docs/product/pc_tools_workstation.md`：同步只读合同、安全边界和普通用户口径。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "honors not-current map radar overlay summary"`，1 个 App 回归用例通过。
- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "formats public API port conflict"`，1 个端口冲突提示回归用例通过。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、382 个用例通过。
- 通过：`npm --prefix pc-tools/workstation run build`，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；Vite 仍保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启本机 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`，启动日志为 `pc-tools workstation API listening on http://0.0.0.0:7001`，没有 `address already in use` 失败误报。
- 通过：只读 `GET /api/health` 返回 `schema=trashbot.pc_tools_workstation.health.v1`、`mode=pc_only_readonly_workstation`、`version=0.2.0`。
- 通过：只读 `GET /api/robot-control/summary` 返回 `robot_api_connection.status=readable`，`readback_summary.map.radar_overlay_wysiwyg_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`，`readback_summary.radar.radar_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`，Nav2 下一步仍为“用 ROS 模式重跑图上路线；执行时会自动启动自动驾驶 runtime，并在同窗口确认轮速 L/R 非零”。

## 剩余风险

- 本轮不启动雷达、不调用 Nav2、不发底盘命令；真实雷达新扫描、摄像头首帧和 Nav2 同窗口 wheel L/R 非零仍需要现场在安全确认后执行。
- 已知旧 artifact 脏文件未触碰：`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`、`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`。

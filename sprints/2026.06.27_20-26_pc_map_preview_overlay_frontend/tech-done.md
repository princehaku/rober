# PC Map Preview Overlay Frontend Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增普通地图 overlay 读取层，优先使用 `/api/robot-control/map/preview.radar_overlay` 随图返回的 `robot_pose` 和 `scan_preview_points`，summary 继续作为兜底。
  - 地图雷达点、机器人 marker、点数 fallback、雷达 freshness 和坐标口径同步标明“地图预览雷达点”，避免把同轮预览材料误说成 summary 实时链路。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 summary 缺位姿/雷达点但 map preview 带 overlay 的回归测试，确认 PC 地图仍画出小车和雷达点，并且不会调用 radar start、manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录前端消费 `radar_overlay` 的所见即所得规则和只读边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- test/App.test.ts --testNamePattern "map preview radar overlay|radar pulse"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 176 skipped (178)`
- 已通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 310 passed (310)`
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - Vite 保留既有 chunk size warning，构建成功。
- 已通过：`git diff --check`
- 已通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 live 检查
  - `lsof` 显示 `node ... TCP *:7001 (LISTEN)`
  - `GET /api/health` 返回 `schema=trashbot.pc_tools_workstation.health.v1`、`mode=pc_only_readonly_workstation`
  - `GET /api/robot-control/map/preview?robotApiBaseUrl=http://192.168.1.11:8787` 返回 `proxy_status=preview_forwarded`、真实图片 `223x116`、`radar_overlay.overlay_status=loaded`、`scan_preview_points=65`、`robot_pose.frame_id=map`

## 剩余风险

- 本轮是 PC 前端只读展示修复，不触发真实摄像头、雷达启动、Nav2 执行、manual、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实车上自动驾驶仍需要在现场安全确认后重跑 Nav2，并以同窗口 wheel raw L/R 非零证明完整路线执行。

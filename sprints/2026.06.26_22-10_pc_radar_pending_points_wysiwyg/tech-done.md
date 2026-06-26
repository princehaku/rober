# PC 雷达待刷新点位所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增雷达待刷新点位口径：当雷达状态为 `雷达待刷新 / 刷新中 / 雷达启动中` 时，地图上已投影的 scan 点显示为 `待刷新雷达点 N 个`，不再写成实时 `雷达点 N 个`。
  - 同步更新地图 `雷达点口径` 与 `坐标口径`：有 map-frame 位姿且点已贴图时，若 latest proof 仍不 fresh，则写明“正在确认实时性，当前地图上显示待刷新雷达点”。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live-shape 回归测试：map-frame 位姿和 scan 点存在，但 LiDAR lifecycle running、latest proof incomplete、`continuous_window_observed=false` 时，地图 marker、scan aria、freshness 和坐标口径都必须显示待刷新点，不触发雷达 start、Nav2、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录雷达 lifecycle running 但 proof stale/incomplete 时的地图点位 WYSIWYG 规则。

## 验证结果

- live 只读证据：本机 7001 summary 显示上位机 `readback_summary.lidar.lifecycle_running=true`、`continuous_scan_status=latest_proof_incomplete_while_lifecycle_running`、`continuous_window_observed=false`、`latest_scan_proof_fresh=false`，同时 `o3_proof_summary.robot_pose` 和 `scan_preview_point_count=8` 已存在。
- 通过：`npm test -- -t "mapped radar points as pending"`，结果 `1 passed / 212 skipped`。
- 通过：`npm test -- -t "radar|雷达|scan|map-frame pose|mapped radar|local radar|freshness"`，结果 `20 passed / 193 skipped`。
- 通过：`npm test`，结果 `213 passed`。
- 通过：`npm run build`，Vite build 成功；保留既有 chunk size warning。
- 通过：`npm run lint`。

## 剩余风险

- 本轮只改 PC 地图/雷达 WYSIWYG 文案和 gate，不刷新 proof、不启动雷达、不执行 Nav2、不发送 manual/keyboard pulse/stop 或 `/cmd_vel`。
- 当前 live 雷达仍需要现场点击 `刷新雷达` 才能证明最新窗口；本轮没有把该状态标记为完成。
- 本轮没有修改 Clash、系统代理或系统端口配置；项目 Node 继续使用 `0.0.0.0:7001`。

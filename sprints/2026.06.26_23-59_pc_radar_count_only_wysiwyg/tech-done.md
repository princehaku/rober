# PC 雷达点数-only 地图口径修正

## Sprint 类型

sprint_type: micro

## 实际改动

- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - 新增统一的雷达点数-only 判断，优先保留 `o3_proof_summary.scan_preview_point_count` 和 `readback_summary.lidar.scan_preview_point_count` 证据。
  - 当 `scan_preview_point_count=N` 但 `scan_preview_points=[]` 时，地图不凭点数伪造坐标，也不再泛化显示 `雷达点位未读取`。
  - 普通地图的 scan label、雷达点口径、坐标口径会明确显示“仅点数，没有点数组”，并区分未显示局部轮廓或未贴到地图。
- 更新 `pc-tools/workstation/test/App.test.ts`：
  - 锁定 live 形态：雷达 lifecycle stopped、latest proof 不 fresh、点数组为空但 summary 点数为 72。
  - 断言地图不画 scan/local dots、不发送控制命令，同时保留 72 个历史点数的 WYSIWYG 说明。
- 更新 `docs/product/pc_tools_workstation.md`：
  - 记录点数-only 雷达材料在普通首屏的展示合同和 no-motion 边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "keeps radar point count visible"`：通过，1 passed / 140 skipped。
- `cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "radar|雷达|lidar|LiDAR"`：通过，22 passed / 119 skipped。

## 剩余风险

- 本轮只修 PC 普通首屏 WYSIWYG 文案和 DOM 状态，不启动真实雷达、不读取新 scan artifact、不做底盘运动 HIL。
- 现场摄像头仍是 `/dev/video1` 无首帧输出；小车真实低速运动和自动驾驶完整闭环仍需后续硬件验证。

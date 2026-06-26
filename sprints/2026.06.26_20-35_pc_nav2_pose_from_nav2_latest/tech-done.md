# PC summary 使用 Nav2 latest 位姿

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`proofRobotPose()` 不再只读取 `localize_proof_latest`，改为按 `localize_proof_latest -> nav2_proof_latest -> nav2_status -> status` 查找结构化 `amcl_pose/robot_pose/map_pose`。这样当定位 proof latest 陈旧、但 Nav2 proof latest 已经带 `/amcl_pose` 时，普通地图仍能拿到真实 map-frame 小车坐标。
- `pc-tools/workstation/test/catalog.test.ts`：新增回归测试，覆盖 `localize latest` 陈旧、`nav2 proof latest` 带 `amcl_pose` 的现场形态，断言 PC summary 返回 `robot_pose_status=map_pose_observed`、x/y 坐标和路线点数。
- `docs/product/pc_tools_workstation.md`：同步记录 PC 工作站最新口径：路线和小车 map 坐标可同时显示，但完整 Nav2 执行未证明时不放宽执行门禁。

## 验证结果

- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，104 tests。
- `cd pc-tools/workstation && npm test`：通过，2 files / 241 tests。
- `cd pc-tools/workstation && npm run build`：通过；仅有 Vite chunk size warning。
- 已重启 PC Node：`HOST=0.0.0.0 PORT=7001 ./node_modules/.bin/tsx src/server/index.ts`，`lsof` 确认监听 `*:7001`。
- 真实 PC 7001 summary 复测：
  - `o3_proof_summary.robot_pose={x: 0.0052897571185793095, y: 0.023728681034303378, yaw: 0.0012964370795674081, frame_id: map, source: /amcl_pose}`
  - `readback_summary.localization.robot_pose_status=map_pose_observed`
  - `readback_summary.nav2.path_generated=true`
  - `readback_summary.nav2.path_preview_point_count=36`
  - `readback_summary.nav2.path_preview_frame_id=map`
  - `safe_to_control=false`

## 剩余风险

- 本轮只修复 PC 聚合层位姿来源，证明“地图上能同时看见小车和路线”；尚未证明完整 Nav2 NavigateToPose 执行成功、feedback 闭环或 delivery success。
- `safe_to_control=false` 仍是执行门禁，不能因为已读到 Nav2 latest 位姿就直接发车。
- 摄像头首帧不可读和多人实时预览的上车端 MJPEG/WebRTC 实际画面仍需单独继续修。

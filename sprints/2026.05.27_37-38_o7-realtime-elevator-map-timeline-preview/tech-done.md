# O7 Realtime/Elevator Map Timeline Preview

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 `Realtime/elevator cloud probe` 区块新增 `Realtime map pose preview`，只从 `robot_pose_summary` 安全字符串解析 `x_m/y_m/yaw_rad`，解析失败显示 `blocked_pose_coordinate_unavailable` 且不画 marker。
- 新增固定 viewBox SVG 的 map frame、中心轴、pose marker 和 yaw heading 展示，并显式展示 `latency_lt_2s_proven=false`、`real_ros2_tf_connected=false`、`real_realtime_api_connected=false`、`safe_to_control=false`、`robot_control_executed=false`。
- 新增 `Elevator state timeline preview`，只展示最多 5 条 `elevator_state_samples_summary` 摘要，空样本显示 `blocked_not_proven`，并固定展示 `real_elevator_state_chain_connected=false`、`floor_recognition_proven=false`、`human_takeover_proven=false`、`safe_to_control=false`。
- 更新 `pc-tools/workstation/test/App.test.ts` 覆盖新面板、SVG、pose marker 字段、timeline sample index 和 fail-closed false 字段。
- 新增 `docs/interfaces/o7_realtime_elevator_probe_api.md`，同步更新 `docs/product/pc_tools_workstation.md` 与 `pc-tools/README.md` 的 O7 probe UI 边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键输出：`✓ 31 modules transformed.`、`✓ built in 2.23s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键输出：`Test Files  2 passed (2)`、`Tests  38 passed (38)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键输出：`eslint .` 无错误退出。
- 通过：`git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_elevator_probe_api.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_37-38_o7-realtime-elevator-map-timeline-preview/tech-done.md`
  - 关键输出：无 whitespace error。

## 剩余风险

- 当前仍是 PC-only software proof；不证明真实地图、ROS2 `/tf`、<2s latency、真实电梯状态链、楼层识别、人工接管、硬件安全或机器人控制。

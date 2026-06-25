# PC 行程操作状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“行程操作”新增 `行程状态` 行。
  - 状态覆盖：未勾安全确认、已确认待准备、路线已准备但地图未显示、图上路线可执行、准备中、检查中、执行中、已完成、旧记录/失败。
  - 状态只解释现有 UI gate；真正执行仍必须显式点击按钮并由后端复查定位和路线。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展行程用例：验证未确认、已确认、准备后未显示地图路线、地图上路线可执行四个关键状态。
- `docs/product/pc_tools_workstation.md`
  - 记录行程状态行的用户口径和安全边界。

## 验证结果

- `npm test -- -t "plain trip|prepared trip|no-motion route|visible route|Nav2 goal"`：通过，2 files / 10 passed / 157 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 167 passed。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- 7001 只读 summary：`source_base_url=http://192.168.1.11:8787`、`normalized_base_url=http://192.168.1.11:8787`、`console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`free_roam_autonomy=locked`、`lidar_running=false`、`robot_pose=null`、`scan_preview_count=72`、`path_preview_point_count=36`、`path_generated=true`、`path_generation_succeeded=true`。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、stop、map start、radar start 或 `/cmd_vel`。
- 完整 Nav2 路线执行仍需要现场显式确认后，在地图路线已可见时点击执行并读取成功结果。

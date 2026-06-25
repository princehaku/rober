# PC 行程路线所见即所得提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `行程操作` 新增 `plain-trip-route-wysiwyg` 提示。
  - 地图上已画出路线时，提示执行前确认地图上的起点、终点和路线。
  - 只读到路线点数但地图未画出路线时，提示先刷新地图画面确认图上路线。
  - 修正旧文案，避免在路线未画出来时说“地图上已显示路线”。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖路线准备后未画出路线的提示。
  - 覆盖地图路线可见时的 WYSIWYG 行程提示。
- `docs/product/pc_tools_workstation.md`
  - 记录 `行程操作` 的路线准备和地图可见性分离口径。

## 验证结果

- `npm test -- -t "plain trip|prepared trip|Nav2 goal|no-motion route"`：通过，2 files / 10 passed / 156 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 166 passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- 7001 只读 summary：
  - `source_base_url=http://192.168.1.11:8787`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `manual_motion_entry_status=controlled_jog_requires_safety_confirmation_only`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `free_roam_autonomy=locked`
  - `lidar_running=not_loaded`
  - `latest_scan_proof_fresh=not_loaded`
  - `robot_pose=null`
  - `scan_preview_count=0`
  - `path_preview_point_count=36`

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、stop、map start、radar start 或 `/cmd_vel`。
- 完整 Nav2 路线执行仍需要现场显式确认后触发真实执行并读取成功结果，本轮只收紧 PC 首屏 WYSIWYG 口径。

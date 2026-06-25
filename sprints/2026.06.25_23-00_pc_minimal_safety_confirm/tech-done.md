# PC 首屏最小安全确认

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `移动/导航` 删除额外 `移动前检查` 按钮。
  - 普通状态文案从“移动前检查”收敛为“安全确认已勾/安全确认已记录”。
  - 本轮进度下一步从“完成移动前检查”改为“勾选安全确认”。
  - 删除普通首屏专用 `submitPlainMotionPrecheck` 死代码，避免留下不可达入口。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定普通首屏不再出现 `移动前检查`。
  - 锁定勾选安全确认不会自动提交 operator report，也不会发送 manual。
- `docs/product/pc_tools_workstation.md`
  - 同步默认首屏契约：发车前最小预检就是勾选 `人在旁边、周围安全、停止手段就绪`。

## 验证结果

- `npm test -- -t "Robot Control V1|motion precheck|keyboard|radar and map proof"`：通过，1 file passed / 12 passed / 154 skipped。
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
  - `lidar_running=false`
  - `latest_scan_proof_fresh=false`
  - `robot_pose=null`
  - `scan_preview_count=72`
  - `path_preview_point_count=36`

## 剩余风险

- 本轮没有触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、stop、map start、radar start 或 `/cmd_vel`。
- 高级诊断中的 operator report / 现场材料提交通道仍保留，用于送达和验收材料，不作为普通首屏发车前预检。

# PC 扫图保存前刷新画面 gate

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“扫地式建图”在地图记录启动后，把保存按钮从 `保存当前地图` 改为 `先刷新画面` 并禁用。
  - 只有 operator 显式点击扫图卡片里的 `刷新扫图画面`，且只读 map preview 成功返回后，普通保存按钮才恢复可点。
  - `下一步` 在键盘扫图停稳后，会优先指向 `刷新扫图画面`，刷新后才指向保存。
  - 修正竞态：页面初载或 lifecycle 自动同步触发的 map preview 不算“本轮扫图画面已刷新”，不能误解锁保存。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 free-roam 流程测试，覆盖开始记录后保存禁用、扫图刷新后保存恢复。
  - 保留断言：启用键盘和下一步聚焦不自动发送 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`
  - 记录普通扫图保存前必须显式刷新当前画面的 WYSIWYG gate。

## 验证结果

- `npm test -- -t "free-roam"`：通过，2 passed / 164 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 166 tests passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- 7001 只读 summary：
  - `source_base_url=http://192.168.1.11:8787`
  - `safe_to_control=false`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `keyboard_reuses_manual_gate=true`
  - `free_roam_autonomy=locked`
  - `camera_status=ready`
  - `robot_pose=null`
  - `scan_preview_count=72`
  - `path_preview_point_count=36`
  - `lidar_running=false`
  - `radar_start_configured=true`

## 剩余风险

- 本轮没有触发真实地图记录、Nav2 execute、manual、keyboard pulse、delivery complete、radar start、stop 或 `/cmd_vel`。
- 自动扫图仍是 `locked`；当前只是把人工扫图流程的保存前可视确认补齐。

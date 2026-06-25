# PC 扫图覆盖刷新口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“扫地式建图”的覆盖提示从“地图记录中，可边扫边刷新画面”改为“覆盖条是上次刷新结果，点刷新扫图画面才是当前画面”。
  - 保持覆盖条只消费只读 `mapPreviewResult`，不自动刷新、不推断真实底盘运动。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 free-roam 流程测试，锁定 map recording started 后的覆盖刷新口径。
  - 既有测试继续验证启动记录后，启用键盘不自动发送 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录扫图覆盖条的 WYSIWYG 口径。

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

## 剩余风险

- 本轮没有触发真实地图记录、Nav2 execute、manual、keyboard pulse、delivery complete、radar start、stop 或 `/cmd_vel`。
- 自动扫图仍是 `locked`；覆盖条仍需 operator 在扫图过程中显式点击 `刷新扫图画面` 才能代表当前地图画面。

# PC 键盘连续手控按住说明

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘手控说明从只列按键，补充为 `按住会持续低速移动，约每 0.26 秒续一次；松开即停`。
  - 节奏来自 summary 的 `keyboard_jog_interval_ms`，不把 endpoint、raw pulse 或 `/cmd_vel` 放进普通首屏。
- `pc-tools/workstation/test/App.test.ts`
  - 在键盘连续手控测试中锁定普通首屏说明文案。
  - 保留断言：未启用键盘时全局按键不发送 manual；复查按钮不发送 manual。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏键盘说明展示连续低速移动节奏，但不改变安全确认 gate。

## 验证结果

- `npm test -- -t "keyboard"`：通过，9 passed / 157 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 166 tests passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- 7001 只读 summary：
  - `source_base_url=http://192.168.1.11:8787`
  - `safe_to_control=false`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `keyboard_reuses_manual_gate=true`
  - `keyboard_jog_interval_ms=260`
  - `keyboard_jog_duration_ms=240`
  - `free_roam_autonomy=locked`
  - `camera_status=ready`
  - `robot_pose=null`
  - `scan_preview_count=72`
  - `path_preview_point_count=36`
  - `lidar_running=false`

## 剩余风险

- 本轮没有触发真实 keyboard pulse、manual、stop、Nav2 execute、delivery complete、map start、radar start 或 `/cmd_vel`。
- 键盘连续手控真实验收仍需要 operator 显式启用键盘并按住方向键，且松开后 stop 成功。

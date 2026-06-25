# PC 扫地式建图扫图状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“扫地式建图”新增 `扫图状态` 行。
  - 状态覆盖：未勾安全确认、未开始记录、记录中待启用键盘、键盘已启用、按住方向键扫图、松开 stop 后待刷新或可保存、地图已保存。
  - 状态只读本地流程、map lifecycle 结果和既有 keyboard/manual 状态，不自动触发任何动作。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 free-roam 用例：验证安全确认、开始记录、启用键盘、按住前进、松开停止后的扫图状态文案。
  - 用例内 manual/stop 仍走固定 mock proxy，并断言未通过 `下一步` 自动发送 manual。
- `docs/product/pc_tools_workstation.md`
  - 记录扫图状态行的用户口径和安全边界。

## 验证结果

- `npm test -- -t "free-roam|扫地式|keyboard continuous|keyboard control"`：通过，1 file / 4 passed / 163 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 167 passed。
- `npm run build`：通过，Vite production build 和 server TypeScript build 均完成。
- 7001 只读 summary：`source_base_url=http://192.168.1.11:8787`、`normalized_base_url=http://192.168.1.11:8787`、`console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`keyboard_jog_interval_ms=260`、`keyboard_jog_duration_ms=240`、`free_roam_autonomy=locked`、`lidar_running=false`、`scan_preview_count=72`、`path_preview_point_count=36`。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮没有触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、map start、radar start 或 `/cmd_vel`。
- 自动自由跑动仍是 `free_roam_autonomy=locked`；当前可用路径仍是人工按住键盘低速扫图。

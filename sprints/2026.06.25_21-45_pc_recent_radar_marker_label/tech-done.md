# PC 地图最近雷达点 marker 口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当 `robot_pose=null`、当前雷达未运行，但 summary 仍带最近 `scan_preview_points` 时，地图主 marker 从 `雷达未运行` 改为 `雷达未运行，显示最近点`。
  - 保持局部点云只作为最近雷达局部轮廓显示，不贴到地图坐标。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 recent local radar scan 测试，锁定 marker 文案和 aria 口径。
  - 继续断言该展示不调用 radar start、manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录雷达已停但有最近 scan 点时，主 marker 也同步说明“显示最近点”。

## 验证结果

- `npm test -- -t "radar"`：通过，14 passed / 152 skipped。
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

- 本轮没有启动雷达、没有刷新 proof、没有触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 当前真实小车仍没有 map-frame robot pose；最近雷达点只能显示为局部轮廓，不能贴到真实地图坐标。

# PC 行程执行对齐图上路线

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏在地图已经显示路线点时，把行程提示改为 `地图上已显示路线 N 个点`。
  - 勾选安全确认后，红色执行按钮从泛化 `执行行程` 改为 `执行图上路线`。
  - 默认无路线点时仍保持 `执行行程`，不改变现有无路线流程。
- `pc-tools/workstation/test/App.test.ts`
  - 更新行程准备和 summary 路线已准备测试，锁定“图上路线”文案。
  - 保留断言：聚焦、准备和检查不自动调用 Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏行程执行文案与地图路线 overlay 对齐的规则。

## 验证结果

- `npm test -- -t "trip"`：通过，9 passed / 157 skipped。
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
  - `o3_proof_summary.path_generated=true`
  - `nav2_route_summary.path_generated=false`
  - `lidar_running=false`

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、map start、radar start、stop 或 `/cmd_vel`。
- 当前真实小车仍没有 map-frame robot pose；执行图上路线仍必须由现场 operator 显式点击，后端继续复查定位和路线。

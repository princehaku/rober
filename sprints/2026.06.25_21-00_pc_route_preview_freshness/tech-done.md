# PC 地图路线预览新旧状态区分

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图仍按真实 `path_preview_points` 绘制路线 polyline，不因为当前 planner 状态缺失就隐藏已有路线点。
  - 当 `path_generated/path_generation_succeeded` 未证明当前 planner 成功时，路线 caption 改为 `最近路线已显示 N/M 个点，待重新规划`。
  - 路线端点和坐标口径同步区分 `路线` 与 `最近路线`，避免把残留路径误认为当前可执行 Nav2 路线。
- `pc-tools/workstation/test/App.test.ts`
  - 更新最近目标点测试，使未证明当前生成的路线显示为最近路线。
  - 新增 `path_generated=false + path_preview_points` 的回归测试，确认地图照实画点但文案要求重新规划。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏地图区分当前路线和最近路线的 WYSIWYG 规则。

## 验证结果

- `npm test -- -t "route"`：通过，15 passed / 151 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 166 tests passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- 7001 只读 summary：
  - `source_base_url=http://192.168.1.11:8787`
  - `safe_to_control=false`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `free_roam_autonomy=locked`
  - `robot_pose=null`
  - `scan_preview_count=72`
  - `path_preview_point_count=36`
  - `o3_proof_summary.path_generated=true`
  - `lidar_running=false`
- PC Node 端口：
  - `node` 正在 `TCP *:7001` 监听。

## 剩余风险

- 本轮没有触发 Nav2 execute、manual、keyboard pulse、delivery complete、map start、radar start、stop 或 `/cmd_vel`。
- 当前真实小车 summary 仍是 `safe_to_control=false`，自动扫图仍是 `locked`；完整 Nav2 路线执行和自由建图还需要现场显式操作与 HIL 证据。

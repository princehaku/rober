# PC 地图雷达实时口径提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图 caption 新增 `雷达点口径`。
  - 雷达运行且有 map-frame 位姿时显示实时雷达点已贴到地图。
  - 雷达运行但缺 map-frame 位姿时显示实时雷达只显示局部轮廓，等待定位后再贴地图。
  - 雷达已停但仍有 scan preview 时显示这是最近记录，不是实时雷达。
- `pc-tools/workstation/test/App.test.ts`
  - 补充三类地图雷达 WYSIWYG 断言：实时贴图、实时局部轮廓、历史最近点。
  - 保留断言这些地图显示不会调用 `/api/base/manual`、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏 `雷达点口径` 的产品语义和安全边界。

## 验证结果

- `npm test -- -t "radar"`：通过，2 files / 14 passed / 152 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 166 passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- 7001 只读 summary：
  - `source_base_url=http://192.168.1.11:8787`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `lidar_running=false`
  - `latest_scan_proof_fresh=false`
  - `robot_pose=null`
  - `scan_preview_count=72`
  - `path_preview_point_count=36`
  - `free_roam_autonomy=locked`

## 剩余风险

- 本轮没有触发真实 radar start、map start、manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`。
- 雷达点是否真正实时仍以后端 summary 的 lifecycle/freshness 字段为准；本轮只把这个口径在 PC 首屏明确显示。

# 2026.06.25 19:20 PC map coordinate truth caption

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏地图 caption 新增 `坐标口径`，明确区分三种 WYSIWYG 状态：机器人位置已读到时雷达点/路线贴到地图；缺机器人位置但有 scan preview 时雷达只显示车身局部轮廓、不贴地图；只有路线时路线仍按地图坐标显示但雷达不贴图。
- `pc-tools/workstation/test/App.test.ts`：在已有 radar/route overlay 回归里补充坐标口径断言，覆盖有定位雷达贴图、无定位局部雷达、无定位路线显示三种状态。
- `docs/product/pc_tools_workstation.md`：同步普通首屏地图 `坐标口径` 的用户语义和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "radar"`：通过，`8 passed / 63 skipped`。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "route"`：通过，`8 passed / 63 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`162 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_pose=null`、`scan_preview_count=72`、`path_preview_count=36`、`lidar_lifecycle_running=false`。该现场状态正需要普通首屏明确提示“雷达局部轮廓不贴地图，路线按地图坐标显示”。

## 剩余风险

- 本轮只增强地图 WYSIWYG 解释，不改变 map preview、雷达 proof、Nav2、manual、keyboard、delivery 或 `/cmd_vel` 的行为；真实定位仍依赖上位机 AMCL/map-frame pose。

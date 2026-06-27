# 2026.06.28 04:01 free-roam latest 普通首屏建图缺口摘要

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `刷新自由移动状态（只读）` 摘要开始消费 `latest_key_values.mapping_missing` 与 `mapping_ready`。
  - latest 读回显示为 `建图缺口：画面首帧未出、雷达未刷新、地图记录未启动、地图画面未刷新`，或在全部满足时显示 `建图验收已 ready`。
  - 该按钮仍只调用 fixed GET latest，不触发 free-roam start/stop、manual、Nav2、delivery、雷达启动、相机打开或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 free-roam autonomy latest 首屏测试 fixture，锁定普通摘要会显示建图验收缺口，并继续断言不发送运动或状态机 start/stop 请求。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录普通首屏 latest 摘要现在直接显示建图缺口，方便现场判断“可自由移动”和“可验收建图”的区别。

## 验证结果

- 首轮 focused 测试失败后已修正测试口径：普通摘要按页面当前可见事实过滤已满足项，不机械显示旧缺口。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "refreshes free-roam autonomy latest as a read-only first-screen action"`，1 passed / 187 skipped。
- 通过：`cd pc-tools/workstation && npm test`，335 passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
  - Vite 仍提示生产包 chunk 大于 500 kB，这是既有前端体积提示，不影响本轮构建通过。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，live 只读
  `GET /api/robot-control/free-roam/autonomy/latest?baseUrl=http://192.168.1.11:8787` 返回
  `proxy_status=latest_loaded`、`remote_http_status=200`、
  `mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、
  `mapping_ready=false`、`safe_to_control=false`、`robot_control_executed=false`。
- 通过：live 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回
  `free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`、
  `free_roam_mapping_missing_reasons=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、
  `nav2_goal_label=自动驾驶服务未启动`，且 `robot_control_executed=false`。

## 剩余风险

- 本轮只改 PC 首屏只读摘要，不修复摄像头 UVC 无首帧、雷达 stale、Nav2 服务未启动或真实自由移动 HIL。
- 是否真的能自由移动、wheel raw L/R 非零、Nav2 完整路线执行和 delivery success 仍需现场安全确认后分别验证。

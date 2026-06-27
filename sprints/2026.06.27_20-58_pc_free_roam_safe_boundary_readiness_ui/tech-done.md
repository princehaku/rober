# PC 自由移动建图 safe boundary 展示

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - 普通首屏建图验收和当前事实优先使用 `safe_command_boundary.free_roam_mapping_ready` 与 `free_roam_mapping_missing_reasons`。
  - PC 已显示真实地图画面或本地刚启动地图记录时，过滤上一拍 summary 里已被本地事实覆盖的 `fresh_map_preview/mapping_active` 旧缺口。
  - 保留自由低速移动和可验收建图的分层：相机首帧、雷达 fresh、地图记录和地图画面只决定建图验收，不阻塞低速自由移动入口。
- 修改 `pc-tools/workstation/test/App.test.ts`：
  - 补强 live 形态回归：旧 `readback_summary.free_roam.mapping_ready=true`、`mapping_missing=not_loaded` 时，普通首屏仍必须按新 safe boundary 显示相机首帧和地图记录缺口。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：
  - 记录 PC 首屏优先消费 safe boundary 建图 readiness 的产品口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "splits free movement from mapping acceptance"`
- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "free-roam|free movement|mapping acceptance|自由移动|建图验收"`
- 通过：`cd pc-tools/workstation && npm test`（312 tests）
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`git diff --check`
- 通过：只读 live summary `GET http://127.0.0.1:7001/api/robot-control/summary?robotApiBaseUrl=http://192.168.1.11:8787`：
  - `free_roam_autonomy=start_ready`
  - `free_roam_motion_start_ready=true`
  - `free_roam_mapping_ready=false`
  - `free_roam_mapping_missing_reasons=[camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview]`
  - `camera.source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `nav2.goal_execution_status=goal_succeeded` 但 `wheel raw L/R=0/0`

## 剩余风险

- 本轮未发送真实自由移动、键盘手控、Nav2 或底盘命令；真实运动仍需要现场 operator 明确安全确认。
- 当前 live 相机仍是 UVC 无首帧，雷达/地图 freshness 仍需继续恢复；这不阻塞低速自由移动，但仍阻止“可验收建图”收口。
- Nav2 的软件 action 已成功且看到非零底盘命令计数，但底盘 wheel raw L/R 仍未非零，真实走动还需要现场安全确认后重跑运动验证。

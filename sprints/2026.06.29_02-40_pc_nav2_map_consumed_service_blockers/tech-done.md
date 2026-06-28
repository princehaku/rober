# 2026-06-29 02:40 PC Nav2 地图消费与路径服务根因

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `STATUS_KEYS` 增加 `latest_map_consumed`、`latest_path_generation_attempted`、`latest_path_generation_service_available`、`latest_path_generation_service_name`。
  - 当 live Nav2 只读状态显示地图未消费、路径服务不可用或路径生成未真正开始时，合成 `current_blocker_reasons`。
  - 增加普通中文 blocker label：地图未被自动驾驶服务消费、路径生成服务不可用、路径生成还没真正开始。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `readback_summary.nav2` 增加对应四个只读字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自动驾驶当前事实直接显示这些 live 根因。
  - 下一步顺序增加“重新加载地图到自动驾驶服务”和“恢复路径生成服务”，避免只显示泛化“准备图上路线”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 PC summary 从 live readback 提取并合成新 blocker。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏展示 live 形态：未读到 `/scan`、未读到 `/amcl_pose`、缺 map->odom、地图未消费、路径服务不可用、路径生成未开始。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录本轮只读 Nav2 blocker 口径。

## 验证结果

- 通过：`ssh root@192.168.1.11 -p 37878` 只读 GET 复核：
  - `/api/nav2/status`：`latest_map_server_active=true`、`latest_amcl_active=true`、`latest_planner_active=false`、`latest_controller_active=false`、`latest_map_consumed=false`、`latest_path_generation_service_available=false`、`latest_path_generation_attempted=false`
  - `/api/camera/health`：`source_first_frame_failed / first_frame_total_timeout / uvc_no_frame_not_exclusive`
  - `/api/radar/status`：latest proof stale，lifecycle stopped
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "current Nav2 blocker reasons"`
- 通过：`cd pc-tools/workstation && npm test -- --run`，2 个文件、358 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`

## 剩余风险

- 本轮只做只读诊断和 PC 文案，不启动 Nav2、不执行路线、不发送 manual/free-roam/keyboard/delivery/stop 或 `/cmd_vel`。
- 真实自动驾驶仍未恢复：live 仍显示 planner/controller inactive、地图未消费、路径服务不可用、路径生成未开始；需要现场安全确认后通过固定 PC 入口恢复服务、准备图上路线并复验 wheel raw L/R。

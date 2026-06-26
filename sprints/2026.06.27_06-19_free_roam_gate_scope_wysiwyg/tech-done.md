# 2026.06.27 06:19 Free Roam Gate Scope WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：给 `safe_command_boundary.free_roam_autonomy_gates[]` 增加可选 `scope` 字段，支持 `free_move_start`、`mapping_acceptance`、`runtime_diagnostic` 三类。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从上车端 runtime gates 生成 scope；自由移动 ready/start_ready 只看停止兜底是否未被显式阻塞，不再要求雷达 freshness、障碍距离、地图覆盖或运动发布诊断全 ready。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏把 gates 显示为“启动条件 / 建图验收 / 只读状态”。雷达、障碍、地图和相机类 gate 明确显示“只影响建图验收，不阻塞低速自由移动”。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：更新 free-roam readiness 与普通首屏断言，覆盖新分组文案。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：同步记录 2026-06-27 06:19 的 gate scope 分层。

## 验证结果

- `npm test -- --run test/catalog.test.ts`：通过，`113 passed`。
- `npm test -- --run test/App.test.ts`：通过，`150 passed`。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。
- 重启 `0.0.0.0:7001` 后确认 live summary：
  `free_roam_autonomy_start_ready=true`；
  `operator_confirmed/stop_available` 输出 `scope=free_move_start`；
  `lidar_fresh/obstacle_clear/mapping_active` 输出 `scope=mapping_acceptance`；
  `motion_hil_unlock` 输出 `scope=runtime_diagnostic`。当前 live 雷达过期和障碍距离只在建图验收 scope 内呈现，不再作为自由移动启动阻塞。

## 剩余风险

- 本轮仍不直接发车；只修正 PC summary/UI 对自由移动 gate 的所见即所得表达，避免继续把雷达/相机/建图验收误当成低速移动门禁。
- 当前现场摄像头仍是上游首帧失败，需要继续处理上位机 `/dev/video*` 出帧链路。
- 当前 Nav2 latest 仍是 action succeeded 但 wheel raw `L/R=0/0`，完整路线和 delivery success 不能验收为完成。

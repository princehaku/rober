# 2026.06.29 23:54 PC 自由移动和建图动作卡证据

sprint_type: micro

## 设计先行

本轮只补 PC 首屏动作卡的结构化只读证据，不新增控制入口。目标是让脚本和 DOM smoke 直接证明：自由移动可以先做，只依赖现场安全确认和停止兜底；相机首帧、雷达新鲜只影响建图启动和验收，不阻塞先低速自由移动。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlActionStatusCard.evidence`，增加自由移动和建图启动证据字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `free_move` 动作卡输出 `free_move_start_ready`、`free_move_safety_only`、停止兜底、相机/雷达不阻塞自由移动、固定 free-roam start 代理和建图缺口。
  - `mapping_start` 动作卡输出建图启动 ready、相机首帧/雷达新鲜要求和缺口数组。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通动作卡兼容旧 summary，从 `safe_command_boundary` 补自由移动/建图只读证据，并暴露对应 DOM `data-*` 属性。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 summary API 中 `free_move.evidence` 和 `mapping_start.evidence`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏 DOM 上能读到“相机/雷达不挡先动”和“建图启动缺相机首帧/雷达新鲜”。
- `pc-tools/README.md`
  - 同步记录只读字段合同和不发送控制命令边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`，1 passed / 167 skipped。
- 首次运行 `cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"` 失败，原因是旧 fixture 没有 `free_roam_mapping_start_missing_reasons`，前端 fallback 未从 `readback_summary.free_roam.mapping_start_missing` / 验收缺口推导建图启动缺口。
- 已修复旧 summary 兼容：前端 action card evidence 会从 `readback_summary.free_roam` 和验收缺口中补 `camera_first_frame,lidar_fresh`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 passed / 217 skipped。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，386 passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，只读 live spot check `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `free_move.evidence.free_move_start_ready=true`、`camera_blocks_free_motion=false`、`radar_blocks_free_motion=false`、`mapping_start.evidence.mapping_start_ready=false`、`mapping_start_missing_reasons=["camera_first_frame"]`。当前 live 说明雷达已不再是建图启动缺口，剩余卡点是相机首帧。

## 剩余风险

- 本轮只补只读合同和 DOM 验证；live spot check 只读 summary，不启动 free-roam、不启动建图、不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。
- 真实自由移动、相机首帧、雷达新鲜后建图启动仍需要现场安全确认和硬件复验。

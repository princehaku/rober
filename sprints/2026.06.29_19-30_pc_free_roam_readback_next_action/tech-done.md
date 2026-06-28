# 2026-06-29 19:30 PC 自由移动 Readback 下一步白话

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `readback_summary.free_roam` 新增 `next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 自由移动 readback 复用既有 `freeRoamAutonomyNextAction()`，让只读 summary 自身能说明下一步。
  - 当 `status=start_ready` 且建图验收 gate 未满足时，readback 直接给出“可先自由移动；建图验收还差哪些”。
  - fail-closed/default summary 也返回“先连接上车自由移动状态机，并确认停止兜底可用”，避免字段缺失。
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
  - 同步合同 fixture 和自由移动 readback 断言。
- `pc-tools/README.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录该字段的所见即所得语义和安全边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam"`
  - `npm --prefix pc-tools/workstation test`
  - `npm --prefix pc-tools/workstation run build`
- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam"` 结果：1 个测试文件通过，11 个测试通过。
- `npm --prefix pc-tools/workstation test` 结果：2 个测试文件通过，373 个测试通过。
- `npm --prefix pc-tools/workstation run build` 结果：TypeScript、Vite client build、server TypeScript 通过；Vite 仍提示 bundle chunk 超过 500 kB，属于既有构建提醒。
- 已重启 PC workstation API，`0.0.0.0:7001` 当前由 `npm run api` / `tsx src/server/index.ts` 监听。
- 只读 live 验证：
  - `curl -sS --max-time 22 http://127.0.0.1:7001/api/robot-control/summary`
  - `robot_api_connection.status=readable`
  - `readback_summary.free_roam.status=start_ready`
  - `readback_summary.free_roam.mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`
  - `readback_summary.free_roam.next_action_plain=当前处于停止请求；勾选现场安全确认后点击开始自由移动会先解除停止请求。勾选现场安全确认后可先自由移动；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面`
  - `safe_command_boundary.free_roam_motion_start_ready=true`
  - `safe_command_boundary.free_roam_mapping_ready=false`

## 剩余风险

- 本轮只补 PC summary/API 的只读下一步字段，不执行真实自由移动、不启动建图、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- live 仍需要现场安全确认后才能启动自由移动；建图验收仍依赖摄像头首帧、雷达新鲜、地图记录和地图画面。

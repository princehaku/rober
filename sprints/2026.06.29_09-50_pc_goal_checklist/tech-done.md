# PC 本轮目标检查清单

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlGoalChecklistItem` 和 `RobotControlSummaryResponse.goal_checklist`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从同轮 `action_status_cards`、`readback_summary` 和 `safe_command_boundary` 生成 7 项只读目标清单：
    画面所见即所得、地图所见即所得、雷达点贴到地图、完整行程执行、键盘连续手控、自由自助移动、传感器 ready 后建图。
  - 修正地图可见判定：`地图画面已读到` 与 `地图画面已显示` 都算当前地图可见。
  - 清单普通读数不泄露 `raw`、`marker`、`overlay` 或内部枚举 token；运动项的 `ready/待安全确认` 不写成完成。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏新增“本轮目标检查”，直接显示每项目标状态、读数和下一步。
- `pc-tools/workstation/src/styles.css`
  - 增加目标检查清单的紧凑响应式样式。
- `pc-tools/workstation/test/catalog.test.ts`
  - 验证 summary 返回 7 项 `goal_checklist`，并验证普通字段不包含 `marker/overlay`。
- `pc-tools/workstation/test/App.test.ts`
  - 验证普通首屏渲染 7 项目标检查，并验证键盘/自由移动不会被误显示为完成。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步记录 `goal_checklist[]` 的合同和无控制边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`
  - `npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`
  - `npm --prefix pc-tools/workstation test`
  - 结果：`2 passed`、`376 passed`
  - `npm --prefix pc-tools/workstation run build`
  - 结果：通过；仅保留既有 Vite chunk size warning。
- 运行验证：
  - PC API 已用新代码重启到 `HOST=0.0.0.0 PORT=7001`；实际监听 `*:7001` 的 Node PID 为 `881`。
  - 只读 `GET http://127.0.0.1:7001/api/health` 通过，schema 为 `trashbot.pc_tools_workstation.health.v1`。
  - 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 通过，返回 7 项 `goal_checklist`：
    `camera_wysiwyg`、`map_wysiwyg`、`radar_map_points_wysiwyg`、`nav2_route_execution`、
    `keyboard_continuous_control`、`free_move`、`mapping_start`。
  - live checklist 中 `free_move.status=needs_safety_confirm`、`nav2_route_execution.status=needs_safety_confirm`，
    JSON 不包含 `raw`、`marker` 或 `overlay`。

## 剩余风险

- 本轮只新增只读目标检查清单，不执行真实 Nav2、键盘连续手控、自由移动或建图。
- 完整目标仍需要现场安全确认后，继续做实车执行和 HIL 验证。

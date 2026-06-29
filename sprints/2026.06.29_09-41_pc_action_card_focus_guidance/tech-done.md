# PC 动作状态卡聚焦引导

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `action_status_cards` 每张卡新增“去处理”按钮。
  - 按钮只做本页 `scrollIntoView` 和 `focus`，把 operator 带到已有真实控件：共享画面、地图刷新、雷达处理、图上行程、键盘手控、自由移动或建图流程。
  - 运动相关卡片不会自动勾安全确认，不会自动点击控件，不会发送 manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
  - 给画面、雷达、地图面板补 `tabindex=-1` 和 ref，保证具体按钮 disabled 时仍能聚焦到对应区域。
- `pc-tools/workstation/src/styles.css`
  - 给状态卡引导按钮补紧凑宽度样式。
- `pc-tools/workstation/test/App.test.ts`
  - 验证 7 张动作卡都有引导按钮。
  - 验证点击自由移动/行程卡只改变焦点，不增加 fetch 调用。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步记录动作状态卡引导按钮的无控制边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`
  - 结果：`1 passed | 214 skipped`
  - `npm --prefix pc-tools/workstation test`
  - 结果：`2 passed`、`376 passed`
  - `npm --prefix pc-tools/workstation run build`
  - 结果：通过；仅保留既有 Vite chunk size warning。
- 运行验证：
  - PC API 已用新代码在后台启动：`HOST=0.0.0.0 PORT=7001`；实际监听 `*:7001` 的 Node PID 为 `94193`。
  - 只读 `GET http://127.0.0.1:7001/api/health` 通过，schema 为 `trashbot.pc_tools_workstation.health.v1`。
  - 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 通过，返回 7 张动作状态卡：
    `camera_preview`、`map_preview`、`radar_map_points`、`nav2_route`、`keyboard_control`、`free_move`、`mapping_start`。
  - live summary 中 `free_move.status=start_ready`、`nav2_route.status=ready_needs_wheel_rerun`，状态卡 JSON 不包含 `marker` 或 `overlay`。

## 剩余风险

- 本轮只改善普通首屏“下一步在哪里”的可用性，不执行真实运动验证。
- 完整目标仍需要现场安全确认后再验证 Nav2 完整路线、键盘连续手控、自由移动、建图启动和真实地图/画面/雷达 WYSIWYG。

# PC 现场验收主入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-field-acceptance-packet` 顶部新增 `plain-field-acceptance-primary`，把当前 `field_acceptance_next_step_id` 直接压成一个主入口。
  - 新增“去处理下一步”按钮：只聚焦到对应卡片和具体落点，例如行程安全确认、键盘启用、自由移动安全确认或建图启动卡片；不发送任何控制请求。
  - 新增“只读读回”按钮：复用既有 `refreshLiveMotionRunbookReadback`，只刷新对应验收端点，不执行 Nav2/manual/keyboard/free-roam/建图/delivery/stop。
  - 每个步骤补充 `data-focus-target-kind`，现场脚本不用猜按钮最终落点。
- `pc-tools/workstation/src/styles.css`
  - 新增主入口横条样式，保持普通首屏紧凑。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖主入口文案、endpoint、focus-only/readback-only 边界，以及点击“去处理下一步”不会增加 fetch 调用。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `plain-field-acceptance-primary` DOM 合同和 no-motion 边界。

## 验证结果

- 已通过：`git diff --check`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示单 bundle 超过 500 kB，这是既有体积警告，不影响本轮验收。
- 已通过：`cd pc-tools/workstation && npm test`，3 files / 421 tests passed。
- 已通过：重启 PC workstation 到 `0.0.0.0:7001`，新 listener PID `41656`。
- 已通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`field_acceptance_packet.next_step_id=run_nav2_route`、`next_step_start_endpoint=/api/robot-control/nav2/goal/execute`、`next_step_sends_motion=true`、`next_step_requires_safety_confirm=true`、`ready_step_ids=[run_nav2_route,hold_keyboard,start_free_move]`、`blocked_step_ids=[start_mapping_when_sensors_ready]`、`field_acceptance_packet.sends_motion_when_clicked=false`、`starts_nav2_when_clicked=false`。
- 已通过：只读检查 `http://127.0.0.1:7001/assets/index-Dk101C3Y.js`，bundle 包含 `plain-field-acceptance-primary`、`只读读回` 和 `data-readback-refresh-sends-motion`。

## 剩余风险

- 本轮仍未发真实运动命令；Nav2 路线、键盘连续手控、自由移动和建图需要现场安全确认后实测。
- 当前只读 summary 显示建图仍受相机首帧阻塞；自由移动不受相机阻塞，但真实启动需要 operator 现场确认安全后点击。

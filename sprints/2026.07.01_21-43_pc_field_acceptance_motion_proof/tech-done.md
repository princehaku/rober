# PC 现场运动验收清单

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 `plain-field-acceptance-packet` 顶部新增 `plain-field-acceptance-motion-proof`。
  - 把完整行程、键盘连续手控、自由自助移动三项运动验收压成现场可读清单，直接显示还差哪些证据。
  - DOM 暴露三项只读验收端点、行程成功 marker、ready/incomplete action ids 和 safety-only 最小预检边界。
  - 该清单固定 `data-sends-motion-when-clicked=false`，不执行 Nav2、manual、keyboard、free-roam、建图、delivery 或 stop。
- `pc-tools/workstation/src/styles.css`
  - 增加现场运动验收清单和单项证据 chip 的紧凑样式。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖运动验收清单的可见文案、data 合同、三项 row 状态和不发车边界。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `plain-field-acceptance-motion-proof` 产品合同。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`，`Tests 233 passed (233)`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`，`Tests 190 passed (190)`。
- 通过：`git diff --check`。
- 通过：`npm --prefix pc-tools/workstation run lint`。
- 通过：`npm --prefix pc-tools/workstation run build`。
  - Vite 仍提示单 chunk 超过 500 kB 的既有 warning，构建成功。
- 通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`，`Tests 423 passed (423)`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，新监听 PID `97464`。
- 通过：只读 smoke `GET /` 和 `GET /map` 均返回 200。
- 通过：只读 summary smoke `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `status=needs_wheel_rerun`。
  - `field_acceptance_next_step_id=run_nav2_route`。
  - `field_acceptance_ready_step_ids=[run_nav2_route,hold_keyboard,start_free_move]`。
  - `field_acceptance_blocked_step_ids=[start_mapping_when_sensors_ready]`。
  - `minimal_precheck_safety_only=true`。
  - 当前真实读数：`route_ready_on_map=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero_proven=false`、`route_delivery_success=false`、`keyboard_continuous_ready=true`、`free_move_start_ready=true`、`mapping_start_ready=false`。

## 剩余风险

- 本轮只改 PC 现场验收清单和只读 DOM 合同，没有执行 Nav2、manual、keyboard、free-roam、建图、delivery 或 stop。
- 完整目标仍未硬件闭环：同窗口 wheel L/R 非零、delivery success、键盘按住窗口轮速/松开停稳、自由移动运行读数和建图启动仍需要现场安全确认后的实机复验。

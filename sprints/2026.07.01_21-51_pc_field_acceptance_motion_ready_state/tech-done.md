# PC 现场运动三项 Ready 状态

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-field-acceptance-motion-proof` 增强当前真实状态提示：当完整行程、键盘连续手控、自由移动三项都 ready 时，清单直接显示“行程可复验”。
  - 勾安全确认前提示先勾安全确认，再去行程卡执行；勾选后提示去行程卡执行，之后只读回行程、轮速和送达。
  - DOM 新增当前缺口、下一模式、送达下一步、行程 safety-ready、键盘运动/停稳、自由移动运行读数等 data 字段。
- `pc-tools/workstation/test/App.test.ts`
  - 新增三项 ready 场景测试，模拟真实当前 summary：`run_nav2_route`、`hold_keyboard`、`start_free_move` 均 ready，建图 blocked。
  - 验证主项回到 `run_nav2_route`，勾安全确认只改变本地 UI，不发任何请求。
- `docs/product/pc_tools_workstation.md`
  - 同步记录三项 ready 时的现场验收合同。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`，`Tests 234 passed (234)`。
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`，`Tests 190 passed (190)`。
- 已通过：`git diff --check`。
- 已通过：`npm --prefix pc-tools/workstation run lint`。
- 已通过：`npm --prefix pc-tools/workstation run build`。
  - Vite 仍提示单 chunk 超过 500 kB 的既有 warning，构建成功。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`，`Tests 424 passed (424)`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，新监听 PID `9994`。
- 已通过：只读 smoke `GET /` 和 `GET /map` 均返回 200。
- 已通过：只读 summary smoke `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `status=needs_wheel_rerun`。
  - `field_acceptance_next_step_id=run_nav2_route`。
  - `field_acceptance_ready_step_ids=[run_nav2_route,hold_keyboard,start_free_move]`。
  - `field_acceptance_blocked_step_ids=[start_mapping_when_sensors_ready]`。
  - `minimal_precheck_safety_only=true`。
  - 当前真实读数：`route_ready_on_map=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero_proven=false`、`route_delivery_success=false`、`keyboard_continuous_ready=true`、`keyboard_continuous_motion_verified=false`、`free_move_start_ready=true`、`free_roam_motion_ready=false`、`mapping_start_ready=false`、`mapping_start_missing_reasons=[camera_first_frame]`。

## 剩余风险

- 本轮没有执行任何 Nav2、manual、keyboard、free-roam、建图、delivery 或 stop。
- 完整目标仍未实机闭环：同窗口 wheel L/R 非零、delivery success、键盘按住窗口轮速/松开停稳、自由移动运行读数和相机首帧仍需现场安全确认与硬件恢复后复验。

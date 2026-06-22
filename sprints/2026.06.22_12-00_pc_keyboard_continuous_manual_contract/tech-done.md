# sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts` 新增 Robot Control 键盘连续手控合同字段：
  - `keyboard_control=bounded repeating manual pulse gated`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `keyboard_jog_interval_ms=260`
  - `keyboard_jog_duration_ms=240`
  - `keyboard_stop_triggers=[key_released, window_blur, page_hidden, direction_changed, button_stop]`
  - `keyboard_reuses_manual_gate=true`
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 改为从 summary 读取 keyboard pulse interval/duration，并在默认关闭的高级诊断中展示 keyboard mode、stop triggers 和固定 proxy endpoint。
- `pc-tools/workstation/src/shared/contracts.ts` 补齐 `safe_command_boundary` 类型字段。
- `pc-tools/workstation/test/catalog.test.ts` 新增断言，锁住键盘连续手控合同，同时确认 `keyboard_control_enabled=false`、`safe_to_control=false`、`delivery_success=false` 不变。
- `docs/product/pc_tools_workstation.md` 同步说明 PC 键盘连续手控是受限 repeating manual pulse，不是 O7/cloud/primary keyboard control 放开。

## 验证结果

- `cd pc-tools/workstation && npm test` 通过，99 tests。
- `cd pc-tools/workstation && npm run lint` 通过。
- `cd pc-tools/workstation && npm run build` 通过。
- `git diff --check` 通过。
- 重启本机 `npm run api` 后，`GET http://127.0.0.1:8787/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回：
  - `keyboard_control=bounded repeating manual pulse gated`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `keyboard_jog_interval_ms=260`
  - `keyboard_jog_duration_ms=240`
  - `keyboard_reuses_manual_gate=true`
  - `keyboard_control_enabled=false`
  - `safe_to_control=false`
  - `delivery_success=false`

## 剩余风险

- 本轮锁住的是 PC 端连续键盘手控合同和 UI 展示；未在真实上车机上执行键盘长按 smoke，避免在缺现场 operator 明确确认时触发连续底盘运动。
- 真实键盘手控仍依赖上位机 operator report 材料 gate；当前若材料不齐，前端会 blocked，不会调用远端 `/api/base/manual`。

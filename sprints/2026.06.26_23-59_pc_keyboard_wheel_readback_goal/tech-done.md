# 2026.06.26 23:59 PC 键盘手控轮速证据收口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `wheel raw L/R 非零` 目标新增键盘 manual pulse 证据来源：当最近一次键盘连续手控回包带 `wheel_feedback_lr_nonzero_proven=true` 或 `wheel_feedback_nonzero_observed=true` 时，目标清单显示本轮键盘手控已读到非零 L/R。
  - 键盘已可用但 wheel raw 仍未完成时，键盘面板、本轮进度和键盘目标下一步都提示 `按住方向键读取非零 L/R 并连续验证`。
  - 该变更只消费已返回的固定 `/api/robot-control/base/manual` 回包，不自动启用键盘、不自动按键、不新增控制通道。
- `pc-tools/workstation/test/App.test.ts`
  - 更新键盘可用但当前 L/R=0/0 的提示断言。
  - 新增回归：键盘 pulse 回包带非零 L/R 时，wheel raw 目标变为完成；PC 键盘连续手控仍需连续脉冲和 stop 收口。
- `docs/product/pc_tools_workstation.md`
  - 同步记录键盘 pulse 非零 L/R 计入 wheel raw 目标的产品口径和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "keyboard"`：1 file passed，12 passed，108 skipped。
- `npm test -- test/App.test.ts`：1 file passed，120 passed。
- `npm test`：2 files passed，216 passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB，这是既有打包提示。
- `npm run lint`：通过。
- `git diff --check`：通过。
- Live 7001 重启验证：
  - `npm run api` 输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
- Live 上位机只读验证：
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `connection=readable`、`keyboard_mode=bounded_repeating_manual_pulse`、`keyboard_reuses_manual_gate=true`、`manual_entry=controlled_jog_requires_safety_confirmation_only`。
  - 同一 summary 返回 `safe_to_control=false`、`delivery_success=false`、当前 wheel `L/R=0/0`、`wheel_nonzero=false`、`feedback_ack=t1001_observed`。
  - free roam runtime 仍为 `state=locked`、`artifact_only=true`、`cmd_vel_publish_enabled=false`。
  - `POST /api/robot-control/base/feedback-samples?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=samples_forwarded`、`robot_control_executed=false`、`sends_motion_commands=false`、`t1001_observed_count=3`、`wheel_feedback_latest_left_speed=0`、`wheel_feedback_latest_right_speed=0`、`wheel_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 当前 live 上位机最近只读 wheel 仍为 `L/R=0/0`，本轮代码只让真实键盘手控回包中的非零 L/R 能被目标进度正确识别，不伪造非零证据。
- 仍需要现场按住键盘/WASD 产生真实 `command_forwarded` 和非零 T1001 L/R 回包，才能完成 wheel raw 与 PC 键盘连续手控 HIL 证据。
- 完整 Nav2 路线执行、delivery success 和自动扫地式自由跑动仍未在 live HIL 中证明完成。

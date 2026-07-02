# Current Keyboard Action Alias

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 `current_keyboard_action_*`，直接表达键盘连续手控的当前动作、入口、停止口、读回端点、缺口、安全边界和按住合同。
- 新字段区分 `current_keyboard_action_enable_sends_motion=false` 与 `current_keyboard_action_hold_sends_motion=true`：点击启用键盘不发车，只有按住 W/A/S/D 或方向键才发送低速脉冲。
- 普通 PC 页面 `plain-keyboard-hold-gate` 优先消费 `current_keyboard_action_*`，并在 DOM 暴露当前动作、读回端点、required markers、post-hold 读回序列和按住合同。
- 旧 `keyboard_*` endpoint/readback 字段复用同一组常量，避免 summary、UI 和现场 curl 口径漂移。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run App.test.ts`：1 个测试文件、237 个用例通过。
- `npm test -- --run robotControlSummary.test.ts catalog.test.ts`：2 个测试文件、191 个用例通过。
- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：3 个测试文件、428 个用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `11702`。
- `GET http://127.0.0.1:7001/` 返回 HTTP 200。
- `GET http://127.0.0.1:7001/map` 返回 HTTP 200。
- 真实 summary smoke：
  - `current_keyboard_action_id=hold_keyboard`
  - `current_keyboard_action_ready=true`
  - `current_keyboard_action_start_endpoint=/api/robot-control/base/manual`
  - `current_keyboard_action_stop_endpoint=/api/robot-control/base/stop`
  - `current_keyboard_action_acceptance_endpoints=[base feedback samples, summary]`
  - `current_keyboard_action_enable_sends_motion=false`
  - `current_keyboard_action_hold_to_move_required=true`
  - `current_keyboard_action_hold_sends_motion=true`
  - `current_keyboard_action_pulse_interval_ms=260`
  - `current_keyboard_action_pulse_duration_ms=240`
  - `current_keyboard_action_stop_triggers=[key_release, window_blur, page_hidden, direction_change, stop_button]`
  - `current_keyboard_action_post_hold_readback_endpoints=[base feedback samples, summary]`
  - `current_keyboard_action_post_hold_feedback_readback_required=true`
  - `current_keyboard_action_post_hold_summary_refresh_required=true`
  - `keyboard_continuous_ready=true`
  - `keyboard_continuous_motion_verified=false`
  - `current_free_move_action_ready=true`
  - `mapping_start_ready=false`
  - `camera_current_visible=false`

## 剩余风险

- 本轮只补 summary/UI 合同，不执行任何 motion/control POST。
- 完整 Nav2 路线的同窗口 wheel L/R 非零、送达确认、PC 键盘连续手控和自由移动真实运动仍需要现场安全确认后验收。
- 相机 WYSIWYG 仍受 USB 12M full-speed / 首帧不可见影响；需要现场换高速 USB/线/供电 Hub 后复测。

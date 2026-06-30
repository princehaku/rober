# PC 键盘动作卡连续手控实时验收字段

sprint_type: micro

## 实际改动

- `keyboard_control` action card evidence 新增键盘连续手控实时验收字段：入口 ready、是否 enabled、是否 armed、按住时是否会发低速 pulse、当前方向、当前按住 pulse 数、最佳连续 pulse 数、最小验收 pulse 数、连续 pulse 是否达标、是否要求 stop 收口、stop 是否已收口、键盘手控是否完整验证。
- 普通首屏 `plain-action-status-card-keyboard_control` 同步新增对应 `data-keyboard-*` DOM 字段，现场脚本不用进入键盘面板即可验收 PC 键盘连续控制状态。
- 保持安全边界不变：点击启用不发车，只有按住方向键/WASD 才会连续发低速 pulse；本轮不发送任何真实运动命令。
- 更新 README、PC 工作站产品文档和测试。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过。
- `npm test -- test/App.test.ts -t "keeps keyboard pulses continuous when summary refresh stalls during hold"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`：通过。
- `npm test -- --run`：通过，2 个测试文件、397 个测试全部通过。
- `npm run lint`：通过，0 errors；仍有既有 4 个 Vue 换行 warning，未新增功能性失败。
- `npm run build`：通过，生成 `dist/assets/index-Mq1QawP4.js`。
- `git diff --check`：通过。
- Live 7001 验收：重启 `npm run api` 后 `node` 监听 `0.0.0.0:7001`，PID `56661`；`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `keyboard_control.evidence.keyboard_start_ready=true`、`keyboard_enabled=false`、`keyboard_armed=false`、`keyboard_sends_motion_while_held=false`、`keyboard_current_direction=none`、`keyboard_current_hold_pulse_count=0`、`keyboard_best_continuous_pulse_count=0`、`keyboard_verified_min_forwarded_pulses=2`、`keyboard_continuous_pulse_verified=false`、`keyboard_stop_required_after_hold=true`、`keyboard_stop_settled_after_pulse=false`、`keyboard_motion_verified=false`。
- 前端产物验收：构建后的 `dist/assets/index-Mq1QawP4.js` 包含 `data-keyboard-motion-verified`、`data-keyboard-current-hold-pulse-count`、`data-keyboard-sends-motion-while-held`，页面 DOM 合同随构建产物发布。

## 剩余风险

- 本轮没有发送真实键盘、manual、free-roam、Nav2、delivery、stop 或 `/cmd_vel` 运动命令；动作卡只证明初始未 armed/未发车和 DOM/summary 合同可观测。
- 真实“按住方向键连续 pulse、松开后 stop 收口、wheel raw L/R 非零”仍需要现场安全确认后执行硬件 smoke。
- 工作区仍保留历史遗留的两个 artifact 脏文件，本轮未修改、未纳入提交。

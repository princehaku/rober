# 2026.07.01 09:23 PC 键盘连续控制专项读回

## sprint_type

micro

## 实际改动

- 在 PC 普通首屏动作清单顶部新增 `plain-live-keyboard-control-readback`。
- 该读回条直接显示键盘连续控制是否 ready/verified、启用是否发车、是否必须按住、最佳连续 pulse 数、同窗口 wheel L/R 和 stop 收口状态。
- 新增 `plain-live-keyboard-control-readback-refresh`，只读回 `/api/robot-control/base/feedback-samples` 与 `/api/robot-control/summary`。
- DOM 明确声明该按钮不执行 Nav2、不发送 manual、不启用 keyboard、不启动 free-roam/map runtime、不提交 delivery、不 stop、不发送 motion。
- 更新 PC 工作站产品边界文档，记录键盘连续控制专项读回合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 file passed，1 test passed，230 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning；当前产物为 `dist/assets/index-C0Osj05w.js` 与 `dist/assets/index-7krFlZYN.css`。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `0.0.0.0:7001`，`GET http://127.0.0.1:7001/map` 返回 `200 OK`。
- 通过：构建产物包含 `plain-live-keyboard-control-readback`、`键盘连续控制`、`启用本身不发车` 和 `读回键盘`。
- 通过：只读 `GET /api/robot-control/summary?robot_api_base_url=http://192.168.1.11:8787` 返回 `keyboard_continuous_control_ready=true`、`keyboard_enabled=false`、`keyboard_motion_verified=false`、`keyboard_best_continuous_pulse_count=0`、`keyboard_verified_min_forwarded_pulses=2`、`wheel_lr_nonzero=false`、`wheel_left=0`、`wheel_right=0`。

## 剩余风险

- 当前改动是 PC 只读 UI/DOM 合同；键盘连续控制真实闭环仍需要现场勾选安全确认后按住 W/A/S/D 或方向键，并读到同一次按住窗口 wheel L/R 非零与 stop 收口。
- 本轮未发送 manual pulse、未启用键盘、未执行 Nav2/free-roam/map start/delivery/stop。

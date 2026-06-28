# PC Keyboard Continuous Control Plain Summary

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `readback_summary.keyboard` 增加 `readiness_plain` 与 `continuous_control_contract_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把键盘可启用状态、启用不发车、按住才移动、ROS 低速脉冲节奏和停止触发压成两句只读白话。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补齐默认夹具和 Robot Control summary 回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录只读 summary 合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`：通过，1 个文件，38 个测试通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `readback_summary.keyboard.status=start_ready`、`readiness_plain=可启用键盘；启用本身不发车，按住方向键/WASD 才连续低速移动。`、`continuous_control_contract_plain=按住时约每 0.26 秒发送一次 0.24 秒 ROS 低速脉冲；松开、失焦、切页、换方向或点击停止都会停。`，同时 `safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 PC 只读字段，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。
- 键盘连续控制的真实运动仍需要现场勾选安全确认、显式启用键盘并按住方向键/WASD。

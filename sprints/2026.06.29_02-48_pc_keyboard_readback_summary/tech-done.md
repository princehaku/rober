# PC keyboard readback summary

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary.readback_summary` 新增 `keyboard` 区块。
- `readback_summary.keyboard` 直接返回：
  - 连续手控模式 `bounded_repeating_manual_pulse`
  - ROS 手控入口 `manual_command_mode=ros`
  - PC manual/stop 代理路径
  - `start_ready=true`、`enabled=false`
  - 按住才移动、松开/失焦/切页/换方向/停止都会停、脉冲节奏和最小门禁白话
- 外部脚本只读 `readback_summary` 时，也能直接理解键盘连续控制，不必从 `safe_command_boundary` 拼字段。
- `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`
  - `Test Files 1 passed (1)`
  - `Tests 38 passed | 120 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仅输出 chunk size warning，构建成功。
- 通过：7001 只读 summary 验证。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001 (LISTEN)`。
  - `GET /api/robot-control/summary` 返回 `readback_summary.keyboard.status=start_ready`、`control_mode=bounded_repeating_manual_pulse`、`manual_command_mode=ros`、`start_ready=true`、`enabled=false`。
  - 同一响应显示 `keyboard_control_enabled=false`、`manual_control_enabled=false`、`command_dispatch_enabled=false`、`safe_to_control=false`、`robot_control_executed=false`，确认本轮验证未执行真实控制动作。

## 剩余风险

- 本轮只补只读 summary 字段，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实键盘连续控制 HIL 验证。

# PC 手控最小安全确认 Micro Sprint

## sprint_type

micro

## 实际改动

- 将 PC 普通首屏手控 gate 收敛为最小安全确认：勾选“人在旁边、周围安全、停止手段就绪”或扫图卡片同等确认后即可启用键盘连续手控。
- `POST /api/robot-control/base/manual` 不再为了普通手控额外读取 `/api/operator/report`；响应记录 `operator_report_preflight.status=not_required_for_confirmed_manual`。
- 保留固定安全边界：只走 `/api/base/manual`，方向枚举固定，速度 `<=0.12 m/s`，时长 `<=800 ms`，stop 仍随时可用，顶层 `safe_to_control=false`、`robot_control_executed=false` 不变。
- “移动/导航”卡片顶部新增普通安全确认 checkbox，避免用户为了启用键盘到行程卡片里找确认项。
- 更新 PC 工作站和扫地式建图文档，明确 operator report、轮速非零、LiDAR delta 仍是证据/验收流程，但不再阻塞普通低速手控入口。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、154 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 和 `vite build` 通过。
- 通过：`git diff --check`。
- 通过：7001 HTTP summary smoke，`non_stop_requires_operator_report_preflight=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`safe_to_control=false`、`robot_control_executed=false`。
- 通过：7001 DOM smoke，只勾选 `plain-motion-safety-confirm`，未点击启用键盘、未按方向键；异步稳定后 `启用键盘（按键才动）` 变为 enabled，live status 为 `未启用，先点启用键盘。`。

## 剩余风险

- 本轮只简化 PC 手控和键盘连续控制的预检，不等于完成无人值守自动扫图；自动扫图仍缺上车端 watchdog、LiDAR 避障、覆盖策略和 HIL 证据。

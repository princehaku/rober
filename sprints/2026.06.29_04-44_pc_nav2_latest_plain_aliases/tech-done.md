# PC Nav2 Latest Plain Aliases

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- started_at: 2026-06-29 04:44 CST
- status: done

## 实际改动

- 扩展 PC Node 只读 `GET /api/robot-control/nav2/goal/execution/latest` 响应合同，新增顶层 `execution_status_plain`、`next_action_plain`、`goal_execution_base_feedback_latest_raw_left/right`。
- 后端 latest 代理复用最近 Nav2 execution artifact 的解析结果，把完整路线证明、wheel raw L/R 未非零、下一步重跑模式直接变成普通可读字段。
- 前端本地 latest fallback 补齐同一组字段，避免网络失败时页面或类型检查出现空洞。
- 补充 catalog 回归，锁定 latest 代理不会重放 Nav2、不会调用 `/api/base/manual`，且能在已证明、未证明、PWM 重跑诊断三类结果中返回顶层白话和 raw L/R。
- 同步 `docs/product/pc_tools_workstation.md`，说明该 latest 入口仍是只读诊断，不执行 Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2 latest execution proxy"`：通过，4 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个测试文件、375 个测试通过。
- 重启 PC API 到 `0.0.0.0:7001` 后执行只读 `GET /api/robot-control/nav2/goal/execution/latest`：通过，返回 `execution_status_plain=上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零...`、`next_action_plain=勾选行程前安全确认后用 ROS 模式重跑图上路线...`、`goal_execution_base_feedback_latest_raw_left/right=0/0`、`robot_control_executed=false`。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只增强 PC Node latest 只读响应，不会真实证明小车已移动；完整 Nav2 路线执行和 wheel raw L/R 非零仍需现场勾选安全确认后由 operator 主动重跑验证。

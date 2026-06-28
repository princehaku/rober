# PC Keyboard Summary Plain Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- started_at: 2026-06-29 05:07 CST
- status: done

## 实际改动

- 扩展 Robot Control summary 的 `readback_summary.keyboard` 合同，新增顶层 `plain_hint`。
- `plain_hint` 合并“可启用键盘但启用本身不发车”和“必须按住 W/A/S/D 或方向键才连续低速移动”，让普通页面和现场脚本只读 summary 时能直接理解键盘连续手控口径。
- 保留既有 `readiness_plain`、`hold_to_move_plain`、`continuous_control_contract_plain`、`stop_triggers_plain`、`pulse_timing_plain` 和 `next_action_plain`，不改变前端键盘发脉冲逻辑。
- 补充 summary 回归测试与 App fixture，锁定 `plain_hint` 非空且不把键盘 enabled 或 robot_control_executed 置真。
- 同步 `docs/product/pc_tools_workstation.md`，说明该字段只读 summary，不启用键盘、不发送 manual、stop、Nav2、delivery、free-roam 或 `/cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies"`：通过，1 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个测试文件、375 个测试通过。
- 重启 PC API 到 `0.0.0.0:7001` 后执行只读 `GET /api/robot-control/summary`：通过，返回 `readback_summary.keyboard.plain_hint=可启用键盘...必须按住 W/A/S/D...`、`keyboard_control_enabled=false`、`readback_summary.keyboard.robot_control_executed=false`。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只增强 summary 的只读可读性；真实 PC 键盘连续手控仍需要现场勾选安全确认、点击启用键盘，并按住方向键/WASD 后由 operator 观察验证。

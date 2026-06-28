# 2026-06-29 19:50 PC 键盘 Teleop Alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `safe_command_boundary` 新增 `keyboard_teleop_start_ready`、`keyboard_teleop_status`、`keyboard_teleop_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新字段镜像既有 `keyboard_control_start_ready/status/next_action`，让外部脚本按 teleop 口径读取时也能得到连续手控下一步。
  - 该 alias 只说明“勾安全确认后启用键盘，按住才会连续低速移动，松开/失焦/切页会停”，不改变控制权限。
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
  - 同步合同 fixture 和 alias 断言。
- `pc-tools/README.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 teleop alias 的普通用户语义和安全边界。

## 验证结果

- 已执行：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "safe command boundary"`：pattern 未匹配，1 个文件 skipped，未作为有效覆盖。
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts`
  - `npm --prefix pc-tools/workstation test`
  - `npm --prefix pc-tools/workstation run build`
- `npm --prefix pc-tools/workstation test -- catalog.test.ts` 结果：1 个测试文件通过，158 个测试通过。
- `npm --prefix pc-tools/workstation test` 结果：2 个测试文件通过，373 个测试通过。
- `npm --prefix pc-tools/workstation run build` 结果：TypeScript、Vite client build、server TypeScript 通过；Vite 仍提示 bundle chunk 超过 500 kB，属于既有构建提醒。
- 已重启 PC workstation API，`0.0.0.0:7001` 当前由 `npm run api` / `tsx src/server/index.ts` 监听。
- 只读 live 验证：
  - `curl -sS --max-time 22 http://127.0.0.1:7001/api/robot-control/summary`
  - `robot_api_connection.status=readable`
  - `keyboard_control_start_ready=true`
  - `keyboard_control_status=start_ready`
  - `keyboard_teleop_start_ready=true`
  - `keyboard_teleop_status=start_ready`
  - `keyboard_teleop_next_action_plain=勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停`
  - `keyboard_control_enabled=false`
  - `robot_control_executed=false`

## 剩余风险

- 本轮只补 PC summary 的只读 alias，不启用键盘、不发送 manual pulse、不调用 stop、Nav2、free-roam、delivery 或 `/cmd_vel`。
- 真实 PC 键盘连续手控仍需要现场勾选安全确认后，由 operator 按住方向键验证。

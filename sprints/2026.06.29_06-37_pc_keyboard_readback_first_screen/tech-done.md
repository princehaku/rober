# PC 键盘 readback 首屏事实行

- sprint_type: micro
- 时间：2026-06-29 06:37 CST
- Owner：User Touchpoint Full-Stack Engineer（主会话执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘区新增 `键盘事实` 行，直接消费 `readback_summary.keyboard.plain_hint`、`hold_to_move_plain`、`continuous_control_contract_plain` 和 `stop_triggers_plain`。
  - 展示内容只来自只读 summary，明确“启用本身不发车、必须按住才连续低速移动、松开/失焦/切页/换方向/点击停止都会停”。
- `pc-tools/workstation/test/App.test.ts`
  - 在 `Robot Control V1` 首屏测试中锁定 `plain-keyboard-readback-summary`，避免后续退回分散提示或只在高级诊断中展示。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏键盘事实行的用户合同和控制边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`
  - 结果：1 个测试文件通过，1 个用例通过，214 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；保留既有 Vite chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`
  - 结果：2 个测试文件通过，375 个用例通过。
- 通过：重启 PC API 到 `0.0.0.0:7001`，实际监听 PID `92672`。
  - 只读 `GET /api/robot-control/summary` 结果：`readback_summary.keyboard.status=start_ready`、`enabled=false`、`start_ready=true`，并返回 `plain_hint`、`hold_to_move_plain`、`continuous_control_contract_plain`、`stop_triggers_plain`。

## 剩余风险

- 本轮不触发真实键盘运动，也不调用 manual/stop/Nav2/free-roam/delivery；真实连续手控仍需要现场 operator 勾安全确认并按住方向键验证。
- live 上位机仍可能受底盘反馈 `wheel raw L/R=0/0` 或相机 UVC 首帧失败影响；这不影响本轮首屏事实展示。

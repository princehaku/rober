# 2026-06-28 02:25 PC 键盘启用焦点可见性

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 点击“启用键盘”后，键盘控制框先 `scrollIntoView({ block: "center", behavior: "smooth" })` 再 `focus({ preventScroll: true })`。
  - 该行为只改变页面焦点和可见性，不发送 manual、stop、Nav2、free-roam、delivery 或 `/cmd_vel` 请求。
- `pc-tools/workstation/test/App.test.ts`
  - 在 PC 键盘连续手控主流程测试中断言启用键盘会滚动并聚焦键盘控制框，且原有不发 manual 请求的断言继续保留。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录“启用键盘后滚动到可见并聚焦”的普通用户体验口径。

## 验证结果

- `npm test -- --runInBand --testNamePattern "manual motion can be started without camera or radar and keyboard continuous control is verified"`：失败，当前 Vitest 版本不支持 `--runInBand`，这是命令参数问题，不是代码失败。
- `npm test -- -t "manual motion can be started without camera or radar and keyboard continuous control is verified"`：返回 0 但 331 条全部 skipped，测试名不匹配，未作为有效验证。
- `npm test -- -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`：通过，1 passed / 330 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：通过，2 files passed / 331 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001`：通过，`node` 监听 `*:7001`。
- 只读检查 `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，schema 为 `trashbot.pc_tools_workstation.robot_control_summary.v1`；`keyboard_control_start_ready=true`、`free_roam_motion_start_ready=true`、`nav2_goal_ready=false`；当前连接降级原因仍是 `camera_health/camera_devices fetch_timeout_2400ms`，相机诊断为 `uvc_no_frame_not_exclusive`，雷达 lifecycle 为 stopped 且 runtime scan stale。

## 剩余风险

- 本轮不发送真实运动命令；键盘连续手控的真实底盘轮速仍需要现场 operator 勾安全确认后按住方向键复验。
- 当前 live 相机仍可能处于 UVC 无首帧状态，雷达 lifecycle 也可能未运行；这不阻塞底盘试动或键盘低速手控，但会继续阻塞“可建图验收”。

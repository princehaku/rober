# PC Live Closure Wheel Rerun Minimal Precheck Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-summary` 和 `plain-live-closure-go` 新增 wheel rerun 专用最小预检 DOM 合同。
  - 明确同窗口轮速复验只要求现场安全确认；相机、雷达和路线 WYSIWYG 不作为 wheel rerun 发车前预检 blocker。
  - 当前卡点按钮继续只做页面聚焦，不执行 Nav2、不发送 manual/keyboard/free-roam/stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认卡点和 `needs_wheel_rerun` 两种状态下的新增字段。
  - 在 wheel rerun 用例里将相机/雷达 WYSIWYG 设为 false，锁定它们不阻断 wheel rerun 最小预检。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步 wheel rerun 安全-only 最小预检边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|keeps live closure wheel rerun as a focus-only Nav2 action"`：通过，2 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、398 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-BcIaMl2c.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：旧 `node` PID `95755` 已停止，新监听进程为 `node` PID `7831`，地址 `TCP *:7001`。
- 只读 smoke：`GET http://127.0.0.1:7001/` 已引用新 bundle；bundle 内命中 `data-wheel-rerun-minimal-precheck-safety-only`、相机/雷达/路线 WYSIWYG 预检 false 字段和 focus-only 字段；`GET /api/robot-control/summary` 返回当前 `live_status=needs_wysiwyg`、`minimal_precheck_safety_only=true`，本轮未发送任何 motion POST。

## 剩余风险

- 本轮只改 PC Web 显示和只读 DOM 合同，不执行真实 Nav2 wheel rerun。
- 当前 live 现场状态仍是 `needs_wysiwyg`，因此本轮 live smoke 没有在真实 summary 上看到 `needs_wheel_rerun=true`；wheel rerun 合同由 fixture 测试覆盖。

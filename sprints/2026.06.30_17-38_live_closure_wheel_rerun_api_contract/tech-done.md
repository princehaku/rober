# Live Closure Wheel Rerun API Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 新增轮速复验最小预检字段：`wheel_rerun_minimal_precheck_safety_only`、`wheel_rerun_safety_confirm_required`、`wheel_rerun_camera_preflight_required=false`、`wheel_rerun_radar_preflight_required=false`、`wheel_rerun_route_wysiwyg_preflight_required=false`、`wheel_rerun_blocked_by_camera_wysiwyg=false`、`wheel_rerun_blocked_by_radar_wysiwyg=false`、`wheel_rerun_command_mode` 和固定 `fixed_wheel_rerun_endpoint`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `buildLiveClosureSummary()` 输出上述 API 字段，让外部脚本只读 summary 时也能确认轮速复验只需要现场安全确认，不被相机、雷达贴图或路线 WYSIWYG 缺口额外阻塞。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 新增 builder 单测，模拟 Nav2 已成功但同窗口 wheel L/R 未非零，验证 API 字段为 safety-only 且固定 Nav2 execute endpoint。
- `pc-tools/workstation/test/App.test.ts`
  - fixture 同步补齐新合同字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 API 级 live closure 轮速复验最小预检合同。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、2 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、401 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Q7ojBxrt.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `52134`，新监听进程为 `node` PID `66033`，地址 `TCP *:7001`。
- live 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_closure_summary.status=needs_wheel_rerun`、
  `needs_same_window_wheel_rerun=true`、`wheel_rerun_minimal_precheck_safety_only=true`、
  `wheel_rerun_safety_confirm_required=true`、`wheel_rerun_camera_preflight_required=false`、
  `wheel_rerun_radar_preflight_required=false`、`wheel_rerun_route_wysiwyg_preflight_required=false`、
  `wheel_rerun_blocked_by_camera_wysiwyg=false`、`wheel_rerun_blocked_by_radar_wysiwyg=false`、
  `wheel_rerun_command_mode=ros`、`fixed_wheel_rerun_endpoint=/api/robot-control/nav2/goal/execute`、
  `sends_motion_when_clicked=false`。

## 剩余风险

- 本轮只补只读 API 合同，不自动执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实同窗口 wheel L/R 非零仍需要现场安全确认后重跑完整路线验证。

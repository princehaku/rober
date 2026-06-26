# PC 键盘 bounded pulse 边界所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘指南从只显示“约每多少秒续一次”，改为显示完整 bounded pulse 边界：续发间隔、单次脉冲时长、速度上限和后端单次时长上限。
  - 文案继续说明松开、窗口失焦或切页面都会停，避免把连续键盘手控误读成无限时长发车。
- `pc-tools/workstation/test/App.test.ts`
  - 更新键盘连续手控测试，锁定默认 live 边界 `0.26s / 0.24s / 0.12 m/s / 800ms` 在普通首屏可见。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 键盘连续手控是受限重复 manual pulse，不绕过安全确认，也不调用 Nav2、delivery、free-roam 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 153 passed (153)`
  - 首轮测试失败于普通首屏 forbidden token `速度`；已把文案收敛为 `最高 0.12 m/s` 后重跑通过。
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `68813` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`、`pc_only=true`。
  - `curl http://127.0.0.1:7001/api/robot-control/summary` 返回 live 键盘边界：`keyboard_control_mode=bounded_repeating_manual_pulse`、`keyboard_reuses_manual_gate=true`、`speed_limit_mps=0.12`、`duration_limit_ms=800`、`keyboard_jog_interval_ms=260`、`keyboard_jog_duration_ms=240`。

## 剩余风险

- 本轮只改普通首屏键盘指南文案，不执行真车键盘手控，不证明 wheel raw L/R 非零。
- live 当前 Nav2 仍是 action 成功但 HIL 轮速未证明；摄像头仍是非独占但无首帧。

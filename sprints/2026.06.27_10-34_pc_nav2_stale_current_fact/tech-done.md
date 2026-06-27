# PC Nav2：当前事实识别旧行程记录

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 首页当前事实中的 Nav2/行程行现在会对 `summary.readback_summary.nav2` 的 `generated_at_ms` 与 `response_generated_at_ms` 做新旧判断。
  - 当 summary 反复刷新旧 `goal_succeeded` artifact 时，当前事实显示“旧路线成功记录，反馈 N 次，约 X 小时前；需重新执行本轮行程”，不再只写“路线返回成功”。
  - 非旧记录仍保留原有 wheel raw L/R、底盘命令、下一次 `ros` 复验等诊断文案。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 summary 自身携带旧 Nav2 成功记录的用例，验证首页当前事实、地图行程标签和行程证据摘要口径一致，且不触发 Nav2、delivery、manual 或 `/cmd_vel`。

## 验证结果

- 已通过定向前端测试：
  - `npm test -- App.test.ts --testNamePattern "stale summary Nav2|summary latest Nav2|Nav2|current facts|行程"`
  - 结果：`Test Files 1 passed (1)`，`Tests 18 passed | 144 skipped (162)`。
- 已通过完整前端验证：
  - `npm run lint`
  - `npm run build`
  - `npm test`
  - `git diff --check`
  - 结果：lint 通过；build 通过（保留 Vite chunk size warning）；`Tests 283 passed (283)`；diff check 通过。
- 已重启 PC API：
  - 分步执行 `launchctl remove rober.pc.api.7001 || true`、清理 `/tmp/rober-pc-api-7001.*`、再 `launchctl submit -l rober.pc.api.7001 ... HOST=0.0.0.0 PORT=7001 npm run api`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
  - `/tmp/rober-pc-api-7001.out` 显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 已读 live summary：
  - Nav2：`status=goal_succeeded_wheel_feedback_not_proven`，`generated_at_ms=1782500121051`，`response_generated_at_ms=1782527749624`，`L/R=0/0`，下一次模式 `ros`。
  - 自由移动：`start_ready=true`，`mapping_missing=camera_first_frame,mapping_active,fresh_map_preview`。
  - 摄像头：`source_first_frame_failed`，共享预览不是独占，设备当前没人占用。

## 剩余风险

- 本轮没有真实重新执行 Nav2；live 仍需要现场安全确认后用 `ros` 模式重新执行并复验执行窗口 wheel raw L/R 非零。
- 当前 live 摄像头仍无首帧，自由移动仍只是 `start_ready=true`，尚未真实启动。

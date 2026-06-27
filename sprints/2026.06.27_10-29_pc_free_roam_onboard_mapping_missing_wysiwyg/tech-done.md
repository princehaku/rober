# PC 自由移动：上车端建图缺口所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `freeRoamMappingMissingPlainLabels` 支持上车端返回逗号字符串形式的 `mapping_missing`，并补齐 `camera_first_frame`、`mapping_active`、`fresh_map_preview` 等 live token 的普通中文翻译。
  - 自由移动/建图 readiness 优先消费 `readback_summary.free_roam.mapping_missing`；上车端明确给出建图缺口时，首页直接显示“上车端明确只按自由移动记录”，不再只靠 PC 本地推断相机/雷达状态。
  - 保持低速自由移动和可验收建图分层：上车端建图缺口只影响建图验收，不阻塞安全确认后的固定自由移动 start 入口。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 live 形状：`mapping_missing=camera_first_frame,mapping_active,fresh_map_preview` 时，普通首页显示“画面首帧未出、地图记录未启动、地图画面未刷新”，且不发送 manual、Nav2、delivery 或 `/cmd_vel`。

## 验证结果

- 已通过定向前端测试：
  - `npm test -- App.test.ts --testNamePattern "free-roam|free movement|mapping readiness|建图验收|自由移动"`
  - 结果：`Test Files 1 passed (1)`，`Tests 20 passed | 141 skipped (161)`。
- 已通过完整前端验证：
  - `npm run lint`
  - `npm run build`
  - `npm test`
  - `git diff --check`
  - 结果：lint 通过；build 通过（保留 Vite chunk size warning）；`Tests 282 passed (282)`；diff check 通过。
- 已重启 PC API：
  - `launchctl submit -l rober.pc.api.7001 ... HOST=0.0.0.0 PORT=7001 npm run api`
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
  - `/tmp/rober-pc-api-7001.out` 显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 已读 live summary：
  - `readback_summary.free_roam.start_ready=true`
  - `readback_summary.free_roam.mapping_ready=false`
  - `readback_summary.free_roam.mapping_missing=camera_first_frame,mapping_active,fresh_map_preview`
  - 摄像头仍为 `source_first_frame_failed`，共享预览不是独占；Nav2 仍为 `goal_succeeded_wheel_feedback_not_proven`，L/R=`0/0`。

## 剩余风险

- 本轮没有真实启动自由移动或建图，只改 PC 端 readiness 展示和测试。
- 当前 live 摄像头仍无首帧；即使自由移动可 start，本轮仍不能按可验收建图收口。
- 真实自由移动仍需要现场 operator 勾安全确认并保持停止兜底。

# PC 自动扫图雷达待刷新引导

## sprint_type

micro

## 背景

- 现场 7001 摘要显示 `lidar_running=true` 但 `latest_scan_fresh=false`，PC 首屏会进入 `雷达待刷新`。
- 自动扫图已经在逐步接入上车端状态机，但在 LiDAR proof stale 时，PC 必须先引导 operator 刷新雷达，而不是让按钮看起来像可以直接开始，或把 operator 带去无关手控步骤。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增自动扫图专用补证按钮文案：当上车端 `free_roam_autonomy=ready` 但 PC 侧证据缺失时，按钮显示具体下一步，例如 `刷新雷达后开始`。
  - 调整自动扫图 readiness 的禁用逻辑：地图刷新 pending 仍禁用等待；雷达 stale、未勾安全、未启动地图等可补救状态允许点击按钮做引导。
  - 新增自动扫图专用下一步焦点：地图记录和地图画面满足后，如果 LiDAR proof stale 或不完整，点击自动扫图按钮只聚焦 `刷新雷达`，不进入人工键盘引导。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `guides ready free-roam autonomy to refresh stale radar proof before starting`，覆盖 ready 自动扫图 + stale 雷达 proof 场景。
  - 断言点击按钮不会调用 `/api/robot-control/free-roam/autonomy/start`、manual、Nav2、delivery 或 `/cmd_vel`，只把焦点带到 `plain-radar-refresh`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 `刷新雷达后开始` 的用户流程和安全边界。
- 未改 Clash/system proxy；Node 仍要求使用本项目自身端口 `7001`。

## 验证结果

- `npm test -- -t "free-roam autonomy|stale radar|locked auto-sweep"`：通过，2 个 test file，10 passed，198 skipped。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 `Some chunks are larger than 500 kB` warning。
- `npm test`：通过，2 个 test file，208 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 进程监听 `TCP *:7001 (LISTEN)`。
- `curl http://127.0.0.1:7001/api/robot-control/summary` 摘要：`source_base_url=http://192.168.1.11:8787`、`safe_to_control=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`free_roam_autonomy=locked`、`lidar_running=true`、`latest_scan_fresh=false`。
- 验证中发现 `test/App.test.ts` 新 fixture 的 gate state 写成 `pending`，TypeScript 只允许 `ready/blocked/not_proven`，已改为 `not_proven` 并重跑通过。
- 全量测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，已用精确 patch 恢复，避免把测试副作用纳入本轮提交。

## 剩余风险

- 本轮是 PC 端 mock/单元验证，未做真实 WAVE ROVER / LiDAR HIL。
- 如果现场上车端 `free_roam_autonomy=ready` 与 LiDAR proof 状态不同步，PC 会继续 fail-closed，引导刷新雷达，不会直接 start。

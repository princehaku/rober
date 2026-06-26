# 2026-06-26 23:55 PC 自动扫图记录模式下一步提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `自动扫图准备` 增加 `自动扫图下一步` 文案，按连接、安全确认、地图记录、扫图画面、雷达和停止兜底顺序提示下一手动作。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当上车端 `free_roam_autonomy_runtime.artifact_only=true` 时，runtime 文案明确显示 `当前只是记录模式，不会自己跑`，避免把 locked/artifact-only 误读成真车自动扫图已运动。
- `pc-tools/workstation/test/App.test.ts`：更新扫地式建图/自动扫图回归，锁定未确认安全时下一步落到安全确认，ready 时下一步为 `点击开始自动扫图（低速）`。
- `docs/product/pc_tools_workstation.md`：同步记录该 UI 口径，并明确不修改 Clash 或系统代理配置，PC 入口仍为 `0.0.0.0:7001`。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "free-roam|sweep|扫图"`，15 tests passed。
- 已通过：`npm test -- test/App.test.ts`，118 tests passed。
- 已通过：`npm test`，214 tests passed。
- 已通过：`npm run build`；Vite 仍有既有 chunk size warning，但构建成功。
- 已通过：`npm run lint`。
- 已通过：`git diff --check`。
- 已通过：重启本机 `npm run api`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
- 已通过：live `GET http://127.0.0.1:7001/api/robot-control/summary` 可读，上位机来源为 `http://192.168.1.11:8787`，连接 `readable`。
- 已通过：live summary 读到 `free_roam_autonomy=locked`，runtime 为 `state=locked`、`reason=还未勾选现场安全确认`、`artifact_only=true`、`cmd_vel_publish_enabled=false`；gates 同时显示 `operator_confirmed=blocked`、`mapping_active=blocked`、`stop_available=ready`、`lidar_fresh=ready`、`motion_hil_unlock=blocked`。

## 剩余风险

- 本轮只把自动扫图 locked/artifact-only 的普通首屏下一步讲清楚，不等于真车自动扫图已经解锁。
- wheel L/R 非零、完整 Nav2 真车执行证明、delivery success、自动扫图真车 HIL 仍需继续用 live 证据推进。

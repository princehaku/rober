# 2026.06.25 19:10 PC free roam next step

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“扫地式建图”新增 `下一步` 流程按钮，按当前状态把焦点带到安全确认、开始记录、启用键盘、键盘手控区、停止或保存地图。该按钮只做 `scrollIntoView + focus`，不自动触发任何机器人动作。
- `pc-tools/workstation/test/App.test.ts`：扩展 free-roam 回归，覆盖未确认、已确认、地图记录已启动、键盘已启用四个状态下的下一步聚焦，并断言不会自动调用 `/api/robot-control/map/start` 或 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步扫地式建图下一步按钮的用户语义和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "free-roam"`：通过，`1 passed / 70 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`162 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`lidar_lifecycle_running=false`、`lidar_lifecycle_state=stopped`、`latest_scan_proof_fresh=false`；未调用 map start、manual、Nav2、delivery complete 或 `/cmd_vel`。

## 剩余风险

- 本轮只改善 PC 扫图流程导航，不新增自动扫图状态机，不证明真实自由自主避障，也没有触发 `/api/base/manual`、Nav2、delivery complete 或 `/cmd_vel`。

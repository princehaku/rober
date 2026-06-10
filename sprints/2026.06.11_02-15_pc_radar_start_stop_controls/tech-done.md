# PC Radar Start/Stop Controls V1

## sprint_type

micro

## 实际改动

- PC 后端新增固定雷达 lifecycle 代理：
  - `POST /api/robot-control/radar/start?baseUrl=<robot-api-base-url>` 固定转发上位机 `/api/radar/start`。
  - `POST /api/robot-control/radar/stop?baseUrl=<robot-api-base-url>` 固定转发上位机 `/api/radar/stop`。
  - 浏览器 body 被忽略，上位机请求 body 固定 `{}`，不开放任意 endpoint 或任意参数透传。
- 复用 Robot API `baseUrl` 回环 / RFC1918 private-LAN guard；空值、非法 URL、非 HTTP、credentials/query/hash、公网 host 均 fail closed。
- 新增 `RobotControlRadarLifecycleResponse` 合同，固定保持：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
- 雷达 lifecycle 允许上位机出现传感器控制相关 `sends_commands=true`，但拦截底盘/运动/安全硬危险字段：`sends_motion_commands=true`、`sends_base_motion_commands=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`uses_base_uart=true`、`safe_to_control=true`、`robot_control_executed=true` 等。
- Vue `RobotControlConsolePanel` 保持普通首屏五卡片不变；雷达首屏只保留 `刷新雷达` 和短状态。
- 默认关闭的 `高级诊断` 雷达详情新增 `启动雷达（高级）` / `停止雷达（高级）` 按钮，并显示最近 lifecycle result：remote endpoint、HTTP status、`command_result`、failure reason、blocked reasons、hard dangerous fields。
- client 新增 `postRobotControlRadarStart(baseUrl)` / `postRobotControlRadarStop(baseUrl)`。
- 更新 `docs/product/pc_tools_workstation.md`，明确 PC Radar Start/Stop V1 是固定高级诊断入口；真实上位机命令未配置时返回 dry-run guard，不等于雷达 runtime start proof。

## 改动文件

- `pc-tools/workstation/src/server/robotControlSummary.ts`
- `pc-tools/workstation/src/server/catalog.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.06.11_02-15_pc_radar_start_stop_controls/artifacts/radar_stop_smoke_response.json`
- `sprints/2026.06.11_02-15_pc_radar_start_stop_controls/artifacts/radar_stop_smoke_http_status.txt`

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过。
  - Vite output: `✓ built in 1.05s`。
- `cd pc-tools/workstation && npm run test`
  - 通过。
  - `Test Files 2 passed (2)`，`Tests 77 passed (77)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过。
- `git diff --check`
  - 通过，无 whitespace error。

## 真实上位机 smoke

- PC 后端启动：`PORT=8791 npm run api`。
- 调用：
  - `POST http://127.0.0.1:8791/api/robot-control/radar/stop?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - body: `{}`
- Artifact:
  - `sprints/2026.06.11_02-15_pc_radar_start_stop_controls/artifacts/radar_stop_smoke_response.json`
  - `sprints/2026.06.11_02-15_pc_radar_start_stop_controls/artifacts/radar_stop_smoke_http_status.txt`
- 摘要：
  - HTTP status: `200`
  - `schema=trashbot.pc_tools_workstation.robot_control_radar_lifecycle_proxy.v1`
  - `action=stop`
  - `proxy_status=lifecycle_forwarded`
  - `remote_endpoint=/api/radar/stop`
  - `remote_http_status=200`
  - `command_result.mode=dry_run_stub`
  - `command_result.executed=false`
  - `command_result.ok=false`
  - `failure_reason=command_not_configured`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `hard_dangerous_true_fields=[]`
- 本轮真实 smoke 未调用 `/cmd_vel`、`/api/base/manual`、Nav2 start/stop、底盘动作或串口控制。
- 未调用真实 `radar/start`，因为 `radar/stop` 已证明固定代理和上位机 dry-run guard；避免在未进一步确认运行时影响的情况下启动传感器进程。

## UI smoke

- 本地页面：`http://127.0.0.1:4174/`。
- Browser DOM 检查通过：
  - 标题为 `Rober 小车控制台`。
  - 首屏卡片仍是 `小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航` 五卡片。
  - 首屏不包含 `启动雷达`、`停止雷达`、`scan_once_observed`、`raw`、`proof_status`、`HIL`、`速度上限`、`前进`、`后退`、`保存地图`。
  - 默认关闭的 `高级诊断` 包含 `启动雷达（高级）`、`停止雷达（高级）`、`lifecycle command_result`、`lifecycle dangerous fields`、`lifecycle blocked reasons`。

## 失败定位

- 首轮 `build`、`test`、`lint`、`git diff --check` 均通过。
- Browser smoke 第一次使用 `networkidle` load state 被当前插件拒绝，已改用 `load` state 重试并通过；这不是产品代码失败。

## 剩余风险

- 当前真实上位机 `radar/stop` 仍是 dry-run guard：`command_not_configured`，不证明真实雷达 runtime 已停止，也不证明 start/stop runtime lifecycle 已联调完成。
- 本轮只真实调用 `radar/stop`；`radar/start` 由单元/API/UI mock 覆盖，未做真实上位机 start smoke。
- PC 页面仍只证明固定代理、安全拦截和高级诊断入口可用；真实雷达 runtime start proof 仍应以 `/api/radar/status`、scan proof、driver process evidence 或上位机后续配置命令为准。

## 完成前反思

- 已限制改动在本轮允许文件范围内，未修改 `onboard` 上位机代码、底盘/运动/串口控制或无关 sprint/OKR。
- 已同步产品文档与 sprint 留档。
- 未留下代码 TODO；剩余风险集中在真实上位机 radar lifecycle 命令未配置和 start 未实机 smoke。
- 记录时间：2026-06-11 02:21:03 CST。

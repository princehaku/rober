# 2026.06.11 12:45 Clean Baseline Radar/Map PC Proxy Refresh

## sprint_type

micro

## 本轮目标

- 不改 PC 普通用户首屏，不把工程/debug 词重新暴露到默认可见界面。
- 通过 PC workstation 本地固定代理 `http://127.0.0.1:18788` 触发真实上位机
  `http://192.168.1.11:8787` 的 radar proof refresh 和 map proof refresh。
- 保存本轮 fresh request/response/summary/cleanup artifacts，并记录 contract 边界。

## 实际改动

- 新增本 sprint 目录与 artifacts：
  - `artifacts/pc_proxy/run_context.json`
  - `artifacts/pc_proxy/radar_request_attempt_*.json`
  - `artifacts/pc_proxy/radar_response_attempt_*.json`
  - `artifacts/pc_proxy/map_request_attempt_*.json`
  - `artifacts/pc_proxy/map_response_attempt_*.json`
  - `artifacts/pc_proxy/summary_readback_after_refresh.json`
  - `artifacts/pc_proxy/direct_latest_readback_after_proxy_refresh.json`
  - `artifacts/pc_proxy/refresh_corrected_summary.json`
  - `artifacts/dom_smoke/pc_plain_user_home_dom_smoke.test.ts`
  - `artifacts/dom_smoke/pc_plain_user_home_dom_smoke.json`
  - `artifacts/dom_smoke/vitest_dom_smoke.log`
  - `artifacts/cleanup/workstation_api_after_stop_readback.log`
  - `artifacts/cleanup/workstation_api_port_18788_lsof_after_stop.log`
  - `artifacts/cleanup/target_cleanup_readback.log`
- 更新 `pc-tools/README.md`：记录本轮真实 PC proxy radar/map refresh 证据和 radar
  `evidence_ref` contract gap。
- 更新 `docs/product/pc_tools_workstation.md`：记录普通首屏保持简易风格、DOM smoke
  forbidden token 结果、fresh radar/map 证据来源。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`：记录 no-motion 硬件边界、cleanup
  readback 和关键 artifacts。

未改动：

- 未修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`。
- 未修改 `pc-tools/workstation/src/App.vue`。
- 未修改 `pc-tools/workstation/src/styles.css`。
- 未修改 `onboard/**` 产品代码、硬件 launch、serial 或 WAVE ROVER 配置。
- 未执行 `/api/base/manual`，未发布 `/cmd_vel`，未执行非零运动。

## 验证结果

### PC proxy radar refresh

命令路径：

```text
PORT=18788 npm run api
POST http://127.0.0.1:18788/api/robot-control/radar/scan-proof/refresh?baseUrl=http%3A%2F%2F192.168.1.11%3A8787
```

第一次自动 summary 误把 `latest_readback_key_values` 里的字符串 `"true"` 当成未观察，
因此脚本按规则重试一次。原始 response 两次都是 HTTP 200；修正后的解析使用实际 PC proxy
contract 和 direct latest readback。

最终采用 attempt 2：

```json
{
  "proxy_http_status": 200,
  "remote_http_status": 200,
  "proxy_status": "refresh_forwarded",
  "scan_once_observed": true,
  "scan_hz_observed": true,
  "raw_packet_once_observed": true,
  "tf_observed": true,
  "hard_dangerous_true_fields": [],
  "generated_at": "2026-06-11T05:06:46.418393Z",
  "generated_at_fresh_for_this_run": true,
  "evidence_ref_contract_status": "contract_absent_for_radar_latest"
}
```

边界：radar latest contract 当前不输出独立 `evidence_ref`，只输出
`artifact.path=runtime/lidar_scan_proof_latest.json`。本轮没有把旧 radar evidence_ref
冒充为 fresh proof；状态记录为 `passed_with_radar_evidence_ref_contract_gap`。

### PC proxy map refresh

命令路径：

```text
POST http://127.0.0.1:18788/api/robot-control/map/proof/refresh?baseUrl=http%3A%2F%2F192.168.1.11%3A8787
```

最终采用 attempt 2：

```json
{
  "proxy_http_status": 200,
  "remote_http_status": 200,
  "proxy_status": "refresh_forwarded",
  "map_once_observed": true,
  "map_file_observed": true,
  "map_metadata_observed": true,
  "evidence_ref": "o3-map-lifecycle-1781154452321",
  "generated_at_fresh_for_this_run": true,
  "evidence_ref_fresh_for_this_run": true,
  "safe_to_control": false,
  "delivery_success": false,
  "primary_actions_enabled": false,
  "robot_control_executed": false,
  "sends_motion_commands": false,
  "publishes_cmd_vel": false,
  "calls_base_manual": false,
  "uses_base_uart": false
}
```

### 首屏 DOM smoke

命令：

```text
cd pc-tools/workstation && npx vitest run --root /Users/m1/apps/rober --config /Users/m1/apps/rober/sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/dom_smoke/vitest.dom-smoke.config.mjs /Users/m1/apps/rober/sprints/2026.06.11_12-45_clean_baseline_radar_map_pc_proxy_refresh/artifacts/dom_smoke/pc_plain_user_home_dom_smoke.test.ts --reporter=verbose
```

结果：

```text
Test Files  1 passed (1)
Tests  1 passed (1)
```

DOM artifact：

```json
{
  "title_text": "Rober 小车控制台",
  "first_screen_card_titles": ["小车连接", "实时画面", "雷达", "地图", "移动/导航"],
  "all_forbidden_tokens_absent": true,
  "advanced_diagnostics_closed_by_default": true
}
```

检查的 forbidden tokens：`HIL`、`proof`、`Nav2`、`/cmd_vel`、
`/api/base/manual`、`task_id`、`Mock`、`检查路径`。

### cleanup readback

本地：

```text
curl: (7) Failed to connect to 127.0.0.1 port 18788 after 0 ms: Couldn't connect to server
```

`lsof -nP -iTCP:18788 -sTCP:LISTEN` 无输出。

目标上位机：

```text
== helper processes ==
== device lsof ==
== device fuser ==
```

说明目标侧未发现本轮 helper 残留，`/dev/ttyS5`、`/dev/ttyACM0` 无 `lsof`/`fuser`
占用输出。

### git diff --check

命令：

```text
git diff --check
```

结果：退出码 0，无输出。

## 用户旅程变化和触点收益

- 普通用户首屏继续保持简易控制台：连接、画面、雷达、地图、移动/导航五张卡片。
- 工程 proof、Nav2、HIL、`task_id`、`/cmd_vel`、`/api/base/manual` 等词继续留在默认关闭的高级区或文档中。
- PC 代理到真实上位机的 radar/map refresh 已有本轮 fresh artifact，可用于后续 O7
  地图/雷达状态消费，不需要普通用户理解 ROS2 topic 或串口。

## 接口影响

- 没有新增或修改 API。
- 继续使用既有固定代理：
  - `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=<robot-api-base-url>`
  - `POST /api/robot-control/map/proof/refresh?baseUrl=<robot-api-base-url>`
- 本轮只记录 contract 事实：radar latest 当前没有独立 `evidence_ref` 字段；map latest
  有 fresh `evidence_ref`。

## 剩余风险

- Radar proof refresh 功能字段全部满足，但 radar latest contract 缺独立 `evidence_ref`；
  后续若验收强制每类 proof 都有 `evidence_ref`，需要机器人侧扩展上位机 radar latest/refresh
  contract，本轮按禁止范围未改 `onboard/**`。
- 本轮是 no-motion radar/map proof，不等于 Nav2 执行、真实路线、底盘 HIL、真实运动或送达成功。
- 首屏 DOM smoke 只覆盖默认可见文本；未跑完整 workstation build/test/lint，因为本轮没有改
  `pc-tools/workstation/src/**` 或 `pc-tools/workstation/test/**`。

## 完成前反思

- 需求是否满足：PC proxy 真实触发 radar/map refresh，保存 fresh artifacts，普通首屏契约有 DOM smoke。
- 是否误改无关文件：未改产品 UI、App、样式、onboard、vendor 或硬件配置。
- 是否留下 TODO：没有新增 TODO；唯一未完成事项是 radar latest `evidence_ref` contract gap。
- 验证缺口：未做真实运动、HIL、Nav2 execution；本轮安全边界明确不做这些验证。

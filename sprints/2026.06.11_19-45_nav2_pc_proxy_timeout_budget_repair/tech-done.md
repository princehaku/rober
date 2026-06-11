# 2026-06-11 19:45 Nav2 PC Proxy Timeout Budget Repair

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 将 Nav2 no-motion proof helper 外层 process cap 从 `84.0s` 调整为 `132.0s`。
  - 新增 `NAV2_PROOF_PC_PROXY_TIMEOUT_BUDGET_S=150.0`，让上位机 artifact/test 明确记录 PC proxy 应晚于 upper helper 超时。
  - 固定 PC body `timeout_s=30 + managed_timeout_s=30 + path_generation_timeout_s=30` 的 upper raw budget 为 `120.0s`，不再被 upper wrapper cap 截断。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 Nav2 no-motion proof refresh proxy 的 `timeout_cap_ms` 从 `90_000` 调整为 `150_000`。
  - 将 Nav2 no-motion proof refresh proxy 的 `safety_margin_ms` 从 `30_000` 调整为 `60_000`，固定 body 计算结果为 `150_000ms`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 单测改为断言 upper fixed body raw/process budget 为 `120.0s`、upper cap 为 `132.0s`、PC proxy budget 为 `150.0s`。
  - 扩展场景仍断言被 `132.0s` cap 截断，避免 helper 无限等待。
- `pc-tools/workstation/test/catalog.test.ts`
  - 单测改为断言 Nav2 proxy computed timeout、AbortSignal timeout 和失败 reason 使用 `150000ms`。
- `docs/navigation/fixed_route_workflow.md`
- `docs/hardware/board_sensor_stack_smoke.md`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
  - 同步 19:45 timeout budget 边界：upper cap `132s`、PC fetch `150s`、fixed body raw `120s`。
  - 保持 no-motion 安全边界：不执行 NavigateToPose、不发布 `/cmd_vel`、不调用 `/api/base/manual`、不打开 `/dev/ttyS5`。

## 验证结果

- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
  - 通过，`Ran 28 tests in 2.347s`，日志：`artifacts/logs/python_unittest_nav2_runtime_proof_helper.log`。
- `cd pc-tools/workstation && npm run test`
  - 通过，`2 passed (2)`、`92 passed (92)`，日志：`artifacts/logs/workstation_npm_test.log`。
- `cd pc-tools/workstation && npm run build`
  - 通过，`tsc + vite build + server tsc` 全部完成，日志：`artifacts/logs/workstation_npm_build.log`。

## 真实上位机同步与 PC Proxy Smoke

- 上位机同步：
  - 仅同步 `onboard/scripts/upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`。
  - `trashbot-upper-robot-api.service=active`。
  - 本机和远端 sha256 均为 `1aee9a5e6849cbbe63d71c5099f7be0330d75184f83e4df65d9614b03215b252`。
  - 远端 grep 读回 `NAV2_PROOF_PROCESS_TIMEOUT_CAP_S = 132.0`、`NAV2_PROOF_PC_PROXY_TIMEOUT_BUDGET_S = 150.0`。
  - 证据：`artifacts/remote/ssh_deploy_service_readback.log`。
- 本机 PC workstation Node proxy:
  - 临时端口：`http://127.0.0.1:18795`。
  - 调用：`POST /api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787`。
  - HTTP code `200`，`remote_http_status=200`。
  - `proxy_status=refresh_forwarded`。
  - `last_result_evidence_ref=o10-amcl-nav2-runtime-1781174465268`。
  - `path_generated=true`、`path_generation_succeeded=true`、`path_point_count=32`、`planner_server_active=true`。
  - `blocked_reasons=[]`、`hard_dangerous_true_fields=[]`。
  - `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
  - elapsed `44083ms`；未触发 84s/90s wrapper failure。
  - 证据：`artifacts/pc_proxy/nav2_pc_proxy_refresh_response.json`、`artifacts/pc_proxy/nav2_pc_proxy_refresh_summary.json`、`artifacts/pc_proxy/nav2_pc_proxy_refresh_elapsed.log`。

## 清理状态

- 上位机清理读回：
  - `trashbot-upper-robot-api.service=active`。
  - 无 `o10_amcl_nav2_runtime_proof`、`map_server`、`amcl`、`planner_server`、`lifecycle_manager`、`controller_server` helper 残留。
  - `/cmd_vel` 返回 `Unknown topic '/cmd_vel'`。
  - `lsof /dev/ttyS5` 与 `fuser -v /dev/ttyS5` 无 holder 输出。
  - 证据：`artifacts/remote/ssh_cleanup_readback.log`。
- 本机临时 workstation API 已停止：
  - `lsof -nP -iTCP:18795 -sTCP:LISTEN` 无输出。
  - 证据：`artifacts/pc_proxy/workstation_api_port_18795_after_stop.log`。

## 剩余风险

- 本轮只修复 PC/upper timeout 预算，并证明 no-motion path generation 可通过 PC proxy 返回；仍不证明 NavigateToPose、controller execution、fixed-route execution、真实运动、HIL pass 或 delivery success。
- 本轮未改 PC 普通首屏 UI，未改 `App.vue`、`RobotControlConsolePanel.vue` 或 `styles.css`。
- 本轮未改 WAVE ROVER base driver、底盘串口配置或 launch 硬件参数；硬件事实入口仍为 `docs/vendor/VENDOR_INDEX.md`。
- 不需要 Product、Hardware、Autonomy 或 Full-Stack 协同；后续若进入真实运动或 NavigateToPose，需要 Autonomy + Hardware 按现场 HIL gate 协同。

记录时间：2026-06-11T18:42:49+0800。

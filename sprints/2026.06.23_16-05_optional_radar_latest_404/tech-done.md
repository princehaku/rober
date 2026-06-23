# 2026-06-23 16:05 可选雷达 latest 404 降级

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增可选只读端点集合，只包含 `radar_scan_proof_latest` 与 `radar_raw_packet_proof_latest`。
  - 当这两个端点返回 HTTP 404 且 JSON 可读时，summary 将该端点记为 `request_status=loaded`、`status=missing`，不再把整机连接状态打成 `blocked`。
  - 将 `status` 与 `camera_health` 这两个重只读端点预算从 4s 扩到 8s，避免真实 80KB 级 status 聚合和摄像头健康探测在并发 summary 读取中被误判 timeout。
  - 其它只读 endpoint 的 HTTP 错误、bad JSON、非 object、危险 true 字段仍保持原有 fail-closed。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增真实上位机兼容测试：其它只读端点正常、两个 radar latest 返回 404 时，`console_status=loaded_fail_closed_summary`、连接 `readable`，雷达 proof 状态为 `missing`。
  - 加宽既有慢端点测试到 5.2s/5.4s，证明超过旧 4s 但低于新 8s 时仍可读取。
- `docs/product/pc_tools_workstation.md`
  - 同步记录该兼容只改善 PC 首屏连接可读性，不自动启动雷达、不执行 Nav2、manual、keyboard、delivery 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts -t "optional radar latest|slow status and camera"`，结果 `1 passed`，`2 passed | 87 skipped`。
- 通过：`npm test`，结果 `2 passed`，`141 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 app/server TypeScript 与 Vite production build。
- 真实 PC proxy smoke：
  - 临时以 `HOST=0.0.0.0 PORT=17071 npm run api` 启动新代码，请求 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`。
  - 返回 `console_status=loaded_fail_closed_summary`、`robot_api_connection.status=readable`、`loaded_count=13`、`blocked_count=0`、`failed_count=0`、`dangerous_true_fields=[]`、`blocked_reasons=[]`。
  - `readback_summary.lidar.latest_scan_proof_status=missing`、`latest_raw_packet_proof_status=missing`、`continuous_scan_status=lifecycle_not_running`。
  - `readback_summary.base` 仍显示 `T1001` 可读但 `wheel_feedback_latest_left_speed=0`、`wheel_feedback_latest_right_speed=0`、`wheel_feedback_lr_nonzero_proven=false`。
- 通过：`git diff --check`。
- 本轮真实只读卡点：
  - 本机 PC proxy 访问真实上位机 summary 时，`/api/radar/scan-proof/latest` 与 `/api/radar/raw-packet-proof/latest` 返回 404，旧逻辑导致 `console_status=blocked`。
  - 真实上位机仍显示 `radar lifecycle_running=false`、底盘 T1001 可读但 L/R 为 `0/0`、Nav2 goal `not_proven`、delivery false、operator 基础安全三项 false。

## 剩余风险

- 本轮没有执行真实雷达启动、first-jog、Nav2、delivery complete 或键盘手控。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需现场安全确认和真实执行证据。

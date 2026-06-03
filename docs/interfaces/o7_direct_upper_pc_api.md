# O7 Direct Upper PC API

## 目标

`pc-tools/workstation` 新增 PC 本机 direct upper-computer mode，用于开发机或现场 PC 直接访问上位机 8787：

```bash
ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run dev -- --host 127.0.0.1 --port 5173
```

该模式绕过 cloud relay 作为必需路径，但只服务 PC 本地浏览器、curl 和调试工具。它不改变生产 4G 云路线，不替代手机端普通用户路径，也不把 8787 HTTP 成功解释成 WAVE ROVER ACK、`T=1001` 或 HIL pass。

## PC 本机接口

所有接口由 PC workstation Express 提供，默认只绑定 `127.0.0.1`。

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/o7/direct-upper/status` | 同时读取上位机 `/health` 与 `/api/status`，返回 PC 可消费摘要。 |
| `POST` | `/api/o7/direct-upper/base/stop` | 同源转发到上位机 `/api/base/stop`，失败时 fail-closed。 |
| `POST` | `/api/o7/direct-upper/base/feedback-request` | 同源转发到上位机 `/api/base/feedback-request`，只请求非运动 `T=130` 反馈。 |
| `POST` | `/api/o7/direct-upper/base/manual` | PC 侧先做方向白名单、低速、短 duration 限制，再转发到上位机 `/api/base/manual`。 |

## 环境变量

- `ROBER_UPPER_API_BASE_URL`：必填。示例 `http://192.168.1.11:8787`。
- 未配置时，四个接口都不会主动探测默认 LAN IP；`status` 返回 `not_configured`，`stop/feedback-request/manual` 返回 `base_url_not_configured`。

## `GET /api/o7/direct-upper/status`

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_status.v1
```

关键字段：

- `mode=direct_upper_computer_lan_only`
- `cloud_relay_bypassed=true`
- `pc_local_only=true`
- `upper_api_base_url`
- `health_request`：`GET /health` 的执行、HTTP 状态、失败原因。
- `status_request`：`GET /api/status` 的执行、HTTP 状态、失败原因。
- `upper_status_summary.camera_status`
- `upper_status_summary.radar_scan_status`
- `upper_status_summary.radar_scan_proof_artifact_status`
- `upper_status_summary.radar_scan_proof_freshness_status`
- `upper_status_summary.radar_scan_proof_age_seconds`
- `upper_status_summary.radar_scan_proof_latest_status`
- `upper_status_summary.radar_scan_proof_blockers`
- `upper_status_summary.lidar_port`
- `upper_status_summary.base_port`
- `upper_status_summary.base_baudrate`
- `upper_status_summary.base_write_control_available`
- `upper_status_summary.robot_ack_connected=false`
- `upper_status_summary.t1001_observed=false`
- `local_api_paths.status/stop/feedback_request/manual`

固定安全字段：

- `production_4g_cloud_route_changed=false`
- `safe_to_control=false`
- `sends_cmd_vel=false`
- `sends_wave_rover_json_directly=false`
- `robot_control_executed=false`
- `robot_ack_connected=false`
- `t1001_observed=false`

## `POST /api/o7/direct-upper/base/stop`

PC 后端只转发到：

```text
<ROBER_UPPER_API_BASE_URL>/api/base/stop
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_stop.v1
```

边界：

- 上位机 HTTP 2xx 且返回 JSON 时，`accepted_by_workstation=true`、`upper_request.ok=true`。
- 远端超时、非 2xx、坏 JSON 或 fetch 失败时，PC 返回 `502`，`fail_closed=true`。
- 未配置 base URL 时，PC 返回 `400`，不触发远端 fetch。
- 响应仍固定 `robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`。

## `POST /api/o7/direct-upper/base/feedback-request`

PC 后端只转发到：

```text
<ROBER_UPPER_API_BASE_URL>/api/base/feedback-request
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_feedback_request.v1
```

边界：

- 该入口只请求上位机发送一次 vendor `T=130` 非运动反馈请求；PC 本机 API 不直写 WAVE ROVER JSON。
- 上位机 HTTP 2xx 且返回 object JSON 时，`accepted_by_workstation=true`、`upper_request.ok=true`。
- 远端超时、非 2xx、坏 JSON 或 fetch 失败时，PC 返回 `502`，`fail_closed=true`。
- 未配置 base URL 时，PC 返回 `400`，不触发远端 fetch。
- 即使远端 JSON 声称包含 `T=1001`，PC 响应仍固定 `safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`；它只说明请求被转发，不证明真实 ACK、HIL 或 `T=1001` 已由同源材料验收。

## `POST /api/o7/direct-upper/base/manual`

请求示例：

```json
{"direction":"forward","speed":0.05,"duration_ms":250}
```

PC 侧限制：

- `direction` 只允许 `forward/back/left/right/stop`。
- `speed` 取绝对值并限制到 `<=0.08 m/s`。
- `duration_ms` 限制到 `1..350ms`。
- 非法 direction 返回 `400 invalid_direction`，不触发远端 fetch。
- 合法请求仍依赖 8787 自身 `/api/base/manual` guardrail 做最终限速、限时和 auto-stop。

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_manual.v1
```

响应里的 `command_payload_summary` 会记录 PC clamp 后的 `direction/speed_mps/duration_ms/clamped_by_pc`。即使远端返回 200，PC 仍固定：

- `safe_to_control=false`
- `sends_commands=false`
- `robot_control_executed=false`
- `robot_ack_connected=false`
- `t1001_observed=false`

## 前端入口

`O7LiveOperatorPanel.vue` 的默认首屏新增 `PC 本机 8787 接口` 卡片：

- 展示 direct mode 状态。
- 展示 `ROBER_UPPER_API_BASE_URL`。
- 展示四个本机 API path，方便浏览器/curl 工具消费。
- 展示 cloud relay 已绕过和 ACK/T=1001 not observed 边界。
- 展示 8787 `radar.scan_proof_latest` 摘要：artifact status、freshness、age、latest proof status 和 top blockers。

现有方向按钮仍保持锁定，不会因为 direct status ready 自动 POST manual。真实运动必须由 operator 明确调用本机 API，并受 PC clamp 与 8787 guardrail 共同限制。

## 证据边界

本轮只证明 PC 本机 API 层、前端入口和 mock/fetch 单测：

- 不证明生产 4G 云 relay。
- 不证明真实 ROS2 `/cmd_vel`。
- 不证明真实 `/odom`、`/imu/data`、`/battery`。
- 不证明 `T=1001` 或 robot ACK。
- 不证明真实 stop/manual 已现场执行。
- 不证明 delivery success。

## 2026-06-03 现场核对结果

早些时候 Hardware worker 现场核对到远端 8787 曾处于：

- `GET http://192.168.1.11:8787/health` ready。
- `GET http://192.168.1.11:8787/api/status` ready。
- `POST http://192.168.1.11:8787/api/base/feedback-request` 当前返回 HTTP `405`，`Allow=OPTIONS`。

后续 O1 8787 部署已改变该状态：远端 `POST /api/base/feedback-request` 与
`POST /api/base/feedback-samples` 已可返回非运动 `T=130 -> T=1001` 材料，
并且 `GET /api/radar/scan-proof/latest` 已返回 HTTP 200、artifact `loaded`。

PC direct upper 现在只消费这些只读摘要和本机转发结果：

- `upper_status_summary.radar_scan_proof_*` 来自 8787 `/api/status.radar.scan_proof_latest`。
- artifact `loaded` 只代表 scan proof collector 的 JSON 可回放。
- `latest_proof_status=blocked_or_not_observed` 时，如果远端摘要没有 blocker 明细，PC 会显示 `radar_scan_proof_blocked_or_not_observed`，不会误报为未加载。
- PC 不执行 collector、不启动 ROS2、不打开 LiDAR 串口、不发送 `A5 60`，也不发送底盘运动命令。

这些材料仍不能声明真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、ACK/HIL、`safe_to_control=true` 或完整上车任务完成。

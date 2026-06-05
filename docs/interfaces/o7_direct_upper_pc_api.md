# O7 Direct Upper PC API

## 目标

`pc-tools/workstation` 新增 PC 本机 direct upper-computer mode，用于开发机或现场 PC 直接访问上位机 8787：

```bash
ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run dev -- --host 127.0.0.1 --port 5173
```

该模式绕过 cloud relay 作为必需路径，但只服务 PC 本地浏览器、curl 和调试工具。它不改变生产 4G 云路线，不替代手机端普通用户路径，也不把 8787 HTTP 成功解释成 WAVE ROVER ACK、`T=1001` 或 HIL pass。

2026-06-04 起，PC 现场 direct-upper 的 `status`、`radar start/stop`、`scan-proof refresh` 和 `operator-report` 写入/回读在缺少显式 env 时会回退到现场默认上位机：

```text
http://192.168.1.11:8787
```

响应必须通过 `upper_api_base_url_source` 标明来源：

- `env`：来自 `ROBER_UPPER_API_BASE_URL`，优先级最高。
- `field_default`：来自当前现场默认 `http://192.168.1.11:8787`。
- `fixture`：来自显式 fixture mode，请求不执行上位机 fetch，只返回可回放的软件护栏 envelope。
- `not_configured`：用于仍要求显式配置的入口，且没有显式 fixture mode。

这个默认值只解决 PC 到上位机 8787 的 HTTP 路由，不会把 `safe_to_control` 改为 `true`，也不会绕过 ACK、`T=1001`、HIL 或 operator evidence。

2026-06-04 13:48 起，direct-upper status 和 command envelope 必须返回 adapter 指纹：

```text
adapter.version=2026-06-04.scan-proof-refresh-v1
adapter.source=pc-tools/workstation/src/server/o7DirectUpperApi.ts
adapter.field_default_enabled=true
adapter.field_default_url=http://192.168.1.11:8787
```

这个字段用于识别 stale Vite dev server。当前 `vite.config.ts` 在插件初始化时执行
`const apiApp = createWorkstationApp()`；如果 5173 上的旧 `npm run dev` 进程没有重启，
它可能继续服务旧 Express middleware，看起来就会仍然返回
`base_url_not_configured` / `upper_request.executed=false`。新 UI 会在 Direct 卡片显示
`adapter=<version>`；如果 API 缺少 `adapter` 或 Radar start 仍显示
`/api/radar/start not_executed`，或 scan-proof refresh 仍显示
`/api/radar/scan-proof/refresh not_executed`，operator 应重启占用 5173 的 dev server 后再复测。

## PC 本机接口

所有接口由 PC workstation Express 提供，默认只绑定 `127.0.0.1`。

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/api/o7/direct-upper/status` | 同时读取上位机 `/health` 与 `/api/status`，返回 PC 可消费摘要。 |
| `POST` | `/api/o7/direct-upper/base/stop` | 同源转发到上位机 `/api/base/stop`，失败时 fail-closed。 |
| `POST` | `/api/o7/direct-upper/base/feedback-request` | 同源转发到上位机 `/api/base/feedback-request`，只请求非运动 `T=130` 反馈。 |
| `POST` | `/api/o7/direct-upper/base/manual` | PC 侧先做方向白名单、低速、短 duration 限制，再转发到上位机 `/api/base/manual`。 |
| `POST` | `/api/o7/direct-upper/radar/start` | 同源转发到上位机 `/api/radar/start`，允许使用 field default，不依赖底盘 ACK/T=1001。 |
| `POST` | `/api/o7/direct-upper/radar/stop` | 同源转发到上位机 `/api/radar/stop`，允许使用 field default，不触碰底盘 UART。 |
| `POST` | `/api/o7/direct-upper/radar/scan-proof/refresh` | 同源转发到上位机 `/api/radar/scan-proof/refresh`，只触发只读 proof refresh，不启动 driver、不控底盘。 |
| `GET` | `/api/o7/direct-upper/radar/scan-proof/latest` | 同源回读上位机 `/api/radar/scan-proof/latest`，只返回 latest artifact 摘要，不触发 refresh、不控底盘。 |
| `POST` | `/api/o7/direct-upper/map/start` | 同源转发到上位机 `/api/map/start`，需要显式 env 或 fixture mode。 |
| `POST` | `/api/o7/direct-upper/map/reset` | 同源转发到上位机 `/api/map/reset`，需要显式 env 或 fixture mode。 |
| `POST` | `/api/o7/direct-upper/map/save` | 同源转发到上位机 `/api/map/save`，保留 `map_id` 和 `evidence_ref`，需要显式 env 或 fixture mode。 |
| `POST` | `/api/o7/direct-upper/map/load` | 同源转发到上位机 `/api/map/load`，保留 `map_id` 和 `evidence_ref`，需要显式 env 或 fixture mode。 |
| `GET` | `/api/o7/direct-upper/map/list` | 同源转发到上位机 `/api/map/list`，需要显式 env 或 fixture mode。 |
| `GET` | `/api/o7/direct-upper/map/proof/latest` | 同源回读上位机 `/api/map/proof/latest`，只展示 canonical path contract、artifact/path、失败原因和 safety false。 |
| `POST` | `/api/o7/direct-upper/localize/reset` | 同源转发到上位机 `/api/localize/reset`，需要显式 env 或 fixture mode。 |
| `POST` | `/api/o7/direct-upper/operator-report` | 同源转发到上位机 `/api/operator/report`，记录 `evidence_ref` 和 `note`；允许使用 field default，不触发运动。 |
| `GET` | `/api/o7/direct-upper/operator-report` | 同源回读上位机 `/api/operator/report` latest artifact；允许使用 field default，只读不触发运动。 |

## 环境变量

- `ROBER_UPPER_API_BASE_URL`：可选但优先。示例 `http://192.168.1.11:8787`。
- 未配置时，`GET /api/o7/direct-upper/status` 使用 field default `http://192.168.1.11:8787` 并返回 `upper_api_base_url_source=field_default`。
- 未配置时，`POST /api/o7/direct-upper/radar/start`、`POST /api/o7/direct-upper/radar/stop`、`POST /api/o7/direct-upper/radar/scan-proof/refresh` 和 `GET /api/o7/direct-upper/radar/scan-proof/latest` 也使用 field default 转发到上位机 `/api/radar/start|stop|scan-proof/refresh|scan-proof/latest`。
- 未配置时，`POST|GET /api/o7/direct-upper/operator-report` 使用 field default 写入/回读上位机 `/api/operator/report`，只作用于 operator report artifact，不访问 base/manual/stop/feedback。
- `ROBER_O7_DIRECT_UPPER_FIXTURE_MODE=1`：显式打开 fixture mode；支持 `1/true/yes/on`。fixture mode 返回 `upper_api_base_url_source=fixture`、`upper_api_base_url=fixture://upper-api`，并且不触发远端 fetch。
- 请求 body 也可传 `fixture_mode=true` 打开单次 fixture mode。UI 的 `fixture mode` 勾选框使用该入口。
- 底盘运动相关的 `base/stop`、`base/feedback-request`、`base/manual` 仍要求显式 `ROBER_UPPER_API_BASE_URL` 或 fixture mode；缺 env 且没有 fixture mode 时返回 `base_url_not_configured`，不触发远端 fetch。
- `map/start|reset|save|load|list|proof/latest` 和 `localize/reset` 仍要求显式 `ROBER_UPPER_API_BASE_URL` 或 fixture mode；缺 env 且没有 fixture mode 时返回 `base_url_not_configured`，不使用 field default。

## Timeout 边界

- `GET /api/o7/direct-upper/status` 仍使用 `1200ms` 短超时读取 `/health` 与 `/api/status`，避免首屏状态刷新被远端慢请求拖住。
- `POST /api/o7/direct-upper/base/stop` 与 `POST /api/o7/direct-upper/base/feedback-request` 仍使用同一短超时；它们不应承担运动 pulse + stop + feedback 回读窗口。
- `POST /api/o7/direct-upper/base/manual` 使用独立 `5500ms` 远端转发超时。这个窗口用于覆盖上位机 `/api/base/manual` 内部的短运动、自动停车、随后 `T=130` 请求和 `T=1001` 反馈读取；超时仍返回 `502`、`failure_reason="timeout"`、`safe_to_control=false`，不把等待失败包装成成功。
- `POST /api/o7/direct-upper/radar/scan-proof/refresh` 使用独立 `55000ms` 远端转发超时。这个窗口只用于等待上位机只读 LiDAR/ROS2 scan proof runtime + collector 返回；PC 仍不发布 `/cmd_vel`、不访问底盘 UART、不把一次 fresh proof 外推成 continuous radar ready。

## `GET /api/o7/direct-upper/status`

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_status.v1
```

关键字段：

- `mode=direct_upper_computer_lan_only`
- `adapter.version=2026-06-04.scan-proof-refresh-v1`
- `adapter.source=pc-tools/workstation/src/server/o7DirectUpperApi.ts`
- `adapter.field_default_enabled=true`
- `adapter.field_default_url=http://192.168.1.11:8787`
- `cloud_relay_bypassed=true`
- `pc_local_only=true`
- `upper_api_base_url`
- `upper_api_base_url_source=env|field_default|fixture|not_configured`
- `adapter.version/source/field_default_enabled/field_default_url/dev_server_reload_hint`
- `health_request`：`GET /health` 的执行、HTTP 状态、失败原因。
- `status_request`：`GET /api/status` 的执行、HTTP 状态、失败原因。
- `upper_status_summary.camera_status`
- `upper_status_summary.radar_scan_status`
- `upper_status_summary.radar_scan_proof_artifact_status`
- `upper_status_summary.radar_scan_proof_freshness_status`
- `upper_status_summary.radar_scan_proof_age_seconds`
- `upper_status_summary.radar_scan_proof_latest_status`
- `upper_status_summary.radar_scan_proof_fresh_observed`：来自上位机机器字段，只表示一次 fresh scan proof 是否观测到 required observations。
- `upper_status_summary.radar_scan_proof_hz_average_rate_hz`：上位机返回的 scan proof 平均频率，缺失时为 `null`。
- `upper_status_summary.radar_scan_proof_tf_observed`：上位机返回的 TF 观测结果，缺失时为 `null`。
- `upper_status_summary.radar_scan_proof_all_required_observations_observed`：上位机 required observations 汇总，缺失时为 `null`。
- `upper_status_summary.radar_scan_proof_runtime_summary_fallback_used`：上位机是否使用 runtime summary fallback。
- `upper_status_summary.radar_scan_proof_runtime_summary_path`：上位机 runtime summary 来源路径，缺失时为 `not_reported`。
- `upper_status_summary.radar_continuous_scan_status`：连续雷达证明状态；当前未证明时必须为 `not_proven`，不得由 fresh artifact 外推成 ready。
- `upper_status_summary.radar_continuous_blockers`：连续雷达未证明 blocker，例如 `scan_continuity_not_observed`。
- `upper_status_summary.radar_scan_proof_blockers`
- `upper_status_summary.radar_raw_packet_proof_artifact_status`
- `upper_status_summary.radar_raw_packet_proof_freshness_status`
- `upper_status_summary.radar_raw_packet_proof_age_seconds`
- `upper_status_summary.radar_raw_packet_proof_latest_status`
- `upper_status_summary.radar_raw_packet_proof_bytes_read`
- `upper_status_summary.radar_raw_packet_proof_sync_header_count`
- `upper_status_summary.radar_raw_packet_proof_packets_parse_ok`
- `upper_status_summary.radar_raw_packet_proof_points_total`
- `upper_status_summary.radar_raw_packet_proof_safe_to_control=false`
- `upper_status_summary.map_proof_latest_status`
- `upper_status_summary.map_proof_artifact_status`
- `upper_status_summary.map_proof_artifact_path`
- `upper_status_summary.map_proof_canonical_path`
- `upper_status_summary.map_proof_resolved_path`
- `upper_status_summary.map_proof_configured_path`
- `upper_status_summary.map_proof_compatibility_paths`
- `upper_status_summary.map_proof_failure_reason`
- `upper_status_summary.map_proof_blockers`
- `upper_status_summary.map_proof_safe_to_control=false`
- `upper_status_summary.lidar_port`
- `upper_status_summary.base_port`
- `upper_status_summary.base_baudrate`
- `upper_status_summary.base_write_control_available`
- `upper_status_summary.robot_ack_connected=false`
- `upper_status_summary.t1001_observed=false`
- `local_api_paths.status/stop/feedback_request/manual/radar_start/radar_stop/scan_proof_refresh/scan_proof_latest/map_start/map_reset/map_save/map_load/map_list/map_proof_latest/localize_reset/operator_report`

固定安全字段：

- `production_4g_cloud_route_changed=false`
- `safe_to_control=false`
- `sends_cmd_vel=false`
- `sends_wave_rover_json_directly=false`
- `robot_control_executed=false`
- `robot_ack_connected=false`
- `t1001_observed=false`

fixture status 边界：

- 只有 `ROBER_O7_DIRECT_UPPER_FIXTURE_MODE=1` 会让 status 返回 fixture 摘要；请求 body 不能影响 `GET /status`。
- fixture status 返回 `status=ready` 只是为了 PC workflow 演示可继续，不证明上位机 8787 在线。
- fixture status 的 `health_request.executed=false`、`status_request.executed=false`，`failure_reason=fixture_mode_no_upper_runtime`。
- fixture status 的 `map_lifecycle_status=fixture_ready_not_proven`、`map_artifact_ref=fixture_map_not_written`、`localization_status=fixture_pose_not_published`。
- fixture status 的 `map_proof_latest_status=fixture_not_runtime`、`map_proof_artifact_path=fixture_not_runtime`、`map_proof_safe_to_control=false`。
- fixture status 固定 `safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`。

## 共通请求字段

控制、雷达、建图、定位和 report 入口共享以下 operator 字段：

```json
{"evidence_ref":"operator_field_report_pending","fixture_mode":false}
```

- `evidence_ref`：operator 当前现场材料引用。PC 会把空值压成 `missing_operator_evidence_ref`，并写入 `command_payload_summary.evidence_ref`。
- `fixture_mode`：单次请求 fixture 开关。为 `true` 时不执行上位机 fetch，`upper_request.executed=false`、`upper_request.ok=true`、`upper_request.failure_reason=fixture_mode_no_upper_fetch`。
- 所有 command response 都包含 `adapter`、`upper_api_base_url_source`、`upper_request`、`command_payload_summary`、`blocked_reasons`、`not_proven` 和固定安全字段。
- fixture command response 仍追加 `fixture_mode_no_upper_runtime`、`field_evidence_not_proven`、`robot_ack_not_connected`、`t1001_feedback_not_observed`，不得被解释成真实 runtime 或现场材料通过。

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
- 未配置 base URL 且没有 fixture mode 时，PC 返回 `400`，不触发远端 fetch。
- fixture mode 时，PC 返回 `200`，`upper_request.executed=false`，不触发远端 fetch。
- `command_payload_summary.evidence_ref` 保留 operator 当前 evidence ref。
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
- 未配置 base URL 且没有 fixture mode 时，PC 返回 `400`，不触发远端 fetch。
- fixture mode 时，PC 返回 `200`，`upper_request.executed=false`，不触发远端 fetch。
- `command_payload_summary.evidence_ref` 保留 operator 当前 evidence ref。
- 即使远端 JSON 声称包含 `T=1001`，PC 响应仍固定 `safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`；它只说明请求被转发，不证明真实 ACK、HIL 或 `T=1001` 已由同源材料验收。

## `POST /api/o7/direct-upper/radar/start`

PC 后端只转发到：

```text
<upper_api_base_url>/api/radar/start
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_radar_start.v1
```

边界：

- 缺少 `ROBER_UPPER_API_BASE_URL` 时使用 `http://192.168.1.11:8787`，响应中 `upper_api_base_url_source=field_default`。
- 显式 fixture mode 优先于 field default，响应中 `upper_api_base_url_source=fixture` 且不触发远端 fetch。
- 上位机 HTTP 2xx 且返回 object JSON 时，PC 返回 `200`，`failure_reason=none`，`upper_request.executed=true`，`upper_request.path=/api/radar/start`。
- 上位机 HTTP 非 2xx、超时或 fetch 失败时，PC 可返回 `502`，但仍必须保留 `upper_request.executed=true`，并显示真实失败如 `upper_http_503` / `timeout` / fetch error；不得回落到 `base_url_not_configured` 或 `/api/radar/start not_executed`。
- `robot_ack_not_connected`、`t1001_feedback_not_observed`、`field_evidence_not_proven` 继续作为 safety/not_proven gaps 保留，但不得阻止 LiDAR start HTTP 转发。
- 响应仍固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`；PC 不访问 ROS graph、不打开 LiDAR 串口、不访问 `/dev/ttyS5`、不发送 WAVE ROVER JSON。

## `POST /api/o7/direct-upper/radar/stop`

PC 后端只转发到：

```text
<upper_api_base_url>/api/radar/stop
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_radar_stop.v1
```

边界与 `radar/start` 相同：缺 env 可使用 `field_default`，HTTP 成功返回 `200` / `failure_reason=none`，但不证明真实 `/scan`、LiDAR 长稳、SLAM/Nav2 消费、ACK 或 HIL。

## `POST /api/o7/direct-upper/radar/scan-proof/refresh`

PC 后端只转发到：

```text
<upper_api_base_url>/api/radar/scan-proof/refresh
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_radar_scan_proof_refresh.v1
```

边界：

- 缺少 `ROBER_UPPER_API_BASE_URL` 时使用 `http://192.168.1.11:8787`，响应中 `upper_api_base_url_source=field_default`。
- 显式 fixture mode 优先于 field default，响应中 `upper_api_base_url_source=fixture` 且不触发远端 fetch。
- 该入口只请求上位机刷新只读 scan proof artifact；PC workstation 不执行 collector、不连接 ROS graph、不打开 LiDAR 串口、不发送 `A5 60`、不访问 `/api/base/manual`、不发送 `/cmd_vel`、不构造 WAVE ROVER JSON，也不触发底盘运动。
- 上位机 HTTP 2xx 且返回 object JSON 时，PC 返回 `200`，`upper_request.executed=true`，`upper_request.path=/api/radar/scan-proof/refresh`。这只证明 PC 同源请求到达 upper read-only refresh route，不证明 fresh `/scan` 或 ROS2 runtime 已验收。
- PC command response 会额外返回 `upper_result_summary`，把上位机业务结果和 HTTP 转发结果拆开展示。字段包括 `status`、`proof_status`、`latest_proof_status`、`artifact_status`、`artifact_path`、`freshness_status`、`freshness_age_seconds`、`fresh_scan_proof_observed`、`scan_hz_average_rate_hz`、`tf_observed`、`all_required_observations_observed`、`runtime_summary_fallback_used`、`runtime_summary_path`、`continuous_scan_status`、`continuous_blocked_reasons`、`blocked_reasons`、`not_proven`，并固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。
- `fresh_scan_proof_observed=true`、`scan_hz_average_rate_hz=<number>` 和 `tf_observed=true` 只证明本次 upper read-only refresh 返回了 fresh proof 机器摘要；如果 `continuous_scan_status=not_proven`，PC 必须继续把 `continuous_scan_status_not_proven` 和 continuous blockers 放入 `blocked_reasons`，并在 `not_proven` 中保留 `continuous_radar_not_proven`。
- 如果上位机 HTTP `200` 但 body 仍是 `status=not_proven` / `proof_status=not_proven` 或返回 `blocked_reasons`，PC 仍返回真实 HTTP code，但 `fail_closed=true`，`blocked_reasons` 会包含远端 blocker，例如 `ros2_command_unavailable`、`upper_api_scan_not_proven`。UI 必须显示 `upper_result=not_proven/...` 和 `upper_blockers=...`，不得只显示成 refresh 已完成。
- 如果上位机 HTTP `200` 且 fresh proof 字段完整，但 `continuous_scan_status=not_proven`，PC 仍返回 `fail_closed=true`。UI 必须显示 `fresh=true`、`hz=...`、`tf=observed`、`fallback=true|false`、`continuous=not_proven` 和 `continuous_blockers=...`，不得把 fresh artifact 包装成 `continuous radar ready`。
- 上位机 HTTP 非 2xx、超时、fetch 失败或坏 JSON 时，PC 返回 `502` 并保留真实失败，如 `upper_http_404`、`upper_http_405`、`upper_http_503`、`timeout` 或 `bad_json`；不得包装成成功，也不得回落为 `/api/radar/start` 或底盘控制失败。
- command response 继续固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`。
- `not_proven` 必须继续包含 HIL、PC WASD 控车、Nav2 消费、SLAM map、delivery success、driver start/stop 等边界；即使 remote refresh 返回 fresh artifact，也不能声明 HIL、PC WASD、Nav2、map 或送达成功。

## `GET /api/o7/direct-upper/radar/scan-proof/latest`

PC 后端只读转发到：

```text
<upper_api_base_url>/api/radar/scan-proof/latest
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_radar_scan_proof_latest.v1
```

边界：

- 缺少 `ROBER_UPPER_API_BASE_URL` 时使用 `http://192.168.1.11:8787`，响应中 `upper_api_base_url_source=field_default`。
- 该入口只做 latest artifact readback，不触发上位机 refresh，不执行 collector，不启动 ROS2/LiDAR runtime，不打开 LiDAR 串口，不访问 `/api/base/manual`、`/cmd_vel`、WAVE ROVER JSON 或底盘运动。
- PC command envelope 与 refresh 共用 `upper_result_summary` 字段，便于 curl 直接看到 `proof_status/latest_proof_status`、artifact、hz、TF、`runtime_summary_fallback_used`、`continuous_scan_status` 和 blocker。
- 即使 latest 返回 `scan_once_hz_raw_packet_tf_observed`，只证明最近一次 artifact 可回读；如果 `continuous_scan_status` 缺失或为 `not_proven`，PC 仍保留 `continuous_radar_not_proven`、`safe_to_control=false`、`robot_control_executed=false`、`hil_pass` 等边界。
- 上位机 HTTP 非 2xx、超时、fetch 失败或坏 JSON 时，PC 返回 `502`，不得落入构建后的 SPA HTML fallback，也不得包装成 runtime success。

## `POST /api/o7/direct-upper/base/manual`

请求示例：

```json
{"direction":"forward","speed":0.05,"duration_ms":250}
```

PC 侧限制：

- `direction` 只允许 `forward/back/left/right/stop`。
- `speed` 取绝对值并限制到 `<=0.08 m/s`。
- `duration_ms` 限制到 `1..350ms`。
- 本机代理远端 fetch timeout 为 `5500ms`；该值只影响 manual，不影响 status 的 `1200ms` 短超时。
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

manual 也保留 `command_payload_summary.evidence_ref`。缺少 `ROBER_UPPER_API_BASE_URL` 且没有 fixture mode 时返回 `400 base_url_not_configured`；fixture mode 时返回 `200`，不触发上位机 fetch，但仍记录 clamp 后的方向、速度、duration 与 `evidence_ref`。

## `POST /api/o7/direct-upper/map/start|reset|save|load`

PC 后端只转发到显式 env 指向的上位机：

```text
<ROBER_UPPER_API_BASE_URL>/api/map/start
<ROBER_UPPER_API_BASE_URL>/api/map/reset
<ROBER_UPPER_API_BASE_URL>/api/map/save
<ROBER_UPPER_API_BASE_URL>/api/map/load
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_map_start.v1
trashbot.pc_tools_workstation.o7_direct_upper_map_reset.v1
trashbot.pc_tools_workstation.o7_direct_upper_map_save.v1
trashbot.pc_tools_workstation.o7_direct_upper_map_load.v1
```

边界：

- 不使用 field default。缺 env 且没有 fixture mode 时返回 `400 base_url_not_configured`，不触发远端 fetch。
- `map/save` 和 `map/load` 的 `command_payload_summary.map_id` 来自 body `map_id`，缺失时为 `not_provided`。
- 每个 map command 都保留 `command_payload_summary.evidence_ref`。
- fixture mode 时返回 `200`，`upper_api_base_url_source=fixture`，`upper_request.executed=false`，不写 map artifact。
- 即使远端 HTTP 成功，PC 仍不证明真实 SLAM Toolbox、真实 `/map`、map file、map server、Nav2 消费或地图质量通过。

## `GET /api/o7/direct-upper/map/list`

PC 后端只转发到显式 env 指向的上位机：

```text
<ROBER_UPPER_API_BASE_URL>/api/map/list
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_map_list.v1
```

边界：

- 不使用 field default。缺 env 且没有 fixture mode 时返回 `400 base_url_not_configured`，不触发远端 fetch。
- 因为 `GET` 不使用 JSON request body，普通 UI 调用会通过 query 传 `evidence_ref` 和 `fixture_mode=true`，例如 `/api/o7/direct-upper/map/list?evidence_ref=operator_field_report_pending&fixture_mode=true`。
- server helper 仍支持测试或内部调用携带 `body.fixture_mode=true`，但浏览器入口以 query 为准。
- fixture mode 时返回 `200`，`upper_request.executed=false`，不读取真实 map artifact 目录。
- 文件候选存在不能证明 map 可被 AMCL/Nav2 消费，也不能证明地图质量通过。

## `GET /api/o7/direct-upper/map/proof/latest`

PC 后端只转发到显式 env 指向的上位机：

```text
<ROBER_UPPER_API_BASE_URL>/api/map/proof/latest
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_map_proof_latest.v1
```

边界：

- 不使用 field default。缺 env 且没有 fixture mode 时返回 `400 base_url_not_configured`，不触发远端 fetch。
- 该入口只读回放 upper map proof latest，不触发 `/api/map/proof/refresh`、SLAM Toolbox、map server、AMCL 或 Nav2。
- `upper_result_summary.artifact_path`、`map_proof_canonical_path`、`map_proof_resolved_path`、`map_proof_configured_path` 和 `map_proof_compatibility_paths` 用于核对 O10 path contract。
- 如果 upper 返回旧 runtime fallback 路径，PC 只展示 compatibility/path 边界，不把它改写成 canonical success。
- 响应仍固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`，也不证明 AMCL/Nav2 消费地图。

## `POST /api/o7/direct-upper/localize/reset`

PC 后端只转发到显式 env 指向的上位机：

```text
<ROBER_UPPER_API_BASE_URL>/api/localize/reset
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_localize_reset.v1
```

边界：

- 不使用 field default。缺 env 且没有 fixture mode 时返回 `400 base_url_not_configured`，不触发远端 fetch。
- `command_payload_summary.evidence_ref` 保留 operator 当前 evidence ref。
- fixture mode 时返回 `200`，`upper_request.executed=false`，不发布 `/initialpose`。
- 即使远端 HTTP 成功，PC 仍不证明 AMCL lifecycle、`/amcl_pose`、TF、定位恢复或 Nav2 可用。

## `POST|GET /api/o7/direct-upper/operator-report`

PC 后端转发到上位机 operator report artifact 入口；缺少显式 env 时允许使用现场默认 8787：

```text
<upper_api_base_url>/api/operator/report
```

POST 请求示例：

```json
{"evidence_ref":"operator_field_report_pending","note":"not_proven: waiting for field evidence","fixture_mode":false}
```

GET readback 示例：

```text
/api/o7/direct-upper/operator-report?evidence_ref=operator_field_report_pending
```

响应 schema：

```text
trashbot.pc_tools_workstation.o7_direct_upper_operator_report.v1
```

边界：

- 缺 env 且没有 fixture mode 时使用 `http://192.168.1.11:8787`，响应中 `upper_api_base_url_source=field_default`。
- `POST` 只写入上位机 operator report latest artifact；`GET` 只回读该 latest artifact。
- 该入口不访问 `/api/base/manual`、`/api/base/stop`、`/api/base/feedback-request`、`/api/base/status`、ROS graph、串口或 LiDAR endpoint。
- `command_payload_summary.evidence_ref` 保留 operator 当前 evidence ref。
- `command_payload_summary.report_note` 最多保留前 120 个字符。
- fixture mode 时返回 `200`，`upper_request.executed=false`，只证明 PC workflow 可以生成 report envelope。
- operator report 不能替代 stop response、post-status、T=1001 vendor material、robot ACK、HIL 或视频/现场记录。

## 前端入口

`O7LiveOperatorPanel.vue` 的默认首屏新增 `PC 本机 8787 接口` 卡片：

- 展示 direct mode 状态。
- 展示 `adapter.version`、`adapter.source` 和 field default 是否启用；缺少 `adapter` 时显示 `stale_dev_server_missing_adapter`。
- 展示 `ROBER_UPPER_API_BASE_URL`。
- 展示本机 API path，包含 `scan-proof/latest` 和 `map/proof/latest`，方便浏览器/curl 工具消费。
- 展示 cloud relay 已绕过和 ACK/T=1001 not observed 边界。
- 展示 8787 `radar.scan_proof_latest` 摘要：artifact status、freshness、age、latest proof status 和 top blockers。
- 展示 8787 fresh scan proof runtime 摘要：`fresh`、`hz`、`tf`、`fallback` 和 `continuous`；这些字段来自 direct-upper 后端契约，前端不得硬编码假状态。
- `continuous=not_proven` 和 continuous blockers 必须与 fresh artifact 分开展示，不能把一次 refresh artifact 解释成 continuous radar ready。
- 展示 8787 `radar.raw_packet_proof_latest` 摘要：artifact status、freshness、age、latest proof status、bytes、sync、packets 和 points。
- 展示 8787 `map proof latest` 摘要：latest status、artifact status/path、canonical/resolved/configured/compatibility paths、failure reason、top blockers 和 `safe_to_control=false`。

2026-06-03 23-24 micro sprint 后，`前进`、`后退`、`左转`、`右转`、`Stop`
按钮不再只调用本地 `showLocked()`，而是通过 client helper POST PC 同源：

```text
/api/o7/direct-upper/base/manual
```

浏览器仍不会直接访问上位机 8787，也不会访问 `/api/base/manual`、`/cmd_vel`
或 WAVE ROVER JSON 串口。UI 会展示本机代理返回的结果：

- 上位机 HTTP 2xx 且返回 JSON：显示“已发送（仍锁定）”、`upper_request.path`、
  HTTP 状态、`ACK not observed`、`T=1001 not observed`、`blocked_reasons` 和
  `safe_to_control=false`。
- 未配置 `ROBER_UPPER_API_BASE_URL`：显示 `base_url_not_configured`，PC 后端返回
  `400`，远端 fetch 不执行。
- 远端非 2xx、超时、fetch 失败或坏 JSON：显示 PC 后端返回的 `failure_reason`，
  通常为 `upper_http_<status>`、`timeout`、`bad_json` 或 fetch error，PC 后端返回
  `502`。
- 所有 direct-upper command 结果都显示 `source=<upper_api_base_url_source>` 和
  `adapter=<adapter.version>`；缺失 adapter 时显示 `missing_adapter_stale_dev_server`，
  用来区分旧 5173 middleware 和真实上位机失败。
- direct status 不是 `ready` 时，按钮结果会把当前 `direct status` 一并显示，避免
  operator 误以为已进入闭环可控状态。
- `W/A/S/D` 键盘快捷键与按钮等价，分别请求 `forward/left/back/right`；`Space` 和
  `X` 请求 `stop`。前端会忽略输入框、滑条、可编辑区域焦点，以及 repeat keydown，避免把长按键变成连续点动。
- `forward/back` 使用当前速度滑块和 `250ms`；`left/right` 使用更明显的 turn pulse：
  UI 请求 `speed=0.08`、`duration_ms=350`，然后仍由 PC 后端和 8787 做二次 clamp 与
  fail-closed；`stop` 请求 `speed=0`。

即使按钮 POST 成功，响应仍固定 `safe_to_control=false`、
`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`。
这只证明 PC 本机 manual 代理请求已发出，不证明真实 ACK、HIL、运动安全或 delivery
success。

## 证据边界

本轮只证明 PC 本机 API 层、前端入口和 mock/fetch 单测：

- 不证明生产 4G 云 relay。
- 不证明真实 ROS2 `/cmd_vel`。
- 不证明真实 `/odom`、`/imu/data`、`/battery`。
- 不证明 `T=1001` 或 robot ACK。
- 不证明真实 stop/manual 已现场执行或真实点动已被 ACK 闭环确认。
- 不证明 continuous radar ready；fresh scan proof artifact、hz 和 TF 只证明一次 read-only refresh 摘要。
- 不证明真实 SLAM/map 可用；map proof latest 只证明 path contract readback，不证明 AMCL/Nav2 consumption。
- 不证明 PC WASD 控车已经现场验收。
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
- `POST /api/o7/direct-upper/radar/scan-proof/refresh` 的按钮结果还会显示本次 POST 的
  `upper_result_summary`，因此 deployed upper route 从 `405` 变成 `200` 后，如果 ROS2
  command 仍不可用，operator 会看到 `upper_result=not_proven/not_proven/...`、
  `upper_blockers=ros2_command_unavailable / upper_api_scan_not_proven` 和 artifact/freshness 摘要，
  不会被 UI 包装成 runtime success。
- PC 不执行 collector、不启动 ROS2、不打开 LiDAR 串口、不发送 `A5 60`，也不发送底盘运动命令。
- `upper_status_summary.radar_raw_packet_proof_*` 来自 8787
  `/api/status.radar.raw_packet_proof_latest`。
- raw packet proof artifact `loaded` 只代表 latest raw bytes/packet/point JSON
  可回放；PC 不执行 raw packet collector、不启动 ROS2、不打开 LiDAR 串口、不发送
  `A5 60` 或底盘命令。

这些材料仍不能声明真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、ACK/HIL、`safe_to_control=true` 或完整上车任务完成。

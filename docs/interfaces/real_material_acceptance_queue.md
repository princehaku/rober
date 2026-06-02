# Real Material Acceptance Queue API

## 定位

`GET /api/real-material/acceptance` 是 PC workstation 的 O5/O6/O7 真实材料验收队列。它把已有证据材料转成 operator 可读、机器可测的 acceptance queue / next actions。

该接口是只读摘要，不是 probe runner、控制面、WebRTC session manager 或 OKR 自动收口器。

## Source Inputs

接口只允许消费已有本地 JSON 材料：

- O5/O6：`GET /api/o5-o6/external-probe-artifact` 的脱敏摘要，来源是 `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 或 `.workstation-runtime/o5-o6-external-live-probe.json`。
- O7：`ROBER_O7_BROWSER_SMOKE_RESULT_JSON` 或 `.workstation-runtime/o7-browser-playback-smoke.json`。

禁止行为：

- 不执行 O5/O6 external probe。
- 不联网，不主动访问公网、私网、LAN camera 或 cloud relay。
- 不读取硬件、串口、ROS2、Nav2、摄像头设备或 WAVE ROVER。
- 不 POST，不访问 `/robots/*`，不访问 `/cmd_vel`。
- 不创建 WebRTC session，不发送 `/offer`。
- 不发送任何机器人控制命令。

## Response Schema

顶层 schema：

- `schema=trashbot.pc_tools_workstation.real_material_acceptance.v1`
- `endpoint=/api/real-material/acceptance`
- `source=software_proof`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `queue_status=accepted | action_required`

固定执行策略：

```json
{
  "reads_existing_artifacts_only": true,
  "network_probe_executed": false,
  "hardware_read_executed": false,
  "post_executed": false,
  "robots_path_accessed": false,
  "webrtc_session_created": false,
  "sends_commands": false
}
```

固定 fail-closed flags：

```json
{
  "safe_to_control": false,
  "sends_commands": false,
  "robot_control_executed": false
}
```

## Queue Items

`items[]` 固定包含三条：

| id | Objective | 材料 |
|---|---|---|
| `o5_tls_external_probe` | O5 | TLS / external probe material |
| `o6_archive_external_probe` | O6 | archive external probe material |
| `o7_browser_long_stability` | O7 | browser 3-5min long stability material |

每条 item 字段：

- `status=accepted | needs_long_run | not_observed | blocked`
- `source_endpoint=/api/o5-o6/external-probe-artifact | /api/o7/local-webrtc-camera`
- `source_artifact_status`：源 artifact 的加载状态，例如 `loaded`、`missing`、`bad_json`。
- `artifact_freshness`：只读 `stat` 已配置或默认 artifact 文件，不打开网络、不创建文件、不执行采集。
  - `status=fresh | stale | missing | not_applicable`
  - `artifact_ref` 只允许显示 `env:<ENV_NAME>` 或 `.workstation-runtime/<file>.json`，不得显示绝对路径。
  - `mtime` / `age_seconds` / `stale_after_seconds` 用于 operator 判断材料是否过期。
- `collection_runbook`：operator 可读采集 runbook，不会由 API 自动执行。
  - `goal`：采集目标。
  - `suggested_commands[]`：安全 recipe / 脚本入口说明。
  - `required_env[]`：需要准备的环境变量。
  - `required_artifacts[]`：期望落盘或通过 env 指向的 artifact。
  - `expected_output`：期望输出 schema。
  - `success_criteria[]`：成功判定。
  - `failure_handling[]`：失败处理。
  - `safety_notes[]`：安全边界。
- `blocking_reason`：单个机器可读阻塞原因。
- `next_action`：operator 下一步动作，不会由接口自动执行。
- `proof_boundary`：本条材料的证明边界。
- `observed_at`：artifact 的安全更新时间或 `null`。
- `safe_to_control=false`
- `sends_commands=false`
- `robot_control_executed=false`

## Status Semantics

O5/O6 item：

- `accepted`：external probe artifact 已加载，TLS summary 为 `tls_status=observed` 且 `tls_observed=true`，对应 endpoint `reachable=true`、`schema_status=matched`，且 `contract_status=observed_fail_closed_contract` 或 `pass`。
- `not_observed`：artifact 缺失、坏 JSON、schema 不匹配，或 expected endpoint 未出现在 artifact 中。
- `blocked`：artifact 已加载但 TLS、endpoint reachability、schema 或 contract status 未满足 accepted 条件。
- `needs_long_run`：O5/O6 不使用该状态。

O7 item：

- `accepted`：browser smoke JSON 已加载，`status=ok`、`first_frame_received=true`，`stability_summary.status=observed`，观察窗口 `>=180000ms`，连接/ICE 持续 connected，视频尺寸 stable，console/page error 增量为 0，且 post-close peer cleanup 为 0 / cleaned。
- `needs_long_run`：除观察窗口 `<180000ms` 外，其余 O7 长稳态条件满足。30s browser artifact 必须落入该状态，不能冒充 accepted。
- `not_observed`：browser smoke artifact 缺失、坏 JSON、未运行，或没有 stability observation。
- `blocked`：artifact 已观察到但首帧、连接、ICE、视频尺寸、错误增量或 peer cleanup 任一关键条件失败。若 browser smoke artifact 已有 `status=failed|fail_closed|degraded`，`blocking_reason` 必须优先暴露脱敏后的 `failure_category`、关键失败 token 和 `remote_health_status`，例如 `browser_smoke_failed__net_err_connection_refused__remote_health_unreachable`；不得退化成笼统的 `first_frame_not_received`。

## Artifact Freshness Semantics

Freshness 只回答“这个 artifact 文件是否存在、mtime 多新”，不回答 artifact 内容是否通过验收：

- `fresh`：文件存在，`age_seconds <= 86400`。
- `stale`：文件存在，但 `age_seconds > 86400`，operator 应优先重采。
- `missing`：`stat` 失败或文件不存在。
- `not_applicable`：当前 item 无可检查 artifact 时保留的兼容状态；现有三条固定 item 默认都有 artifact ref。

Freshness 不能覆盖 `status`：例如坏 JSON 可能 freshness 是 `fresh`，但 item 仍必须 `not_observed` 或 `blocked`。

## Collection Runbook Semantics

Runbook 是 recipe，不是执行结果。API 返回 runbook 时仍必须保持：

- 不执行 probe。
- 不联网。
- 不 SSH。
- 不 POST。
- 不创建 WebRTC session。
- 不读取硬件。
- 不发送控制。

O5/O6 runbook 指向现有 `npm run o5o6:external-probe`，要求 operator 准备 `ROBER_PC_BASE_URL`、`ROBER_CLOUD_BASE_URL` 和 `ROBER_O5_O6_BEARER_TOKEN`，并把输出落到 `.workstation-runtime/o5-o6-external-live-probe.json` 或通过 `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 指向。

O7 runbook 现在先指向 `npm run o7:camera-service-readiness`，再指向 `npm run o7:browser-long-stability`。当上一份 browser smoke artifact 已经显示 `ERR_CONNECTION_REFUSED` / `remote_health_unreachable` 时，queue 的 `next_action` 必须优先提示 readiness collector，先确认板端 HTTP/WebRTC camera 服务是否监听、SSH 是否可达、端口/进程线索是否存在，再重跑 180s 长稳态。

`npm run o7:camera-service-readiness` 默认检查：

- HTTP GET `http://192.168.1.11:8088/health`
- HTTP GET `http://192.168.1.11:8088/devices`
- SSH `root@192.168.1.11 -p 37878` 上的只读诊断：`uname`、`ss`/`netstat` 监听摘要、camera/WebRTC 相关进程摘要

可通过 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL` / `--base-url`、`ROBER_O7_CAMERA_SERVICE_SSH_TARGET` / `--ssh-target`、`ROBER_O7_CAMERA_SERVICE_SSH_PORT` / `--ssh-port` 覆盖目标；输出 artifact 默认为 `.workstation-runtime/o7-camera-service-readiness.json`，schema 为 `trashbot.o7.camera_service_readiness.v1`。该 collector 不 POST `/offer`、不创建 WebRTC session、不读取串口/底盘/ROS2 控制、不发送机器人控制命令。

readiness artifact 的关键分类字段包括：

- `readiness.http_health_unreachable`
- `readiness.http_connection_refused`
- `readiness.ssh_unreachable`
- `readiness.port_not_listening`
- `readiness.process_hint_missing`
- `readiness.ready_for_long_stability`

只有 `ready_for_long_stability=true` 后，operator 才应继续运行 `npm run o7:browser-long-stability`。长稳态入口仍要求 operator 准备 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL`，默认委托现有 `scripts/o7-browser-playback-smoke.mjs`，并把 `ROBER_O7_BROWSER_SMOKE_STABILITY_MS` 强制提升到 `>=180000`，输出落到 `.workstation-runtime/o7-browser-playback-smoke.json` 或通过 `ROBER_O7_BROWSER_SMOKE_RESULT_JSON` 指向。

2026-06-02 11-12 真实采集记录：默认 `http://192.168.1.11:8088/` 运行 `npm run o7:browser-long-stability` 时，browser smoke artifact 为 `status=failed`，`failure_category=browser_smoke_failed`，`remote_health_status=remote_health_unreachable`，`start_clicked=false`，`offer_executed_by_browser=false`，`first_frame_received=false`，`stability_summary.status=not_observed`，`server_peer_close_status=not_attempted`；脱敏后 queue 的 O7 `blocking_reason` 应显示 `browser_smoke_failed__net_err_connection_refused__remote_health_unreachable`。该结果说明板端 HTTP/WebRTC 服务当前拒绝连接或未监听，不是 180s 稳定性窗口失败；本轮未创建 WebRTC session、未 POST `/offer`、未拿到首帧。

本地无相机或只想校验命令入口时，可运行：

```bash
cd pc-tools/workstation && npm run o7:camera-service-readiness -- --dry-run
cd pc-tools/workstation && npm run o7:browser-long-stability -- --dry-run
```

readiness dry-run 只输出 `trashbot.o7.camera_service_readiness.v1` 机器可读 JSON，固定 `network_probe_executed=false`、`ssh_probe_executed=false`、`post_executed=false`、`webrtc_session_created=false`、`offer_executed=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`，且不写 artifact。long-stability dry-run 只输出 `trashbot.o7.browser_long_stability_collector.v1` 机器可读 JSON，固定 `network_probe_executed=false`、`post_executed=false`、`webrtc_session_created=false`、`artifact_written=false` 和控制安全字段；它不联网、不 POST `/offer`、不创建 WebRTC session、不写 artifact，因此不能作为 O7 180s 真实材料。

## UI Contract

O7 Console 首屏的 `真实材料验收队列` 只能展示后端返回的 queue item，不得在 Vue 侧二次推断材料是否 accepted。

UI 必须展示：

- status summary：`accepted / needs_long_run / not_observed / blocked`
- 每条 item 的 objective、status、source endpoint、artifact status、artifact freshness、runbook 摘要、blocking reason、next action、proof boundary
- fail-closed flags
- execution policy

UI 不得展示 raw cloud base URL、token、artifact path、traceback、证书完整 DN、SAN 域名列表、设备路径或 SSH 目标。

## 不可外推

即使三条 item 都是 `accepted`，该接口也不证明：

- 机器人可控制。
- delivery success。
- O5 真实 4G/SIM、production DB/queue、OSS/CDN live traffic 完整通过。
- O6 真实生产归档、真实 OSS upload、真实模型 runtime 或真实上车数据完成。
- O7 真实公网/云 relay/TURN/鉴权、真实手机体验或真实 safe command dispatch 完成。
- O1 WAVE ROVER、UART、LiDAR、HIL 或任何硬件能力完成。

OKR 进度仍需 Product / OKR Owner 基于真实材料和 sprint 证据单独判定。

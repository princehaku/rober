# Real Material Acceptance Queue API

## 定位

`GET /api/real-material/acceptance` 是 PC workstation 的 O5/O6/O7 真实材料验收队列。它把已有证据材料转成 operator 可读、机器可测的 acceptance queue / next actions。

该接口是只读摘要，不是 probe runner、控制面、WebRTC session manager 或 OKR 自动收口器。

## Source Inputs

接口只允许消费已有本地 JSON 材料：

- O5/O6：`GET /api/o5-o6/external-probe-artifact` 的脱敏摘要，来源是 `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 或 `.workstation-runtime/o5-o6-external-live-probe.json`。该 artifact 可由 PC Node probe、上位机 Python stdlib probe，或 PC 侧 SSH collector 拉回生成。
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
  - `suggested_commands[]`：兼容旧 UI 的安全 recipe / 脚本入口摘要。
  - `collection_paths[]`：结构化采集路径列表；O5/O6 item 会列出 PC Node、上位机 Python、PC 侧 SSH collector 三条入口，O7 item 仍沿用 `suggested_commands[]`。
    - `id=pc_node_npm | upper_computer_python_stdlib | pc_upper_ssh_collector`
    - `runtime=node | python_stdlib | node_ssh`
    - `host_role=pc_workstation | upper_computer | pc_to_upper_computer`
    - `command`：人工执行命令；API 不执行该命令。
    - `preflight_checks[]`：该路径进入采集前必须人工确认或由 dry-run 输出的预检项。
    - `failure_classification[]`：该路径会暴露的机器可读失败分类 token，方便测试和 runbook 不靠自然语言判断。
    - `required_env[]`：该路径需要的环境变量。
    - `required_artifact`：该路径的 artifact 落盘或回传方式。
    - `artifact_write_mode=writes_output_file | stdout_json_optional_output`
    - `success_criteria[]`：该路径的成功门槛。
    - `safety_notes[]`：该路径的 no POST / no `/robots/*` / no hardware read / no robot command 边界。
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

O5/O6 runbook 必须同时暴露 PC 本地、上位机本地、PC 侧 SSH 三类采集路径，避免真实材料采集只依赖 PC Node/npm 环境，也避免上位机 stdout artifact 需要人工复制：

1. `pc_node_npm`
   - 运行位置：PC workstation。
   - runtime：Node。
   - 命令入口：
     `cd pc-tools/workstation && ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL=http://127.0.0.1:8787 ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL=https://<production-cloud-base> TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=<redacted> npm run o5o6:external-probe -- --output .workstation-runtime/o5-o6-external-live-probe.json`
   - 所需 env：
     `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL`、
     `ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL` 或 `ROBER_CLOUD_RELAY_BASE_URL`、
     `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN` 或 `ROBER_CLOUD_RELAY_BEARER_TOKEN`。
   - artifact：`.workstation-runtime/o5-o6-external-live-probe.json`，或由 `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 指向。

2. `upper_computer_python_stdlib`
   - 运行位置：上位机（Orange Pi / Ubuntu 环境），适合没有 npm/node_modules 的现场采集。
   - runtime：Python stdlib only。
   - 命令入口：
     `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL=http://<pc-workstation-host>:8787 ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL=https://<production-cloud-base> TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=<redacted> python3 cloud-relay/scripts/o5_o6_external_live_probe.py --once-json --output .workstation-runtime/o5-o6-external-live-probe.json`
   - 所需 env：
     `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL`、
     `ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL` 或 `ROBER_CLOUD_RELAY_BASE_URL`、
     `TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN` 或 `ROBER_CLOUD_RELAY_BEARER_TOKEN`。
   - artifact：脚本 stdout 输出 `trashbot.o5_o6.external_live_probe.v1` JSON；传 `--output` 时写入 JSON 文件。operator 可把该文件复制回 PC workstation `.workstation-runtime/o5-o6-external-live-probe.json`，或用 `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` 指向实际路径。

3. `pc_upper_ssh_collector`
   - 运行位置：PC workstation，通过 SSH 在上位机执行 Python stdlib probe，并把 stdout JSON 拉回 PC runtime artifact。
   - runtime：Node + SSH + remote Python stdlib。
   - 执行模式：
     - `installed_script`：默认先进入远端 `remote_root`，执行已安装的 `cloud-relay/scripts/o5_o6_external_live_probe.py`。
     - `stdin_fallback`：若 SSH 可达、`remote_root` 可进入，但远端缺 probe 脚本，collector 会把 PC 本地 `cloud-relay/scripts/o5_o6_external_live_probe.py` 通过 SSH stdin 喂给 `python3 -` 一次性只读执行；不 scp、不写远端文件、不持久修改上位机。
  - 命令入口：
     `cd pc-tools/workstation && npm run o5o6:upper-ssh-collector -- --ssh-command "ssh <upper-ssh-target> -p <ssh-port>" --pc-base-url http://<pc-workstation-host>:8787 --cloud-base-url https://<production-cloud-base> --output .workstation-runtime/o5-o6-external-live-probe.json`
  - 可覆盖参数/env：
     `--ssh-command "ssh root@192.168.1.11 -p 37878"`（operator 可粘贴实际 SSH 入口；acceptance API 只展示占位符，不回显真实 IP/账号）、
     `ROBER_O5_O6_UPPER_SSH_TARGET` / `--ssh-target`、
     `ROBER_O5_O6_UPPER_SSH_PORT` / `--ssh-port`、
     `ROBER_O5_O6_UPPER_REMOTE_ROOT` / `--remote-root`、
     `ROBER_O5_O6_UPPER_REMOTE_SCRIPT` / `--remote-script`、
     `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL` / `--pc-base-url`、
     `ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL` 或 `ROBER_CLOUD_RELAY_BASE_URL` / `--cloud-base-url`、
     `ROBER_O5_O6_EXTERNAL_PROBE_ARTIFACT` / `--output`、
     `ROBER_O5_O6_UPPER_SSH_TIMEOUT_SECONDS` / `--timeout-seconds`、
     `ROBER_O5_O6_UPPER_PROBE_TIMEOUT_MS` / `--probe-timeout-ms`。
  - 凭证边界：collector 不通过 CLI 或 SSH args 传 bearer token；`TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN` 或 `ROBER_CLOUD_RELAY_BEARER_TOKEN` 必须在上位机运行环境中配置，artifact 只允许显示 `token_status=present|absent`。
  - artifact：默认写回 `.workstation-runtime/o5-o6-external-live-probe.json`；失败时也写 `trashbot.o5_o6.external_live_probe.v1` blocked artifact，供 acceptance queue 分类为 not observed / blocked。若 remote probe 输出合法 JSON 但以 exit 2 表示 `probe_status=fail_closed`，collector 仍保留该 JSON 并标记 `ssh_collection.status=collected`。
  - 关键字段：`ssh_collection.execution_mode=installed_script|stdin_fallback`、`ssh_collection.attempted_execution_modes[]`、`ssh_collection.fallback_used`、`ssh_collection.fallback_reason`、`ssh_collection.stdin_fallback_remote_write=false`。
  - 预检字段：dry-run 与 live artifact 的 `ssh_collection.preflight` 使用 `trashbot.o5_o6.upper_ssh_collector_preflight.v1`，固定 `network_probe_executed=false`、`post_executed=false`、`robots_path_accessed=false`、`cmd_vel_accessed=false`、`hardware_read_executed=false`、`robot_control_executed=false`。
  - 预检分类：`preflight.checks[]` 固定覆盖 `ssh_target`、`ssh_port`、`pc_base_url`、`cloud_base_url`、`remote_bearer_token`、`remote_root`、`remote_probe_script`。其中 target/port 可由 `--ssh-command` 解析；PC/cloud URL 缺失会直接标为 `blocked`；remote bearer/root/script 在 dry-run 中只标为 `requires_remote_runtime` 或 `requires_ssh_probe`，不会通过 PC 预检伪造为已通过。
  - 机器失败分类：`preflight.failure_classification[]` 和 `collection_paths[].failure_classification[]` 至少覆盖 `ssh_target_not_configured`、`ssh_port_not_configured`、`pc_base_url_not_configured_for_upper_ssh`、`cloud_base_url_not_configured`、`remote_bearer_token_not_verified_by_pc_preflight`、`remote_repo_root_missing`、`remote_repo_present_but_probe_script_missing`、`ssh_auth_failed`、`ssh_connection_refused`、`ssh_timeout`、`ssh_network_unreachable`、`ssh_stdin_fallback_probe_failed`、`ssh_stdin_fallback_stdout_bad_json`、`ssh_stdin_fallback_probe_schema_mismatch`。
  - PC base URL 合同：上位机 SSH collector 不默认使用 `http://127.0.0.1:8787`，因为远端 loopback 指向上位机自身，不是 PC workstation。operator 必须显式传 `--pc-base-url http://<pc-workstation-host>:8787`，或配置 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL` 为上位机可达地址。
   - 常见阻塞：若未显式提供 PC base URL，collector / artifact 应写 `pc_base_url_not_configured_for_upper_ssh`，并把 `next_action` 指向 `--pc-base-url http://<pc-workstation-host>:8787` 或 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL`。若 SSH 可达、`remote_root` 可进入，但远端缺少 `cloud-relay/scripts/o5_o6_external_live_probe.py`，collector 应先尝试 `stdin_fallback`。若 fallback 仍失败，blocked artifact 应写 `ssh_stdin_fallback_probe_failed` / `ssh_stdin_fallback_stdout_bad_json` / `ssh_stdin_fallback_probe_schema_mismatch` 等机器原因，并给出检查远端 `python3`、本地 probe 源和 stdout contract 的 `next_action`。
   - dry-run：
     `cd pc-tools/workstation && npm run o5o6:upper-ssh-collector -- --dry-run --ssh-target root@192.168.1.11 --ssh-port 37878 --cloud-base-url https://example.invalid`
     或 `cd pc-tools/workstation && npm run o5o6:upper-ssh-collector -- --dry-run --ssh-command "ssh root@192.168.1.11 -p 37878" --cloud-base-url https://example.invalid`
     只输出计划、预检分类和安全边界，不 SSH、不联网、不写 artifact；dry-run 会展示 `installed_script` 与 `stdin_fallback` 两种 SSH argv，但不会输出 probe 源码。若未传 PC base URL，dry-run 必须在 `pc_base_url_contract` 和 `preflight.failure_classification[]` 中暴露 `pc_base_url_not_configured_for_upper_ssh` 和 operator next action。

三条 O5/O6 路径的共同成功门槛：

- `tls_evidence.tls_status=observed` 且 `tls_observed=true`。
- O5 `/api/o5/readiness/health` 或 O6 `/api/o6/archive/health` 对应 endpoint `reachable=true` 且 `schema_status=matched`。
- `contract_status=observed_fail_closed_contract` 或 `pass`。
- `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`reads_hardware=false` 固定不变。

三条 O5/O6 路径的共同安全边界：

- 只发送固定 allowlist GET。
- 不 POST。
- 不访问 `/robots/*`。
- 不访问 `/cmd_vel`。
- 不读取串口、ROS2、Nav2、摄像头设备、WAVE ROVER 或任何硬件。
- 不发送机器人控制命令。
- SSH stdin fallback 只把本地只读 probe 源码送入 `python3 -`，不通过 stdin、CLI、SSH argv 或 artifact 传 bearer/token。

O7 runbook 现在先指向 `npm run o7:camera-service-readiness`，再指向 `npm run o7:browser-long-stability`。当上一份 browser smoke artifact 已经显示 `ERR_CONNECTION_REFUSED` / `remote_health_unreachable` 时，queue 的 `next_action` 必须优先提示 readiness collector，先确认板端 HTTP/WebRTC camera 服务是否监听、SSH 是否可达、端口/进程线索是否存在，再重跑 180s 长稳态。

`npm run o7:camera-service-readiness` 默认检查：

- HTTP GET `http://192.168.1.11:8088/health`
- HTTP GET `http://192.168.1.11:8088/devices`
- SSH `root@192.168.1.11 -p 37878` 上的只读诊断：`uname`、`ss`/`netstat` 监听摘要、camera/WebRTC 相关进程摘要、`trashbot-local-webrtc-camera.service` 的 `systemctl show` 摘要、systemd/unit 摘要、远端脚本摘要

可通过 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL` / `--base-url`、`ROBER_O7_CAMERA_SERVICE_SSH_TARGET` / `--ssh-target`、`ROBER_O7_CAMERA_SERVICE_SSH_PORT` / `--ssh-port` 覆盖目标；输出 artifact 默认为 `.workstation-runtime/o7-camera-service-readiness.json`，schema 为 `trashbot.o7.camera_service_readiness.v1`。该 collector 不 POST `/offer`、不创建 WebRTC session、不读取串口/底盘/ROS2 控制、不发送机器人控制命令。

readiness artifact 的关键分类字段包括：

- `readiness.http_health_unreachable`
- `readiness.http_connection_refused`
- `readiness.ssh_unreachable`
- `readiness.port_not_listening`
- `readiness.process_hint_missing`
- `readiness.service_unit_missing_or_inactive`
- `readiness.service_unit_not_installed`
- `readiness.service_unit_inactive`
- `readiness.remote_script_missing`
- `readiness.action_category`
- `readiness.safe_start_command_hint`
- `readiness.ready_for_long_stability`

`readiness.action_category` 用于把 operator 下一步机器化：

- `remote_script_present_but_service_inactive`：SSH 可达、远端存在 `local_webrtc_camera_smoke.sh/.py`，但 8088 未监听且没有可见 service/unit；operator 应人工启动脚本或安装 service 后重跑 readiness。
- `service_process_present_but_port_closed`：有 camera/WebRTC 进程线索，但 8088 未监听；operator 应检查绑定地址、端口和日志。
- `service_unit_not_installed`：远端脚本存在但固定 unit `trashbot-local-webrtc-camera.service` 未安装；operator 应先运行 `bash onboard/scripts/install_o7_camera_service.sh --dry-run`，确认只会安装 camera smoke 后再安装。
- `service_unit_inactive`：固定 unit 已可识别但不是 active；operator 应重启 `trashbot-local-webrtc-camera.service` 并检查日志、依赖和 8088 绑定。
- `service_unit_missing_or_inactive`：没有可见 camera/WebRTC service/unit 线索；operator 应先补服务安装/启动材料。
- `remote_script_missing`：远端脚本缺失；operator 应先同步 `onboard/scripts/local_webrtc_camera_smoke.*`。
- `service_not_listening_on_8088`：HTTP/SSH 证据都指向端口未监听，但脚本/unit 线索不足以更细分。

`safe_start_command_hint` 只作为人工提示，不由 collector 或 acceptance API 执行。当前提示优先指向 `install_o7_camera_service.sh --dry-run`，避免继续依赖 operator-run/nohup。若 queue 读取到 readiness artifact，会在 O7 item 的 `o7_camera_service_readiness` 中暴露脱敏摘要，并把非 ready 的 `action_category` 追加到 `blocking_reason`，例如 `browser_smoke_failed__net_err_connection_refused__remote_health_unreachable__service_unit_not_installed`。

`ready_for_long_stability=true` 的最小恢复口径是：HTTP `/health` 与 `/devices` 可达、SSH 可达、8088 正在监听、camera/WebRTC 进程线索存在、远端 `local_webrtc_camera_smoke.*` 脚本存在，并且固定 unit `trashbot-local-webrtc-camera.service` 已安装且 `active`。operator-run/nohup 直接启动脚本只能证明当前 8088 在线，不能写成 systemd 持久化 ready；此时 queue 必须保留 `service_unit_not_installed` 或 `service_unit_inactive`，并把下一步指向安装/重启固定 unit。

只有 `ready_for_long_stability=true` 后，operator 才应继续运行 `npm run o7:browser-long-stability`。长稳态入口仍要求 operator 准备 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL`，默认委托现有 `scripts/o7-browser-playback-smoke.mjs`，并把 `ROBER_O7_BROWSER_SMOKE_STABILITY_MS` 强制提升到 `>=180000`，输出落到 `.workstation-runtime/o7-browser-playback-smoke.json` 或通过 `ROBER_O7_BROWSER_SMOKE_RESULT_JSON` 指向。

2026-06-02 16-17 只读 recovery readiness 记录：默认 `http://192.168.1.11:8088/` 运行 `npm run o7:camera-service-readiness` 时，SSH 可达但 8088 不在监听列表，HTTP `/health` 与 `/devices` 不可达，远端只读诊断未发现 camera/WebRTC systemd service/unit 或活跃进程；远端存在 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.sh` 和 `.py`。因此 readiness artifact 分类为 blocked，`action_category=remote_script_present_but_service_inactive`，下一步是人工启动/安装该 camera service 后重跑 readiness；本轮未启动服务、未 POST `/offer`、未创建 WebRTC session、未发送任何机器人控制命令。

2026-06-02 18-19 恢复记录：operator 通过 SSH 在 `/root/rober` 下显式启动 `HOST=0.0.0.0 PORT=8088 ROBER_CAMERA_SOURCE=0 bash onboard/scripts/local_webrtc_camera_smoke.sh`，远端日志出现 `aiohttp_server_started`，`/health` 和 `/devices` 返回 200，SSH 监听摘要显示 `python3` 监听 `0.0.0.0:8088`。readiness collector 因此可进入 `ready_for_long_stability`；但该启动仍是 `nohup` operator-run，不是 systemd 持久化服务，生产化 service 安装/自启动仍未证明。

2026-06-04 03-04 O5/O6 上位机 SSH 实连记录：`ssh root@192.168.1.11 -p 37878` 可达，远端 hostname 脱敏角色为上位机，`/root/rober` 存在且主要包含 `onboard/`、`docs/`、`scripts/`、`sprints/` 与历史 runtime；只读路径探测未发现 `cloud-relay/scripts/o5_o6_external_live_probe.py`。因此默认 collector 写回 `.workstation-runtime/o5-o6-external-live-probe.json`，`probe_status=fail_closed`，O5/O6 acceptance queue 应分类为 `blocked`，关键原因 `remote_repo_present_but_probe_script_missing`。本轮未修改远端机器文件，下一步是同步 `cloud-relay/scripts/o5_o6_external_live_probe.py` 到远端 repo，或用 `--remote-root` / `--remote-script` 指向包含该脚本的路径后重跑。

2026-06-04 05-06 O5/O6 上位机 PC base URL 合同修正记录：`pc_upper_ssh_collector` 不再在缺省情况下把 `http://127.0.0.1:8787` 传给上位机。未显式传 `--pc-base-url` 或 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL` 时，installed script 与 stdin fallback 都向远端 probe 传空 PC base URL，PC aggregate 保持 fail-closed，并在 collector artifact 中追加 `pc_base_url_not_configured_for_upper_ssh`、`ssh_collection.pc_base_url_configured_for_upper_ssh=false` 和 operator next action。该修正只改变采集合同与 blocked 分类，不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读串口/ROS2/硬件、不发送 robot command、不通过 CLI/SSH args/stdin/artifact 传 bearer/token。

2026-06-04 06-07 O5/O6 acceptance API runbook 修正记录：`GET /api/real-material/acceptance` 的 `collection_runbook.suggested_commands[]` 中，`pc_upper_ssh_collector` 示例命令必须展示 `--pc-base-url http://<pc-workstation-host>:8787`，不得展示 `--pc-base-url http://127.0.0.1:8787`。PC workstation 本地 Node 采集路径仍可使用本机 loopback；只有通过 SSH 让上位机发起 probe 时，operator 必须填写上位机可达的 PC workstation 地址。该记录只修正 API-facing recipe，不执行 SSH、不联网、不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读硬件、不发送 robot command。

2026-06-04 07-08 O5/O6 shared contract 修正记录：`pc-tools/workstation/src/shared/contracts.ts` 的 `RealMaterialCollectionPath` 已把 `pc_upper_ssh_collector`、`runtime=node_ssh`、`host_role=pc_to_upper_computer` 纳入正式 TypeScript 合同。`GET /api/real-material/acceptance` 的第三条 `collection_paths[]` 不再需要 `unknown` cast，PC/UI typed consumers 可直接消费 SSH collector 路径；该修正只关闭合同类型滞后，不执行 SSH、不联网、不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读硬件、不发送 robot command，未产出 accepted live material 时不提升 O5/O6 百分比。

2026-06-04 08-09 O5/O6 SSH collector preflight/failure classification 记录：`pc_upper_ssh_collector` dry-run 已支持 `--ssh-command "ssh root@192.168.1.11 -p 37878"` 这类 operator 粘贴入口，并输出 `trashbot.o5_o6.upper_ssh_collector_preflight.v1`。预检分类能把缺 SSH target/port、PC base URL、cloud base URL、远端 bearer、remote root、remote probe script/stdin fallback 等缺口拆成机器 token；`GET /api/real-material/acceptance` 的 `collection_paths[]` 同步暴露 `preflight_checks[]` 与 `failure_classification[]`。该增强只做 GET-only/metadata/preflight/fail-closed 合同，不执行 SSH、不联网、不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读串口/ROS2/硬件、不发送 robot command；未采到 accepted live artifact 时不提升 O5/O6 百分比。

2026-06-04 04-05 stdin fallback 更新口径：`pc_upper_ssh_collector` 在 `remote_repo_present_but_probe_script_missing` 时不再直接停止，而是自动进入 `stdin_fallback`，把 PC 本地 `cloud-relay/scripts/o5_o6_external_live_probe.py` 通过 SSH stdin 交给远端 `python3 - --once-json` 执行。该模式不 scp、不写远端、不持久修改 `/root/rober`，安全边界仍为固定 allowlist GET，不 POST、不访问 `/robots/*`、不访问 `/cmd_vel`、不读硬件、不发送控制命令、不把 bearer/token 写入 CLI/SSH args/artifact。artifact 新增 `ssh_collection.execution_mode`、`attempted_execution_modes`、`fallback_used`、`fallback_reason` 与 `stdin_fallback_remote_write=false`，用于区分已安装脚本执行、stdin fallback 采集和 fallback 自身失败。

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

# Sprint 2026.05.12_07-08 Remote Cloud Production Preflight - Tech Done

## 状态

- 阶段：tech-done
- Owner：`full-stack-software-engineer`
- 任务：Task A / Task B
- 证据边界：`software_proof_docker_preflight_gate`
- 结论：DONE_WITH_CONCERNS。Docker/local production preflight gate 已可执行并能阻断缺生产条件的配置；本轮没有声明真实云、真实 4G、真实 TLS、公网入口、OSS/CDN 实流量、生产 DB/队列、Nav2/fixed-route、WAVE ROVER 或 HIL 完成。

## 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `production_preflight_payload()`，输出 machine-readable JSON。
  - 新增 `PREFLIGHT_EVIDENCE_BOUNDARY=software_proof_docker_preflight_gate`。
  - 新增 `GET /preflightz` endpoint，不改变既有 command/status/ack response shape。
  - 新增 `--preflight` CLI；blocked 时返回 exit code 2。
  - 检查项覆盖 credential provisioning、TLS/public ingress、OSS/CDN、state store、phone-safe output。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加 `/preflightz` blocked/脱敏测试。
  - 增加 local HTTP/占位凭证/OSS-CDN placeholder/file store warning 测试。
  - 增加不可写 state store blocked 测试。
- `scripts/remote_cloud_relay_docker_smoke.sh`
  - 增加 Docker service `/preflightz` smoke。
  - 增加 CLI 不可写 state store smoke。
  - 增加 evidence boundary 和敏感输出过滤检查。
- `.env.example`
  - 增加 production preflight placeholder env：public base URL、public ingress、OSS credential mode、state backend。
- `docker-compose.remote-cloud-relay.yml`
  - 将 preflight 所需 env 注入 Docker service。
- `docs/product/cloud_4g_infrastructure.md`
  - 补充 production preflight gate 口径、环境变量、OSS/CDN 边界和 CLI/endpoint 用法。
- `docs/product/remote_4g_mvp.md`
  - 补充 `/preflightz` 与 `--preflight` 的手机/云端产品语义和 blocked 解释。

## 用户旅程变化和触点收益

- 手机/云端上线前不再只看 service 是否存活；现在能区分“本地 Docker proof 可运行”和“生产云入口仍 blocked”。
- 输出包含 `safe_summary`、`retry_hint`、`checks[].code`，后续手机 UI 可直接把缺凭证、缺 TLS/公网、OSS/CDN 未实证、state store 不可写解释给普通用户或运维。
- blocked preflight 被明确归类为 cloud setup blocked，不会被误写成机器人送达失败、4G 成功、OSS 上传成功或 HIL 结果。

## 接口影响

- 新增旁路接口：

```text
GET /preflightz
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

- 未改变既有 API：

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

## 验证结果

### Unit test

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
.........
----------------------------------------------------------------------
Ran 11 tests in 4.712s

OK
```

### Compile

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
exit 0
```

### Preflight CLI smoke - writable file store with local placeholders

```text
env ... TRASHBOT_REMOTE_CLOUD_STATE=/tmp/rober_remote_cloud_preflight_writable.json ... python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
exit_status=2
```

关键 JSON 结果：

```json
{
  "evidence_boundary": "software_proof_docker_preflight_gate",
  "production_ready": false,
  "overall_status": "blocked",
  "blocked_count": 3,
  "warning_count": 1,
  "checks": [
    {"name": "credential_provisioning", "status": "blocked", "code": "missing_or_placeholder_credential"},
    {"name": "tls_public_ingress", "status": "blocked", "code": "https_public_ingress_missing"},
    {"name": "oss_cdn", "status": "blocked", "code": "oss_cdn_not_production_ready"},
    {"name": "state_store", "status": "warning", "code": "file_backed_store_only"},
    {"name": "phone_safe_output", "status": "pass", "code": "redaction_self_check_passed"}
  ]
}
```

### Preflight CLI smoke - unwritable state store

```text
TRASHBOT_REMOTE_CLOUD_STATE=/dev/null/relay_state.json python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
exit_status=2
```

关键 JSON 结果：

```json
{
  "evidence_boundary": "software_proof_docker_preflight_gate",
  "production_ready": false,
  "overall_status": "blocked",
  "checks": [
    {"name": "state_store", "status": "blocked", "code": "state_store_not_writable"}
  ]
}
```

### Sensitive output self-check

```text
python3 - /tmp/rober_preflight_writable.json /tmp/rober_preflight_unwritable.json
preflight smoke redaction/evidence checks passed for writable and unwritable scenarios
```

检查确认输出未包含 local token、production-like token、Authorization、Bearer、OSS secret、root password、`/cmd_vel`、`ttyUSB`、baudrate 或 WAVE ROVER 字符串。

### Docker smoke

```text
TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT=18088 TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token PYTHONDONTWRITEBYTECODE=1 bash scripts/remote_cloud_relay_docker_smoke.sh
```

关键结果：

```text
ros-rbs-remote-cloud-relay:dev  Built
== production preflight endpoint expects Docker/local blocked ==
"evidence_boundary": "software_proof_docker_preflight_gate"
"production_ready": false
"overall_status": "blocked"
"missing_or_placeholder_credential"
"https_public_ingress_missing"
"oss_cdn_not_production_ready"
"file_backed_store_only"
== production preflight CLI with unwritable state expects blocked ==
"state_store_not_writable"
== post status / enqueue command / robot get next command / post ack / read ack / read status ==
all returned ok=true
```

说明：wait readiness 阶段首次 curl 出现一次 `Recv failure: Connection reset by peer`，脚本重试后 `/readyz` 成功；这是容器启动窗口内的瞬时连接失败，不影响最终 smoke 结果。

## 失败定位和修复

- 首轮 preflight CLI smoke 失败于 zsh 将 `rober/<robot_id>/<date>/<task_id>/` 中的 `<...>` 解析为重定向。后续改用 `env 'TRASHBOT_REMOTE_CLOUD_OSS_PREFIX=...'` 方式运行，不属于产品代码失败。
- 首轮 unit test 暴露 `secret_provisioning` check name 被通用脱敏规则替换成 `[redacted]`，导致机器可读字段不稳定。已改为 `credential_provisioning` / `missing_or_placeholder_credential`，保留保守脱敏。
- 首轮 CLI blocked 未返回非 0，因为 `main()` 没有通过 `SystemExit` 传回退出码。已修复为 blocked 返回 2。

## 剩余风险

- 本轮只证明 Docker/local preflight gate，不证明真实云主机、域名、HTTPS/TLS、公网入口、防火墙、真实 4G/SIM、弱网恢复、OSS 上传、CDN 回源、生产 DB/队列、多实例一致性或密钥 rotate。
- `state_store=file` 只能作为 proof store；生产仍需要数据库或队列，并补充备份、并发和灾备证据。
- `/preflightz` 是部署 gate，不是机器人任务状态；手机 UI 需要把 blocked 显示为云端配置未就绪，不能显示为机器人失败或硬件失败。

## Task C Robot Platform 验收 - remote bridge 兼容性

- 时间：2026-05-12
- Owner：`robot-software-engineer`
- 范围：只验证 `RemoteCloudClient.post_status -> get_next_command -> post_ack` 与 `remote_bridge` cursor/action/ACK 语义；未修改 remote bridge 产品代码或测试代码。
- 结论：DONE。现有围栏覆盖 status-command-ack round trip、ACK 只代表 command envelope 已处理、auth failed、malformed response、cloud unreachable、ACK 失败不推进 cursor；新增 `/preflightz` 和 `--preflight` 作为旁路 gate，没有改变 robot 侧既有 status/command/ack 契约。

### Task C 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge.py
....../opt/homebrew/Cellar/python@3.13/3.13.2/Frameworks/Python.framework/Versions/3.13/lib/python3.13/threading.py:1265: ResourceWarning: unclosed <socket.socket [closed] fd=4, family=2, type=1, proto=6>
  def _make_invoke_excepthook():
ResourceWarning: Enable tracemalloc to get the object allocation traceback
.........................
----------------------------------------------------------------------
Ran 31 tests in 15.218s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
exit 0
```

```text
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge.py sprints/2026.05.12_07-08_remote-cloud-production-preflight/tech-done.md
exit 0
```

### Task C 覆盖确认

- `RemoteCloudClient.post_status -> get_next_command -> post_ack` 兼容性：`test_status_and_command_ack_round_trip`、`test_client_round_trips_status_command_and_ack_with_independent_relay`、`test_poll_posts_status_then_collects_and_acks` 通过。
- ACK 语义：`test_client_round_trips_status_command_and_ack_with_independent_relay` 明确 ACK 只证明 command envelope 已处理，真实送达结果继续依赖 status/task record。
- auth failed：`test_bearer_auth_failure_maps_to_phone_safe_cloud_error`、`test_auth_failed_get_posts_phone_safe_status_without_cursor_advance` 通过，确认不推进 cursor、不触发本地 action、不伪造 terminal ACK。
- malformed response：`test_malformed_cloud_response_does_not_start_action_or_advance_cursor` 通过，确认不推进 cursor、不触发本地 action、不伪造 terminal ACK。
- cloud unreachable：`test_status_cloud_outage_does_not_poll_command_or_advance_cursor`、`test_ack_failure_does_not_persist_cursor_state` 通过，确认 outage 不推进 cursor，ACK 失败也不持久化 terminal cursor。
- preflight blocked：`/preflightz` 和 `--preflight` 是 remote cloud relay 的部署旁路 gate；本轮 robot 侧围栏证明既有 status/command/ack API 未被 preflight gate 改 shape 或改语义。blocked preflight 不是 robot command，不进入 `RemoteBridgeWorker.poll_once()` 的本地 action/ACK 路径。

### Task C 剩余风险

- 本轮没有跑 Docker relay smoke、真实云、真实 4G、TLS、公网入口、生产 state store 或 HIL；证据边界仍是 `software_proof_docker_preflight_gate` / robot 侧 unittest + py_compile。
- unittest 输出 1 条 Python 3.13 `ResourceWarning: unclosed <socket.socket [closed]>`，不影响本轮结果，但后续可在测试夹具层面清理 HTTP server socket 生命周期。

## Reviewer Important 修复 - phone-safe preflight redaction

- 时间：2026-05-12
- Owner：`full-stack-software-engineer`
- 范围：`remote_cloud_relay.py`、`test_remote_cloud_relay.py`
- 结论：DONE。`/preflightz` 和 `--preflight` 的 env-derived detail 字段不再回显任意环境变量字符串；TLS/public ingress、OSS credential mode、state backend 进入输出前先压成白名单枚举或安全默认值，敏感文本兜底脱敏补充覆盖 serial、ROS topic、`/cmd_vel`、WAVE ROVER、凭证和 root password 类 marker。

### Reviewer Important 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `_safe_enum()`，preflight details 只输出白名单枚举：`tls_mode`、`public_ingress`、`credential_mode`、`backend`。
  - 将畸形 `TRASHBOT_REMOTE_CLOUD_TLS_MODE` / `TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS` / `TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE` 输出降级为 `invalid_or_unsupported`。
  - 将畸形 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND` 输出降级为 `file`，避免把 DB/backend env 原文透传给手机端。
  - 扩展文本脱敏 marker：`/dev/`、`ttyACM`、`serial_port`、`/odom`、`/imu`、`/battery`、root password、OSS secret 等。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 `test_preflight_redacts_env_derived_hardware_and_ros_markers`，覆盖 `/dev/ttyACM0`、`/dev/cu.usbserial`、`serial_port`、`/odom`、`/imu/data`、`/battery`、`/trashbot/...`、`/cmd_vel`、baudrate、WAVE ROVER、Authorization、Bearer/token、root password、OSS secret。

### Reviewer Important 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
............
----------------------------------------------------------------------
Ran 12 tests in 4.714s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
exit 0
```

Focused probe：

```text
env TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS='public_https /imu/data /battery /trashbot/collect_trash' \
    TRASHBOT_REMOTE_CLOUD_TLS_MODE='terminated /dev/ttyACM0 serial_port=/dev/cu.usbserial /odom' \
    TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE='sts /cmd_vel baudrate WAVE ROVER Authorization Bearer token' \
    TRASHBOT_REMOTE_CLOUD_STATE_BACKEND='postgres root password OSS secret' \
    PYTHONPATH=src/ros2_trashbot_behavior \
    PYTHONDONTWRITEBYTECODE=1 \
    python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
exit_status=2
output_bytes=2555
leaks=none
```

```text
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py sprints/2026.05.12_07-08_remote-cloud-production-preflight/tech-done.md
exit 0
```

### Reviewer Important 失败定位

- 首次 focused probe 未进入产品逻辑，原因是 zsh 中 `status` 是只读特殊变量；验证脚本变量改为 `rc` 后同一探针通过。
- reviewer 指出的泄露根因是 preflight `details` 直接写入 env-derived enum/detail 字符串；修复点放在 preflight 输入归一化处，而不是只依赖最终 JSON 字符串过滤。

### Reviewer Important 剩余风险

- 本修复只证明 phone-safe preflight redaction，不证明真实云、真实 4G、真实 TLS、公网入口、OSS 上传、生产 DB/队列或 HIL。
- 后续新增 preflight detail 字段时仍必须先定义白名单枚举、布尔值或单位明确的数值，不得把原始 env、ROS topic、串口或硬件参数原样输出。

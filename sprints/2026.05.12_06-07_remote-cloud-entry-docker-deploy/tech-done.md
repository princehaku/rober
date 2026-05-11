# Sprint 2026.05.12_06-07 Remote Cloud Entry Docker Deploy - Tech Done

## 状态

- 阶段：tech-done
- 更新时间：2026-05-12 04:13 CST
- 主责 Engineer：`full-stack-software-engineer`
- 覆盖任务：Task A Docker deploy proof；Task B health/readiness and phone-safe smoke
- 证据边界：`software_proof_docker_deploy`

## 用户旅程变化和触点收益

- 手机/云入口不再只停留在本机 Python proof：现在可以用 compose 启动 independent relay container，并通过 env 占位配置 host、port、state path、bearer token、future TLS/OSS/CDN 变量。
- 编排系统和未来 phone diagnostics 可以调用 `/healthz` 与 `/readyz` 区分“服务活着”和“可接控制面流量”。`/readyz` 覆盖 protocol/version、credential gate、state store writable、phone-safe failure redaction。
- command/status/ack 仍保持 `trashbot.remote.v1`，ACK 仍只表示 command envelope 处理，不代表真实送达、Nav2/fixed-route、WAVE ROVER 或 HIL。

## 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `/healthz`、`/readyz`。
  - 新增 readiness payload 和 state store writable check。
  - 新增 phone-safe failure redaction self-check，避免 readiness/error 泄露 Authorization、bearer token、credential URL、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel` 或 traceback。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加 health/readiness 成功路径测试。
  - 增加未配置 credential gate 时 `/readyz` 返回 503 的测试。
- `docker/remote-cloud-relay/Dockerfile`
  - 新增 independent relay 最小 Python runtime 镜像，不引入 ROS2/Humble build 链路。
- `docker-compose.remote-cloud-relay.yml`
  - 新增 `remote-cloud-relay` service、env 配置、named volume、healthcheck。
- `.env.example`
  - 新增 bearer token、state path、host/port、future TLS/OSS/CDN 占位；不包含真实密钥。
- `scripts/remote_cloud_relay_docker_smoke.sh`
  - 新增 Docker deploy smoke，覆盖 compose build、容器启动、health/readiness、post status、enqueue command、robot-style next command、post ack、read ack/status、停止容器。
- `docs/product/cloud_4g_infrastructure.md`
  - 补充 Docker deploy proof 运行方式、env 边界、health/readiness、验证命令和真实云缺口。
- `docs/product/remote_4g_mvp.md`
  - 补充 Docker deploy proof、fenced smoke 命令、readiness contract 和证据边界。

## 验证结果

### Targeted unittest

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
........
----------------------------------------------------------------------
Ran 8 tests in 4.167s

OK
```

### Python compile

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# exit 0, no output
```

### Scoped diff check

```text
$ git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/tech-done.md
# exit 0, no output
```

新增 Docker/env/smoke 文件也用 `git diff --check --no-index -- /dev/null <file>` 做了 whitespace check；无 whitespace 输出。`--no-index` 对新增文件存在内容差异会返回 1，因此只按输出检查 whitespace 问题。

### Docker deploy smoke

Compose config preflight:

```text
$ TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token docker compose -f docker-compose.remote-cloud-relay.yml config
services:
  remote-cloud-relay:
    healthcheck:
      test:
        - CMD-SHELL
        - python -c "import json,os,urllib.request; port=os.environ.get('TRASHBOT_REMOTE_CLOUD_PORT','8088'); data=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/readyz', timeout=2)); raise SystemExit(0 if data.get('ok') else 1)"
# exit 0
```

命令：

```bash
TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT=18088 \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
scripts/remote_cloud_relay_docker_smoke.sh
```

关键输出：

```text
== build image ==
ros-rbs-remote-cloud-relay:dev  Built
== start relay container ==
Container ros-rbs-remote-cloud-relay-smoke-remote-cloud-relay-1  Started
== wait for readiness ==
{"ok": true, "service": "remote_cloud_relay", "protocol_version": "trashbot.remote.v1", "evidence_boundary": "software_proof_docker_deploy", "checks": {"protocol": true, "credential_gate": true, "state_store": true, "phone_safe_failure": true}, "safe_phone_copy": "云端中转服务已就绪。"}
== healthz ==
{"ok": true, "service": "remote_cloud_relay", "protocol_version": "trashbot.remote.v1", "evidence_boundary": "software_proof_docker_deploy"}
== post status ==
{"ok": true, "status": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "state": "idle", "message": "docker smoke status", "updated_at": 1778530547.29393, "diagnostics": {"network": "docker_deploy_smoke"}}}
== enqueue command ==
{"ok": true, "command": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "id": "cmd-docker-smoke-1", "type": "collect", "expires_at": 2778256300.0, "payload": {"target": "trash_station", "trash_type": 0}, "created_at": 1778530547.314003}, "duplicate": false}
== robot get next command ==
{"ok": true, "command": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "id": "cmd-docker-smoke-1", "type": "collect", "expires_at": 2778256300.0, "payload": {"target": "trash_station", "trash_type": 0}, "created_at": 1778530547.314003}}
== post ack ==
{"ok": true, "ack": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "command_id": "cmd-docker-smoke-1", "state": "acked", "message": "docker smoke ack", "updated_at": 1778530547.29393, "result": {"bridge": "submitted"}}}
== read ack ==
{"ok": true, "ack": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "command_id": "cmd-docker-smoke-1", "state": "acked", "message": "docker smoke ack", "updated_at": 1778530547.29393, "result": {"bridge": "submitted"}}}
== read status ==
{"ok": true, "status": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "state": "idle", "message": "docker smoke status", "updated_at": 1778530547.29393, "diagnostics": {"network": "docker_deploy_smoke"}}}
Container ros-rbs-remote-cloud-relay-smoke-remote-cloud-relay-1  Removed
Volume ros-rbs-remote-cloud-relay-smoke_remote-cloud-relay-state  Removed
Network ros-rbs-remote-cloud-relay-smoke_default  Removed
```

## 失败定位和修复

- 第一次 Docker smoke 失败在最后 `GET /robots/trashbot-001/status`：脚本使用固定旧 `updated_at=1778256012.0`，relay 正确返回 `status_stale` 409。定位为 smoke 数据过期，不是 relay 缺陷；已改为运行时生成当前 timestamp。
- 第二次 Docker smoke 失败在 timestamp 生成：macOS 主机没有 `python` 命令，只有 `python3`。已把脚本改为 `python3`。
- readiness 等待期间第一轮 `curl` 曾出现 `Recv failure: Connection reset by peer`，随后重试成功；这是容器刚启动时端口尚未完全可用，脚本已通过 retry 覆盖。

## 剩余风险和边界

- 本轮只证明 `software_proof_docker_deploy`，不证明真实云主机、域名、公网入口、HTTPS/TLS、4G/SIM、弱网、OSS/CDN、生产 DB/队列、多实例一致性、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。
- `FileBackedRelayStore` 仍是单机 proof store；生产云需要数据库/队列、备份、审计、rotate、provisioning 和多租户边界。
- Task C robot compatibility fence 尚未由 `robot-software-engineer` 追加；本轮未改 `remote_bridge` 或 Task C robot files。

## Task C - Robot Client Compatibility Fence

- 更新时间：2026-05-12 04:19 CST
- 主责 Engineer：`robot-software-engineer`
- 代码改动：无。现有 `RemoteCloudClient.post_status -> get_next_command -> post_ack` 与 `RemoteBridgeWorker.poll_once` 围栏已覆盖 independent relay response shape、bearer auth failure、malformed response、cloud/status/ack outage、cursor safety 和 terminal ACK 语义，本轮未新增测试，避免为了测试而加测试。
- 兼容结论：robot client 对 Docker deploy entry/independent relay 仍兼容；`post_status` 能消费 relay status response，`get_next_command` 能解析 relay command envelope，`post_ack` 能提交 terminal ACK。auth failed、malformed response、cloud unreachable 保持保守语义：不执行不可信 command、不推进 `last_ack_id`/cursor、不伪造 terminal ACK。

### Task C 验证结果

Targeted robot client unittest：

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
...../opt/homebrew/Cellar/python@3.13/3.13.2/Frameworks/Python.framework/Versions/3.13/lib/python3.13/threading.py:1265: ResourceWarning: unclosed <socket.socket [closed] fd=4, family=2, type=1, proto=6>
  def _make_invoke_excepthook():
ResourceWarning: Enable tracemalloc to get the object allocation traceback
..........................
----------------------------------------------------------------------
Ran 31 tests in 15.223s

OK
```

Python compile：

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
# exit 0, no output
```

Docker relay smoke：

```text
$ TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT=18088 \
  TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
  scripts/remote_cloud_relay_docker_smoke.sh
== build image ==
ros-rbs-remote-cloud-relay:dev  Built
== start relay container ==
Container ros-rbs-remote-cloud-relay-smoke-remote-cloud-relay-1  Started
== wait for readiness ==
curl: (56) Recv failure: Connection reset by peer
{"ok": true, "service": "remote_cloud_relay", "protocol_version": "trashbot.remote.v1", "evidence_boundary": "software_proof_docker_deploy", "checks": {"protocol": true, "credential_gate": true, "state_store": true, "phone_safe_failure": true}, "safe_phone_copy": "云端中转服务已就绪。"}
== healthz ==
{"ok": true, "service": "remote_cloud_relay", "protocol_version": "trashbot.remote.v1", "evidence_boundary": "software_proof_docker_deploy"}
== post status ==
{"ok": true, "status": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "state": "idle", "message": "docker smoke status", "diagnostics": {"network": "docker_deploy_smoke"}}}
== robot get next command ==
{"ok": true, "command": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "id": "cmd-docker-smoke-1", "type": "collect", "payload": {"target": "trash_station", "trash_type": 0}}}
== post ack ==
{"ok": true, "ack": {"protocol_version": "trashbot.remote.v1", "robot_id": "trashbot-001", "command_id": "cmd-docker-smoke-1", "state": "acked", "message": "docker smoke ack", "result": {"bridge": "submitted"}}}
Container ros-rbs-remote-cloud-relay-smoke-remote-cloud-relay-1  Removed
Volume ros-rbs-remote-cloud-relay-smoke_remote-cloud-relay-state  Removed
Network ros-rbs-remote-cloud-relay-smoke_default  Removed
# exit 0
```

Scoped diff check：

```text
$ git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/tech-done.md
# exit 0, no output
```

### Task C 失败定位和剩余风险

- 失败定位：无阻断失败。unittest 期间 Python 3.13 输出一次 `ResourceWarning: unclosed <socket.socket [closed]>`，测试进程最终 `OK`；该 warning 来自本地 HTTP test server teardown 时机，不影响本轮 client contract 结论。
- Docker smoke readiness 第一轮出现 `curl: (56) Recv failure: Connection reset by peer`，随后 retry 成功，符合容器刚启动时端口未完全就绪的预期。
- 剩余风险：本轮仍是 `software_proof_docker_deploy`。没有证明真实云主机、HTTPS/TLS、公网入口、真实 4G/SIM、弱网恢复、生产 DB/队列、多实例一致性、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。

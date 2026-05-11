# Sprint 2026.05.12_05-06 Remote Cloud Service Docker Proof - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 05:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：`software_proof_docker_only`

## 技术目标

把 `operator_gateway` 内嵌 local/mock cloud 已验证的 `trashbot.remote.v1` 语义推进成独立 HTTP cloud relay service proof。服务必须能在本机/Docker 环境运行，使用 bearer auth、file-backed persistence、phone-safe errors，并保持 robot outbound polling client 兼容。

本计划完成后，主节点可直接派发 `full-stack-software-engineer` 和 `robot-software-engineer` 执行；两个任务文件范围不重叠，允许并行。若实现过程中发现共享接口 shape 冲突，由 `robot-software-engineer` 只做兼容事实补充，最终仍以 `full-stack-software-engineer` 的服务端 contract 为主责。

## 证据依据

- `OKR.md`：O6 约 19%，是最低完成度；缺真实云、HTTPS/TLS、公网入口、真实 4G/SIM、弱网恢复、生产鉴权、STS/OSS/CDN 和生产持久化。
- 04-05 final：local/mock auth gate、remote_readiness/degradation、cursor safety 完成，但仍是 `software_proof_docker_only` / local mock cloud。
- 04-05 tech-done：operator tests `Ran 66 tests ... OK`、remote bridge tests `Ran 23 tests ... OK`、integration smoke `Ran 89 tests ... OK`，说明上一轮 contract 可作为本轮服务端语义输入。
- `docs/product/remote_4g_mvp.md`：已定义 command/status/ack、bearer auth、cursor、ACK/status 边界和 current limits。
- `docs/product/cloud_4g_infrastructure.md`：当前缺失，是 O6 KR2 文档缺口。

## 文件结构和职责

### Task A - Full-stack Independent Relay Service

Owner：`full-stack-software-engineer`

允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md`

职责：

- 新建独立 HTTP relay service module。
- 新建 file-backed store，保存 commands/status/acks。
- 实现 bearer auth gate 和 phone-safe JSON errors。
- 实现 command/status/ack API。
- 写 targeted unittest 覆盖 contract/auth/persistence/error redaction。
- 创建 `docs/product/cloud_4g_infrastructure.md`，同步 `remote_4g_mvp.md` 的 independent service 边界。
- 在 `tech-done.md` 记录实际改动、验证输出、失败定位和剩余风险。

### Task B - Robot Client Compatibility Smoke

Owner：`robot-software-engineer`

允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md`

职责：

- 用独立 relay service 的 API shape 做 robot client compatibility smoke。
- 优先新增/调整 tests；只有发现 `RemoteCloudClient` 与 `trashbot.remote.v1` 服务端 response shape 不兼容时，才做最小代码修正。
- 验证 auth failed、malformed response、cloud unreachable 仍不执行不可信 command、不推进 cursor、不伪造 terminal ACK。
- 在 `tech-done.md` 追加 Task B 验证输出、失败定位和剩余风险。

## 接口影响

### HTTP API

必须保持：

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

### Payload 约束

- `protocol_version` 固定为 `trashbot.remote.v1`。
- `command.id` 是 idempotency key。
- 支持 command type：`collect`、`confirm_dropoff`、`cancel`。
- terminal ACK state：`acked`、`failed`、`ignored`。
- status 是持续任务状态 surface；ACK 不是送达结果。

### 安全和脱敏

- 受保护路径使用 bearer auth。
- 错误响应和 persisted state 不得包含 bearer token、Authorization header、credential-bearing URL、serial device、baudrate、WAVE ROVER 参数、`/cmd_vel` 或 ROS topic 名。
- phone-safe error 至少区分 `auth_failed`、`bad_request`、`not_found`、`status_missing`、`status_stale`、`malformed_json`。

## 子 Agent 派发 Prompt 要点

### 给 `full-stack-software-engineer`

本轮任务：

实现 independent Docker/local HTTP cloud relay service proof，复用 `trashbot.remote.v1` command/status/ack 语义、bearer auth、file-backed persistence、phone-safe errors，并补齐 `docs/product/cloud_4g_infrastructure.md`。

文件范围：

```text
src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
docs/product/cloud_4g_infrastructure.md
docs/product/remote_4g_mvp.md
sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

输出要求：

1. 实际改动文件列表。
2. 验证命令输出日志片段。
3. 失败定位和修复记录。
4. 剩余风险，必须明确 Docker/local proof 不等于真实云、4G、OSS/CDN 或 HIL。

### 给 `robot-software-engineer`

本轮任务：

验证 robot outbound polling client 与 independent relay service API shape 兼容。优先写 targeted tests/smoke；只有发现 `RemoteCloudClient` response handling 与服务端 contract 不兼容时，才做最小修正。

文件范围：

```text
src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
src/ros2_trashbot_behavior/test/test_remote_bridge.py
sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

输出要求：

1. 实际改动文件列表。
2. 验证命令输出日志片段。
3. 失败定位和修复记录。
4. 剩余风险，必须明确 ACK 不是 delivery result，client compatibility 不等于真实云或 HIL。

## 集成验收命令

工程任务完成后，主节点应要求主责或集成 owner 运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

## 本阶段计划文档验收命令

本阶段只创建三份计划文档，验收命令为：

```bash
git diff --check -- \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/pre_start.md \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/prd.md \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-plan.md
```

## 风险边界

- 本轮不接触硬件，因此不需要查 `docs/vendor/VENDOR_INDEX.md`；如果工程实现漂移到串口、WAVE ROVER、ESP32、Orange Pi、波特率、JSON 底盘指令或电气信息，必须停止并先查 vendor 资料。
- 本轮只证明 independent Docker/local relay，不证明真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN 或 HIL。
- file-backed persistence 是软件 proof，不等于生产数据库或多实例队列。
- service tests 是围栏；不要扩展为大规模测试补课。
- 工程完成后必须更新 `tech-done.md`；Product Acceptance 阶段再创建 `side2side_check.md` 和 `final.md`，并按证据边界决定是否更新 `OKR.md`。

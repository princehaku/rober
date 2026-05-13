# Sprint 2026.05.13_08-09 Cloud Public Ingress TLS Gate - Tech Done

## Task A Full-Stack Cloud Public Ingress/TLS Gate

### 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `trashbot.cloud_public_ingress_tls_gate` artifact，证据边界为 `software_proof_docker_cloud_public_ingress_tls_gate`。
  - 新增 `TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT` / `--cloud-public-ingress-tls-artifact` preflight 消费入口，以及 `--write-cloud-public-ingress-tls-artifact` 生成入口。
  - preflight 新增 `cloud_public_ingress_tls` check，用 `missing_public_ingress_tls_config` 区分完全缺公网入口/TLS/反向代理配置，用 `public_ingress_tls_config_present_not_externally_proven` 区分配置包存在但缺真实外部 HTTPS/TLS、公网入口、DNS、反向代理、防火墙实证。
  - 两种状态都保持 `production_ready=false`、`overall_status=blocked`，并继续禁止输出真实 URL、credential-bearing URL、Authorization header、bearer token、TLS private key、证书私钥路径、root password、OSS AK/SK、DB/queue URL、本地 state path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 增加 missing-config、config-present-not-externally-proven、hostile artifact 三组围栏，覆盖 evidence boundary、blocked 状态、preflight 消费和 phone-safe 脱敏。
  - 修正 evidence boundary 优先级断言：public ingress/TLS gate 只高于基础 deployment readiness，不覆盖 backup、network recovery、credential、queue、transaction、production recovery 等更具体 artifact 证据。
- `cloud-relay/scripts/docker_smoke.sh`
  - 增加 Docker smoke 中 public ingress/TLS missing-config artifact、config-present artifact、preflight 消费三段断言。
  - 保留既有 external probe、backup/restore、command/status/ack 和 SQLite restart proof 围栏。
- `cloud-relay/README.md`
  - 增加 public ingress/TLS gate 的生成、preflight 消费、状态语义和敏感字段禁止清单。
- `docs/product/cloud_4g_infrastructure.md`
  - 补充 `2026.05.13_08-09_cloud-public-ingress-tls-gate` 证据边界、两类 blocked 状态和新增环境变量。
- `docs/product/remote_4g_mvp.md`
  - 补充 phone/cloud 产品路径下 public ingress/TLS gate 的用户触点语义、CLI 入口和证据边界。

### 用户旅程变化和触点收益

- 手机/云端 operator 现在能区分“完全没有公网入口/TLS/反向代理配置包”和“配置包形态存在但还没有真实外部 HTTPS/DNS/反向代理/防火墙实证”。
- preflight 不再只给泛化的 TLS/public ingress blocked，而是给可执行的下一步：先补配置包，或拿配置包去做外部 HTTPS/DNS/反向代理/防火墙证据。
- 该变化仍是 Docker/local software proof；不会让普通用户误以为真实公网、真实 HTTPS/TLS、真实云、4G/SIM、OSS/CDN live traffic、production DB/queue、HIL 或真实送达已经完成。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：第一次失败 8 个 evidence boundary 优先级断言，根因是新 gate 覆盖了已有更高阶 artifact boundary；修正优先级后复跑通过，`Ran 58 tests in 7.079s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
```

结果：通过，无输出。

```bash
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
```

结果：通过。关键日志包含：

- `evidence_boundary=software_proof_docker_cloud_public_ingress_tls_gate`
- `state=missing_public_ingress_tls_config`
- `state=public_ingress_tls_config_present_not_externally_proven`
- `production_ready=false`
- `overall_status=blocked`
- external probe、backup/restore、command/status/ack、SQLite restart proof 均完成既有 smoke 围栏。

```bash
git diff --check -- cloud-relay onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
```

结果：通过，无输出。

### 剩余风险

- 本 Task A 只建立 `software_proof_docker_cloud_public_ingress_tls_gate`，没有真实云主机、真实 HTTPS/TLS 证书、真实公网入口、DNS 解析、反向代理 live routing、防火墙实证、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、HIL 或真实送达。
- 配置包存在状态只来自枚举化环境变量和 artifact；后续还需要真实外网 curl/TLS/DNS/反向代理/防火墙证据包来关闭 `public_ingress_external_probe` 缺口。

## Task B Robot Compatibility Fence

### 实际改动

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 增加 public ingress/TLS metadata 混入有效 command response 的兼容围栏，确认 backend action 只来自有效 `trashbot.remote.v1` command envelope，ACK/status 不回传 `cloud_public_ingress_tls`、`public_ingress_tls`、`cloud_public_ingress_tls_gate`、`deployment_readiness`、`delivery_success`、`cursor_override`、Authorization/token、credential URL 或 `/cmd_vel`。
  - 增加 metadata-only public ingress/TLS response 围栏，覆盖 `cloud_public_ingress_tls`、`public_ingress_tls`、`cloud_public_ingress_tls_gate`、`deployment_readiness` 四类字段；确认不触发 backend action、不 POST ACK、不推进 `last_ack_id`、不持久化 cursor。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - 增加 protocol normalization 围栏，确认 command envelope 外 public ingress/TLS readiness metadata 被剥离，不进入 robot command payload。
- `docs/interfaces/ros_contracts.md`
  - 明确 public ingress/TLS readiness metadata 属于 deployment readiness / phone-safe support metadata，不改变 `trashbot.remote.v1` command/status/ACK envelope。
  - 明确 ACK 仍只是 accepted/processing evidence，不是 delivery success，也不证明真实 HTTPS/TLS/public ingress。

### 验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
```

结果：`Ran 72 tests in 35.978s`，`OK`。运行中出现一个既有 `ResourceWarning: unclosed <socket.socket [closed] ... remote_cloud_relay.py:329`，测试结果仍为通过；该 warning 来自本任务范围外 relay 兼容测试依赖。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
```

结果：通过，无输出。

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

结果：通过，无输出。

### 剩余风险

- 本 Task B 只证明 robot-side software compatibility fence，不证明真实 HTTPS/TLS、公网入口、真实云、4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- `remote_bridge.py` / `remote_bridge_protocol.py` 运行时代码保持现有白名单式 command envelope 行为，未做额外 runtime 改动；当前风险由新增围栏测试覆盖。

## Task C Product Closeout

### 用户价值和产品北极星

本轮把云中转公网入口/TLS readiness 从泛化 blocked 拆成两个可执行状态：缺少配置包，以及配置包存在但缺外部实证。对普通手机用户的价值不是“已经能公网使用”，而是未来手机端和售后能明确下一步该补配置还是该做真实外部 HTTPS/DNS/反向代理/防火墙验证，避免把本地 Docker proof 误读为 production ready。

产品北极星仍是普通用户用手机发起、观察和恢复送垃圾任务；本轮只推进云中转控制面进入 production 前的证据闸门，不声明真实送达闭环。

### OKR 映射和 KR 拆解

- Objective 5：云中转 + OSS/CDN 数据通路产品化，从约 59% 保守上调到约 61%。
- 直接映射 KR1：commands/status/ack 控制面前置公网入口/TLS gate，但仍没有真实 HTTPS/TLS。
- 直接映射 KR2：`docs/product/cloud_4g_infrastructure.md` 已同步公网入口/TLS gate、preflight consumption 和证据边界。
- 间接映射 KR5/KR6：gate 保持敏感字段脱敏、`production_ready=false`、`overall_status=blocked`，并给后续真实网络/配置证据留下清晰缺口。
- Objective 1/2/3/4 本轮不调整。

### 本轮核心抓手

- Task A 交付 `software_proof_docker_cloud_public_ingress_tls_gate`，preflight 明确区分 `missing_public_ingress_tls_config` 与 `public_ingress_tls_config_present_not_externally_proven`。
- Task B 交付 robot metadata-only compatibility fence，证明 public ingress/TLS readiness metadata 不触发 robot side effect。
- Task C 完成 sprint closeout、OKR 当前快照和 OKR 进度日志同步。

### 责任 Engineer 和验收口径

- Task A：`full-stack-software-engineer` 主责云中转 gate、Docker smoke、产品文档同步。
- Task B：`robot-software-engineer` 主责 robot compatibility fence、protocol normalization 和接口文档同步。
- Task C：`product-okr-owner` 主责验收、OKR 更新、进度日志和 sprint 收口。

验收口径：只接受 Docker/local software proof、targeted unittest、`py_compile`、Docker smoke 和 scoped diff check；不把 ACK、artifact、preflight 或 metadata-only response 解释成 delivery success、真实公网入口或 production readiness。

### Task C 验证结果

```bash
test -f docs/product/cloud_4g_infrastructure.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md && test -f docs/process/okr_progress_log.md
```

结果：通过，exit 0，无输出。

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate
```

结果：通过，exit 0，无输出。

### 剩余风险

- 本 sprint 证据边界是 `software_proof_docker_cloud_public_ingress_tls_gate`。
- 不声明真实 HTTPS/TLS、公网入口、真实云、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery、真实手机设备/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。

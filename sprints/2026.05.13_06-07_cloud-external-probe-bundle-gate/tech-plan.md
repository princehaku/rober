# Sprint 2026.05.13_06-07 Cloud External Probe Bundle Gate - Tech Plan

## 目标

实现 `software_proof_docker_cloud_external_probe_bundle_gate`：在 Docker-only 条件下，为未来真实公网 URL 建立可复用 cloud external probe bundle/artifact 口径，对 `/healthz`、`/readyz`、`/preflightz` 做 phone-safe / preflight-safe 探测摘要。本轮只证明本地 Docker/local probe contract 和 artifact 校验，`production_ready=false` 必须保持。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 中完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 57%；Objective 4 约 58%，Objective 1/2/3 分别约 75%/77%/77%。
2. 本 sprint 直接针对 Objective 5。
3. 选择理由：本机仍是 Docker-only，O1/O2/O3 的真实硬件、HIL、Nav2/fixed-route 和真实送达证据不可在当前环境内闭环；O5 的 external probe bundle 可以继续推进真实云上线前的产品化证据链，且不重复消费真实云/4G blocker。

## 证据依据

- `OKR.md` 4.1：O5 当前约 57%，主要缺口是真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery、real phone app/device、HIL、Nav2/fixed-route、WAVE ROVER 或 real delivery。
- `sprints/2026.05.13_05-06_mobile-task-start-confirmation-gate/final.md`：上一轮只推进 O4，Objective 5 不调整；robot fence 已把 metadata-only phone confirmation 和 action/ACK/cursor side effects 隔离。
- `sprints/2026.05.13_04-05_cloud-deployment-readiness-gate/final.md`：已有 deployment readiness gate，但缺真实外部部署证据；Docker smoke 仅证明 `/preflightz` blocked with local software proof。
- `cloud-relay/README.md`：当前已定义 `/healthz`、`/readyz`、`/preflightz`、Docker smoke 和 deployment readiness artifact；路线图仍要求 TLS / 反向代理、生产 DB、多实例一致性、灾备、真实 4G / 真实公网 / 真实 OSS / CDN。

## 并行 owner 拆分

### Owner A：full-stack-software-engineer

文件范围：

- `cloud-relay/`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `.env.example`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `cloud-relay/README.md`

任务：

1. 新增 external probe artifact schema，建议命名为 `trashbot.cloud_external_probe_bundle`，`schema_version=1`。
2. 添加 CLI 或现有 relay CLI 参数，用本地或未来公网 base URL 探测 `/healthz`、`/readyz`、`/preflightz`。
3. 输出字段至少包含 `evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate`、`production_ready=false`、`overall_status`、endpoint result、`not_proven`、`safe_summary`、`retry_hint`、`redaction_status`。
4. 将 probe summary 接入 preflight 消费路径；`/preflightz` 或 CLI preflight 不得因本地 probe 成功而变成 production ready。
5. 更新 Docker smoke fence，使本地 relay 启动后执行 external probe 并断言 endpoint 覆盖、artifact schema、blocked/prod false、敏感字段脱敏。
6. 更新 `.env.example` 只加入占位配置，不加入真实 URL、token、AK/SK、DB/queue URL。
7. 同步产品文档和 `cloud-relay/README.md`，写明该 gate 是 Docker/local software proof，不是真实云或公网证明。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
git diff --check -- cloud-relay onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py .env.example docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
```

输出证据必须包含：

- external probe artifact 的 schema、evidence_boundary、production_ready、overall_status 片段。
- Docker smoke 中 `/healthz`、`/readyz`、`/preflightz` 都被 probe 覆盖的日志片段。
- 敏感字段脱敏断言结果。

### Owner B：robot-software-engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- 如现有 robot contract 文档已有更准确位置，可只读确认后更新该文档，并在 `tech-done.md` 说明替代路径。

任务：

1. 增加 compatibility fence：`cloud_external_probe` / `deployment_readiness` / `cloud_deployment_readiness` / `preflight` metadata-only response 不触发 backend robot action。
2. 确认 metadata-only response 不 POST ACK、不推进内存 cursor、不持久化 cursor。
3. 确认 protocol normalization 仍剥离 command envelope 外的 deployment/probe metadata，不把它们变成 `trashbot.remote.v1` command。
4. 更新接口文档，写明 cloud external probe 是 diagnostic/deployment metadata，不属于 robot command，不改变 ACK 语义。
5. 保持 ACK 语义：accepted/processing only，不能代表 delivery success、真实送达、HIL 或 robot action 完成。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

输出证据必须包含：

- metadata-only response 不触发 backend action 的测试名或日志片段。
- 不 POST ACK、不推进 cursor、不持久化 cursor 的断言结果。
- ACK 语义和 probe metadata 边界的文档更新片段。

## 集成验收

两个 owner 返回后，主节点只做结果验收和 sprint closeout，不直接写工程代码。集成验收应核对：

- `software_proof_docker_cloud_external_probe_bundle_gate` 出现在 artifact、文档和 smoke 证据中。
- Artifact `production_ready=false`，并列出真实云、HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue 等 `not_proven`。
- `/healthz`、`/readyz`、`/preflightz` 全部被 external probe 覆盖。
- Robot compatibility fence 明确无 action、无 ACK、无 cursor side effect。
- `docs/` 已同步，且技术注释若有新增代码必须使用中文并保持 >20% 注释比例。

## 后续工程验收命令汇总

供主节点复制给工程子 agent：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token bash scripts/docker_smoke.sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
git diff --check -- cloud-relay onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py .env.example docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/interfaces/ros_contracts.md cloud-relay/README.md
```

## 非证明项

本 sprint 完成后仍不得声明以下内容：

- 真实云、真实 HTTPS/TLS、公网入口、公网 DNS 或生产可用。
- 真实 4G/SIM、真实手机设备、production app 或真实 PWA install prompt。
- OSS/CDN live traffic、production DB/queue、多实例一致性或 production disaster recovery。
- Nav2/fixed-route、WAVE ROVER、HIL、真实送达或任务成功。

## Closeout 文档要求

- `tech-done.md`：记录两个 owner 的实际改动文件、验证命令输出、失败定位和剩余风险。
- `side2side_check.md`：按 PRD 对照验收 external probe bundle、robot side-effect fence 和证据边界。
- `final.md`：更新 O5 进展建议、保留非证明项、说明是否满足 `software_proof_docker_cloud_external_probe_bundle_gate`。
- `OKR.md` 和 `docs/process/okr_progress_log.md`：只在工程实现和验收完成后更新。

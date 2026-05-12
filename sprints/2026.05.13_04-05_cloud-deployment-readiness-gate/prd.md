# Sprint 2026.05.13_04-05 Cloud Deployment Readiness Gate - PRD

## 背景

`cloud-relay/` 已经从 onboard 目录里的旧实现面推进为自包含 runtime 和 Docker/local smoke 入口。前序 sprint 也已覆盖 preflight、SQLite state、backup/restore、OSS/CDN manifest、network recovery、credential rotation、provisioning audit、production store/queue、queue ordering、transaction isolation 和 production recovery 等软件证明。

当前 Objective 5 的缺口不是再证明一次本地 relay 能跑，而是把这些离散 gate 汇成一个清晰的 cloud deployment readiness 交接面：云部署需要哪些环境变量、哪些 artifact、哪些 preflight check、哪些 Docker smoke 输出，以及哪些真实外部证据仍未证明。

## 用户价值和产品北极星

用户价值：

- 手机用户未来通过云端入口下发任务时，产品团队能明确知道云端是否只是本地 Docker 可跑，还是具备真实上线所需的配置证据。
- 工程和运维能用一个 readiness artifact / preflight 输出判断缺 TLS、缺公网入口、缺生产 DB/queue、缺 OSS/CDN 实流量、缺 4G/SIM，避免把 local smoke 当成 production ready。
- 机器人端不会因为云部署元数据出现在 command polling response 中而误触发动作、ACK 或 delivery success。

产品北极星：

- 正式 4G 路径是 phone web/app -> cloud API -> robot outbound polling -> ROS2 behavior。
- 云中转只承担 command/status/ack 控制面，大对象通过 OSS/CDN；本轮只补 Docker/local deployment readiness gate，不宣称真实云或真实生产链路。

## OKR 映射

Primary: Objective 5 - 云中转 + OSS/CDN 数据通路产品化。

- KR1：继续固化 `trashbot.remote.v1` commands/status/ack 契约和 HTTPS/public ingress 前置检查，但不改变 envelope。
- KR2：把 4C 8G 云端基线、healthcheck、部署环境变量和 production gap 写入 cloud deployment readiness 文档/输出。
- KR3/KR4：把 OSS/CDN 配置、manifest/artifact 消费和非证明项继续作为 readiness gate 的一部分，不声称真实上传或 CDN 回源。
- KR5：`.env.example` 只放占位符，真实凭证不入仓库；preflight 输出必须脱敏。
- KR6：4G 中断、云配置不完整、生产 DB/queue 缺失等必须呈现 graceful blocked/warning，不让手机或机器人误判为可交付。

Secondary: Objective 2 - 可送垃圾任务完整闭环。

- 仅作为 robot safety guardrail：deployment readiness metadata-only response 不得触发 robot action、不 ACK、不推进 cursor、不持久化 cursor、不把 ACK 解释成 delivery success。

## KR 拆解

### KR-A: Deployment readiness artifact

- 在 `cloud-relay/` 形成 deployment readiness artifact 的生成或读取入口。
- Artifact 必须包含 schema/version、evidence boundary、deployment checks、not_proven、safe_summary、retry_hint、generated_at 或 updated_at，以及 checksum 或等价完整性字段。
- Artifact 必须保持 `production_ready=false`，除非后续真实云/TLS/4G/DB/queue/OSS-CDN 证据补齐；本轮不允许补齐为 true。

### KR-B: Preflight / CLI / Docker smoke

- `cloud-relay` CLI 或 existing `--preflight` 能消费 deployment readiness artifact 或生成 readiness 输出。
- Docker smoke 覆盖 build/start、`/healthz`、`/readyz`、`/preflightz` 或等价 CLI smoke，以及 blocked-by-design readiness 断言。
- `.env.example` 新增或修正云部署占位变量，placeholder 必须让 preflight 维持 blocked/warning。

### KR-C: Product docs sync

- `cloud-relay/README.md` 写清运行入口、readiness artifact、CLI/Docker smoke 和非证明项。
- `docs/product/cloud_4g_infrastructure.md` 写清 deployment readiness gate 与真实云/TLS/4G/DB/queue/OSS-CDN 证据的差异。
- `docs/product/remote_4g_mvp.md` 写清 phone/cloud/robot contract 不因 deployment metadata 改变。

### KR-D: Robot compatibility fence

- 在 `test_remote_bridge.py` 或相近 compatibility fence 中覆盖 deployment-readiness metadata-only response。
- 断言 metadata-only response 不触发 collect/dropoff/cancel，不 POST ACK，不推进 `last_ack_id`，不写 cursor state，不改变 `trashbot.remote.v1` envelope。
- 断言 ACK 仍是 command accepted/processing evidence only，不是 delivery success。

### KR-E: Product closeout

- 实现完成后由 `product-okr-owner` 补齐 `tech-done.md`、`side2side_check.md`、`final.md`。
- 按实际证据更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，保守评估 Objective 5 进度，不把软件证明写成真实云完成。

## 范围边界

In scope:

- `cloud-relay/` deployment readiness artifact/preflight/CLI/Docker smoke。
- `.env.example` 的占位符级云部署配置。
- `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`cloud-relay/README.md` 同步。
- Robot remote bridge compatibility fence。
- Sprint closeout 文档、OKR 和 progress log 在实现完成后更新。

Out of scope:

- 真实云主机部署、域名申请、TLS 证书签发、公网入口开放或公网 healthcheck。
- 真实 4G/SIM、真实 OSS 上传、STS 签发、CDN 回源或实流量。
- 生产 DB/queue、多实例一致性、真实灾备恢复。
- 手机 production app、真实手机设备/浏览器验收。
- ROS2 行为状态机、Nav2/fixed-route、WAVE ROVER、UART、HIL 或真实送达。
- 改变 `trashbot.remote.v1` command/status/ack envelope。

## 优先级

- P0：deployment readiness artifact/preflight/CLI 能表达 blocked-by-design 缺口，且不泄漏 secret。
- P0：Docker smoke 或 CLI smoke 覆盖 `/healthz`、`/readyz`、`/preflightz`/readiness 输出，并断言 `production_ready=false`。
- P0：robot compatibility fence 证明 deployment metadata 不触发动作、ACK 或 cursor 变化。
- P1：`.env.example` 占位变量与 product docs 同步。
- P1：closeout 更新 OKR/progress log，保持 `software_proof_docker_cloud_deployment_readiness_gate` 边界。

## 验收口径

本轮验收通过的最小标准：

- `cloud-relay` 可生成或消费 deployment readiness artifact，并在 CLI/preflight/Docker smoke 中输出 `evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate`。
- 本地占位配置下输出必须保持 `production_ready=false` 或等价 blocked/warning；不得把 Docker/local proof 写成真实生产 ready。
- 输出不得泄漏 bearer token、Authorization header、OSS AK/SK、root password、DB URL、queue URL、credential-bearing URL、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel`、traceback 或完整敏感 artifact。
- Robot compatibility targeted unittest 通过，确认 metadata-only deployment readiness response 不触发 robot action、不 ACK、不推进或持久化 cursor、不改变 envelope。
- `docs/product/` 与 `cloud-relay/README.md` 同步完成，并明确本轮非证明项。
- 只运行围栏验证：targeted unittest、`py_compile`、cloud-relay Docker smoke 或 CLI smoke、scoped `git diff --check`。

## 责任 Engineer

- `full-stack-software-engineer`：实现 KR-A/B/C 中 cloud deployment readiness gate、`.env.example` 与云产品文档同步。
- `robot-software-engineer`：实现 KR-D 的 compatibility fence。
- `product-okr-owner`：实现完成后执行 KR-E 收口，不参与产品代码或测试代码实现。

## 风险、阻塞和证据链缺口

- 真实云、HTTPS/TLS、公网入口、4G/SIM、OSS/CDN 实流量、生产 DB/queue、多实例一致性仍全部缺失。
- 本机没有真实硬件，不能 claim WAVE ROVER motion、UART feedback、HIL、Nav2/fixed-route 或 delivery success。
- Readiness artifact 如果字段过多，容易被误读为 production checklist 已完成；文档和输出必须保留 `not_proven` 与 blocked/warning。
- 若 worker 需要变更 shared `remote_cloud_relay.py`，必须保持现有 command/status/ack、artifact gates 和 phone-safe summaries 兼容。

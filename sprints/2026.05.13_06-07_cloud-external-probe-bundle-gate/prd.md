# Sprint 2026.05.13_06-07 Cloud External Probe Bundle Gate - PRD

## 产品问题

Objective 5 当前最低且可在 Docker-only 条件下继续推进。上一轮 O4 已把手机发车确认 gate 做到本地软件证明，但云中转仍停在 deployment readiness gate：它能说明哪些生产条件还没就绪，却缺少一个面向未来公网 URL 的可复用 external probe bundle，用同一 artifact 口径读取 `/healthz`、`/readyz`、`/preflightz`，并把结果转成 phone-safe / preflight-safe 摘要。

如果没有这个 bundle，下一次接入真实 VM、反向代理、TLS 或 4G/SIM 时，团队会重复写临时 curl 和人工判断，且容易把 `/healthz` 活着误读为生产可用。

## 用户价值和产品北极星

用户价值：普通用户最终只看到手机端清晰状态，例如“云服务未就绪，任务仍可走本地 fallback”或“部署检查阻塞，需要运维处理”，而不是 raw curl、traceback、token、OSS secret、ROS topic 或串口细节。

产品北极星：云中转是手机控制和机器人 outbound polling 的产品通路；任何部署证据必须能被 Product、Full-stack、Robot 三方用同一 schema 审计，并且明确区分 Docker/local software proof 与真实公网/生产证明。

## 证据输入

- `OKR.md` 4.1：Objective 5 约 57%，低于 Objective 4 约 58%，主要缺口包括真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性和 production disaster recovery。
- `05-06_mobile-task-start-confirmation-gate/final.md`：本轮只推进 O4，Objective 5 不调整；同时保留 robot compatibility fence 对 metadata-only response 的保护。
- `04-05_cloud-deployment-readiness-gate/final.md`：已完成 `trashbot.cloud_deployment_readiness` 和 Docker/local preflight gate，但明确不是 real cloud、real HTTPS/TLS、public ingress、real 4G/SIM、OSS/CDN live traffic 或 production DB/queue。
- `cloud-relay/README.md`：当前标准入口包含 `/healthz`、`/readyz`、`/preflightz`、Docker smoke 和 deployment readiness artifact；路线图仍列出 TLS / 反向代理、生产 DB、多实例一致性、灾备、真实 4G / 公网 / OSS / CDN。

## 功能范围

本 sprint 交付 `software_proof_docker_cloud_external_probe_bundle_gate`，目标是建立 external probe bundle/artifact 的软件契约：

- 输入：一个未来可替换为公网 URL 的 relay base URL；本轮只允许 Docker/local URL，例如 `http://127.0.0.1:8088`。
- 探测：`GET /healthz`、`GET /readyz`、`GET /preflightz`。
- 输出：版本化 artifact，包含 schema、schema_version、evidence_boundary、probe_target_safe_summary、endpoint results、overall_status、production_ready、not_proven、safe_summary、retry_hint、redaction_status。
- 安全：不得泄漏 bearer token、Authorization header、OSS AK/SK、root password、DB URL、queue URL、credential-bearing URL、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic、`/cmd_vel` 或 traceback。
- preflight 消费：现有 preflight 或 CLI 能读取/生成该 external probe summary，并保持 `production_ready=false`。
- Docker smoke：在本地 Docker relay 上运行 probe，断言 artifact schema、endpoint 覆盖、blocked 边界和敏感字段脱敏。
- Robot compatibility：`cloud_external_probe`、deployment readiness 或 preflight metadata-only response 不触发机器人 action、不 POST ACK、不推进 cursor、不持久化 cursor。

## 非目标

- 不证明真实云主机、真实 HTTPS/TLS、公网入口或公网 DNS。
- 不证明真实 4G/SIM、真实手机设备或真实 app。
- 不证明 OSS/CDN live upload/fetch、production DB/queue、多实例一致性或 production disaster recovery。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实送达或任务成功。
- 不改变 ACK 语义；ACK 仍只代表 command accepted/processing evidence。

## KR 拆解或更新

- KR-A：external probe artifact schema 固化，能够记录 `/healthz`、`/readyz`、`/preflightz` 的 HTTP 状态、safe body summary 和 failure class。
- KR-B：preflight/CLI 能生成或消费该 artifact，且在本地 Docker/local 条件下明确 `evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate`、`production_ready=false`。
- KR-C：Docker smoke 对本地 relay 执行 external probe，验证 endpoint 覆盖、blocked-by-design、脱敏和 retry hint。
- KR-D：Robot bridge/protocol 测试证明 metadata-only external probe response 不会触发 robot side effects。
- KR-E：相关产品/接口文档同步说明 external probe 是部署前证据包，不是生产上线证明。

## 优先级和验收口径

- P0：artifact schema、CLI/preflight 入口、Docker smoke、robot compatibility fence。
- P1：`.env.example` 中加入未来 external probe 配置占位，且只放占位值。
- P1：`docs/product/` 与 `docs/interfaces/` 同步证据边界和 ACK/metadata 语义。
- P2：README 标准入口补充 external probe 示例；不得引入真实凭证或生产 URL。

验收必须是围栏式验证：targeted unittest、`py_compile`、Docker smoke、scoped `git diff --check`。不要求 broad regression、不要求真实公网、不要求真实硬件。

## 对应责任 Engineer

- full-stack-software-engineer：主责 external probe artifact/CLI/preflight/Docker smoke 与产品文档。
- robot-software-engineer：主责 robot metadata-only compatibility fence 与接口文档。
- Product Owner：只负责 sprint 文档、验收口径、工程结果 closeout 和 OKR 更新，不写工程代码。

## 风险、阻塞和需要补齐的证据链

- 阻塞：无真实公网 URL、TLS、4G/SIM、OSS/CDN live traffic、production DB/queue。
- 风险：`/healthz` 成功可能被误读为生产可用；artifact 必须把 readiness 和 preflight blocked 解释清楚。
- 风险：metadata-only response 若被 robot bridge 误当 command，会造成误动作；robot owner 必须提供 side-effect fence。
- 证据缺口：真实外部 probe 要等 CEO 提供公网 VM / HTTPS / 域名 / 4G/SIM / 生产存储后另开 sprint。

## 需要创建或更新的 sprint 文档

- 已创建或本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程后更新：`tech-done.md` 记录两个 worker 的实际改动和验证；`side2side_check.md` 做产品验收对照；`final.md` 收口 OKR 进展和剩余风险。

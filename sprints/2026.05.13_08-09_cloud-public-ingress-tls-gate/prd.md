# Sprint 2026.05.13_08-09 Cloud Public Ingress TLS Gate - PRD

## 背景

`OKR.md` 4.1 显示 Objective 5 云中转 + OSS/CDN 数据通路产品化约 59%，低于 Objective 4 约 60%，是当前 Docker-only 主机上最低且可继续推进的 Objective。Objective 1/2/3 仍受无真实 WAVE ROVER、无真实串口、无真实 Nav2/fixed-route 实跑和无 HIL 约束，本轮不得声明 HIL 或真实送达。

最近的 `sprints/2026.05.13_06-07_cloud-external-probe-bundle-gate/final.md` 已完成 external probe bundle，但明确剩余公网 VM、HTTPS、域名、反向代理、防火墙实配证据。`sprints/2026.05.13_07-08_mobile-operation-log-gate/final.md` 则把 O4 上调到约 60%，并建议若 O5 低于 O4，则切回云链路。`cloud-relay/README.md` 的路线图也把 TLS / 反向代理列为下一步。

本轮不是做真实云部署，而是在 Docker/local 环境推进一个可审计的软件证明：`software_proof_docker_cloud_public_ingress_tls_gate`。它要让 deployment readiness / preflight 能识别"有公网/TLS/反向代理配置包但未实证"与"完全缺配置"的差异，同时继续 fail closed。

## 用户价值和产品北极星

用户价值：普通手机用户、售后和运维支持看到云链路不可用时，能得到 phone-safe 的原因分类和下一步补证方向，例如"缺公网入口实证"、"TLS 配置包存在但未外部验证"、"反向代理配置未实配"，而不是只看到笼统 blocked。

产品北极星：rober 的云中转产品化必须把控制面、数据面、部署面和证据面分清楚。软件配置 gate 可以提高部署准备度，但必须严格区别于真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性和灾备证明。

## 目标用户

- 普通手机用户：只需要知道云链路当前是否可用、是否应走 fallback、是否需要等待运维处理。
- 售后/运维支持：需要一份脱敏、结构化、可复用的公网入口/TLS/反向代理配置摘要，用于真实云部署前检查。
- 工程团队：需要 preflight 和 robot compatibility fence 确认该 metadata 不会触发机器人动作、ACK 或 delivery success 语义。

## OKR 映射

- Objective 5 KR1：为 HTTPS 云中转契约增加部署前配置 gate，但不声明真实 HTTPS。
- Objective 5 KR2：把公网入口、反向代理、防火墙策略和运维边界从文档缺口推进到可机读 readiness artifact。
- Objective 5 KR4：继续保护 CDN / public URL 语义，不把配置占位当作 OSS/CDN live traffic。
- Objective 5 KR5：凭证和证书相关输出必须脱敏，`.env` 与私钥不进入仓库和 artifact。
- Objective 5 KR6：为未来网络中断、入口不可达、TLS 失败和云/机器人问题区分打基础。

## KR 拆解或更新

### KR-A：Public ingress/TLS 配置 artifact

- 定义 `trashbot.cloud_public_ingress_tls_gate` 或等价 schema，`schema_version=1`。
- artifact 只记录 phone-safe 配置状态、字段存在性、配置来源类别、脱敏校验和 not_proven 列表。
- 不记录真实 base URL、credential-bearing URL、Authorization header、证书私钥、root password、DB/queue URL、OSS AK/SK、本地 state path、串口、ROS topic 或 `/cmd_vel`。
- artifact 必须输出 `evidence_boundary=software_proof_docker_cloud_public_ingress_tls_gate`、`production_ready=false`、`overall_status=blocked`。

### KR-B：Deployment readiness / preflight 消费

- deployment readiness / `--preflight` 能消费该 artifact 或配置包。
- 完全缺配置时，输出明确 blocked 原因。
- 配置包存在但未实证公网/TLS 时，输出不同 blocked 原因：`config_present_but_not_externally_proven` 或同等 phone-safe 分类。
- 不允许 Docker/local smoke 因配置包存在而通过 production ready。

### KR-C：phone-safe summary 与文档同步

- `cloud-relay/README.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md` 写清该 gate 是 deployment readiness proof，不是真实公网/TLS proof。
- phone-safe 文案能解释缺口：公网 VM、DNS、TLS 证书链、反向代理、防火墙、真实外部 probe、4G/SIM、production DB/queue、OSS/CDN live traffic。

### KR-D：Robot metadata-only compatibility fence

- `remote_bridge` / protocol 测试确认 public ingress/TLS metadata-only response 不触发 backend action。
- 不 POST ACK。
- 不推进或持久化 cursor。
- protocol normalization 剥离 command envelope 外 metadata。

### KR-E：Product closeout 与 OKR 边界

- Product 收口时只在 worker 返回真实改动和验证后更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 若只完成 Docker/local gate，可保守提高 Objective 5，但不得声明真实 HTTPS/TLS、公网入口、真实云/4G、OSS/CDN live traffic、production DB/queue、HIL 或真实送达。

## 本轮核心抓手

本轮抓手是"公网入口/TLS/反向代理 readiness 从文档缺口变成可机读、可脱敏、可 fail-closed 的配置证明"。它不是上线、不是外部 probe 成功、不是证书签发成功，也不是真实 4G 或 OSS/CDN 生产流量。

## 需要做什么

1. full-stack-software-engineer 增加 cloud public ingress/TLS artifact 或 gate，接入 cloud-relay deployment readiness / preflight，并同步 cloud-relay 与产品文档。
2. robot-software-engineer 增加 remote bridge / protocol metadata-only compatibility fence，确认该 readiness metadata 不改变 robot command/status/ack 语义。
3. product-okr-owner 在实现后做 side-by-side 验收，确认 evidence boundary、OKR 口径、剩余风险和下一步真实云/公网补证路径。

## 优先级和验收口径

P0：

- artifact / gate 生成并包含 `evidence_boundary=software_proof_docker_cloud_public_ingress_tls_gate`。
- `production_ready=false`、`overall_status=blocked` 在配置存在和配置缺失两种路径都保持正确。
- preflight 能区分"配置完全缺失"与"配置存在但未公网/TLS实证"。
- 输出不泄漏 token、Authorization、证书私钥、OSS AK/SK、root password、DB/queue URL、本地路径、ROS topic、`/cmd_vel`、串口或 WAVE ROVER 参数。
- robot compatibility fence 证明 metadata-only response 不触发 action、ACK 或 cursor。

P1：

- `cloud-relay/README.md` 路线图从笼统 TLS / 反向代理更新为本 gate 的具体证据边界。
- `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md` 写清真实公网/TLS/4G 仍需后续实证。
- Product closeout 补齐 sprint 六文档链路并保守更新 OKR。

## 对应责任 Engineer

- full-stack-software-engineer：cloud-relay / onboard relay artifact、preflight consumption、Docker/local smoke、cloud 文档同步。
- robot-software-engineer：remote_bridge / protocol metadata-only compatibility fence、接口文档同步。
- product-okr-owner：side2side 验收、`OKR.md`、`docs/process/okr_progress_log.md`、sprint closeout。

## 非目标

- 不申请、签发或验证真实 TLS 证书。
- 不配置真实公网 VM、域名解析、反向代理或云防火墙。
- 不做真实 4G/SIM、真实手机设备、production app 或 OSS/CDN live traffic。
- 不接入 production DB/queue、多实例一致性或 production disaster recovery。
- 不做 ROS2 runtime、Nav2/fixed-route、WAVE ROVER、串口、HIL 或真实送达。
- 不把配置包存在误读为 production ready。

## 风险、阻塞和需要补齐的证据链

- 真实公网 VM / DNS / TLS / 反向代理 / 防火墙仍是后续实证 blocker。
- 真实 4G/SIM、真实手机设备、OSS/CDN live traffic、production DB/queue 和 disaster recovery 仍缺。
- Robot path 只能验证 metadata 不产生副作用，不能证明真实机器人执行或送达。
- 本轮需要补齐的证据链是 targeted unittest、`py_compile`、Docker/local smoke 或 CLI drill、scoped `git diff --check`，并明确 `software_proof_docker_cloud_public_ingress_tls_gate`。

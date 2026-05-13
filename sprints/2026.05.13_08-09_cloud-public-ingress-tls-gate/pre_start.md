# Sprint 2026.05.13_08-09 Cloud Public Ingress TLS Gate - Pre Start

## Sprint Type

- `sprint_type: epic`
- 本轮是 Objective 5 云中转 + OSS/CDN 数据通路产品化的跨 owner Epic sprint planning。
- 当前阶段只创建 planning docs：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 本阶段不改产品代码、测试代码、`OKR.md` 或 `docs/` 正文；后续实现必须由对应 Engineer 子 agent 执行。

## 启动依据

- `OKR.md` 4.1 最新快照更新时间：2026-05-13 07:14 Asia/Shanghai。
- 当前 Docker-only 主机上最低且可推进 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 59%。
- Objective 4 已在 `sprints/2026.05.13_07-08_mobile-operation-log-gate/final.md` 中因 mobile operation log gate 上调到约 60%，该 final 建议若 O5 低于 O4，则切回云链路。
- Objective 1/2/3 分别约 75%/77%/77%，主要缺真实 WAVE ROVER、真实串口、Nav2/fixed-route 实跑、HIL 和真实送达；本机只有 Docker，本轮不得声明 HIL 或真实送达。
- `sprints/2026.05.13_06-07_cloud-external-probe-bundle-gate/final.md` 已完成 `software_proof_docker_cloud_external_probe_bundle_gate`，但剩余真实公网 VM、HTTPS、域名、反向代理、防火墙实配证据。
- `cloud-relay/README.md` 当前路线图把 TLS / 反向代理列为下一步，同时提醒 deployment readiness / preflight 必须保持 `production_ready=false`、`overall_status=blocked`，不能把 Docker/local proof 误读为生产就绪。

## 上轮未完成项

- Objective 5 仍缺真实云、真实 HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、多实例一致性、production disaster recovery、real phone app/device、HIL、Nav2/fixed-route、WAVE ROVER 或 real delivery。
- 上轮 external probe bundle 只能证明本地或未来公网 base URL 的 `/healthz`、`/readyz`、`/preflightz` 合同可被探测并生成 phone-safe artifact；未实证公网入口、TLS 证书链、域名解析、反向代理或防火墙。
- 当前 cloud relay deployment readiness 已能报告若干缺口，但还需要一个 phone-safe 的公网入口/TLS/反向代理配置 gate，使 preflight 区分"已有配置包但未实证"和"完全缺配置"。

## 本轮目标

建立 `software_proof_docker_cloud_public_ingress_tls_gate`：

- 新增或验证 phone-safe 的公网入口/TLS/反向代理配置 artifact 或 gate。
- deployment readiness / preflight 能区分"有公网/TLS配置包但未实证"和"完全缺配置"。
- artifact 与 phone-safe summary 不泄漏域名凭证、证书私钥、bearer token、root password、DB/queue URL、OSS AK/SK 或本地路径。
- 必须保持 `production_ready=false`、`overall_status=blocked`。
- 不声明真实 HTTPS/TLS、公网入口、真实云、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、HIL 或真实送达。

## 用户价值和产品北极星

用户价值：普通手机用户和售后支持不需要理解 Nginx、证书、域名、防火墙或 Docker 内部细节，也能看到云端控制链路为什么还不能上线，以及下一步需要运维补齐哪类真实证据。

产品北极星：rober 的云中转链路要能把部署准备度拆成可审计、可脱敏、可复用的证据层级；软件配置证明只能说明"部署包准备度提升"，不能替代真实公网、TLS、4G、生产 DB/queue 或 OSS/CDN live traffic 证明。

## OKR 映射

- Objective 5 KR1：继续推进云中转 HTTPS/outbound polling 契约的部署准备度，但只做 Docker/local gate，不声明真实 HTTPS。
- Objective 5 KR2：补齐公网入口、反向代理、防火墙、运维边界的配置证明和 preflight 表达。
- Objective 5 KR4：保持 CDN base URL 和公网只读视图的边界，避免把未实证配置当 live traffic。
- Objective 5 KR5：配置 artifact 与 preflight 输出必须继续脱敏，不能泄漏真实 token、证书私钥或云凭证。
- Objective 5 KR6：为未来真实公网/4G/OSS/CDN 验证提供 readiness gate，失败时能区分网络入口缺口、TLS 配置缺口和生产数据层缺口。

## 范围边界

后续工程允许范围建议：

- full-stack-software-engineer：
  - `cloud-relay/`
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - `docs/product/cloud_4g_infrastructure.md`
  - `docs/product/remote_4g_mvp.md`
- robot-software-engineer：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - `docs/interfaces/ros_contracts.md`
- product-okr-owner：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - 本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`

本 planning 阶段只允许创建：

- `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/pre_start.md`
- `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/prd.md`
- `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/tech-plan.md`

## 阻塞与风险

- 无真实公网 VM、域名、TLS 证书或反向代理实配：本轮只能做配置 artifact / preflight gate，不能证明真实公网入口。
- 无真实 4G/SIM 或手机设备：本轮不能证明真实 mobile-to-cloud-to-robot 链路。
- 无 production DB/queue、多实例和灾备：本轮不能声明 production_ready。
- 无真实硬件、Nav2/fixed-route 或 HIL：本轮不能提高 O1/O2/O3 的真实闭环证据。
- 若 artifact 设计过宽，可能泄漏证书路径、token、云账号、DB URL 或把未实证配置误报为可上线；必须 fail closed。

## 需要创建或更新的 sprint 文档

- 已创建/待填写：`pre_start.md`
- 已创建/待填写：`prd.md`
- 已创建/待填写：`tech-plan.md`
- 后续执行后必须补齐：`tech-done.md`
- 后续验收后必须补齐：`side2side_check.md`
- 后续收口后必须补齐：`final.md`

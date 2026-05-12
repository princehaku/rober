# Sprint 2026.05.13_04-05 Cloud Deployment Readiness Gate - Pre Start

## Sprint Type

- sprint_type: epic
- Theme: `cloud-deployment-readiness-gate`
- Product Owner: `product-okr-owner`
- Primary Objective: Objective 5 - 云中转 + OSS/CDN 数据通路产品化
- Secondary Guardrail: Objective 2 - robot remote bridge 不得把部署元数据解释成任务动作
- Evidence boundary target: `software_proof_docker_cloud_deployment_readiness_gate`
- OKR number update: 本启动任务不更新 `OKR.md` 数字；实现和验证完成后由 `product-okr-owner` 在收口阶段保守更新。

## 用户价值和产品北极星

用户价值：普通手机用户最终需要通过云端入口控制小车，而不是要求手机和小车在同一 WiFi。下一步最有价值的不是继续堆本地 mock，而是让云中转服务具备可交接给真实云部署的 readiness artifact、preflight、CLI 和 Docker smoke，明确告诉工程和运维还缺什么。

产品北极星：把 rober 做成手机可操作、可远程诊断、可逐步上线的低成本 ROS2 送垃圾机器人。本轮只推进 cloud deployment readiness 的 Docker/local 软件证据，不声明真实云、公网 HTTPS/TLS、4G/SIM、OSS/CDN 实流量、生产 DB/queue、HIL 或真实送达。

## 启动证据

- `OKR.md` 4.1 当前快照显示 Objective 5 约 55%，Objective 4 约 56%，Objective 1/2/3 约 75%/77%/77%；按数字排序 Objective 5 是当前最低 Objective。
- `sprints/2026.05.13_03-04_mobile-web-entrypoint-gate/final.md` 显示上轮 Objective 4 已从约 54% 推进到约 56%，但 Objective 5 保持约 55%，仍缺真实云、公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、多实例一致性、OSS/CDN 实流量。
- `sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/final.md` 已完成 `cloud-relay/` self-contained runtime gate，并建议继续 Objective 5 的真实云前置链路：生产环境配置审计、部署凭证占位校验、TLS/域名/healthcheck runbook 或云端队列替身到真实服务切换计划。
- `docs/product/cloud_4g_infrastructure.md` 已明确 `/healthz`、`/readyz`、`/preflightz`、CLI `--preflight`、artifact gate 和 `production_ready=false` 边界；本轮应复用该梯子，不新造真实云结论。
- `cloud-relay/README.md` 将 `cloud-relay/` 定义为公网云中转服务部署单位，但路线图仍留下 TLS/反向代理、生产 DB、多实例一致性和灾备 backup 策略。

## 上轮未完成项和本轮切换原因

03-04 final 建议若没有真实手机/云/硬件，则不要夸大证据。当前 live `OKR.md` 已使 Objective 5 低于 Objective 4；同时本机仍只有 Docker，没有真实硬件、真实 4G/SIM、真实公网云或真实手机设备。因此本轮回到 Objective 5，但只做 deployment readiness gate，不重复消费 02-03 已完成的 self-contained runtime gate，也不声称真实生产部署。

本轮不触碰 WAVE ROVER、ESP32、Orange Pi、UART、电气、机械或 HIL 配置；无需读取 vendor 硬件资料作为实现前置。若后续 worker 任务新增任何硬件事实，必须回到 `docs/vendor/VENDOR_INDEX.md`。

## 本轮核心抓手

1. 在 `cloud-relay/` 增加 deployment readiness artifact / preflight / CLI / Docker smoke，使生产云部署缺口可机器读取、可审计、可交给运维继续补证据。
2. 将 `.env.example` 补齐为占位符级别的云部署配置入口，确保真实 secret 不入仓库，placeholder 必须保持 blocked。
3. 同步 `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md` 与 `cloud-relay/README.md`，明确本轮证据边界是 `software_proof_docker_cloud_deployment_readiness_gate`。
4. 用 robot compatibility fence 证明 deployment-readiness metadata-only response 不触发 robot action、不 ACK、不推进或持久化 cursor、不改变 `trashbot.remote.v1` envelope。
5. 收口阶段由 product owner 更新 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`。

## 责任 Owner

- `full-stack-software-engineer`：主责 `cloud-relay/` deployment readiness artifact/preflight/CLI/Docker smoke、`.env.example` 占位和云产品文档同步。
- `robot-software-engineer`：主责 remote bridge compatibility fence，确认 deployment-readiness metadata-only response 不污染 robot command/status/ack envelope。
- `product-okr-owner`：本启动阶段只负责 PRD、验收口径、owner 边界和 sprint 留档；实现完成后负责 OKR 口径、progress log 与 Epic closeout。

## 阻塞和风险

- 当前没有真实云主机、域名、TLS 证书、公网 healthcheck、真实 4G/SIM、生产 DB/queue、真实 OSS/CDN 流量或多实例环境；本轮只能形成 Docker/local software proof。
- Deployment readiness artifact 不能因为字段齐全就写成 `production_ready=true`；真实外部证据缺失时必须保持 blocked 或 warning。
- `.env.example` 只能新增占位符，不得写入真实 bearer token、OSS AK/SK、root password、DB URL、queue URL 或 credential-bearing URL。
- Robot 侧必须把 deployment readiness metadata 视为云端诊断元数据，不能触发 `/trashbot/collect_trash`、dropoff confirm、cancel、ACK、cursor 推进或 delivery success 文案。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后必须补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- 最终收口时按实际证据更新：`OKR.md`、`docs/process/okr_progress_log.md`。

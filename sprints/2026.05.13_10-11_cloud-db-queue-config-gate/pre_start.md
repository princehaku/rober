# Sprint 2026.05.13_10-11 Cloud DB/Queue Config Gate - Pre Start

## sprint_type

sprint_type: epic

## 启动时间

2026-05-13 10:04 Asia/Shanghai

## 本轮目标

本轮继续推进当前 `OKR.md` 4.1 中最低完成度的 Objective 5（约 61%）：云中转 + OSS/CDN 数据通路产品化。目标不是声明真实生产 DB/queue ready，而是在 Docker-only 主机上补齐 production DB/queue 配置包 gate，让 preflight、phone-safe summary 和 robot compatibility fence 能区分：

- 缺 production DB/queue 配置包；
- 配置包形态存在，但还没有真实外部 DB/queue、多实例、备份、灾备和公网云实证。

## 证据来源

- `OKR.md` 4.1：Objective 5 约 61%，低于 Objective 4 约 62%，O1/O2/O3 均更高。
- `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/final.md`：O5 已完成 public ingress/TLS 配置 gate，但剩余真实 production DB/queue、多实例一致性、production disaster recovery。
- `sprints/2026.05.13_09-10_mobile-action-feedback-gate/final.md`：上轮推进 Objective 4，不调整 Objective 5；O5 仍保留 production DB/queue 缺口。
- `cloud-relay/README.md` roadmap：下一个 sprint 明确列出 TLS/反向代理、生产 DB（PostgreSQL）、多实例一致性、灾备 backup 策略。

## Blocker 扫描

最近两轮没有连续消费同一个 blocker：

- `08-09_cloud-public-ingress-tls-gate`：公网入口/TLS/反向代理配置 gate，本地软件证明，真实外部 HTTPS/TLS/DNS/防火墙仍缺。
- `09-10_mobile-action-feedback-gate`：手机动作回执 gate，推进 Objective 4，未消费 O5 DB/queue blocker。

本机没有真实硬件、真实云、真实 4G/SIM 或 production DB/queue 凭证；本轮只做 Docker/local software proof，不碰 WAVE ROVER、UART、HIL、Nav2/fixed-route 或真实 delivery。

## Owner

- Full-Stack Engineer：实现 cloud DB/queue config gate、preflight 消费、Docker smoke 和产品/部署文档。
- Robot Platform Engineer：补 robot-side metadata-only compatibility fence，确保 DB/queue 配置 metadata 不触发本地任务、ACK、cursor 或 command payload 污染。
- Product Manager / OKR Owner：实现返回后做 side2side/final、OKR 和 progress log 收口。

## 验收边界

只接受 targeted unittest、`py_compile`、Docker smoke、scoped `git diff --check` 和引用路径检查。不把 artifact、preflight、ACK、metadata-only response 或 local Docker smoke 解释成真实生产 DB/queue、多实例一致性、真实云、真实 4G/SIM、OSS/CDN live traffic、HIL 或真实送达。

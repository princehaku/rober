# Sprint 2026.05.13_14-15 OSS/CDN Live Probe Gate - Pre Start

## Sprint 声明

- sprint_type: epic
- 当前时间：2026-05-13 14:02 Asia/Shanghai
- 主目标：Objective 5 云中转 + OSS/CDN 数据通路产品化。
- 证据边界：`software_proof_docker_oss_cdn_live_probe_gate`。

## 启动依据

`OKR.md` 4.1 当前最低完成度为 Objective 5 约 65%。上一轮 `2026.05.13_13-14_mobile-device-acceptance-readiness-gate/final.md` 明确收口后 Objective 5 成为下一轮最低完成度，并建议围绕真实云、4G、OSS/CDN live traffic 或 production DB/queue 外部证据推进。

近期 O5 证据链显示：

- `2026.05.13_12-13_cloud-db-queue-external-probe-gate` 已完成 DB/queue external probe bundle，但仍明确没有真实 DB/queue connectivity、真实云、真实 4G/SIM 或 OSS/CDN live traffic。
- `docs/product/cloud_4g_infrastructure.md` 已固化 OSS/CDN manifest proof 只验证对象引用 shape、prefix/CDN URL 和 checksum，不等于真实 OSS upload 或 CDN origin fetch。
- 当前主机没有真实硬件，只有 Docker；本轮不消费 O1/HIL blocker，不声明 WAVE ROVER、Nav2/fixed-route、真实送达或真实 4G 完成。

## 本轮目标

把 OSS/CDN live traffic 缺口推进为可执行、可审计、可被 preflight 和 robot compatibility fence 消费的 live probe gate：

- Full-stack owner 增加 `oss_cdn_live_probe` artifact/preflight/CLI 能力。
- Robot owner 增加 metadata-only compatibility fence，证明该 readiness metadata 不触发 robot action、ACK 或 cursor 推进。
- Product owner 在工程证据返回后更新 OKR、progress log 和 sprint closeout。

## 风险边界

- 本机 Docker/local proof 不能证明真实 OSS 上传、CDN 回源、生产账号、真实云、真实 4G/SIM、手机设备/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 command envelope accepted/processing evidence，不是 delivery success。
- 验证只做围栏：targeted unittest、`py_compile`、scoped `git diff --check` 和一个 CLI smoke。

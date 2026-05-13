# Sprint 2026.05.13_12-13 Cloud DB/Queue External Probe Gate - Pre Start

## sprint_type

sprint_type: epic

## 启动时间

2026-05-13 12:03 Asia/Shanghai

## 启动背景

本轮按 `OKR.md` 4.1 重新排序：Objective 5 云中转 + OSS/CDN 数据通路产品化约 63%，低于 Objective 4 约 64%、Objective 1 约 75%、Objective 2/3 约 77%。当前主机没有真实硬件，只有 Docker；因此不再重复消费 O1/HIL 串口 blocker，也不把本地 software proof 说成真实云或真实生产。

最近证据：

- `sprints/2026.05.13_10-11_cloud-db-queue-config-gate/final.md`：已完成 `software_proof_docker_cloud_db_queue_config_gate`，但明确剩余真实 production DB/queue、多实例一致性、queue ordering、transaction isolation、production disaster recovery。
- `sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/final.md`：手机首屏已消费 cloud/preflight/DB/queue readiness 摘要，但 Objective 5 未提升，仍缺真实云/4G/OSS/CDN/production DB/queue 外部证据。
- `docs/product/remote_4g_mvp.md` 当前 DB/queue config gate 只能区分 missing 与 config-present-not-externally-proven，下一步需要可复用的 external probe bundle 入口。

## 本轮目标

建立 `software_proof_docker_cloud_db_queue_external_probe_gate`：在 Docker/local 环境下提供 DB/queue external probe bundle artifact、preflight consumption、phone-safe blocked 摘要和 robot metadata-only compatibility fence。该 gate 只证明 artifact schema、redaction、preflight 消费和兼容性，不连接真实 production DB/queue，不声明 production_ready。

## Owner

- Task A：`full-stack-software-engineer`，负责 cloud relay artifact/preflight/CLI、Docker smoke 或 targeted relay validation、产品文档。
- Task B：`robot-software-engineer`，负责 remote bridge / protocol metadata-only compatibility fence 和接口文档。
- Task C：`product-okr-owner`，负责 sprint closeout、OKR 和 progress log 收口。

## 风险和边界

- 本轮不需要真实 WAVE ROVER、串口、Nav2、手机设备或真实云凭证。
- DB/queue probe bundle 不得输出 DB URL、queue URL、credential-bearing endpoint、Authorization、bearer token、root password、本机路径、ROS topic、`/cmd_vel` 或硬件字段。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
- `production_ready=false` 与 `overall_status=blocked` 必须保持，除非未来有真实外部生产证据。

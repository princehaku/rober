# Sprint 2026.05.13_02-03 Cloud Relay Self-Contained Gate - Pre Start

## sprint_type

`epic`

## 背景证据

- `OKR.md` 4.1 当前快照更新到 2026-05-13 01:33，最新功能进度仍以 `2026.05.13_00-01_phone-offline-resume-gate` 的 O5 约 54%、O6 约 53% 为有效数字；`2026.05.13_01-02_codebase-restructure-four-tier` 明确不调整 OKR。
- `sprints/2026.05.13_01-02_codebase-restructure-four-tier/final.md` 明确遗留 P5：`operator_gateway` 与 relay 源码迁入 `cloud-relay` 并集成，且上一轮按 CEO 指令跳过全部测试与构建。
- `sprints/2026.05.12_25-26_remote-production-recovery-gate/final.md` 证明 O6 production recovery gate 仍是 `software_proof_docker_production_recovery_gate`，没有真实云、4G/SIM、生产 DB/queue、OSS/CDN 实流量。
- `docs/process/okr_progress_log.md` 连续记录 O6 relay / preflight / production recovery proof 仍以 onboard behavior 包源码作为实现面，目录分层后需要把 cloud-relay 变成更清晰的部署单位。

## 本轮目标

把 `cloud-relay/` 从“Dockerfile/compose 包装层”推进为可独立验证的云中转部署入口：源码入口、Docker context、smoke 命令、产品文档和 OKR 留档都指向 `cloud-relay/`，但继续保持证据边界为 Docker/local software proof。

## Owner

- 主责实现：`full-stack-software-engineer`
- 兼容性与 bringup 边界核对：`robot-software-engineer`
- OKR / sprint 收口：`product-okr-owner`

## 范围边界

- 做：`cloud-relay/` 自包含源码入口、Dockerfile/compose/smoke 路径对齐、O6 产品文档同步、必要的 ROS2 behavior 兼容围栏。
- 不做：真实公网 HTTPS/TLS、4G/SIM、真实 OSS/CDN 上传或回源、生产 DB/queue、多实例一致性、HIL、真实手机设备验收。
- 不做：把本地 `operator_gateway` 从 ROS2 bringup 中移除；本轮只处理 cloud-relay 独立部署入口，避免破坏本地 fallback 调试。

## Blocker 扫描

最近两轮：

- `2026.05.13_00-01_phone-offline-resume-gate`：功能完成，剩余风险是真实手机/云/硬件缺口，不是 blocked sprint。
- `2026.05.13_01-02_codebase-restructure-four-tier`：结构治理完成但验证跳过，遗留 P5，不是同一 blocker 重复消费。

本轮不继续消费 `/dev/ttyUSB0`、真实云账号、4G/SIM 或 Docker registry blocker。

## 验收口径

- `cloud-relay/` 可以通过 Docker/local smoke 证明服务启动、ready/preflight、commands/status/ack、artifact drill 的基本路径。
- 针对性 Python tests 与 `py_compile` 通过。
- 文档明确新路径与旧 `docker-compose.remote-cloud-relay.yml` / `scripts/remote_cloud_relay_docker_smoke.sh` 的迁移关系。
- `OKR.md` 只做保守 O6 小幅进展，且必须写清楚不是真实生产云证明。

# Sprint 2026.05.13_02-03 Cloud Relay Self-Contained Gate - Side2Side Check

## 验收对照

| 计划验收项 | 实际结果 | 结论 |
| --- | --- | --- |
| `cloud-relay/` 可以作为 Docker/local self-contained runtime 入口 | 新增 `cloud-relay/src/ros2_trashbot_cloud_relay/`，Dockerfile/compose/smoke 使用新 module 入口 | 通过 |
| Docker/local smoke 覆盖服务启动、ready/preflight、commands/status/ack 与 artifact drill | `bash cloud-relay/scripts/docker_smoke.sh` 通过，覆盖 build/start、`/readyz`、`/healthz`、production preflight blocked with `production_ready=false`、command/status/ACK、backup/restore drill、restart recovery | 通过 |
| `trashbot.remote.v1` command/status/ack envelope 不被 runtime metadata 污染 | robot compatibility fence `Ran 97 tests in 45.900s OK`，确认 metadata 不触发 action、不 ACK、不推进 cursor、不把 ACK 解释成 delivery success | 通过 |
| 文档同步新路径，保守写明真实云/4G/HIL 缺口 | `cloud-relay/README.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`mobile/README.md`、`README.md` 已由 engineer 同步 | 通过 |
| OKR 只做保守 O6/O5 云中转小幅进展 | Objective 5（历史 O6）仅从约 53% 上调到约 55%，证据边界为 `software_proof_docker_cloud_relay_self_contained_gate` | 通过 |

## 用户价值核对

- 产品北极星：普通手机用户最终面对稳定云端入口，而不是依赖开发者理解 ROS2 包路径或旧仓库结构。
- 本轮抓手：把云中转从四分层后的包装层推进为可独立验证的 `cloud-relay/` runtime 部署单元。
- KR 映射：支撑 Objective 5 KR1、KR2、KR5、KR6；其中 KR1/KR2 的部署入口清晰度提升，KR5/KR6 的凭证与降级口径保持保守。

## 证据边界核对

本轮可以声明：

- `software_proof_docker_cloud_relay_self_contained_gate`
- Docker/local relay 启动与 readiness smoke 通过
- `production_ready=false`
- commands/status/ACK envelope 与 robot compatibility fence 通过

本轮不能声明：

- 真实云或公网 HTTPS/TLS 已上线
- 真实 4G/SIM 链路可用
- 真实 OSS upload、CDN origin fetch 或 OSS/CDN 实流量完成
- 生产 DB/queue、多实例一致性或生产级灾备完成
- WAVE ROVER、HIL、真实 Nav2/fixed-route 或真实送达完成

## 文档路径核对

- `OKR.md`：存在，已更新当前快照。
- `docs/process/okr_progress_log.md`：存在，已追加本轮记录。
- `docs/product/cloud_4g_infrastructure.md`：存在，由 engineer 同步新 `cloud-relay/` 入口。
- `docs/product/remote_4g_mvp.md`：存在，由 engineer 同步新 `cloud-relay/` 入口。
- `cloud-relay/README.md`：存在，由 engineer 同步 runtime / smoke 入口。

## 收口判断

本轮满足 sprint PRD 与 tech-plan 的产品验收口径，可以收口为完成。下一步不应继续重复证明同一个 Docker/local self-contained gate，而应推进真实云/4G 前置准备中不依赖硬件的最短链路，或在 CEO 提供凭证/设备后转入真实云与上车验收。

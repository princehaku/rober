# Sprint 2026.05.12_19-20 Remote Production Store Queue Gate - PRD

## 用户价值

远程手机入口要进入真实云前，普通用户和运维都需要知道：当前系统是否只是本地 proof，还是已经具备生产级 command/status/ack 持久化、队列和多实例一致性证据。本轮把这个阻断项产品化为可校验、可展示、可复盘的 phone-safe gate。

## OKR 映射

- 主目标：Objective 6 `4G 云中转 + OSS/CDN 数据通路产品化`
- 支撑 KR：KR1 commands/status/ack 契约、KR2 云端基线、KR5 凭证与生产边界、KR6 graceful degradation。
- 证据边界：`software_proof_docker_production_store_queue_gate`

## 核心需求

1. remote cloud relay 能生成 production store/queue gate artifact。
2. Artifact 必须写清 backend、queue contract、multi-instance、migration、backup/restore、disaster recovery 的软件边界和 `not_proven`。
3. `--preflight` / `/preflightz` 能消费该 artifact，输出 `production_store_queue` check。
4. Operator `/api/status.phone_readiness` 与 `/api/diagnostics` 能展示 phone-safe 摘要，不暴露路径、token、Authorization、AK/SK、串口、ROS topic 或 `/cmd_vel`。
5. Robot compatibility fence 确认新增 gate 不改变 robot-side command/status/ack envelope 和 ACK 语义。

## 非目标

- 不接真实云账号。
- 不搭真实生产 DB/queue。
- 不证明多实例一致性。
- 不证明真实 4G/SIM、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 验收口径

- 新 artifact 可通过 CLI 生成并通过 checksum/schema/phone-safe 校验。
- preflight 有效 artifact 后新增 `production_store_queue=pass` 软件证明 check，但 `production_ready=false` 和真实生产缺口必须保持。
- missing/invalid/stale artifact 必须 fail closed 或 warning，并给 phone-safe retry hint。
- Operator status/diagnostics 消费 ready/missing/invalid/stale 摘要。
- Targeted tests、py_compile、scoped diff check 通过。

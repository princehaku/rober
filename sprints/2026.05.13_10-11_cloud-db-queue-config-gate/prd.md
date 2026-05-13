# Sprint 2026.05.13_10-11 Cloud DB/Queue Config Gate - PRD

## 用户价值

普通手机用户不需要理解 PostgreSQL、Redis、NATS、RabbitMQ、多实例或灾备。系统应把云端控制面是否具备生产 DB/queue 配置包，转换成可读、可恢复、不可误解的状态：缺配置时提示补配置包；配置形态存在但无外部实证时提示继续做真实 DB/queue、多实例、备份和灾备验证。

## OKR 映射

- Objective 5 KR1：commands/status/ack 控制面要走云中转；生产 DB/queue 是控制面从 Docker proof 走向公网可用的关键前置。
- Objective 5 KR2：云端服务端基线和运维边界需要明确生产存储/队列配置。
- Objective 5 KR5：凭证和敏感字段不能泄漏到 artifact、preflight 或 phone-safe 输出。
- Objective 5 KR6：失败必须 graceful degradation；缺 DB/queue 或仅配置形态存在时不能显示绿色 ready。

## 范围

本轮新增 `trashbot.cloud_db_queue_config_gate` software proof：

- 通过环境变量或 CLI 生成本地 artifact，保存枚举化 DB/queue 配置状态、迁移/runbook/backup/monitoring 状态和缺口摘要。
- `production_preflight_payload` 能消费 artifact 或 inline gate，并输出 `cloud_db_queue_config` check。
- 所有路径保持 `production_ready=false` 和 `overall_status=blocked`，并保留真实 production DB/queue、多实例一致性、生产 queue ordering、transaction isolation、备份、灾备、真实云、真实 4G/SIM 等 `not_proven`。
- Robot bridge 证明这些 metadata 只属于 readiness/support，不进入 `trashbot.remote.v1` command/status/ACK envelope。

## 非目标

- 不连接真实 PostgreSQL、Redis、NATS、RabbitMQ 或云厂商 DB/queue。
- 不做真实公网、真实 TLS、4G/SIM、OSS/CDN live traffic、HIL、Nav2/fixed-route 或真实送达。
- 不改底盘、硬件、UART、WAVE ROVER、launch 参数或自主导航。
- 不新增大批测试；只加围栏测试。

## 验收口径

- Full-Stack：targeted relay unittest、relay `py_compile`、`cloud-relay/scripts/docker_smoke.sh`、scoped diff check。
- Robot：targeted remote bridge/protocol unittest、`py_compile`、scoped diff check。
- Product：`OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout 引用路径存在性检查。

## 成功标准

本轮成功时，Objective 5 可以从约 61% 保守推进到约 63%，证据边界命名为 `software_proof_docker_cloud_db_queue_config_gate`。该提升只代表 Docker/local 配置 gate、preflight 消费、phone-safe 摘要和 robot side-effect fence 完成。

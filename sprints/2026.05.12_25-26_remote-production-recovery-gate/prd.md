# Sprint 2026.05.12_25-26 Remote Production Recovery Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 目标证据：`software_proof_docker_production_recovery_gate`

## 用户价值和产品北极星

北极星仍是：普通手机用户不懂 ROS2、云中转、数据库、备份或灾备，也能用手机发起、观察和处理一次 trash delivery。4G 产品路径必须保证云端恢复能力没有被软件 proof 误包装成生产能力。

本轮用户价值是把 production recovery 风险从“文档里的剩余缺口”推进为可执行 gate：当生产备份/灾备、生产 DB/queue、多实例一致性、真实云/4G 尚未证明时，preflight 和手机诊断必须能明确阻断并解释，而不是显示绿色 ready。

## OKR 映射

- O6 / KR1：继续保护 `trashbot.remote.v1` command/status/ack 契约，新增 recovery metadata 不改变既有 envelope。
- O6 / KR2：把 production backup/disaster recovery 从剩余缺口推进为 Docker/local artifact + preflight/status/diagnostics gate。
- O6 / KR5：继续保持凭证、DB/queue URL、local path、ROS/hardware 细节不进入 phone-safe 输出。
- O6 / KR6：让恢复、备份、灾备、状态丢失风险可以被 preflight 和 phone diagnostics 解释；真实生产能力未满足时必须 blocked。
- O5：本轮只给手机首屏/诊断提供 O6 recovery 摘要素材，不构成正式手机 app、真实设备验收或真实用户验收。
- O1/O2/O3/O4：没有真实硬件、导航、相机或 HIL 证据，不提升。

## KR 拆解或更新

- KR6.1：新增 `trashbot.production_recovery_gate` artifact，字段至少包含 schema、schema_version、robot_id、generated_at、evidence_boundary、local_backup_restore_status、recovery_drill_status、production_backup_policy_status、disaster_recovery_status、state_backend_status、db_queue_status、multi_instance_status、retention_status、restore_objective_status、production_ready、overall_status、not_proven、safe_summary、retry_hint、checksum。
- KR6.2：artifact 必须区分 Docker/local recovery proof 与真实 production backup/disaster recovery；有效 artifact 仍必须 `production_ready=false`、`overall_status=blocked`。
- KR6.3：preflight 能通过 `TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT` 或 CLI 参数消费 artifact；有效 artifact 只证明上线前置 recovery gate 可执行，不证明真实生产灾备。
- KR6.4：operator status/diagnostics 输出 `production_recovery` phone-safe summary，状态至少覆盖 `ready|missing|invalid|stale|failed|blocked`。
- KR6.5：remote bridge compatibility fence 证明新 metadata 不触发 robot action、不 ACK、不推进或持久化 cursor、不把 ACK 当 delivery success。

## 本轮核心抓手

用最小可执行 artifact gate 对齐三个产品问题：

1. 恢复能力是否可验证：Docker/local 能生成和校验 production recovery gate artifact。
2. 产品语义是否保守：`production_ready=false`、`overall_status=blocked` 必须保持，不能把本地 backup/restore proof 等同真实生产灾备。
3. 上线阻断是否可解释：preflight、phone readiness 和 diagnostics 能告诉用户或支持同学“production recovery gate 已生成/缺失/损坏/过期/失败/阻断”，但不泄露内部实现、凭证或路径。

## 需要做什么

### Task A / full-stack-software-engineer

主实现 `trashbot.production_recovery_gate`：

- 在 `remote_cloud_relay.py` 新增 Docker/local production recovery artifact writer、validator、CLI 参数、preflight 消费和 safe summary builder。
- 在 `operator_gateway_http.py` 与 `operator_gateway_diagnostics.py` 接入 phone-safe summary。
- 更新 targeted tests，覆盖 artifact pass、missing、invalid、stale、failed、blocked、preflight consumption、status/diagnostics summary 和敏感字段过滤。
- 同步 `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md`。

### Task B / robot-software-engineer

兼容性围栏：

- 在 `test_remote_bridge.py` 增加 metadata-only production recovery payload 场景。
- 验证新 metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
- 验证 metadata-only blocked response 不触发 robot action、不发送 ACK、不推进或持久化 cursor。
- 只有发现生产 `remote_bridge.py` 必须改才能保持兼容时才允许改它，并同步 `docs/interfaces/ros_contracts.md` 说明风险和兼容边界。

### Task C / product-okr-owner

实现与验证完成后 closeout：

- 更新 `OKR.md`，只做保守 O6 进度更新，并保持真实生产灾备、真实云/4G、真实 OSS/CDN、真实 HIL 未完成边界。
- 更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 核对 docs/product 与 docs/interfaces 路径存在且口径不滞后。

## 优先级和验收口径

- P0：artifact/preflight/phone-safe summary 完整，且 `production_ready=false`、`overall_status=blocked` 保持。
- P0：明确区分 Docker/local backup/restore 或 recovery proof 与真实 production backup/disaster recovery。
- P0：ACK 文案和 schema 明确 ACK 不等于 delivery success，也不等于 production recovery 完成。
- P0：robot compatibility fence 通过，不触发 action/ACK/cursor。
- P1：文档同步覆盖 O6 proof ladder、not_proven、phone-safe 输出字段。
- P2：只做围栏验证，不扩展 broad regression、不引入真实云/4G/HIL 假设。

验收通过的最低证据：

- Task A targeted tests 通过。
- Task A `py_compile` 通过。
- Task A artifact CLI smoke 生成 artifact。
- Task A preflight smoke 输出 `software_proof_ready=True`、`production_ready=False`、`overall_status=blocked`、`production_recovery=pass` 或等价 recovery check。
- Task B targeted tests 通过。
- Task B `py_compile` 通过。
- scoped `git diff --check` 通过。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A 主实现和产品文档同步。
- `robot-software-engineer`：Task B remote bridge compatibility fence 和接口文档同步。
- `product-okr-owner`：Task C closeout、OKR 进度、sprint 文档收口。

## 风险、阻塞和证据链

- 真实生产 DB/queue、备份策略、灾备恢复、多实例一致性仍缺外部环境和生产组件，本轮只做 Docker/local gate。
- 如果 artifact 没有 `not_proven` 或没有 blocked production 状态，则不满足本轮产品目标。
- 如果 phone-safe summary 暴露完整 artifact、checksum、local path、DB/queue URL、token、Authorization、ROS topic、`/cmd_vel`、serial、baudrate 或 WAVE ROVER 参数，必须阻断。
- 如果实现只复用旧 backup/restore drill 而没有把 production recovery 缺口结构化为 gate，也不满足本轮目标。

## 需要创建或更新的 sprint 文档

当前规划阶段只创建：

- `sprints/2026.05.12_25-26_remote-production-recovery-gate/pre_start.md`
- `sprints/2026.05.12_25-26_remote-production-recovery-gate/prd.md`
- `sprints/2026.05.12_25-26_remote-production-recovery-gate/tech-plan.md`

实现完成后再更新 closeout docs，不提前预生成。

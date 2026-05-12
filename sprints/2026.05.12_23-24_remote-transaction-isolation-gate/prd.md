# Sprint 2026.05.12_23-24 Remote Transaction Isolation Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 目标证据：`software_proof_docker_transaction_isolation_gate`

## 用户价值和产品北极星

北极星仍是：普通手机用户不懂 ROS2、云队列或硬件调试，也能发起和理解一次 trash delivery。4G 产品路径必须保证手机命令、robot 状态和 ACK 在云中转中不会产生危险误导。

本轮用户价值不是新增按钮，而是降低未来远程发车的系统性风险：并发写入时，手机和云端不能因为 ACK 到达顺序或 cursor 错误而认为一个未完成命令已经被越过，更不能把 ACK 解读为送达成功。

## OKR 映射

- O6 / KR1：继续保护 `trashbot.remote.v1` command/status/ack 契约，新增 metadata 不改变既有 envelope。
- O6 / KR2：把 `transaction isolation` 从纯缺口推进为 Docker/local 可执行 gate，作为生产 DB/queue 前置阻断证据。
- O6 / KR5：继续保持凭证、DB/queue URL、ROS/hardware 细节不进入 phone-safe 输出。
- O6 / KR6：让 transaction isolation 风险可以被 preflight、phone readiness 和 diagnostics 解释，而不是上线后才暴露。
- O5：本轮只给手机首屏/诊断提供 O6 摘要素材，不构成正式手机 app 或真实设备验收。
- O1/O2/O3/O4：没有真实硬件、导航、相机或 HIL 证据，不提升。

## KR 拆解或更新

- KR6.1：新增 `trashbot.transaction_isolation_drill` artifact，字段包含 schema、schema_version、robot_id、updated_at、evidence_boundary、transaction_invariant、cursor_invariant、ack_invariant、concurrent_write_scenario、production_ready、overall_status、not_proven、safe_summary、retry_hint、checksum。
- KR6.2：artifact 必须覆盖同一 robot 的并发 command/status/ack 写入，特别是“中间命令未 terminal ACK，后续命令先 ACK”的场景。
- KR6.3：preflight 能通过 `TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT` 或 CLI 参数消费 artifact；有效 artifact 只让 `transaction_isolation=pass`，仍保持 `production_ready=false`。
- KR6.4：operator status/diagnostics 输出 `transaction_isolation` phone-safe summary，状态至少覆盖 `ready|missing|invalid|stale|failed`。
- KR6.5：remote bridge compatibility fence 证明新 metadata 不触发 robot action、不 ACK、不推进或持久化 cursor、不把 ACK 当 delivery success。

## 本轮核心抓手

用最小可执行 artifact gate 对齐三个产品问题：

1. 并发写入时 cursor 是否保守：后续 ACK 不能越过前序未完成命令。
2. 用户语义是否保守：ACK 仍只是 accepted/processing/failure envelope 证据，不是 delivery success。
3. 上线阻断是否可解释：preflight 和 phone-safe summary 能告诉用户或支持同学“本地 transaction isolation gate 通过/缺失/损坏/过期/失败”，但不泄露内部实现或凭证。

## 需要做什么

### Task A / full-stack-software-engineer

主实现 `trashbot.transaction_isolation_drill`：

- 在 `remote_cloud_relay.py` 新增 Docker/local transaction isolation drill artifact writer、validator、CLI 参数、preflight 消费和 safe summary builder。
- 在 `operator_gateway_http.py` 与 `operator_gateway_diagnostics.py` 接入 phone-safe summary。
- 更新 full-stack/operator tests，覆盖 artifact pass、missing、invalid、stale、failed、preflight consumption、status/diagnostics summary 和敏感字段过滤。
- 同步 `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md`。

### Task B / robot-software-engineer

兼容性围栏：

- 在 `test_remote_bridge.py` 增加 metadata-only transaction isolation payload 场景。
- 必须验证新 metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
- 必须验证 blocked/metadata-only response 不触发 robot action、不发送 ACK、不推进或持久化 cursor。
- 必要时只在 `remote_bridge.py` 做兼容修复，并同步 `docs/interfaces/ros_contracts.md`。

### Product closeout

实现与验证完成后再由 Product 更新：

- `OKR.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-done.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/side2side_check.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/final.md`

本次规划阶段不提前创建 closeout docs。

## 优先级和验收口径

- P0：artifact/preflight/phone-safe summary 完整，且 `production_ready=false` 保持。
- P0：cursor invariant 覆盖未完成命令缺口，不允许后续 ACK 推进 cursor 越过缺口。
- P0：ACK 文案和 schema 明确 ACK 不等于 delivery success。
- P0：robot compatibility fence 通过，不触发 action/ACK/cursor。
- P1：文档同步覆盖 O6 边界、not_proven、phone-safe 输出字段。
- P2：只做围栏验证，不扩展 broad regression、不引入真实云/4G/HIL 假设。

验收通过的最低证据：

- Task A targeted tests 通过。
- Task A `py_compile` 通过。
- Task A CLI smoke 输出 `software_proof_ready=True`、`production_ready=False`、`transaction_isolation=pass`。
- Task B targeted tests 通过。
- Task B `py_compile` 通过。
- scoped `git diff --check` 通过。

## 风险、阻塞和证据链

- 真实生产 DB/queue、transaction isolation、多实例一致性仍缺外部环境和生产组件，本轮只做 Docker/local gate。
- 如果没有明确构造并发 command/status/ack interleaving，artifact 只能算普通 queue check，不满足本轮目标。
- 如果 summary 暴露完整 artifact、checksum、local path、DB/queue URL、token、Authorization、ROS topic、`/cmd_vel`、serial、baudrate 或 WAVE ROVER 参数，必须阻断。
- 如果实现让 ACK cursor 依据字符串顺序或后到 ACK 直接推进，必须阻断。

## 需要创建或更新的 sprint 文档

当前规划阶段只创建：

- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/pre_start.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/prd.md`
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-plan.md`

实现完成后再更新 closeout docs，不提前预生成。

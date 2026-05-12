# Sprint 2026.05.12_21-22 Remote Queue Ordering Drill - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 目标 evidence boundary：`software_proof_docker_queue_ordering_drill`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`

## 用户价值和产品北极星

普通用户最终只应该看到“任务是否能发车、是否在处理、失败时该怎么做”，不应该理解队列、cursor、ACK 或生产数据库。但如果云中转队列在并发或顺序上出错，手机可能显示错误的下一步，小车可能跳过命令，或者把 ACK 误读成送达成功。

本轮 PRD 的用户价值是：在没有真实云和真实生产队列前，先把 queue ordering + concurrency 的最小风险变成可执行、可复查、phone-safe 的 Docker/local 演练，确保后续接入生产 DB/queue 时有明确验收基线。

## OKR 映射

- O6 / KR1：命令、状态、ACK 仍按 `trashbot.remote.v1` envelope 交互；新增 ordering metadata 不改变 command/status/ack shape。
- O6 / KR2：云中转服务端基线补充 queue ordering drill 的上线前置证据。
- O6 / KR5：artifact、preflight、status、diagnostics 不泄露凭证、数据库、队列或硬件敏感信息。
- O6 / KR6：并发、顺序、stale/invalid/missing artifact 能被 phone-safe 降级解释。

## KR 拆解或更新

- KR6.1：新增 `trashbot.queue_ordering_drill` artifact，记录 schema/version、并发提交样例、ordering invariant、cursor invariant、ACK semantics、not_proven、checksum 和 evidence boundary。
- KR6.2：preflight 能消费该 artifact；missing 是 warning，invalid/stale/failed 是 blocked，passed 只让 `software_proof_ready=true`，不得让 `production_ready=true`。
- KR6.3：operator `/api/status` 和 `/api/diagnostics` 输出 phone-safe queue ordering 摘要，覆盖 `ready|missing|invalid|stale|failed`。
- KR6.4：remote bridge 兼容性围栏证明新增 metadata 不改变 command/status/ack envelope、不触发本地 action、不推进 cursor、不把 ACK 当 delivery success。

## 本轮核心抓手

围绕 queue ordering + concurrency drill 做最小闭环：

1. 在 independent relay 的 Docker/local 语义下生成可校验 artifact。
2. 将 artifact 接入 preflight、operator status 和 diagnostics。
3. 用 targeted tests 固化并发提交、`cmd-9` / `cmd-10` 顺序、ACK/cursor 保守语义。
4. 用 robot compatibility fence 保持 `remote_bridge` 与 `trashbot.remote.v1` 契约稳定。

## 范围内

- Remote relay 本地 artifact/CLI/preflight/status/diagnostics。
- Operator gateway phone-safe 摘要消费。
- `.env.example` 新增占位环境变量，不提交真实密钥或真实连接串。
- `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md` 同步边界。
- `test_remote_cloud_relay.py`、operator gateway 相关 tests、`test_remote_bridge.py` 兼容性围栏。

## 范围外

- 真实生产 DB/queue、真实多实例、真实 transaction isolation、真实备份/灾备。
- 真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM。
- 真实 OSS upload、STS issuance、CDN origin fetch。
- 正式手机 app、真实手机设备验收。
- Nav2/fixed-route、WAVE ROVER、串口、HIL 或真实送达。

## 优先级和验收口径

- P0：artifact schema/checksum/evidence boundary 正确，顺序和并发 invariant 可被 targeted tests 复现。
- P0：preflight/status/diagnostics 的 phone-safe 摘要不泄露敏感字段，且 `production_ready=false`。
- P0：remote bridge envelope/cursor/ACK 兼容性围栏通过。
- P1：文档同步说明 queue ordering drill 与真实生产队列的差异。
- P2：如有实现成本，优先保持现有 relay store 抽象，避免引入真实队列依赖。

验收通过只代表 `software_proof_docker_queue_ordering_drill`。Product closeout 不得把本轮写成真实云、真实 4G、生产 DB/queue、多实例一致性或 HIL 证据。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，负责 artifact、preflight、operator status/diagnostics、docs/tests 和 `tech-done.md`。
- `robot-software-engineer`：Task B，负责 remote bridge compatibility fence 和必要的 protocol tests。
- `product-okr-owner`：工程完成后负责验收对照、`side2side_check.md`、`final.md`、`OKR.md` 保守更新。

## 风险、阻塞和需要补齐的证据链

- 当前没有真实生产 DB/queue，因此无法证明跨进程锁、事务隔离、消息可见性、多实例一致性或灾备。
- 当前没有真实云/4G，因此无法证明公网延迟、运营商 NAT、TLS 终止、云服务稳定性或 incident recovery。
- 当前没有真实机器人运行，因此 ACK 仍只能是 command accepted/processing evidence。
- 下一阶段若要提升 O6，需要在真实生产队列、真实云公网入口、真实 4G/SIM、真实 OSS/CDN 或生产运维任一链路取得外部证据。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 已创建：`prd.md`
- 本轮创建：`tech-plan.md`
- 工程完成后更新：`tech-done.md`
- Product closeout 更新：`side2side_check.md`、`final.md`、`OKR.md`

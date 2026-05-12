# Sprint 2026.05.12_21-22 Remote Queue Ordering Drill - Side2Side Check

## 状态

- 阶段：side2side_check
- Product Owner：`product-okr-owner`
- Evidence boundary：`software_proof_docker_queue_ordering_drill`
- 验收结论：通过 Product 对照验收，可进入 final closeout。

## 用户价值和产品北极星

本轮继续服务北极星：普通用户只用手机，通过 4G 云中转控制小车，并在异常时看到可解释、可恢复的状态。queue ordering 本身不应暴露给普通用户，但如果云中转队列顺序、cursor 或 ACK 语义出错，用户可能看到错误任务状态，小车也可能跳过命令。

本轮已把 queue ordering/concurrency 风险做成 Docker/local 可执行证据，并通过 phone-safe status/diagnostics 暴露给支持与验收流程；但它仍不是生产队列或真实云证据。

## OKR 映射和 KR 对照

- O6 / KR1：`trashbot.remote.v1` command/status/ack envelope 未被 queue ordering metadata 污染。
- O6 / KR2：新增 queue ordering drill artifact/preflight/status/diagnostics，为云中转上线前置检查补齐顺序风险口径。
- O6 / KR5：`.env.example` 只新增占位变量；status/diagnostics 不暴露 token、DB URL、queue URL、artifact path、checksum、robot id、ROS topic、串口或硬件参数。
- O6 / KR6：missing/invalid/stale/failed/ready 均能以 phone-safe 摘要表达，且 preflight 继续保持 `production_ready=false`。
- O5：只消费 phone-safe 摘要素材，不提升真实手机或正式 app 进度。
- O1/O2/O3/O4：无硬件、Nav2/fixed-route、相机、WAVE ROVER、HIL 或真实送达证据，不提升。

## PRD / Tech Plan 对照

| 验收项 | 证据 | Product 判断 |
| --- | --- | --- |
| 新增 `trashbot.queue_ordering_drill` artifact | Task A tech-done 记录 artifact schema/version、boundary、not_proven、safe_summary、retry_hint、updated_at、checksum | 通过 |
| 覆盖并发提交与 `cmd-9` / `cmd-10` 顺序风险 | Task A targeted tests `Ran 117 tests in 26.630s OK`，CLI smoke 输出 `queue_ordering_drill=pass` | 通过，仅限 Docker/local invariant |
| preflight/status/diagnostics phone-safe 消费 | Task A 新增 preflight `queue_ordering_drill`、`/api/status.phone_readiness.queue_ordering_drill`、`/api/diagnostics.queue_ordering_drill` | 通过 |
| `production_ready=false` 保持 | CLI smoke 输出 `software_proof_ready=True production_ready=False boundary=software_proof_docker_queue_ordering_drill` | 通过 |
| remote bridge envelope/cursor/ACK 兼容性围栏 | Task B targeted tests `Ran 46 tests in 23.041s OK` | 通过 |
| metadata-only blocked/invalid/stale 不触发 robot action | Task B tech-done 记录不触发 action、不 ACK、不推进/持久化 cursor | 通过 |
| ACK 不等于 delivery success | Task A/B 均保留 command accepted/processing evidence 口径 | 通过 |

## 实际证据

- Task A Full-stack validation：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ...` -> `Ran 117 tests in 26.630s OK`
  - `py_compile` -> 通过，无输出
  - scoped `git diff --check` -> 通过，无输出
  - CLI smoke -> `software_proof_ready=True production_ready=False boundary=software_proof_docker_queue_ordering_drill queue_ordering_drill=pass`
- Task B Robot validation：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ...` -> `Ran 46 tests in 23.041s OK`
  - `py_compile` -> 通过，无输出
  - scoped `git diff --check` -> 通过，无输出

## 风险、阻塞和需要补齐的证据链

- 仍没有真实生产 queue ordering、production DB/queue、多实例一致性或 transaction isolation。
- 仍没有真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、真实 OSS/CDN 流量、生产账号或正式运维证据。
- 仍没有正式手机 app、真实手机设备 Safari/Chrome 验收或普通用户真实远程流程。
- 仍没有 Nav2/fixed-route、WAVE ROVER、HIL、真实串口反馈或真实送达。
- 本轮只能支持 O6 保守小幅提升；不得提升 O1/O2/O3/O4/O5。

## 需要创建或更新的 sprint 文档

- 已完成：`pre_start.md`
- 已完成：`prd.md`
- 已完成：`tech-plan.md`
- 已完成：`tech-done.md`
- 本文件已创建：`side2side_check.md`
- 已创建：`final.md`
- Product closeout 更新：`OKR.md`

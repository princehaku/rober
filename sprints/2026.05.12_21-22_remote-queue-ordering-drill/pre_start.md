# Sprint 2026.05.12_21-22 Remote Queue Ordering Drill - Pre Start

## 状态

- 阶段：pre_start
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 目标 evidence boundary：`software_proof_docker_queue_ordering_drill`
- 环境边界：当前本机只有 Docker/local 软件验证条件，无真实硬件、无真实云、无真实 4G/SIM、无生产 DB/queue、无 HIL。

## 用户价值和产品北极星

北极星仍是：普通用户只用手机，通过 4G 云中转让小车完成送垃圾任务，并在异常时获得清晰、可恢复、可解释的状态。

上一轮 O6 production store/queue gate 已经能说明“生产 DB/queue 未就绪”，但还没有把 queue ordering、并发提交、cursor/ACK 保守语义和多实例前的顺序风险做成可执行演练。本轮价值是把“队列顺序不能乱、ACK 不能被误读成送达成功、并发下不能跳过命令”变成 Docker/local 可复现证据，为后续真实生产队列选型和多实例部署留出验收口径。

## OKR 映射

- Objective 6：当前约 47%，是本机 Docker-only 条件下最低且可行动的主线。
- KR1：继续保护 `trashbot.remote.v1` commands/status/ack 契约，不暴露 `/cmd_vel` 或 inbound robot 入口。
- KR2：补强云端控制面队列边界，明确 local drill 与生产 DB/queue 的差异。
- KR5：继续保持 `.env.example` 占位、phone-safe redaction 和敏感字段不入库/不出 API。
- KR6：让 queue ordering/concurrency 缺口以 phone-safe status/diagnostics 呈现，支持 graceful degradation。
- O5：上一轮已完成 phone task-flow readiness，本轮只消费 phone-safe 摘要，不提升手机真实设备验收。
- O1/O2/O3/O4：本轮无真实硬件、Nav2/fixed-route、相机或 HIL 证据，不提升。

## 上轮输入

- `sprints/2026.05.12_19-20_remote-production-store-queue-gate/final.md` 已完成 O6 production store/queue gate；剩余真实生产 DB/queue、多实例一致性、queue ordering、transaction isolation、备份/灾备。
- `sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/final.md` 已完成 O5 phone task-flow readiness；O6 未提升。
- `OKR.md` live snapshot 显示 O6 约 47%、O5 约 48%、O1/O2/O3/O4 约 74-76%，因此本轮优先 O6。

## 本轮核心抓手

在 Docker/local relay 和 operator surfaces 上新增 queue ordering + concurrency drill：

- 证明并发提交和相邻 command id 不依赖字符串排序。
- 证明 next command selection 使用提交顺序或显式 cursor 语义，不跳过 `cmd-9` / `cmd-10` 等顺序风险。
- 证明 ACK 仍只是 command accepted/processing evidence，不是 delivery success。
- 证明 metadata-only blocked/diagnostics response 不触发 robot action、不推进或持久化 cursor。
- 输出 phone-safe artifact/preflight/status/diagnostics 摘要，继续保持 `production_ready=false` 和 `overall_status=blocked`。

## Owner 和任务

- Task A：`full-stack-software-engineer`，负责 remote cloud relay artifact/preflight/status/diagnostics/docs/tests。
- Task B：`robot-software-engineer`，负责 remote bridge compatibility fence。
- Product closeout：`product-okr-owner`，负责 `side2side_check.md`、`final.md`、`OKR.md`，但只在工程证据返回后更新。

## 风险和证据边界

- 本轮只能产生 `software_proof_docker_queue_ordering_drill`，不得声明真实云、真实 4G、真实生产 DB/queue、生产 transaction isolation、多实例一致性、备份/灾备、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- 若 drill 只验证单进程 file/SQLite store，必须在文档中写明它不是生产队列一致性证明。
- 若新增 metadata 进入 remote status 或 diagnostics，必须确保普通用户看不到 DB URL、queue URL、token、Authorization、OSS secret、raw state path、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。
- 若 robot compatibility fence 发现 envelope 或 cursor 语义回退，必须由 `robot-software-engineer` 修复后再进入 Product closeout。

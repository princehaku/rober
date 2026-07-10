# 预启动：O5 SQLite shadow same-task gate

- sprint_type: epic
- 时间：2026-07-10 05:10 CST
- 目标 Objective：O5 云中转控制面产品化（当前约 83%）
- 主责 owner：Robot Software Engineer
- 产品收口 owner：Product Manager / OKR Owner

## 上轮未完成项与阻塞

上一轮 `2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke` 已证明本地/mock O5 reconciliation terminal material 可以进入 Algorithm manifest、O6 archive/readback 和 `same_task_mission_evidence_gate`。但其 proof boundary 明确仍是 `software_proof_o5_reconciliation_same_task_archive_smoke_only`，不证明真实 production cloud、真实 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation 或真实 delivery success。

本轮不能继续把同一 in-process/file local smoke 当作 OKR 主进展。可推进切口是把同一 `task_id` 的 command/result/reconciliation 链路迁到 SQLite state backend，并验证 relay restart 后仍能 readback terminal result 和 same-task gate。该结果仍不是 production DB/queue，但比上一轮更接近 O5 的 production-like endpoint / DB / queue 缺口。

## 本轮目标

在不需要真实云凭证和真实硬件的当前环境中，新增一个可复跑的 SQLite shadow smoke：

1. 使用 bearer-gated HTTP relay 和 `state_backend=sqlite`。
2. 写入 phone command、robot status、ACK、robot-facing terminal result。
3. 关闭并重启 relay，使用同一 SQLite state 读取 `trashbot.cloud_command_result_reconciliation.v2`。
4. 将 readback reconciliation 输入 Algorithm manifest。
5. 写入 O6 field evidence archive，并读取 `include=same_task_mission_evidence_gate`。
6. 输出明确的 false safety fields 与 proof boundary。

## 重复 blocker 判断

最近两轮均没有 blocked，但都强调下一步必须消费 production-like 或准现场 same-task material。本轮不是继续新增 wrapper/decoder，而是验证同一任务的 O5 command/result 主路径跨 SQLite store 和 relay restart 保持可恢复。这仍会保守标为 software shadow proof，不宣称真实生产云。

## 风险与边界

- 无真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic。
- 无真实 live Nav2 route execution、robot motion、delivery record、operator confirmation、真实手机/browser 验收。
- SQLite 只证明单实例本地 shadow store 和 restart/readback，不证明生产多实例 DB/queue、一致性、备份恢复或 cutover。

# Sprint 2026.05.16_16-17 Route Task Terminal Completion Rehearsal - PRD

sprint_type: epic

## 1. 用户价值

现场执行 route/elevator 复测时，终态材料最容易断链：路线状态、任务记录、dropoff/cancel 终态、失败恢复原因和手机可见摘要可能不在同一个 `evidence_ref` 下。普通用户或现场支持人员看不到“这次任务到底停在哪一步、缺什么材料、下一步该补什么”。

本轮产品目标是把“终态复账”做成可重复的软件链路：即使本机没有硬件，也能用 Docker/local proof 验证字段、摘要和 fail-closed 口径，为下一次真实现场材料回填打底。

## 2. OKR 映射

- Objective 2：补强可送垃圾任务 + 电梯 assisted delivery 的终态复账链路，尤其是 dropoff/cancel、失败恢复、人工介入和同一 `evidence_ref`。
- Objective 3：补强固定路线和 route/task replay 的可验证材料链，确保 route status、task record、completion signal 和 terminal rehearsal summary 可以交叉核对。
- Objective 4：手机端只读展示终态复账，帮助普通用户和支持人员理解当前状态，但不改变 Start / Confirm Dropoff / Cancel gating。
- Objective 5：本轮不推进。没有真实外部云/4G/OSS/CDN/DB/queue 材料，不提升 O5。
- Objective 1：本轮不推进。没有真实 WAVE ROVER/UART/HIL，不提升 O1。

## 3. 核心抓手

新增 `route_task_terminal_completion_rehearsal` 软件证明链：

1. Robot task record 产生或归一化终态复账摘要。
2. PC evidence gate 读取 route status、task record、existing completion signal，输出 terminal completion rehearsal artifact / summary。
3. Robot diagnostics metadata-only 消费该 summary，并保持 fail closed。
4. Mobile/web 首屏新增只读“任务终态复账” panel，展示终态、dropoff/cancel material status、failure/recovery reason、same `evidence_ref` 和 safe copy。

## 4. 验收口径

必须满足：

- 所有新增 summary 使用 `software_proof_docker_route_task_terminal_completion_rehearsal_gate`。
- 所有链路保留 `delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。
- 缺 route/task/completion source、unsupported schema、evidence_ref mismatch、unsafe success/control wording 必须 fail closed。
- Mobile copy/export whitelist-only，不展示 raw JSON、ROS topic、串口、凭证、完整本机路径、checksum、完整 artifact 或成功送达文案。
- Start / Confirm Dropoff / Cancel gating 不改变。
- 验证只跑 focused unittest、`py_compile`、`node --check`、required `rg` 和 scoped `git diff --check`。

## 5. 不做事项

- 不跑全量 Docker/Humble build。
- 不声明真实 dropoff completion、真实 cancel completion 或 delivery success。
- 不声明真实手机、真实 PWA prompt/user choice、production app、真实 route/elevator field pass、HIL 或 O5 external proof。
- 不继续堆硬件 procurement receipt 的下一层包装，除非有真实材料输入。

## 6. 成功标准

本轮成功标准是一个可被下一次现场 session 使用的 terminal completion rehearsal contract：现场人员能按同一 `evidence_ref` 回填 route/task/dropoff/cancel 材料，Robot diagnostics 和手机端能一致地显示“哪些已成形、哪些仍缺、为什么不能宣称完成”。

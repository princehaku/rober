# Sprint 2026.05.19_11-12 Task Terminal Completion Mainline - Pre Start

## sprint_type: epic

Run time: 2026-05-19 11:00 Asia/Shanghai。

## 1. 启动原因

CEO 本轮明确要求：基于 live `OKR.md` 和近期 PR/评审证据，避免继续堆 O5/O1/PR #4 同类 metadata wrapper，转为推进 Docker 可验证的真实功能链路 `task_terminal_completion_mainline`。

live `OKR.md` 4.1 显示 Objective 5 约 68% 是最低项，但当前 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser proof。本轮不继续 O5 local metadata depth，不提高 Objective 5。

Objective 1 约 81% 是下一低项，但最新 sprint `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/final.md` 刚完成 O1 硬件真实材料升级请求，并明确 Docker/local `software_proof` 不能冒充真实 WAVE ROVER/UART/HIL、2D LiDAR / ToF 或 PR #5 真实材料。PR #5 只把部分 docs review thread 判定为可关闭，mandatory sensor real materials 仍是 `blocked_pending_real_materials`。本轮不继续堆 O1 metadata wrapper。

PR #4 route/elevator field materials 已被多轮消耗并触发重复 blocker 红线。继续做 route/elevator 材料 wrapper 不能越过真实现场材料缺口。本轮只取 PR #4 中仍可 Docker 推进的主链路缺口：dropoff / cancel terminal action 当前仍容易停在只读材料、回执或 review handoff，尚未形成 Robot task_record、diagnostics、mobile web 一致可观察、可复盘、fail-closed 的主链路契约。

## 2. 用户价值和产品北极星

用户价值：现场 owner 下一次带真实 dropoff / cancel 材料回来时，不再需要人工猜测 terminal action 应该写进哪个 task record 字段、diagnostics 如何显示、手机端如何解释给普通用户。本轮要先把主路径的软件契约铺好，让同一 `evidence_ref` 下的 terminal action 状态、用户确认语义、安全边界和复盘字段保持一致。

产品北极星保持不变：普通手机用户最终能用低成本 ROS2 自主送垃圾机器人完成“放入垃圾 -> 发车 -> 到站 -> 投放/取消/恢复 -> 复盘”的闭环。本轮不是证明真实投放或取消完成，而是把 terminal action 从旁路材料推进到主链路可观察契约。

## 3. OKR 映射

- Objective 5：约 68%，数字最低。本轮不针对 O5 completion，因为没有真实 external proof；不声明公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser 通过。
- Objective 1：约 81%，仍缺真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 真实材料。上一轮已完成材料升级请求，本轮不继续 O1 metadata wrapper。
- Objective 2：约 99%，本轮主要映射。推进 dropoff / cancel terminal action 在任务状态机输出、task_record、diagnostics summary 中的一致字段契约，但保持 `not_proven`。
- Objective 3：约 99%，本轮辅助映射。terminal action summary 必须能和 route/fixed-route/task evidence 使用同一 safe `evidence_ref` 复盘，但不证明真实 Nav2/fixed-route。
- Objective 4：约 99%，本轮辅助映射。mobile/web 展示 terminal action mainline 状态，帮助普通手机用户理解“已确认、待材料、未证明、需人工复核”的差异，同时不扩大 Start/Confirm Dropoff/Cancel gating。

## 4. 上轮未完成项和阻塞

- O5 阻塞：仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser proof。
- O1 阻塞：仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report，以及 PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- PR #4 阻塞：真实 route/elevator field materials 仍缺真实门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、真实 task record、completion signal、真实 dropoff completion、真实 cancel completion 和 delivery result。
- 当前可推进点：不再包装材料 blocker，而是让 dropoff / cancel terminal action 在 Robot task_record、diagnostics 和 mobile web 主链路里拥有一致字段、状态语义和 fail-closed 边界。

## 5. 本轮核心抓手

核心抓手：`task_terminal_completion_mainline`。

本轮要把 terminal action 从“只读材料或回执旁路”推进为 Docker 可验证的软件主链路：

1. Robot 主链路：task_record / diagnostics 输出 terminal action summary，覆盖 dropoff、cancel、operator confirmation、same `evidence_ref`、terminal status、failure reason、safe next steps。
2. Full-Stack：mobile/web 展示 terminal action mainline 状态，保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大；没有材料时 fail closed。
3. Product：收口 docs、OKR、progress log 和 sprint closeout，明确本轮只得到 `software_proof`，不提高真实完成度。
4. Autonomy：只读咨询 route/fixed-route evidence 字段，不写文件。
5. Hardware：本轮不写文件，不涉及硬件参数或 vendor detail 改动。

## 6. 责任 Engineer

| Owner | 责任 |
| --- | --- |
| robot-software-engineer | 主责 Robot task_record / diagnostics terminal action summary；保证只读、同一 `evidence_ref`、fail-closed，不触发真实 motion 或 completion claim。 |
| full-stack-software-engineer | 主责 mobile/web 展示 terminal action mainline 状态；保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大。 |
| product-okr-owner | 主责 sprint docs、OKR、progress log 和 closeout；确保边界不被写成真实 dropoff/cancel completion。 |
| autonomy-engineer | 只读咨询 route/fixed-route/task evidence 字段边界，不写文件。 |
| hardware-engineer | 本轮不写文件；不涉及 WAVE ROVER、UART、引脚、电压、传感器或 vendor detail 改动。 |

## 7. 范围边界

本轮允许做 Docker/local `software_proof` 主链路契约，不允许声明或暗示：

- 真实 dropoff completion。
- 真实 cancel completion。
- `delivery_success=true` 或真实送达。
- 真实电梯、真实 Nav2/fixed-route、真实 route/elevator field pass。
- 真实手机/iPhone/Android/production app/browser 通过。
- 真实 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 材料通过。
- Objective 5 external proof 通过。

所有输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 8. 需要创建或更新的 sprint 文档

本轮 Epic sprint 先创建：

- `sprints/2026.05.19_11-12_task-terminal-completion-mainline/pre_start.md`
- `sprints/2026.05.19_11-12_task-terminal-completion-mainline/prd.md`
- `sprints/2026.05.19_11-12_task-terminal-completion-mainline/tech-plan.md`

实现完成后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

实现若改动 Robot 或 mobile/web 行为，必须同步更新对应 `docs/` 文档；Product closeout 必须最终更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但不得上调真实 dropoff/cancel、O1 HIL 或 O5 external proof 完成度。

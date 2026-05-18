# Sprint 2026.05.19_02-03 Elevator Feedback Task Record Trace - Pre Start

## sprint_type: epic

Run time: 2026-05-19 02:03 Asia/Shanghai

## 用户价值和产品北极星

用户价值：field owner 在一次任务结束后，能把手机上看到的电梯阶段、Robot 产出的 task_record、operator diagnostics 和同一 `evidence_ref` 串起来复盘，不再只依赖实时手机状态或口头描述判断“等门、进电梯、请求按楼层、等目标楼层、出电梯、恢复送达”是否真的进入了可回放证据链。

产品北极星：普通手机用户完成低成本 trash delivery；本轮推进的是可解释、可复盘的 assisted delivery 证据闭环，不把本地 trace、fixture、diagnostics 或文档计划写成真实电梯、真实 Nav2/fixed-route、真实手机、HIL 或 delivery success。

## 开工依据

- Live `OKR.md` 4.1 显示 Objective 5 约 68%，是数字最低 Objective；但本机仍是 Docker-only，缺真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和 real phone/browser external proof。本轮不得继续做 O5 本地 wrapper，也不得把本地 trace 当成 O5 external proof。
- Live `OKR.md` 4.1 显示 Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 暴露的 2D LiDAR / ToF vendor-source/material 缺口也未补。本轮不消费同一硬件 blocker。
- `sprints/2026.05.19_00-01_elevator-assist-action-feedback-mainline/final.md` 已完成 Robot action feedback 主链：`TrashCollection.Feedback.current_step=elevator:<phase>` 进入 phone-safe 实时 feedback，边界是 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `sprints/2026.05.19_01-02_mobile-elevator-action-feedback-display/final.md` 已完成 mobile/web 只读展示：手机能展示 `current_step=elevator:<phase>`，但仍缺 post-run task_record、diagnostics 和 same evidence_ref 对齐。
- PR #4 表明 elevator assisted delivery 已进入必达主链，下一步应把实时阶段推进到 post-run trace，而不是另起一个本地云 wrapper。
- PR #5 review 暴露的 hardware baseline/default set、2D LiDAR / ToF vendor-source/material 缺口必须继续独立标注；本轮 software proof 不覆盖该硬件材料缺口。

## 本轮核心抓手

把实时 action feedback 的 `current_step=elevator:<phase>` 转成 post-run 可复盘 trace contract：同一 `evidence_ref` 下，Robot task_record 必须能记录电梯阶段序列，operator diagnostics 必须能安全摘要该 trace，mobile/web 必须能只读展示“上一轮电梯阶段复盘”并明确 `software_proof` / `not_proven` 边界。

本轮目标不是实机复跑，而是让后续 field owner 一旦拿到真实现场材料，就能按同一 `evidence_ref` 对齐：

- 手机实时阶段：`current_step=elevator:<phase>`
- post-run task_record：阶段时间线、终态、错误/人工接管原因
- diagnostics：安全摘要、缺失项、下一步证据
- mobile trace：用户可读复盘卡片，不启用 Start Delivery、Confirm Dropoff、Cancel

## Sprint 归属和 owner

本轮是跨 owner Epic sprint，预计需要 Robot 和 Full-Stack 并行执行，Product 负责验收边界和 OKR 收口。

| Owner | 责任 | 范围边界 |
| --- | --- | --- |
| product-okr-owner | 本规划文档、OKR 映射、验收口径和风险边界 | 只创建 `pre_start.md`、`prd.md`、`tech-plan.md`；不预生成 `tech-done.md` / `side2side_check.md` / `final.md` |
| robot-software-engineer | task_record trace contract、diagnostics safe summary、最小验证 | 只做 metadata-only / software-proof trace，不声明真实 field pass |
| full-stack-software-engineer | mobile/web post-run trace 只读展示、fixture、前端验证 | 不改变 primary action gating，不把 trace 作为 command 或 delivery result |
| hardware-engineer | 只读确认 PR #5 硬件材料缺口保持独立 | 不在本轮改硬件配置，不用 software proof 覆盖 2D LiDAR / ToF 材料 |

## Blocker 扫描

- O5 external proof blocker：真实 HTTPS/TLS、4G/SIM、OSS/CDN、DB/queue、worker/cutover、real phone/browser external proof 均缺失，且过去多轮已证明本地 wrapper 不能推进 O5 完成度；本轮切到 Objective 2 / Objective 4 可行动缺口。
- O1 hardware blocker：真实 WAVE ROVER/UART/HIL 与 PR #5 2D LiDAR / ToF 材料缺失；本机无真实硬件，不继续消费同一 blocker。
- PR #4 field material blocker：真实电梯门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、真实 task_record/completion signal、dropoff/cancel completion 和 delivery result 仍缺失。本轮只补“将来怎么对齐”的 software proof trace。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 本阶段不得创建：`tech-done.md`、`side2side_check.md`、`final.md`。
- 实现完成后由对应 worker 更新 `tech-done.md`；Product 验收后再进入 `side2side_check.md` 和 `final.md`。

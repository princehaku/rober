# Sprint 2026.05.20_05-06 PR5 Review Reply Publication Closeout - PRD

## 1. 背景

PR #5 的硬件 source/material review 已进入一个很窄的可执行缺口：`PRRT_kwDOSWB9286CJ3tQ` 和 `PRRT_kwDOSWB9286CJ3tU` 已 resolved，`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，reviewer 要求为新增 mandatory sensor assumptions 引用 vendor sources。

上一轮 `pr5_vendor_source_review_reply_dispatch` 已生成可人工发布的 Markdown reply，状态为 `ready_for_manual_github_review_reply_not_proven`。该 reply 已明确引用 `docs/vendor/VENDOR_INDEX.md` 及本地 vendor source refs，同时保留 `hardware_material_pending`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮 PRD 只定义实际发布 GitHub reply 的产品验收口径。它不是第三次包装同一 blocker，也不是把本地 source-boundary reply 写成真实硬件材料。

## 2. 用户价值和产品北极星

用户价值：让 reviewer 和团队在同一条 GitHub review thread 上看到清晰、可追溯、保守的 vendor/source reply，避免 PR #5 因“尚未发布已生成回复”继续阻塞。

产品北极星：持续把机器人送达能力推进成可验证、可复盘、边界可信的产品；凡是硬件、云端或手机真实材料没到位，都必须保持 `not_proven`，不能用流程动作替代真实验收。

## 3. OKR 映射

### Objective 5：云中转 + OSS/CDN 数据通路产品化

- 当前约 68%，数字最低。
- 本轮不推进 Objective 5 completion，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof。
- 本轮 closeout 必须明确：GitHub reply publication 不是 O5 external proof。

### Objective 1：硬件协议可信底盘

- 当前约 81%，是本轮可触达的 review-risk 相关 Objective。
- 本轮只处理 PR #5 `PRRT_kwDOSWB9286CJ3tX` 的 vendor/source reply 发布缺口，帮助 reviewer 理解当前 source boundary 和硬件材料仍缺。
- 本轮不能提高 Objective 1 completion，除非后续额外出现真实 2D LiDAR / ToF 或 WAVE ROVER/UART/HIL 材料；当前计划不包含这些材料。

### Objective 4：手机用户体验与量产边界

- 本轮不改手机端。
- 若后续 closeout 要同步展示发布状态，必须另开任务并保持只读、fail-closed，不启用 Start Delivery / Confirm Dropoff / Cancel。

## 4. KR 拆解或更新

- O1 / PR #5 review KR：把 `PRRT_kwDOSWB9286CJ3tX` 的 `ready_for_manual_github_review_reply_not_proven` 从本地 Markdown artifact 推进到实际 GitHub reply 发布证据。
- O1 material KR：继续要求真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；本轮不满足。
- O1 HIL KR：继续要求真实 WAVE ROVER/UART/HIL、真实 feedback、真实 ROS topic 样本；本轮不满足。
- O5 external KR：继续要求真实公网/4G/OSS/CDN/DB/queue/phone external proof；本轮不满足。

不更新 `OKR.md` 的数值与 KR 文案；本轮先计划发布动作，等实际 GitHub reply 和 closeout 证据完成后再判断文档同步范围。

## 5. 本轮核心抓手

核心抓手是“发布已生成的 review-thread reply，并把发布动作与真实材料证明分开”：

- 输入：`sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply.md`
- 目标 thread：`PRRT_kwDOSWB9286CJ3tX`
- 目标 PR：PR #5
- 发布前必须核验：reply 中仍保留 `software_proof`、`not_proven`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`。
- 发布后必须记录：GitHub reply URL / comment id / thread evidence，且只能说明 “GitHub reply 已发布”。

## 6. 需要做什么

1. Hardware worker 复核上一轮 reply 的 vendor/source 引用仍来自 `docs/vendor/VENDOR_INDEX.md` 和本地 vendor refs，不新增未经核验的硬件假设。
2. GitHub 执行者把上一轮 Markdown reply 发布到 `PRRT_kwDOSWB9286CJ3tX`。
3. Product closeout 核对发布证据并补 `tech-done.md`、`side2side_check.md`、`final.md`。
4. Product closeout 保持边界：发布 reply 不等于 reviewer resolved，不等于真实 2D LiDAR / ToF materials、HIL、route/elevator field pass、O5 external proof 或 delivery success。

## 7. 优先级和验收口径

- P0：GitHub reply 必须发布到正确的 `PRRT_kwDOSWB9286CJ3tX` thread，而不是顶层 PR comment 或错误 thread。
- P0：发布内容必须沿用上一轮 reply 的 conservative wording，不删除 `not_proven` 和 `hardware_material_pending`。
- P0：closeout 必须记录发布证据和证据边界，不更新 `OKR.md` 为完成度提升。
- P1：若 GitHub API 或权限阻塞，closeout 只能写 blocked on GitHub publication，不能写成已发布。
- P1：如果 reviewer 后续 resolved，应单独记录 reviewer action；本轮不能自行把 unresolved 写成 resolved。

验收通过的最小证据：

- Hardware worker 返回 reply 核验结果：source refs、thread id、status boundary 均一致。
- GitHub 执行者返回发布证据：reply URL/comment id/thread evidence。
- Product closeout 文档包含 `GitHub reply`、`PRRT_kwDOSWB9286CJ3tX`、`ready_for_manual_github_review_reply_not_proven`、`software_proof`、`not_proven`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`。

## 8. 对应责任 Engineer

- 主责 Product：`product-okr-owner`，负责本 PRD、验收口径和后续 closeout。
- 核验主责：`hardware-engineer`，负责 vendor/source reply 内容核验。
- 发布执行：主会话或 GitHub 执行者，负责实际 GitHub reply publication。
- 暂不派发：`robot-software-engineer`、`full-stack-software-engineer`、`autonomy-engineer`，除非发布后需要新增 downstream 展示或 field-material handoff。

## 9. 风险、阻塞和需要补齐的证据链

- GitHub 权限/API/线程定位可能阻塞发布；阻塞时不得伪造发布结果。
- 发布到错误位置会让 reviewer 无法关联 `PRRT_kwDOSWB9286CJ3tX`，必须避免。
- Reply 发布后 reviewer 可能仍保持 thread unresolved，因为真实 2D LiDAR / ToF materials 仍缺。
- 本轮没有真实硬件，没有真实手机，没有真实公网/4G/OSS/CDN/DB/queue external proof。
- 需要后续补齐真实材料链：2D LiDAR / ToF SKU/source/receipt、安装接线电源、标定、HIL-entry、Nav2/SLAM field pass、WAVE ROVER/UART/HIL、真实 route/elevator field pass。

## 10. 需要创建或更新的 sprint 文档

Planning-only 阶段：

- 创建 `pre_start.md`
- 创建 `prd.md`
- 创建 `tech-plan.md`

执行/收口阶段：

- GitHub reply 发布后再创建 `tech-done.md`
- 验收对照后再创建 `side2side_check.md`
- closeout 后再创建 `final.md`
- 本轮 planning-only 不修改 `OKR.md`、`docs/process/okr_progress_log.md` 或其他文件。

## 11. Closeout 状态补记

- 2026-05-20 05:11 Asia/Shanghai：PRD 定义的 publication gap 已关闭，GitHub reply 已发布到 `PRRT_kwDOSWB9286CJ3tX`。
- 发布证据：comment id `3269642220`，URL `https://github.com/princehaku/rober/pull/5#discussion_r3269642220`。
- 未关闭事项：`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，所以不提升 Objective 1、Objective 4 或 Objective 5 completion。

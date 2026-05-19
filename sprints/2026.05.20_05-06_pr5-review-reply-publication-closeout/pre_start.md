# Sprint 2026.05.20_05-06 PR5 Review Reply Publication Closeout - Pre Start

## 1. Sprint 类型

- sprint_type: epic
- Sprint 主题：`pr5_review_reply_publication_closeout`
- 启动时间：2026-05-20 05:06 Asia/Shanghai
- 当前阶段：planning only；本文件仅启动计划，不生成 `tech-done.md`、`side2side_check.md`、`final.md`，也不修改 `OKR.md`。

## 2. 用户价值和产品北极星

产品北极星仍是：让普通手机用户可以信任机器人完成低成本、可复盘的垃圾送达，而不是依赖没有来源的硬件假设或本地 metadata 自我证明。

本轮用户价值是关闭一个真实流程缺口：上一轮已经生成可人工发布的 PR #5 review-thread Markdown reply，但 GitHub reply 尚未实际发布。发布 reply 可以让 reviewer 看到 vendor/source boundary 和剩余真实材料缺口，减少 PR #5 在硬件假设来源上的沟通阻塞。

## 3. 开工依据

- `OKR.md` 4.1：Objective 5 约 68%，仍是数字最低 Objective；但缺的是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof，本轮不能继续堆 O5 local metadata。
- Objective 1 约 81%，PR #5 仍关联硬件 source/material 边界；但本轮只能发布已有 reply，不证明真实 WAVE ROVER/UART/HIL，也不证明真实 2D LiDAR / ToF 材料。
- PR #5 live review state：`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，评审要求 “Cite vendor sources for new mandatory sensor assumptions”。
- 上一轮 sprint `2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch` 已生成 `ready_for_manual_github_review_reply_not_proven` Markdown reply / sanitized summary，但明确没有实际发布 GitHub reply。
- 硬件资料入口已复核：`docs/vendor/VENDOR_INDEX.md` 只支持 vendor/source boundary，不支持把 2D LiDAR / ToF 写成真实 procurement、installation、wiring、power、calibration、HIL-entry 或 field pass。

## 4. 本轮核心抓手

本轮抓手是 `GitHub reply publication closeout`：

1. Hardware worker 先复核上一轮生成的 Markdown reply 是否仍与 `docs/vendor/VENDOR_INDEX.md` 和本地 vendor source boundary 一致。
2. 主会话或明确授权的 GitHub 执行者把该 Markdown reply 发布到 PR #5 `PRRT_kwDOSWB9286CJ3tX` review thread。
3. Product closeout 后续只记录“GitHub reply 已发布”的流程缺口关闭，不把它写成 thread resolved、reviewer accepted、真实材料到位、HIL、route/elevator field pass、O5 external proof 或 delivery success。

## 5. Owner 和责任边界

- `product-okr-owner`：本轮计划、验收口径、证据边界和后续 closeout wording；本 planning-only 任务只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。
- `hardware-engineer`：后续核验 reply 引用的 vendor/source boundary，确认 `hardware_material_pending`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 仍成立。
- GitHub 执行者：后续实际发布 GitHub reply，并返回 reply URL、comment id 或 review-thread 证据。该角色只处理 GitHub 操作，不扩展硬件结论。
- `robot-software-engineer`、`full-stack-software-engineer`、`autonomy-engineer`：本轮默认不改代码；如 GitHub 发布结果需要 downstream 展示或 field-material handoff，另开后续任务。

## 6. 风险、阻塞和证据链缺口

- 发布 reply 只关闭“没有发布 reply”的流程缺口；不关闭 `PRRT_kwDOSWB9286CJ3tX` 的真实材料缺口。
- `PRRT_kwDOSWB9286CJ3tX` 是否由 reviewer resolved 取决于 reviewer 后续操作，不能由本轮自动声明。
- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍是 `hardware_material_pending`。
- 真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 样本仍缺。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 和真实手机/browser external proof。

## 7. 本轮需要创建或更新的 sprint 文档

本 planning-only 阶段只允许创建：

- `sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout/pre_start.md`
- `sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout/prd.md`
- `sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout/tech-plan.md`

后续 Hardware worker 核验和 GitHub reply 发布完成后，再由 Product closeout 更新 `tech-done.md`、`side2side_check.md`、`final.md`，并按证据决定是否更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 8. Closeout 状态补记

- 2026-05-20 05:11 Asia/Shanghai：GitHub reply 已发布到 `PRRT_kwDOSWB9286CJ3tX`，comment id `3269642220`，URL `https://github.com/princehaku/rober/pull/5#discussion_r3269642220`。
- Live thread state after publication：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`。
- 当前仍是 `software_proof` / `not_proven` / `hardware_material_pending`；保留 `delivery_success=false`、`primary_actions_enabled=false`，不提高 OKR completion。

# Sprint 2026.05.20_05-06 PR5 Review Reply Publication Closeout - Tech Plan

## 1. 技术方案

本 sprint 主题是 `pr5_review_reply_publication_closeout`。技术上不新增代码能力，核心是把上一轮已生成的 Markdown reply 从本地 artifact 推进到 GitHub review thread，并在 closeout 中保留严格证据边界。

输入 artifact：

- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply_dispatch_summary.json`

目标 GitHub review thread：

- PR #5
- `PRRT_kwDOSWB9286CJ3tX`
- Review requirement: “Cite vendor sources for new mandatory sensor assumptions”

必须保留的证据边界：

- `ready_for_manual_github_review_reply_not_proven`
- `software_proof`
- `not_proven`
- `hardware_material_pending`
- `delivery_success=false`
- `primary_actions_enabled=false`

本计划不访问真实串口、不运行 ROS graph、不修改硬件配置、不发布云资源、不执行 O5 external probe、不证明真实手机/browser。

## 2. Owner / 文件范围

### product-okr-owner

本 planning-only 子任务已完成后，后续 closeout 允许改动：

- `sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout/tech-done.md`
- `sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout/side2side_check.md`
- `sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout/final.md`

本 planning-only 子任务不得修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 任何代码、测试、硬件配置或 mobile/web 文件

### hardware-engineer

后续核验允许只读检查：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply.md`
- `sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply_dispatch_summary.json`

输出要求：

- 说明 source refs 是否仍一致。
- 说明是否存在未引用 vendor source 的新增 mandatory sensor assumption。
- 明确 `2D LiDAR / ToF` 仍为 `hardware_material_pending` / `not_proven`。
- 不改代码、不改硬件配置、不写新的 product docs，除非主会话另行派发。

### GitHub 执行者

允许动作：

- 将上一轮 Markdown reply 原文或经 Hardware worker 确认的保守版本发布到 `PRRT_kwDOSWB9286CJ3tX`。
- 返回 GitHub reply URL、comment id、thread id 或足以证明已发布的证据。

禁止动作：

- 不点击 resolve / mark resolved，除非 reviewer 或 CEO 明确要求。
- 不把 `PRRT_kwDOSWB9286CJ3tX` 写成 resolved。
- 不删除 `software_proof`、`not_proven`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`。

## 3. 并行启动计划

本 sprint 是 Epic，但本 planning-only 任务只创建三份计划文档。进入执行阶段后：

- 并行启动 `hardware-engineer` 做只读 vendor/source reply 核验。
- 主会话或 GitHub 执行者并行准备 GitHub thread 定位与发布动作，但必须等 Hardware 核验通过后发布。
- Product closeout 等待两个证据：Hardware 核验结果和 GitHub publication evidence。

降级说明：

- 当前 planning-only 文件只由 `product-okr-owner` 负责，因为用户明确要求先创建计划阶段文档，且限定文件范围为三份 sprint 文档。
- 后续执行不是单线 sprint；至少需要 Hardware 核验和 GitHub publication 两条证据链。

## 4. 执行步骤

1. Hardware worker 读取 `docs/vendor/VENDOR_INDEX.md` 和上一轮 reply/summary。
2. Hardware worker 核对 reply 中 source refs 是否与上一轮 summary 一致，并确认没有把 `docs/vendor/` source boundary 扩大成真实材料证明。
3. GitHub 执行者定位 PR #5 review thread `PRRT_kwDOSWB9286CJ3tX`。
4. GitHub 执行者发布上一轮 Markdown reply。
5. GitHub 执行者返回发布证据。
6. Product closeout 创建 `tech-done.md`、`side2side_check.md`、`final.md`，只记录 publication closeout，不提高 OKR 完成度。

## 5. 验收命令

### Planning-only Product fence

```bash
rg -n "sprint_type: epic|pr5_review_reply_publication_closeout|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|ready_for_manual_github_review_reply_not_proven|GitHub reply|software_proof|not_proven|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|OKR 最低优先级核对" sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout
git diff --check -- sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout
```

### Hardware worker fence

```bash
test -f docs/vendor/VENDOR_INDEX.md
test -f sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply.md
test -f sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence/pr5_vendor_source_review_reply_dispatch_summary.json
rg -n "PRRT_kwDOSWB9286CJ3tX|docs/vendor/VENDOR_INDEX.md|base_ctrl.py|config.yaml|json_cmd.h|2D LiDAR|ToF|hardware_material_pending|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_manual_github_review_reply_not_proven" sprints/2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch/evidence docs/vendor/VENDOR_INDEX.md
```

### GitHub publication fence

```bash
# 由 GitHub 执行者使用可用的 GitHub tool / connector 完成，不在 planning-only 阶段运行。
# 必须返回：reply URL 或 comment id、thread id PRRT_kwDOSWB9286CJ3tX、发布时间、发布正文摘要。
```

### Product closeout fence

```bash
rg -n "GitHub reply|PRRT_kwDOSWB9286CJ3tX|ready_for_manual_github_review_reply_not_proven|published|software_proof|not_proven|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|Objective 5|Objective 1" sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout
git diff --check -- sprints/2026.05.20_05-06_pr5-review-reply-publication-closeout
```

## 6. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5 completion；本 sprint 针对 Objective 1 / PR #5 review reply publication closeout。
3. 不继续 Objective 5 的理由：
   - O5 当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 和真实手机/browser external proof。
   - 最新 `cloud_ack_outage_replay_guard`、`cloud_pending_ack_status_guard`、`cloud_command_expiry_safety_guard` 已证明继续堆本地 O5 metadata 不会提高 completion。
   - 发布 GitHub reply 不能替代任何 O5 external proof。
4. 选择 Objective 1 / PR #5 closeout 的理由：
   - `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，且 reviewer 明确要求 “Cite vendor sources for new mandatory sensor assumptions”。
   - 上一轮已经生成 `ready_for_manual_github_review_reply_not_proven` reply，但尚未实际发布 GitHub reply；这是一个可以关闭的流程缺口。
   - 本轮只关闭 publication gap，不把 `hardware_material_pending` 写成真实 2D LiDAR / ToF materials，不把 `software_proof` 写成 HIL 或 delivery success。

## 7. 风险边界

- GitHub reply 发布不等于 reviewer resolved；只有 reviewer/GitHub thread state 后续实际变化才能记录 resolved。
- GitHub reply 发布不等于真实 2D LiDAR / ToF SKU/source/receipt、procurement、installation、wiring、power、calibration、HIL-entry 或 Nav2/SLAM field pass。
- GitHub reply 发布不等于 WAVE ROVER/UART/HIL、真实 feedback、真实 `/odom`、`/imu/data`、`/battery`。
- GitHub reply 发布不等于 route/elevator field pass、真实 dropoff/cancel completion、delivery result 或 delivery success。
- GitHub reply 发布不等于 Objective 5 external proof，不证明公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser。

## 8. 完成前反思清单

- 是否只创建了三份 planning 文件，没有提前写 `tech-done.md`、`side2side_check.md` 或 `final.md`？
- 是否没有修改 `OKR.md`、`docs/process/okr_progress_log.md` 或其他文件？
- 是否把 Objective 5 数字最低但 blocked 的事实写入 `OKR 最低优先级核对`？
- 是否明确本轮为什么选择 Objective 1 / PR #5 review reply publication closeout？
- 是否保留 `software_proof`、`not_proven`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`？
- 是否明确 publication gap 不等于真实材料、HIL、field pass、O5 external proof 或 delivery success？

## 9. Closeout 状态补记

- Product closeout 已记录 GitHub reply 已发布：comment id `3269642220`，URL `https://github.com/princehaku/rober/pull/5#discussion_r3269642220`。
- `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`；`PRRT_kwDOSWB9286CJ3tQ` 和 `PRRT_kwDOSWB9286CJ3tU` 保持 resolved。
- 验收边界保持 `software_proof`、`not_proven`、`hardware_material_pending`、`delivery_success=false`、`primary_actions_enabled=false`；本轮不提升任何 OKR percentage。

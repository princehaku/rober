# PRD - Cloud command lifecycle support owner-response review decision

- sprint_type: epic
- sprint: `2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate`

## 1. 用户价值和产品北极星

用户价值：当云命令生命周期验收包已经交给 support / field owner 后，系统要把 owner/support response 从 intake 转成明确 review-decision 状态，让支持人员知道响应是 accepted、missing、rejected、unsafe 还是 blocked，并知道下一步需要补什么证据。

产品北极星：普通手机用户不需要理解 ROS2、ACK、队列、串口或硬件资料，也不会因为看到 owner response 就误以为机器人已经送达成功。所有主操作继续 fail closed，support 只拿到经过裁剪的可复核状态。

## 2. OKR 映射

- Objective 5：云中转 + OSS/CDN 数据通路产品化。当前完成度约 68%，仍是最低 Objective。本 sprint 针对 O5 的本地 Docker/software-proof 链路，补齐 owner/support response 的 review-decision 状态。
- Objective 4：手机用户体验与低成本量产边界。手机端只做只读面板和 fail-closed 展示，避免让用户把 support metadata 当成可操作控制。
- Objective 1：硬件协议可信底盘。仅保留 `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending` 边界，不规划新的 PR #5 硬件材料治理 rung，不声明硬件进度。

## 3. KR 拆解或更新

- O5 KR1：扩展 `trashbot.remote.v1` command/status/ack 旁路的 support review metadata，仍不暴露 `/cmd_vel`、raw ROS topics、serial/UART、WAVE ROVER 参数或 credential。
- O5 KR6：把缺 verified terminal result、外部云、4G、OSS/CDN、DB/queue 的场景保持 graceful degradation，review decision 只说明状态和下一证据，不放开主操作。
- O4 KR1/KR5：手机端继续让用户理解当前阻塞和支持交接状态；不要求用户 SSH、ROS2、串口或硬件调试。

本轮不更新 OKR 百分比；只有后续拿到真实外部材料、真实手机/browser、verified terminal result 或生产云证据，才可评估 O5 进度提升。

## 4. 本轮核心抓手

把 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake` 的后继状态落成 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`：

- Robot/API 侧产生安全 summary 和 diagnostics alias。
- Mobile/web 侧消费安全 summary，显示 review decision、原因和 next required evidence。
- Product closeout 侧保留 no OKR percentage lift 和 proof boundary。

## 5. 需要做什么

Robot Platform Engineer:

- 在 `remote_cloud_relay.py` 中新增 review-decision safe alias / summary builder。
- 在 focused unittest 中覆盖 accepted、missing、rejected、unsafe、blocked 等状态，以及 unsafe/raw 字段 fail closed。
- 更新 `docs/product/remote_4g_mvp.md`，说明该 review-decision 只读、不可控制、不可证明 delivery success。

User Touchpoint Full-Stack Engineer:

- 在 `mobile/web/app.js` 新增只读面板，消费 Robot safe summary。
- 新增 fixture `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision.json`。
- 在 focused mobile unittest 中证明面板 fail closed、主操作保持禁用、危险字段不展示。
- 更新 `docs/product/mobile_user_flow.md`。

Product closeout later:

- 在 sprint `tech-done.md`、`side2side_check.md`、`final.md` 记录实际改动和验证证据。
- 在 `OKR.md` 和 `docs/process/okr_progress_log.md` 保守记录 O5 no percentage lift，以及仍缺真实外部材料。

## 6. 优先级和验收口径

P0:

- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate` 必须出现在 Robot、mobile 和 docs 证据中。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 必须保持。
- 文案必须明确 `not verified terminal result`、`not true phone/browser proof`、`no OKR percentage lift`。

P1:

- Review decision 要能解释 accepted / missing / rejected / unsafe / blocked 的差异，并给出 next required evidence。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 只能作为 `hardware_material_pending` 边界展示，不进入新的治理 ladder。

验收通过条件：

- Robot 和 Full-Stack 各自 targeted commands 通过。
- Required `rg` 能命中 capability、proof boundary 和 fail-closed 字段。
- Scoped `git diff --check` 通过。
- Product closeout later 记录 no OKR percentage lift 和剩余风险。

## 7. 对应责任 Engineer

- Robot Platform Engineer：Robot/API safe summary、diagnostics alias、remote 4G product docs。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、focused tests、mobile flow docs。
- Product Manager / OKR Owner：sprint closeout、OKR/progress-log 保守更新、验收边界。

## 8. 风险、阻塞和证据链

- O5 真实进度阻塞：仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result。
- O1 独立阻塞：`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，不能把本轮 O5 support review decision 写成 PR #5 resolved。
- 产品风险：review decision 很容易被误读为交付完成；必须把 accepted/processing/support-review 与 delivery success 分开。
- 工程风险：Robot summary 和 mobile panel 的 fallback 字段必须一致；unsafe raw fields、credentials、ROS topics、serial/UART、WAVE ROVER details、tracebacks、complete artifacts、checksums 必须 fail closed。

## 9. 需要创建或更新的 sprint 文档

本 planning task 创建：

- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/pre_start.md`
- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/prd.md`
- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/tech-plan.md`

后续 implementation / closeout 必须创建或更新：

- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/tech-done.md`
- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/side2side_check.md`
- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

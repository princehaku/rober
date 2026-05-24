# PRD - Cloud command lifecycle support owner-response reviewer ACK review handoff

- sprint_type: epic
- sprint: `2026.05.24_18-19_cloud-command-lifecycle-support-owner-response-reviewer-ack-review-handoff`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_gate`
- PRD owner: Product Manager / OKR Owner

## User Value And Product North Star

用户价值：支持、field owner 和 reviewer 可以在同一 safe `command_id` / safe `evidence_ref` 下看到 reviewer ACK review-decision 已经被安全交接给下一个 owner/reviewer/support 路由，而不读取 raw diagnostics、不触发任何控制动作、不误以为任务已真实完成。

产品北极星：普通手机用户只看到可理解、可停、可解释的机器人状态；支持同学获得足够的安全交接信息；任何 Docker-only proof 都不能突破 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## OKR Mapping

- Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 68%，本轮针对最低 Objective。
- KR1：继续强化 `trashbot.remote.v1` command/status/ack 解释链路，不暴露 `/cmd_vel`，不接受 inbound robot control。
- KR6：把云命令生命周期中的 blocked / pending / handoff 状态做成 graceful degradation 支持证据，帮助区分网络/材料/终态缺失问题。
- Objective 4 只作为只读 mobile/web 展示触点，不提升完成度；本轮 is not true phone/browser proof。

## KR Decomposition

1. Robot/API 必须新增 reviewer ACK review-handoff safe summary，来源只能是上轮 reviewer ACK review-decision safe summary 或兼容 safe diagnostics/status summary。
2. Summary 必须显式包含 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff`、`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_gate`、safe `command_id`、safe `evidence_ref`、source review decision、handoff owner/support/reviewer route、handoff reason、next required evidence、blocker status、PR #5 thread `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
3. Summary 必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`not verified terminal result`、`not true phone/browser proof`、`no OKR percentage lift`。
4. `mobile/web` 必须新增只读 panel，位置在 reviewer ACK review-decision panel 后；Start Delivery、Confirm Dropoff、Cancel 继续 disabled。
5. Product docs 必须同步更新 `docs/product/remote_4g_mvp.md` 与 `docs/product/mobile_user_flow.md`，但本 planning task 不改这些文件，实施阶段由对应 Engineer 更新。

## Core Grab

本轮核心抓手不是再包装一个模糊状态，而是把 reviewer ACK review-decision 到 review-handoff 的责任边界说清楚：谁接手、为什么交接、还缺什么证据、为什么不能控制机器人、为什么不能算 delivery success。

## Requirements

### Robot/API Requirements

- 新增或扩展 Robot/API summary builder，命名围绕 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff`。
- 接口字段必须使用 safe 字段，不包含 raw command payload、ACK cursor、Authorization、signed URL、local path、checksum、traceback、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER detail 或完整 artifact。
- Supported states 至少覆盖：
  - `accepted_for_reviewer_ack_review_handoff_not_proven`
  - `reviewer_ack_review_handoff_needs_reassignment_not_proven`
  - `reviewer_ack_review_handoff_missing_material_not_proven`
  - `reviewer_ack_review_handoff_rejected_unsafe_not_proven`
  - `blocked_missing_source_reviewer_ack_review_decision_not_proven`
  - `reviewer_ack_review_handoff_evidence_ref_mismatch_not_proven`
- Missing source、unsafe source、evidence_ref mismatch、true-state flags 或 success wording 必须 fail closed。

### Mobile Requirements

- 新增 read-only panel，标题可使用 `云命令交接 owner response reviewer ACK review handoff`。
- Panel 只展示 safe summary：review handoff status、source review decision、safe command id、safe `evidence_ref`、owner/support/reviewer route、handoff reason、next required evidence、blocker status、PR #5 thread `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`、proof boundary 和 false-state flags。
- Panel 不得新增 replay/resubmit、ACK/cursor mutation、material upload、review mutation、handoff mutation、GitHub mutation、diagnostics mutation、owner-response submission、reviewer-ACK submission、raw artifact fetch 或 robot command path。
- Existing Start Delivery / Confirm Dropoff / Cancel gating 不得被放宽；`primary_actions_enabled=false` 必须在 fixture 和测试中出现。

## Priority And Acceptance

P0：
- Robot/API summary 只从 safe source 派生，并完整输出 proof boundary 和 false-state flags。
- Mobile panel 只读、fail closed、位置正确、动作按钮 disabled。
- Focused tests 覆盖 accepted 和 blocked/unsafe/mismatch 至少两个路径。

P1：
- Product docs 同步写明本轮 proof boundary、fields 和非声明边界。
- Fixture 覆盖 PR #5 `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending`。

验收口径：本轮完成后只能声明 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_gate`，不得声明 verified terminal result、true phone/browser proof、real cloud proof、HIL、PR #5 resolved、delivery success 或 OKR percentage lift。

## Responsible Engineers

- Robot Platform Engineer：Robot/API summary、diagnostics/status embedding、focused Python tests、`docs/product/remote_4g_mvp.md` 同步。
- User Touchpoint Full-Stack Engineer：`mobile/web` panel、fixture、focused mobile tests、`docs/product/mobile_user_flow.md` 同步。

## Risks And Evidence Gaps

- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，会继续阻断任何硬件材料和 PR thread resolved claim。
- Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 verified terminal result。
- 没有真实 iPhone/Android browser proof；mobile/web 只能算 local software proof。
- 没有真实 WAVE ROVER/UART/HIL、Nav2/fixed-route、route/elevator field pass 或 delivery success。
- 如果实施阶段发现同一 capability 已被其他并行 sprint 实现，必须只做验收/留档，不覆盖他人改动。

## Sprint Docs To Create Or Update

- 已创建/更新：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施后必须创建：`tech-done.md`。
- Epic 收口必须创建：`side2side_check.md`、`final.md`。
- 本 planning task 不更新 `OKR.md`；实施 closeout 若仍是 Docker-only proof，应记录 no OKR percentage lift。

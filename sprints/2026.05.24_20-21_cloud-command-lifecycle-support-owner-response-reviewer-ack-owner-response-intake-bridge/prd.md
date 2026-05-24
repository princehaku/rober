# PRD - Cloud command lifecycle support owner-response reviewer ACK owner-response intake bridge

- sprint_type: epic
- sprint: `2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate`
- PRD owner: Product Manager / OKR Owner

## User Value And Product North Star

用户价值：support owner 和 field owner 能把 reviewer ACK follow-up escalation 的 safe summary 接回 owner-response intake 主线，而不是停在一个无法继续复账的 escalation 状态。普通手机用户只看到只读、可解释、fail-closed 的支持状态；主操作仍不可用，避免把支持材料回流误解成真实送达、真实终态或真实远程控制可用。

产品北极星：普通手机用户只接触可理解、可停、可解释的机器人状态；support 可以在同一 safe `command_id` 和 safe `evidence_ref` 下推进材料复账；任何 Docker/local proof 都必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## OKR Mapping

- Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 68%，是本轮最低优先级 Objective。
- KR1：继续强化 `trashbot.remote.v1` command/status/ack 支持链路，不暴露 `/cmd_vel`，不接受 inbound robot control。
- KR6：把云命令生命周期中的 handoff / reviewer ACK / follow-up escalation / owner-response intake bridge 做成 graceful degradation 支持证据，帮助区分材料缺口、owner-response 缺口和终态缺失问题。
- Objective 4 只作为只读 `mobile/web` 消费触点，不提升完成度；本轮 is not true phone/browser proof。

## KR Decomposition

1. Robot/API 必须新增 owner-response intake bridge safe summary，来源只能是上一轮 reviewer ACK follow-up escalation safe summary 或兼容 safe diagnostics/status summary。
2. Summary 必须显式包含 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`、`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate`、safe `command_id`、safe `evidence_ref`、source follow-up escalation status、bridge status、owner-response intake readiness、accepted / missing / rejected / unsafe / blocked material classifications、owner/support/reviewer route、next required evidence、PR #5 thread `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
3. Summary 必须保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`not verified terminal result`、`not true phone/browser proof`、`no OKR percentage lift`。
4. `mobile/web` 必须消费该 safe summary，并把它显示为既有 owner-response intake 链路的 bridge/read-only 状态；它不是新的独立 UI wrapper。
5. Product docs 必须同步更新 `docs/product/remote_4g_mvp.md` 与 `docs/product/mobile_user_flow.md`，但本 planning task 不改这些文件，实施阶段由对应 Engineer 更新。
6. Product closeout 必须在 Task C 记录 no-lift 结论，且不得更新 `OKR.md` 百分比。

## Core Grab

本轮核心抓手是把 reviewer ACK follow-up escalation 的 safe summary 安全桥回 owner-response intake：来源可追溯、字段可复账、状态可回归测试、控制面继续 fail closed。它解决的是支持链路断点，不是新增可操作控制，不是新材料上传入口，也不是真实云或真实终态验收。

## Non-Goals

- 不新增 robot command、ACK/cursor mutation、material upload、review mutation、handoff mutation、GitHub mutation、diagnostics mutation、owner-response submission、reviewer-ACK submission、raw artifact fetch、Nav2 trigger、WAVE ROVER/UART path 或 delivery-success inference。
- 不修改硬件/vendor 文件，不新增硬件配置，不触发 GitHub mutation。
- 不做真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、HIL、route/elevator field pass 或 delivery result 验证。
- 不更新 `OKR.md` 百分比，不把 PRD、support bridge 或 local Docker proof 当业务闭环完成。

## Requirements

### Robot/API Requirements

- 新增或扩展 Robot/API summary builder，命名围绕 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`。
- Source 必须是 safe reviewer ACK follow-up escalation status summary；缺 source、unsafe source、source capability 不匹配或 evidence_ref mismatch 必须 fail closed。
- 接口字段必须使用 safe 字段，不包含 raw command payload、ACK cursor、Authorization、bearer token、signed URL、local path、checksum、traceback、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER detail、完整 artifact 或 true-state flags。
- Supported statuses 至少覆盖：
  - `accepted_for_owner_response_intake_bridge_not_proven`
  - `owner_response_intake_bridge_missing_owner_material_not_proven`
  - `owner_response_intake_bridge_rejected_unsafe_not_proven`
  - `owner_response_intake_bridge_blocked_hardware_material_pending_not_proven`
  - `blocked_missing_source_reviewer_ack_followup_escalation_status_not_proven`
  - `owner_response_intake_bridge_evidence_ref_mismatch_not_proven`
  - `owner_response_intake_bridge_source_not_ready_not_proven`
- Bridge 输出必须能被既有 owner-response intake/review/handoff 主线复账，但不得自动提交 owner response 或打开任何控制动作。

### Mobile Requirements

- 新增 read-only consumption/panel，标题可使用 `云命令交接 owner response intake bridge`。
- Panel 应放在 reviewer ACK follow-up escalation status 之后，语义上回到 owner-response intake 主线，不作为独立可操作 wrapper。
- Panel 只展示 safe summary：bridge status、source follow-up status、safe command id、safe `evidence_ref`、owner-response intake readiness、accepted / missing / rejected / unsafe / blocked classifications、owner/support/reviewer route、next required evidence、PR #5 thread `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`、proof boundary 和 false-state flags。
- Existing Start Delivery / Confirm Dropoff / Cancel gating 不得被放宽；`primary_actions_enabled=false` 必须在 fixture 和测试中出现。

## Priority And Acceptance

P0：
- Robot/API summary 只从 safe source 派生，并完整输出 proof boundary、bridge status、owner-response intake classifications 和 false-state flags。
- Mobile consumption 只读、fail closed、位置正确、动作按钮 disabled。
- Focused tests 覆盖 accepted bridge、missing owner material / hardware material pending、unsafe or evidence_ref mismatch 中至少两类路径。

P1：
- Product docs 同步写明本轮 proof boundary、fields、状态枚举、bridge 到 owner-response intake 的产品语义和非声明边界。
- Fixture 覆盖 PR #5 `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending`。

验收口径：本轮完成后只能声明 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate`，不得声明 verified terminal result、true phone/browser proof、real cloud proof、HIL、PR #5 resolved、delivery success 或 OKR percentage lift。

## Responsible Engineers

- Task A Robot Platform Engineer：Robot/API bridge summary、diagnostics/status embedding、focused Python validation、`docs/product/remote_4g_mvp.md` 同步。
- Task B User Touchpoint Full-Stack Engineer：`mobile/web` read-only consumption、fixture、focused mobile validation、`docs/product/mobile_user_flow.md` 同步。
- Task C Product Closeout / Integration Validation：核对 sprint docs、OKR no-lift、side-by-side evidence、final boundary、`OKR.md` 与 `docs/process/okr_progress_log.md` 的保守记录。

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
- Task C 如更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，必须保守记录 `no OKR percentage lift`。

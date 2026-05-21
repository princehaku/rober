# Cloud ACK Accepted Result Pending Guard PRD

Run time: 2026-05-22 00:01 Asia/Shanghai

## 用户价值和产品北极星

用户价值：当手机看到云命令 ACK 已经 `accepted` 或 `processing`，但还没有真实 delivery result / dropoff completion / cancel completion 时，用户必须理解为“命令正在处理，尚未成功完成”，不能误判为送达成功、投放完成、取消完成或可以继续触发主操作。

产品北极星：普通手机用户不需要理解 ACK、queue、cursor、ROS topic 或云端内部细节，也能知道当前是否可操作；ACK accepted/processing 只代表控制面收到并处理中，不代表真实交付闭环完成。

## Problem

Objective 5 的 command/status/ack 链路已经覆盖多个 fail-closed 状态，但仍缺一个关键中间语义：ACK 已经存在并显示 `accepted` / `processing`，而真实任务结果还没有出现。若这个状态被 UI 或 diagnostics 写成成功、完成、可继续操作，用户可能误触发 Start / Confirm Dropoff / Cancel，支持侧也可能把控制面 ACK 误当作真实交付结果。

本轮目标不是补外部云证明，也不是继续 owner-ack material wrapper；目标是把 ACK accepted/processing 与 delivery success 明确拆开。

## OKR 映射

- Primary: Objective 5 KR1 / KR6，云中转 commands/status/ack contract 与 graceful degradation。
- Supporting: Objective 4 KR1 / KR5 / KR7，手机端主操作安全、用户可理解状态和支持诊断。
- Boundary: Objective 1 / 2 / 3 不因本 sprint 增加进度；本 sprint 不提供硬件、路线、电梯、HIL、真实手机、真实云或 delivery proof。

Objective 5 当前约 68% 且是最低完成度 Objective。本 sprint 仍选择 O5，因为 ACK accepted/processing without terminal result 是 distinct command/status safety gap；但没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 或真实交付证据，所以不提高 O5 完成度。

## KR 拆解或更新

本 sprint 不改 `OKR.md` 百分比，只为后续实现定义可验收 KR 子项：

- KR5.1 Robot/API must classify accepted/processing ACK without terminal result as `degradation_state=ack_accepted_result_pending`.
- KR5.2 The state must carry `ack_semantics=accepted_processing_only_not_delivery_success`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- KR5.3 Mobile/web must render accepted/processing ACK as waiting for result, keep Start Delivery / Confirm Dropoff / Cancel disabled, and preserve Diagnostics / Support Handoff.
- KR5.4 Tests and docs must preserve non-claim wording: accepted/processing ACK is not dropoff completion, cancel completion, delivery result, or delivery success.

## 本轮核心抓手

Create a named fail-closed result-pending contract:

- `cloud_ack_accepted_result_pending_guard`
- `ack_accepted_result_pending`
- `accepted_processing_only_not_delivery_success`
- `software_proof_docker_cloud_ack_accepted_result_pending_guard`

The contract turns an ambiguous accepted/processing ACK into product-safe state that all surfaces can display consistently.

## Required Behavior

When Robot/API or mobile/web sees a command ACK whose cloud/robot processing state is accepted or processing, but no real terminal result exists:

- `remote_readiness.remote_ready=false`
- `remote_readiness.safe_to_control=false`
- `remote_readiness.delivery_success=false`
- `remote_readiness.primary_actions_enabled=false`
- `remote_readiness.capability=cloud_ack_accepted_result_pending_guard`
- `remote_readiness.degradation_state=ack_accepted_result_pending`
- `remote_readiness.ack_semantics=accepted_processing_only_not_delivery_success`
- `remote_readiness.retry_hint=wait_for_delivery_result_or_contact_support`
- `remote_readiness.safe_phone_copy` must be Chinese, phone-safe, and explain that the command is accepted/processing but real delivery/cancel/dropoff result is still pending.
- `remote_readiness.proof_boundary=software_proof_docker_cloud_ack_accepted_result_pending_guard`

The state must not enqueue a new command, replay a command, mark delivery successful, infer dropoff/cancel completion, mutate terminal command state, or unlock primary controls.

## 需要做什么

1. Robot Platform Engineer adds a canonical accepted-result-pending readiness helper and applies it wherever ACK accepted/processing can be observed without terminal result.
2. Robot Platform Engineer adds focused API/diagnostics tests proving accepted/processing ACK remains pending and not success.
3. User Touchpoint Full-Stack Engineer adds mobile/web fixture and rendering so this pending state is visible and fail-closed.
4. Both owners update relevant `docs/` files to keep product and interface docs in sync.
5. Product Manager / OKR Owner closes the sprint only after worker validation lands and keeps Objective 5 at about 68% unless real external evidence appears.

## 优先级和验收口径

Priority: P0 for O5 command/status safety while O5 remains lowest and real external materials are unavailable.

Acceptance:

- Accepted/processing ACK without terminal result carries canonical `remote_readiness`.
- Robot/API and diagnostics expose `ack_accepted_result_pending` without raw tokens, raw cloud responses, ROS topics, serial paths, tracebacks, or hardware details.
- Phone/mobile renders `ack_accepted_result_pending` as “命令已接收 / 正在处理，但尚无真实结果”.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Diagnostics / Support Handoff remain available.
- Focused tests pass.
- Docs explicitly say this is `software_proof_docker_cloud_ack_accepted_result_pending_guard` and not delivery success.
- `OKR.md` percentage does not increase without real external cloud/phone/delivery evidence.

## 对应责任 Engineer

- Robot Platform Engineer: Robot/API ACK accepted-result-pending contract, diagnostics normalization, Python tests, `docs/product/remote_4g_mvp.md`, and interface docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, fixture, UI tests, and `docs/product/mobile_user_flow.md`.
- Hardware Infra Engineer: read-only confirmation only if implementation wording risks hardware/vendor/HIL claims; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending.
- Product Manager / OKR Owner: sprint closeout, OKR wording, evidence boundary, and validation checklist after implementation.

## 风险、阻塞和证据链

Risks:

- ACK accepted/processing could be misread as delivery success if UI copy or diagnostics use completion language.
- Cancel/dropoff completion could be inferred from control-plane ACK if tests do not enforce terminal-result separation.
- A local Docker proof could be overstated as public HTTPS/TLS, 4G/SIM, true phone/browser, or production cloud proof.
- This could drift into another generic wrapper unless it stays anchored to accepted/processing ACK without terminal result.

Required evidence chain:

- `OKR.md` 4.1: Objective 5 about 68%, lowest, no percentage increase.
- Latest final: `sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/final.md` says not to repeat owner-ack local wrappers.
- Recent O5 guards: `cloud_support_handoff_safe_export`, `cloud_cancel_pending_command_safety_guard`, and `cloud_ack_lookup_pending_status_guard` already exist and must not be repeated.
- PR #5: `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending; comment `3269642220` is software-proof reply publication only.
- PR #6: README/docs-only, no runtime, hardware, or cloud proof.

## 需要创建或更新的 sprint 文档

Planning sprint creates:

- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/pre_start.md`
- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/prd.md`
- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/tech-plan.md`

After implementation, Product must update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

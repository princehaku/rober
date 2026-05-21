# Cloud ACK Lookup Pending Status Guard PRD

Run time: 2026-05-21 22:07 CST

## 用户价值和产品北极星

用户价值：手机查询某条 command ACK 时，如果云端还没有 ACK，用户看到的状态必须明确是“机器人尚未处理 / 仍需等待”，而不是失败、成功、或可以继续下发 Start / Confirm / Cancel。

产品北极星：普通手机用户不需要理解 ACK、cursor、ROS topic 或云端内部错误，也能判断当前是否可以继续操作；缺 ACK 时只能等待或联系支持，不能误触发主路径。

## Problem

`docs/product/remote_4g_mvp.md` 已定义 `GET /robots/{robot_id}/commands/{command_id}/ack`：missing ACK 返回 `ack_not_found`，手机应继续 polling 或显示 robot 尚未处理。当前 `operator_gateway_http.py` 的 `MockCloudStore.get_ack` 对 missing ACK 只返回 plain `remote_error("ack_not_found", ...)`，缺少 canonical `remote_readiness`，导致手机/支持侧缺一个稳定、可测试、可展示的 pending 状态。

## OKR 映射

- Primary: Objective 5 KR1 / KR6，云中转 commands/status/ack contract 与 graceful degradation。
- Supporting: Objective 4 KR1 / KR5 / KR7，手机端主操作安全、用户可理解状态和支持诊断。
- Boundary: Objective 1 / 2 / 3 不因本 sprint 增加进度；本 sprint 不提供硬件、路线、电梯、HIL、真实手机、真实云或 delivery proof。

Objective 5 当前约 68% 且最低；本 sprint 针对 O5 的 distinct control-plane gap，但因为仍缺真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser，所以不提高 O5 完成度。

## KR 拆解或更新

本 sprint 不改 `OKR.md` 百分比，只为后续实现定义可验收 KR 子项：

- KR5.1 ACK read endpoint missing ACK must return `ack_not_found` plus phone-safe `remote_readiness`.
- KR5.2 `remote_readiness` must include `capability=cloud_ack_lookup_pending_status_guard`, `degradation_state=ack_lookup_pending`, `ack_semantics=ack_lookup_pending_not_delivery_success`, and `proof_boundary=software_proof_docker_cloud_ack_lookup_pending_status_guard`.
- KR5.3 Phone/mobile must render missing ACK as pending/waiting, keep Start Delivery / Confirm Dropoff / Cancel disabled, and preserve Diagnostics / Support Handoff.
- KR5.4 Tests and docs must preserve non-claim wording: ACK lookup pending is not delivery success and not external cloud proof.

## 本轮核心抓手

Create a named fail-closed ACK lookup pending contract:

- `cloud_ack_lookup_pending_status_guard`
- `ack_lookup_pending`
- `ack_lookup_pending_not_delivery_success`
- `software_proof_docker_cloud_ack_lookup_pending_status_guard`

The contract turns a plain missing-ACK error into product-safe state that the phone can display consistently.

## Required Behavior

When phone/API calls `GET /robots/{robot_id}/commands/{command_id}/ack` and no ACK exists:

- HTTP may remain `404` with `error.code=ack_not_found`.
- Response must also include safe `remote_readiness`.
- `remote_readiness.remote_ready=false`.
- `remote_readiness.safe_to_control=false`.
- `remote_readiness.delivery_success=false`.
- `remote_readiness.primary_actions_enabled=false`.
- `remote_readiness.capability=cloud_ack_lookup_pending_status_guard`.
- `remote_readiness.degradation_state=ack_lookup_pending`.
- `remote_readiness.ack_semantics=ack_lookup_pending_not_delivery_success`.
- `remote_readiness.retry_hint=continue_polling_or_contact_support`.
- `remote_readiness.safe_phone_copy` must be Chinese, phone-safe, and explain that the robot has not processed the command yet.
- `remote_readiness.proof_boundary=software_proof_docker_cloud_ack_lookup_pending_status_guard`.

Mobile/web must consume only safe fields and keep primary actions disabled while keeping diagnostics/support visible.

## 需要做什么

1. Robot Platform Engineer adds the canonical pending readiness helper and returns it with missing ACK lookup responses.
2. Robot Platform Engineer adds focused API/diagnostics tests proving missing ACK is pending, not success/failure completion.
3. User Touchpoint Full-Stack Engineer adds mobile/web fixture and rendering so the pending state is visible and fail-closed.
4. Both owners update relevant `docs/` files to keep product docs in sync.
5. Product Manager / OKR Owner closes the sprint only after worker validation lands and keeps Objective 5 at about 68% unless real external evidence appears.

## 优先级和验收口径

Priority: P0 for O5 control-plane safety while O5 remains lowest and real external materials are unavailable.

Acceptance:

- Missing ACK response carries both `ack_not_found` and canonical `remote_readiness`.
- Phone/mobile renders `ack_lookup_pending` as “机器人尚未处理 / 继续等待或联系支持”.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Diagnostics / Support Handoff remain available.
- Focused tests pass.
- Docs explicitly say this is `software_proof_docker_cloud_ack_lookup_pending_status_guard` and not delivery success.
- `OKR.md` percentage does not increase without real external cloud/phone evidence.

## 对应责任 Engineer

- Robot Platform Engineer: Robot/API ACK lookup contract, diagnostics normalization, Python tests, `docs/product/remote_4g_mvp.md`, and interface docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, fixture, UI tests, and `docs/product/mobile_user_flow.md`.
- Hardware Infra Engineer: read-only confirmation that no hardware/vendor/HIL claim is made and PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending.
- Product Manager / OKR Owner: sprint closeout, OKR wording, evidence boundary, and validation checklist after implementation.

## 风险、阻塞和证据链

Risks:

- Missing ACK could be misread as failed command if UI copies remain generic.
- ACK could be misread as delivery success if docs/tests do not enforce `ack_lookup_pending_not_delivery_success`.
- A local Docker proof could be overstated as public HTTPS/TLS, 4G/SIM, true phone/browser, or production cloud proof.

Required evidence chain:

- `OKR.md` 4.1: Objective 5 about 68%, lowest, no percentage increase.
- Latest `field-evidence-real-material-owner-ack-intake` final: next useful work is not another local metadata wrapper; O5 work must be a distinct control-plane gap.
- PR #5: `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` resolved; `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending; comment `3269642220` is software-proof reply publication only.
- Product contract: `docs/product/remote_4g_mvp.md` ACK read endpoint and `ack_not_found` behavior.
- Runtime gap: `operator_gateway_http.py` missing ACK path currently lacks phone-safe `remote_readiness`.

## 需要创建或更新的 sprint 文档

Planning sprint creates:

- `sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/pre_start.md`
- `sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/prd.md`
- `sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/tech-plan.md`

After implementation, Product must update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

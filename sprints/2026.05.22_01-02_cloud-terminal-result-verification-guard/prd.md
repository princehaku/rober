# Cloud Terminal Result Verification Guard PRD

Run time: 2026-05-22 01:02 Asia/Shanghai

## 用户价值和产品北极星

用户价值：用户和支持人员不能因为某个 result 字段存在就以为送达、投放或取消已经完成。只有字段值被验证为真实终态，才能退出 `ack_accepted_result_pending`；否则手机端必须继续显示“命令已接收/处理中，尚无真实结果”，并保持主操作禁用。

产品北极星：云中转链路要让普通手机用户获得可信状态，而不是暴露云端 ACK 细节。产品闭环的关键不是“云端有响应字段”，而是“真实 delivery/dropoff/cancel terminal result 已到达并可复盘”。

## Problem

上一轮 `cloud_ack_accepted_result_pending_guard` 已经把 accepted/processing ACK without terminal result 归一成 fail-closed pending state。但当前已知缺口在 backend terminal-result 判定：`operator_gateway_http._has_terminal_delivery_result()` 使用 truthy 判断，可能将以下非终态字符串误判为真实结果：

- `delivery_result="pending"`
- `terminal_result="accepted"`
- `dropoff_completion="processing"`
- `cancel_completion="pending"`

这会造成两个产品风险：

1. Robot/API 可能不再输出 `ack_accepted_result_pending`，而把控制面中间态当成 terminal result。
2. mobile/web 可能因此渲染出可继续操作或完成语义，绕过上一轮 guard。

## OKR 映射

- Primary：Objective 5 KR1 / KR6，云中转 commands/status/ack contract 和 graceful degradation。
- Supporting：Objective 4 KR1 / KR5 / KR7，手机端主路径安全、异常解释和普通用户可理解状态。
- Boundary：Objective 1 / 2 / 3 不因本 sprint 增加进度；本 sprint 不提供硬件、路线、电梯、HIL、真实手机、真实云或 delivery proof。

Objective 5 当前约 68% 且是最低完成度 Objective。本 sprint 针对 O5，是因为 terminal-result verification 是 distinct command/status safety gap；但当前没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 或真实交付证据，所以不提高 O5 完成度。

## KR 拆解或更新

本 sprint 不直接更新 `OKR.md` 百分比，只定义可验收 KR 子项：

- KR5.1 Robot/API must distinguish terminal result presence from terminal result verification.
- KR5.2 Non-terminal strings such as `pending`, `accepted`, `processing`, `queued`, `running`, `in_progress`, `submitted`, and `unknown` must not satisfy terminal delivery result checks.
- KR5.3 Only explicit terminal success/failure/canceled/completed result values, or structured result payloads with verified terminal status, may exit `ack_accepted_result_pending`.
- KR5.4 Mobile/web must render `cloud_terminal_result_verification_guard` as fail-closed when backend reports non-terminal result fields.
- KR5.5 Tests and docs must preserve `software_proof_docker_cloud_terminal_result_verification_guard` and must not claim delivery success.

## 本轮核心抓手

Create a stricter terminal-result verification guard:

- `cloud_terminal_result_verification_guard`
- `terminal_result_pending`
- `ack_accepted_result_pending`
- `accepted_processing_only_not_delivery_success`
- `software_proof_docker_cloud_terminal_result_verification_guard`

核心产品规则：字段存在不是结果；值通过终态验证才是结果。

## Required Behavior

When ACK is accepted or processing and any result-like field exists with a non-terminal value:

- `remote_readiness.remote_ready=false`
- `remote_readiness.safe_to_control=false`
- `remote_readiness.delivery_success=false`
- `remote_readiness.primary_actions_enabled=false`
- `remote_readiness.capability=cloud_terminal_result_verification_guard`
- `remote_readiness.degradation_state=terminal_result_pending`
- `remote_readiness.ack_semantics=accepted_processing_only_not_delivery_success`
- `remote_readiness.retry_hint=wait_for_verified_terminal_result_or_contact_support`
- `remote_readiness.proof_boundary=software_proof_docker_cloud_terminal_result_verification_guard`

Phone-safe copy must explain in Chinese that the command/result field is still pending or processing, and no verified terminal delivery/dropoff/cancel result exists.

## 需要做什么

1. Robot Platform Engineer tightens terminal-result verification in `operator_gateway_http.py`.
2. Robot Platform Engineer adds focused tests covering non-terminal strings in `delivery_result`, `terminal_result`, `dropoff_completion`, and `cancel_completion`.
3. Robot Platform Engineer updates diagnostics/API docs so non-terminal result fields are documented as pending, not success.
4. User Touchpoint Full-Stack Engineer adds a mobile/web fixture and rendering for `cloud_terminal_result_verification_guard`.
5. User Touchpoint Full-Stack Engineer adds focused mobile-web tests proving Start Delivery / Confirm Dropoff / Cancel stay disabled.
6. Product Manager / OKR Owner closes the sprint only after worker evidence lands, and keeps Objective 5 at about 68% unless real external proof appears.

## 优先级和验收口径

Priority: P0 for O5 command/status safety, because a false terminal result can turn a safe pending state into a user-visible completion claim.

Acceptance:

- Non-terminal strings do not satisfy `_has_terminal_delivery_result()`.
- Accepted/processing ACK with non-terminal result-like fields remains `ack_accepted_result_pending` or `terminal_result_pending`.
- Robot/API and diagnostics expose the state without raw tokens, raw cloud responses, ROS topics, serial paths, tracebacks, credentials, WAVE ROVER details, or success wording.
- Phone/mobile renders the state as “尚无已验证终态结果”.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Diagnostics / Support Handoff remain visible.
- Focused Robot and mobile tests pass.
- Relevant `docs/` files are updated during implementation.
- `OKR.md` percentage does not increase without real external cloud/phone/delivery evidence.

## 对应责任 Engineer

- Robot Platform Engineer：backend terminal-result verification, API/diagnostics normalization, Python tests, `docs/product/remote_4g_mvp.md`, and `docs/interfaces/operator_gateway_diagnostics.md`.
- User Touchpoint Full-Stack Engineer：mobile/web fail-closed rendering, fixture, UI tests, and `docs/product/mobile_user_flow.md`.
- Hardware Infra Engineer：read-only confirmation only if wording risks hardware/vendor/HIL claims; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending.
- Product Manager / OKR Owner：sprint closeout, OKR wording, evidence boundary, and validation checklist after implementation.

## 风险、阻塞和需要补齐的证据链

Risks:

- Truthy result-like fields may keep bypassing `ack_accepted_result_pending` if verification remains too broad.
- UI copy may accidentally describe accepted/processing as completed.
- Local Docker proof may be overstated as public cloud, true phone/browser, HIL, route/elevator field pass, or delivery success.
- This sprint could become another metadata wrapper unless it closes the exact `_has_terminal_delivery_result()` verification bug.

Required evidence chain:

- `OKR.md` 4.1: Objective 5 about 68%, lowest, no percentage increase.
- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/final.md`: do not repeat O5 metadata depth unless closing a distinct command/status safety gap.
- Previous guard: `cloud_ack_accepted_result_pending_guard` / `ack_accepted_result_pending` / `software_proof_docker_cloud_ack_accepted_result_pending_guard`.
- Current defect: truthy `delivery_result` / `terminal_result` / `dropoff_completion` / `cancel_completion` can misclassify non-terminal strings.
- PR #5: `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending; comment `3269642220` is software-proof reply publication only.
- PR #6: docs-only, no review threads, no runtime/hardware/cloud proof.

## 需要创建或更新的 sprint 文档

Planning sprint creates:

- `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/pre_start.md`
- `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/prd.md`
- `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/tech-plan.md`

After implementation, Product must update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

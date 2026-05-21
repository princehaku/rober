# Cloud Manual Takeover Command Safety Guard Pre Start

## Sprint Declaration

- sprint_type: epic
- run_time: 2026-05-21 10:00 CST
- capability: `cloud_manual_takeover_command_safety_guard`
- evidence_boundary: `software_proof_docker_cloud_manual_takeover_command_safety_guard`
- required preserved states: `source=software_proof`, `not_proven`, `manual_takeover_required`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## User Value And North Star

The product north star remains: a normal phone user can hand trash to the robot, understand the current delivery state, and recover safely without learning ROS2, SSH, cloud logs, serial/UART, or hardware debug.

This sprint targets the independent user safety gap where the remote-control path says a human must take over. If `manual_takeover_required` or equivalent human-help state is active, the phone and cloud/operator surfaces must fail closed: no Start Delivery, Confirm Dropoff, Cancel, hidden replay, ACK cursor, or automatic resubmit can be presented as safe. Diagnostics and support copy remain visible so a support owner can collect safe evidence.

## Evidence Read Before Planning

- `AGENTS.md`: Epic sprint requires full planning docs and later parallel Engineer execution; product planning must not edit product code, tests, hardware config, `OKR.md`, or final docs in this planning pass.
- `OKR.md` 4.1 current snapshot: Objective 5 is the lowest at about 68%, Objective 1 is about 81%, and Objectives 2/3/4 are about 99%.
- Latest sprint final `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/final.md`: next sprint should not add another local-only success wrapper; if O5/O1 real materials are absent, only a bounded software-proof gap is acceptable.
- GitHub PR evidence supplied by CEO: PR #5 merged; review threads `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` resolved; `PRRT_kwDOSWB9286CJ3tX` unresolved / material pending; PR #6 is docs-only.
- `docs/product/remote_4g_mvp.md`: `phone_readiness.command_safety` already blocks primary commands for stale status, pending ACK, auth failure, cloud unreachable, malformed response, command ID conflict, command sequence regression, cloud poll backoff, manifest issues, and manual takeover, but manual takeover has no dedicated proof boundary/status guard.

## Blocker Scan And Re-Rank

- Objective 5 remains the numerical lowest Objective. Real external O5 materials are not present: no public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser evidence.
- Objective 1 remains blocked on real material and PR #5 thread `PRRT_kwDOSWB9286CJ3tX`; no true 2D LiDAR / ToF source, receipt, installation, calibration, WAVE ROVER/UART/HIL, or reviewer resolution is available.
- The recent field-evidence-rerun closeout says not to create another local success wrapper. This sprint is allowed only because `manual_takeover_required` is a named but unguarded command-safety failure mode in the existing O5 product contract.
- This sprint must not increase OKR percentages unless later Engineer work unexpectedly brings real external cloud/phone or hardware materials. Expected closeout is conservative: Objective 5 remains about 68%, Objective 1 remains about 81%.

## Core Sprint Grab

Create a dedicated Docker/local software-proof guard for manual takeover in the O5 remote-control command safety family:

- Robot/API status and diagnostics expose a phone-safe `manual_takeover_required` degraded state with `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- `mobile/web` consumes the same state through the existing command safety gate and renders support-safe copy while keeping Start Delivery / Confirm Dropoff / Cancel disabled.
- `docs/product/remote_4g_mvp.md`, `docs/product/mobile_user_flow.md`, and sprint closeout later preserve the boundary `software_proof_docker_cloud_manual_takeover_command_safety_guard`.

## Owners For Execution

- Robot Platform Engineer: owns Robot/API status, diagnostics summary, schema normalization, and backend tests.
- User Touchpoint Full-Stack Engineer: owns `mobile/web` rendering, fixture, parser/fallback behavior, and mobile tests.
- Product Manager / OKR Owner: owns sprint closeout docs, OKR evidence language, docs/product alignment verification, and no-percent-increase boundary.

## Non Goals

- Do not implement real cloud hosting, real public HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, HIL, WAVE ROVER/UART proof, route/elevator field pass, dropoff/cancel completion, or delivery success.
- Do not close or claim resolution of PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- Do not enable any primary control action from manual takeover/human-help state.
- Do not expose tokens, Authorization headers, raw JSON, ROS topics, `/cmd_vel`, serial/UART paths, WAVE ROVER details, local paths, tracebacks, checksums, or full artifacts to phone or diagnostics.

## Required Next Sprint Documents

This planning pass creates:

- `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/pre_start.md`
- `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/prd.md`
- `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/tech-plan.md`

After Engineer execution, Product must update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`


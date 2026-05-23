# Verified Terminal Result Material Owner Response Reviewer ACK Follow-up Escalation Status PRD

Run time: 2026-05-24 02:03 Asia/Shanghai

## Product North Star

真实证据优先。机器人、手机和云链路只有在真实外部材料、真实 field evidence 或 HIL 到位后才能推进 OKR 或控制能力；Docker-only 主机上的输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## User Value

现场 owner 和 reviewer 当前需要知道：哪个真实材料 blocker 仍 unresolved、谁负责补、什么时候 due/overdue/escalated、下一份证据必须是什么、哪些状态绝不能被读成 delivery success 或 OKR progress。`verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status` 的价值是让 follow-up 从“聊天里提醒”变成 PC gate、Robot diagnostics、mobile read-only panel 都能复账的 fail-closed 状态。

## Problem Statement

Objective 5 约 68%，仍是 `OKR.md` 4.1 最低 Objective。上一轮 `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff` 已把 reviewer ACK review-decision 转成 handoff metadata，但 latest final 明确 `Do not repeat another local-only metadata wrapper as OKR progress`。

当前 Docker-only 主机没有真实硬件、真实 4G/公网/OSS/CDN/生产 DB/queue、真实手机浏览器、真实 route/elevator field 或 HIL。因此本轮不能提升 OKR 百分比，不能声称 PR #5 resolved，也不能把本地 follow-up status 当成 real terminal result。

## OKR Mapping

- Objective 5：最低目标，约 68%。本轮只建立 follow-up escalation status gate，用来暴露 real external/material evidence 缺口；`no OKR percentage lift`。
- Objective 1：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`。本轮只引用缺口，不证明 2D LiDAR / ToF、WAVE ROVER、UART 或 HIL。
- Objective 2/3：本轮不证明 route/elevator field pass、Nav2/fixed-route runtime pass、dropoff/cancel completion、delivery result 或 delivery success。
- Objective 4：本轮 mobile 只能展示 read-only fail-closed panel，不证明 true phone/browser proof、production app、PWA prompt 或 iPhone/Android device behavior。

## KR Breakdown

KR1 Autonomy / PC evidence gate:

- Implement `verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status` as a deterministic PC gate.
- Consume prior reviewer ACK review-handoff material or a safe fixture.
- Emit `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate`.
- Require `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, unresolved PR #5 blocker, owner/reviewer route, due/overdue/escalated state, and next required evidence.

KR2 Robot diagnostics safe alias:

- Surface a sanitized Robot diagnostics alias for the PC summary.
- Preserve read-only and fail-closed behavior.
- Exclude raw artifacts, credentials, ROS topics, `/cmd_vel`, UART/serial details, complete raw JSON, local paths, ACK mutation hints, and control/action hints.

KR3 Full-Stack mobile read-only panel:

- Add a mobile panel for the escalation status.
- Show blocker status, owner/reviewer routes, due/overdue/escalated state, next evidence, and safe copy.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.

KR4 Product closeout:

- After engineers return evidence, update `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md`.
- Preserve `no OKR percentage lift` unless real external/material evidence arrives.

## Core Product Grip

The gate must answer one operational question: "What real material is still blocking Objective 5 / PR #5 progress, who owns it, and is the follow-up pending, due, overdue, or escalated?"

It must not answer or imply:

- real terminal result exists
- O5 external proof exists
- true phone/browser proof exists
- PR #5 `PRRT_kwDOSWB9286CJ3tX` is resolved
- route/elevator field pass exists
- HIL exists
- delivery success exists
- robot is safe to control

## Priority And Acceptance Criteria

P0:

- All outputs carry `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`.
- The gate has explicit follow-up states and next required evidence.
- The UI and diagnostics are read-only and sanitized.

P1:

- Owner route, reviewer route, support route, escalation reason, due/overdue/escalated status, and safe `evidence_ref` are visible across PC summary, Robot diagnostics, and mobile panel.
- Tests prove unsafe copy, success wording, missing blocker identity, control flags, raw artifacts, credentials, and command hints fail closed.

P2:

- Product closeout captures why this is useful operationally but not OKR progress.
- Future real-material intake path is explicit enough for the next owner to act without another planning round.

## Responsible Engineers

- Autonomy Algorithm Engineer: PC evidence gate and tests.
- Robot Platform Engineer: diagnostics safe alias and tests.
- User Touchpoint Full-Stack Engineer: mobile read-only panel, fixture, and tests.
- Product Manager / OKR Owner: closeout docs and OKR/process log after implementation evidence exists.

## Evidence Chain And Remaining Risks

Required evidence still missing:

- Objective 5: real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/migration/cutover, true phone/browser proof, verified terminal delivery/dropoff/cancel result.
- Objective 1 / PR #5: real 2D LiDAR / ToF SKU/source/receipt, procurement, mounting, wiring, power, calibration, HIL entry, Nav2/SLAM field pass, reviewer resolution.
- Objective 2/3/4: real route/elevator field pass, Nav2/fixed-route runtime, route completion signal, real phone/browser, delivery result, delivery success.

Remaining risk: this sprint can improve coordination and prevent unsafe claims, but it cannot move OKR percentages until real evidence arrives.

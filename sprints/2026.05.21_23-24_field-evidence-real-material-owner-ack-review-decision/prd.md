# Field Evidence Real Material Owner Ack Review Decision PRD

## 1. 用户价值和产品北极星

用户价值：现场 owner acknowledgement 不是验收结论。支持人员需要一个明确的 review decision，把已收到的 owner ack 分成 `accepted`、`needs_more_evidence` 或 `rejected`，并告诉下一步该补什么材料、谁负责、是否仍保持 fail-closed。

产品北极星：普通用户只需要手机看到清晰、保守、可解释的材料复核状态；工程和支持人员用同一 safe `evidence_ref` 回填真实 task record、route/elevator logs、door/floor evidence、dropoff/cancel completion 和 true phone/browser proof。所有软件证明必须继续和真实现场通过分开。

## 2. 问题定义

上一轮 `field_evidence_real_material_owner_ack_intake` 已经能记录 owner acknowledge 了材料升级请求，但 ack 本身仍无法回答三个问题：

1. owner 提供或承诺的材料是否结构上足够进入下一步 review/backfill？
2. 还缺哪些真实材料，缺口是否阻塞 O2/O3/O4 的现场材料链？
3. 手机和 Robot diagnostics 应该如何展示这个状态，才能避免把 acknowledgement 写成真实 delivery success？

本轮不解决真实材料本身，而是补齐 ack 后的决策层。

## 3. OKR 映射

- Objective 5：当前约 68%，最低，但本轮不针对 O5。继续提高 O5 必须有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser external proof。`cloud_ack_lookup_pending_status_guard` 已覆盖 distinct local read-side pending state，不能继续用同类本地 metadata wrapper 提高 O5。
- Objective 2：为真实送垃圾 / 电梯 assisted delivery 的现场材料链提供 review decision 入口；仍不证明真实送达、真实电梯、dropoff/cancel completion、delivery result 或 delivery success。
- Objective 3：为 route completion signal、Nav2/fixed-route runtime log 和 task record 的同一 safe `evidence_ref` 复核做入口；仍不证明真实路线实跑。
- Objective 4：为手机端提供只读、中文优先、fail-closed 的 owner ack review decision panel；仍不证明真实 iPhone/Android browser、production app 或 PWA prompt。
- Objective 1：不推进。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false`，真实 2D LiDAR / ToF vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺。

## 4. KR 拆解或更新

### KR1: Structured Review Decision

输入：上一轮 owner ack intake artifact 或 fixture，包含 owner、ack status、safe `evidence_ref`、claimed materials、missing material groups 和 owner next action。

输出：`trashbot.field_evidence_real_material_owner_ack_review_decision.v1` artifact / summary，decision 只允许：

- `accepted`: materials are structurally acceptable for the next software-proof review/backfill step, not field pass.
- `needs_more_evidence`: ack is valid but material groups remain missing.
- `rejected`: ack is invalid, unsafe, stale, mismatched, or contains success/HIL/external-proof claims.

所有输出必须固定：`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

### KR2: Robot Diagnostics Safe Summary

Robot diagnostics must expose a safe alias such as `robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary` with only phone-safe fields:

- `review_decision`
- `safe_evidence_ref`
- `source_ack_status`
- `decision_reasons`
- `missing_required_materials`
- `next_required_evidence`
- `owner_handoff`
- `proof_boundary`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

It must not expose raw artifacts, credentials, local paths, serial/UART details, WAVE ROVER details, ROS topics, `/cmd_vel`, complete logs, checksums, HIL/pass wording, delivery success, or PR #5 resolved claims.

### KR3: Mobile Read-Only Panel

`mobile/web` must show a read-only panel for the review decision. It may render decision, safe evidence ref, missing materials, owner handoff, and next required evidence. It must keep Start Delivery / Confirm Dropoff / Cancel disabled and must not trigger ACK, cursor, diagnostics fetch, review routes, material routes, or robot commands.

### KR4: Hardware Boundary Consultation

Hardware Infra must only consult `docs/vendor/VENDOR_INDEX.md`, local vendor source boundaries, production hardware boundary docs, and PR #5 thread state. Unless a strict documentation correction is required, no implementation changes are expected from Hardware in this sprint.

## 5. 本轮核心抓手

把 owner ack 从“收到升级请求”推进到“复核决策”。这能减少现场材料链卡在 acknowledgement 层，也能让下一轮真实材料 backfill / rerun 有明确输入要求。

## 6. 需要做什么

1. Autonomy builds the PC gate and tests.
2. Robot adds diagnostics safe summary and tests.
3. Full-Stack adds mobile/web read-only panel, fixture, tests, and product docs.
4. Hardware performs read-only vendor / PR #5 boundary consultation.
5. Product later closes `tech-done.md`, `side2side_check.md`, `final.md`, and decides whether `OKR.md` / `docs/process/okr_progress_log.md` should record software-proof progress without percentage inflation.

## 7. 优先级和验收口径

P0 acceptance:

- The review decision vocabulary is exactly `accepted`, `needs_more_evidence`, `rejected`.
- Accepted does not mean true material arrival, route/elevator field pass, HIL, delivery success, Objective 5 external proof, true phone/browser proof, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved.
- Missing or unsafe fields fail closed to `needs_more_evidence` or `rejected`.
- All PC / Robot / mobile outputs preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Mobile and diagnostics copy filters raw technical or sensitive material.
- Hardware consultation cites `docs/vendor/VENDOR_INDEX.md` and confirms no hardware proof claim.

P1 acceptance:

- Docs under `docs/` are updated by implementation owners to explain the new boundary.
- Tests cover positive and negative paths.
- Final closeout explicitly says whether O5 remains about 68% and why this sprint does not increase O5.

## 8. 对应责任 Engineer

- Autonomy Algorithm Engineer: `pc-tools/evidence/field_evidence_real_material_owner_ack_review_decision.py`, related test file, and PC evidence docs.
- Robot Platform Engineer: onboard behavior diagnostics safe alias / summary, diagnostics tests, and `docs/interfaces/ros_contracts.md` or equivalent interface docs.
- User Touchpoint Full-Stack Engineer: `mobile/web` app fixture / panel / tests and `docs/product/mobile_user_flow.md`.
- Hardware Infra Engineer: read-only consultation over `docs/vendor/VENDOR_INDEX.md`, local vendor boundaries, and PR #5 material state.

## 9. 风险、阻塞和需要补齐的证据链

- Real O5 evidence remains absent: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved until true 2D LiDAR / ToF source, receipt, procurement, installation, wiring, power, calibration, and HIL-entry evidence exists and reviewer resolves it.
- O2/O3/O4 still need true task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor evidence, human-assistance note, dropoff/cancel completion, delivery result, true phone/browser evidence, and route/elevator field pass under the same safe `evidence_ref`.
- This sprint can be accepted only as Docker/local software proof; it must not change hardware, move the robot, enable primary controls, or claim delivery success.

## 10. 需要创建或更新的 sprint 文档

- Already created in planning: `pre_start.md`, `prd.md`, `tech-plan.md`.
- Required after implementation: `tech-done.md`, `side2side_check.md`, `final.md`.
- If implementation lands, Product must review whether `OKR.md` and `docs/process/okr_progress_log.md` need conservative software-proof updates.

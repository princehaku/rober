# Mobile Current Panel Browser Proof Refresh Latest Field Evidence PRD

Run time: 2026-05-23 09:07 Asia/Shanghai

## 1. 用户价值和产品北极星

普通手机用户不应该看到过期的 current-panel 证据覆盖范围。最新 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake` 已经落到 `mobile/web`，但当前 browser proof refresh 仍停在 2026-05-22 的 panel 集合；这会让 support 无法用 fresh browser proof 证明最新现场证据 ACK intake 在手机入口中可见且 fail closed。

产品北极星：手机端必须成为普通用户理解机器人是否可控、是否需要等待或联系支持的唯一入口。本轮只证明本地 Docker/local `mobile/web` fresh-profile browser proof 能覆盖最新 read-only panel，并保持 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`；它是 `not true phone/browser`。

## 2. OKR 映射

- Objective 4：主映射。本轮补齐手机入口 current-panel browser proof 对最新 field-evidence panel 的覆盖，属于 O4 手机用户体验和安全展示边界。
- Objective 5：最低 Objective，当前约 68%，但本轮不直接推进 O5。缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal delivery/dropoff/cancel result 时，不能继续堆 O5 metadata depth，也不能提升 O5 百分比。
- Objective 1：当前约 81%，本轮不推进。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，本轮不碰硬件、不声称 PR #5 resolution。
- Objective 2 / Objective 3：本轮不修改 task_orchestrator、route/elevator、Nav2/fixed-route runtime、delivery/dropoff/cancel result。

## 3. KR 拆解或更新

本轮不改 `OKR.md` KR 文本，不提升任何 Objective 百分比，除非后续 closeout 阶段出现真实外部/手机/硬件/现场材料。KR-like 可交付项如下：

- Capability: `mobile_current_panel_browser_proof_refresh_latest_field_evidence`
- Boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`
- Required latest panel: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake`
- Required blocked flags: `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`
- Required non-claim: `not true phone/browser`

## 4. 本轮核心抓手

1. Full-Stack 让 `phone_browser_acceptance_gate.py` 和 mobile tests 覆盖最新 field-evidence reviewer ACK intake panel，并产出 fresh-profile browser evidence。
2. Robot 只读核查 `mobile/web` current panel 所消费的 Robot diagnostics summary 是否仍是 phone-safe，不暴露 raw ROS/control/hardware/secret/path/traceback/checksum/完整 artifact。
3. Product 在 closeout 时只接受 `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`，并在无真实材料时保持 no OKR percentage lift。

## 5. 需要做什么

- 刷新 current-panel browser gate 对最新 `mobile/web` panel 的覆盖。
- 确认 Start Delivery / Confirm Dropoff / Cancel 在 blocked / not_proven fixture state 下继续禁用。
- 更新 `docs/product/mobile_user_flow.md`，说明 latest field-evidence reviewer ACK intake panel 的 phone-safe 展示边界。
- 将 browser proof evidence 写入本 sprint `evidence/`。
- 后续 closeout 创建并更新 `tech-done.md`、`side2side_check.md`、`final.md`，再按证据判断是否更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

Priority P0:

- Browser gate 必须在 fresh profile 下检查 latest field-evidence panel。
- 必须确认 `software_proof_docker_mobile_current_panel_browser_proof_refresh_latest_field_evidence_gate`。
- 必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 必须明确 `not true phone/browser`。

Priority P1:

- Robot diagnostics summary 只读核查必须确认 panel 不暴露 raw ROS topic、`/cmd_vel`、hardware params、secret、local path、traceback、checksum、完整 artifact。
- Product closeout 必须写清 Objective 5 不提升、Objective 1 不提升、PR #5 `PRRT_kwDOSWB9286CJ3tX` 不关闭。

## 7. 对应责任 Engineer

- Task A: `full-stack-software-engineer`
- Task B: `robot-software-engineer`
- Task C: `product-okr-owner`

## 8. 风险、阻塞和需要补齐的证据链

- O5 风险：当前无 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal delivery/dropoff/cancel result；本轮不能作为 O5 external proof。
- O1 风险：`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`；本轮不补真实 2D LiDAR / ToF、WAVE ROVER、UART、HIL、operator report。
- O2/O3/O4 风险：本轮不证明真实 route/elevator field pass、真实 Nav2/fixed-route runtime、真实 dropoff/cancel completion、delivery result 或真实手机设备验收。
- Browser 风险：如果 gate 通过，只能说明 local Chromium-family fresh-profile software proof 通过；不是真实 iPhone/Android、不是真实 PWA prompt/userChoice、不是 production app。

## 9. Sprint 文档计划

本规划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现/验收阶段创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- 必要时更新 `OKR.md` 与 `docs/process/okr_progress_log.md`；若无真实外部/手机/硬件/现场材料，no OKR percentage lift。


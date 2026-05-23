# Field Evidence Rerun Reviewer ACK Owner Response Intake Bridge Pre-start

Run time: 2026-05-24 03:04 Asia/Shanghai

## Sprint Type

sprint_type: epic

## User Value And Product North Star

用户价值：现场 owner、reviewer 和 support 已经看到上一轮 reviewer ACK follow-up escalation status，但真实 O2/O3/O4 route/elevator/dropoff/cancel/phone materials 仍没有回到 owner response intake 主链。本轮要把这个 safe source bridge 接回主链，让现场 owner 明确回填同一 safe `evidence_ref` 的真实 task record、dropoff/cancel completion、Nav2/fixed-route runtime log、route completion signal、电梯门状态、楼层确认、人工协助记录、delivery result、route/elevator field pass 和真实手机/browser 证据。

产品北极星：小车只在真实可验证证据到位时推进 OKR 和控制能力；Docker/local bridge 只能让材料回流路径更清楚，必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## OKR Mapping

- 当前 `OKR.md` 4.1 最低 Objective 是 Objective 5，约 68%。
- Objective 5 只有拿到真实外部材料时才继续 completion：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal delivery/dropoff/cancel result。
- Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，仍缺真实 2D LiDAR / ToF SKU/source/receipt、安装、接线、标定、HIL-entry、WAVE ROVER powered bench/UART/HIL logs。
- O5 外部材料和 O1 真实硬件材料当前都不可用，因此本轮转入 Objective 2/O3/O4 现场 owner material re-entry bridge。
- Capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`。
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`。

## Latest Evidence Inputs

- 自动化记忆记录上一轮 `sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status/` 已完成，commit `de88884` 已推送。
- 最新 `OKR.md` 第 6 节明确：不要用本地 O5 metadata depth 重复消费 Objective 5；没有真实 O5 外部材料时不得提升 O5。
- 最新 `OKR.md` 第 6 节也明确：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍需要真实硬件材料；本机只有 Docker，不能 claim HIL、WAVE ROVER UART、LiDAR/ToF installed proof 或 PR resolved。
- 近期已有 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`；尚缺把该 reviewer ACK follow-up safe source 接回 owner response intake 主链的 bridge。
- 既有类似模式是 `field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge`：不是新控制面，而是让 owner-response intake 接受 safe reviewer ACK follow-up source 并输出 `source_bridge`。

## Core Product Hook

本轮核心抓手：把上一轮现场 reviewer ACK follow-up escalation status 作为 safe source bridge 接入既有 owner response intake 主链，要求现场 owner 回填真实 O2/O3/O4 route/elevator/dropoff/cancel/phone materials。

必须表达：

- `source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`。
- 同一 safe `evidence_ref` 必须贯穿 follow-up source、owner response intake 和后续真实材料。
- 输出是 Docker/local fail-closed bridge，不是 route/elevator field pass、真实手机/browser、dropoff/cancel completion、delivery result 或 OKR uplift。
- PC、Robot diagnostics 和 `mobile/web` 都只能显示 sanitized summary；Start Delivery、Confirm Dropoff、Cancel 等主操作保持 disabled。

## Sprint Scope

本轮 planning 拆成四个 owner，后续实现必须并行启动 3 个 Engineer，并由 Product 只做收口：

- Autonomy Engineer：扩展 PC gate `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py`、focused tests 和接口文档。
- Robot Engineer：扩展 `operator_gateway_diagnostics.py`、diagnostics tests 和接口/产品文档，让 safe alias 可见 `source_bridge`。
- Full-Stack Engineer：扩展 `mobile/web` read-only owner response intake panel、fixture、tests 和产品文档，展示 bridge summary 但主操作保持 disabled。
- Product/OKR：实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，不改百分比。

## Out Of Scope

- 本 planning pass 禁止改产品代码、测试代码、`OKR.md`、`docs/process/okr_progress_log.md`、closeout docs 或既有 sprint 文档。
- 不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、HIL、真实 WAVE ROVER/UART、真实 2D LiDAR/ToF、真实 route/elevator field pass、真实投放、dropoff/cancel completion、delivery result 或 delivery success。
- 不启用控制、不新增命令路径、不上传材料、不请求 GitHub mutation、不关闭 PR #5 thread、不改变 OKR 百分比。

## Risks And Blockers

- Real OKR movement remains blocked by missing external/material evidence, not by missing local schema.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` cannot be closed without real 2D LiDAR / ToF and HIL-entry evidence or reviewer action.
- Bridge 只能帮助现场 owner 重新进入材料回填主链；如果没有真实 owner response materials，后续仍会停在 `not_proven`。
- Mobile read-only panel 必须避免用户把 bridge summary 理解成真实路线、电梯、手机或投放完成。

## Required Sprint Documents

This planning pass creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Future implementation must create/update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`

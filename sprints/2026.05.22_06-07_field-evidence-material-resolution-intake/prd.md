# Field Evidence Material Resolution Intake PRD

Run time: 2026-05-22 06:07 Asia/Shanghai

## Product Problem

项目已经把真实外部云、硬件/HIL、route/elevator/phone field-material 缺口升级为 blocker escalation pack，也已经把 terminal-result material intake 推进到 review-decision metadata。但现在缺少一个“resolution intake”层：当 field owner 提供一个 safe resolution packet 时，系统还不能用同一 safe `evidence_ref` 把它和原 blocker escalation artifact/summary/Robot alias 对齐复核。

如果继续新增 missing-material wrapper，产品价值很低：用户仍看不到哪些材料被接受、哪些仍缺、哪些被拒绝、哪些因 unsafe/mismatch blocked。下一步应把 blocker 转成可消费的 resolution intake，而不是继续包装缺口。

## User Value And North Star

用户价值：support / field owner 能提交一个安全、脱敏的 resolution packet，并看到它是否真正解决了此前 blocker；手机端只读显示当前 resolution status 和下一步证据要求。

产品北极星：普通手机用户只看到安全、明确、可行动的现场材料状态；任何未被同一 safe `evidence_ref` 证明的材料都不能开启控制动作、不能写成 delivery success、不能提升真实外部云/HIL/field pass 口径。

## OKR Mapping

| Objective | Mapping | Product Decision |
| --- | --- | --- |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 当前最低，约 68%。本轮可消费 O5 external blocker escalation 和 owner resolution packet，但 Docker-only 环境不能证明 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 terminal result。 | 针对最低 Objective 的材料 intake path，但不提升完成度，除非后续真实外部材料被提供并通过 same safe `evidence_ref` 复核。 |
| Objective 1：硬件协议可信底盘 | 约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`，要求 mandatory sensor assumptions 引用 vendor sources。 | Hardware 只读咨询 PR #5/vendor source 边界；不改硬件配置，不宣称 HIL、WAVE ROVER/UART 或 reviewer resolution。 |
| Objective 2/3/4：送达、电梯、导航、手机 | 均约 99%，但仍缺真实 field rerun、真实手机/browser、真实 route/elevator materials、真实 terminal delivery/dropoff/cancel result。 | 允许把 route/elevator/phone safe resolution packet 进入 intake，但只输出 `software_proof` / `not_proven` read-only summary。 |

## KR Breakdown

### KR-A Autonomy PC Gate

- Build `field_evidence_material_resolution_intake` PC evidence gate.
- Inputs: blocker escalation artifact/summary/Robot alias + owner-provided safe resolution packet.
- Required checks: supported schema, safe source, same safe `evidence_ref`, no raw artifacts, no local paths, no credentials, no `/cmd_vel`, no ROS topics, no serial/UART details, no success/control claims.
- Output: sanitized summary with decision `accepted`、`missing`、`rejected`、`blocked` plus `next_required_evidence`, `owner_handoff`, `proof_boundary=software_proof_docker_field_evidence_material_resolution_intake_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.

### KR-B Robot Diagnostics Alias

- Expose `robot_diagnostics_field_evidence_material_resolution_intake_summary` in `operator_gateway_diagnostics.py`.
- Preserve read-only behavior on `/api/status` and `/api/diagnostics`.
- Fail closed on unsafe copy, missing source summary, evidence-ref mismatch, truthy action/control/success flags, raw artifact leakage, or unsupported schema.

### KR-C Full-Stack Mobile Panel

- Add read-only mobile/web panel consuming Robot safe alias first, then compatible summary fallback.
- Panel must show resolution decision, safe evidence ref, accepted/missing/rejected/blocked summaries, next required evidence, owner handoff, evidence boundary, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Start Delivery、Confirm Dropoff、Cancel must stay disabled; panel must not fetch raw diagnostics or add control routes.

### KR-D Hardware Boundary Consultation

- Hardware owner reads `docs/vendor/VENDOR_INDEX.md` and PR #5-related local docs only to confirm source-boundary wording for `PRRT_kwDOSWB9286CJ3tX`.
- No hardware config, no launch params, no serial/UART assumptions, no new vendor claim without local vendor source citation.
- Output is consultation text for implementation owners and Product closeout.

### KR-E Product Closeout

- After implementation workers finish, Product updates sprint `tech-done.md`、`side2side_check.md`、`final.md` and, if worker evidence is valid, updates `OKR.md` and process progress log conservatively.
- Product must keep Objective percentages unchanged unless real external/hardware/field evidence appears.

## Acceptance Criteria

- All surfaces use the same capability name: `field_evidence_material_resolution_intake`.
- All output is `software_proof` and `not_proven`.
- Required false-state flags remain exact: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Accepted materials mean “accepted for owner review / material resolution intake,” not delivery success, cloud proof, HIL, field pass, dropoff completion, cancel completion, or PR #5 thread resolution.
- Missing/rejected/blocked states give concrete `next_required_evidence` and owner handoff.
- Unsafe raw content is blocked, not displayed.
- Mobile panel remains read-only and does not enable primary actions.
- Robot diagnostics alias does not mutate ACK, cursor, command, ROS, Nav2, WAVE ROVER, HIL, or control state.

## Priority And Owner Routing

| Priority | Owner | Why |
| --- | --- | --- |
| P0 | Autonomy | PC gate defines canonical contract and test fixtures for all downstream consumers. |
| P0 | Robot | Robot diagnostics alias is the safe bridge from PC artifact to status/diagnostics surfaces. |
| P0 | Full-Stack | Mobile user value requires phone-safe read-only visibility without control enablement. |
| P1 | Hardware | PR #5 unresolved thread requires vendor-source boundary consultation, but no hardware config changes. |
| P1 | Product | Product closeout validates evidence boundaries and updates sprint/OKR records after workers. |

## Risks And Evidence Gaps

- No real owner resolution packet may exist during Docker-only implementation; fixture proof must remain `software_proof`.
- `accepted` could be misread as real proof; UI, diagnostics, docs and Product closeout must explicitly say accepted is not delivery success or Objective completion.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved until reviewer resolves it; local source alignment or resolution intake cannot close the thread.
- Real O5 progress still needs public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser or verified terminal result material.
- Real O1 progress still needs 2D LiDAR / ToF source/procurement/install/calibration and WAVE ROVER/UART/HIL evidence.

## Sprint Documents To Create Or Update

Current planning task creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Future implementation/closeout must create or update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- Implementation docs under `docs/interfaces/`, `docs/product/`, `pc-tools/README.md`, and diagnostics/mobile docs as assigned in `tech-plan.md`.

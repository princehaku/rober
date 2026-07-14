# Tech Plan - O3 Fixed Route Intent Replay Material

## Objective

`robot-algorithm-engineer` 单 owner 继续 O3/O1 strict no-motion，把 `2026.07.12_21-57` accepted same-run planner-only path proof 转成 fixed-route replay / route-intent material。

本 sprint 的输入事实是：

- `path_generation_attempted=true`
- `path_generated=true`
- `path_point_count=21`
- `fallback_mode=ros2_cli_action_send_goal`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- Product acceptance boundary: strict no-motion planner-only proof, not route execution.

不得无证据回退到 radar status、baudrate、map_server lifecycle、`/scan` timeout、graph timeout、O5 support-only 或 O6/O7 surface。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 / 当前推进区完成度最低的 Objective：O5，约 `85%`。
- 本 sprint 是否针对最低 Objective：否。
- 不针对 O5 的理由：O5 当前缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。继续做 local support-only、readiness packet、cutover checklist、external probe readback、handoff 或状态面板不会产生 `external_artifact_delta`，只会重复 `okr_credit_allowed=false`。
- 本 sprint 选择 O3/O1 strict no-motion 的理由：21:57 已证明 current same-run planner-only `path_generated=true`，当前最近可执行的 mission 台阶是把该 path proof 转成 fixed-route replay / route-intent material。它比继续 O5 support-only 更接近 route execution、delivery/operator acceptance 和 current live HIL。
- 收口复核口径：若本轮只产出 route-intent / replay material，O5/O1/O6/O7 百分比保持 flat，KR `不归档`；只有 route execution、delivery/operator acceptance、current live HIL 或 real production external evidence 进入 Product percentage review。

## Owner, Priority, And Role Split

- P0 owner: `robot-algorithm-engineer`.
- Product owner: `product-okr-owner` only for acceptance and final OKR wording.
- Robot Software: support only if source proof artifact schema, helper output path, or artifact field extraction blocks Algorithm.
- Hardware: not involved; no hardware config, UART, WAVE ROVER, serial, baudrate, wiring, voltage, firmware, or HIL work in this sprint.
- Full-stack: not involved; independent O7 surface/checklist/handoff is frozen for this sprint.

Priority order:

1. Consume 21:57 source path proof without rerunning motion/control actions.
2. Produce route-intent JSON summary with stable `route_intent_id` or `task_id`.
3. Produce replay JSONL or `route.csv` that preserves path order and planned pose/waypoint summary.
4. Preserve strict no-motion safety booleans false.
5. Emit next evidence required for route execution, delivery/operator acceptance, HIL, and production readback.

## Planned File Scope For Algorithm

Allowed implementation files:

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py` only if source artifact export needs a tiny, no-motion-compatible material writer or field normalization.
- `onboard/tests/test_nav2_runtime_proof_helper.py` only if the material writer is implemented in the helper.
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/tech-done.md`

Preferred artifact-only path:

- If source path proof already has enough fields, do not touch helper code. Create artifacts under this sprint and document the extraction/normalization in `tech-done.md`.

Product closeout files after implementation:

- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/side2side_check.md`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/final.md`

Forbidden without new Product routing:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 implementation files.
- UI/API/cloud/product code.
- Hardware config, UART, WAVE ROVER, ESP32, serial, baudrate, wiring, voltage, firmware, or vendor-backed hardware edits.
- Historical sprint files outside reading the 21:57 source proof.

## Interface Boundary

Algorithm may create only strict no-motion route material. The contract must keep these boundaries:

- Input boundary: accepted source path proof from `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/`.
- Output boundary: structured JSON summary plus replay JSONL or `route.csv`.
- Safety boundary: no movement, no manual base control, no route execution.
- Handoff boundary: next owner receives a `route_intent_id` / `task_id` plus `next_evidence_required`, not a claim of route success.

Required artifact fields or equivalent summaries:

- `route_intent_id` or `task_id`.
- `source_path_proof_ref`.
- `source_sprint`.
- `path_generation_attempted=true`.
- `path_generated=true`.
- `path_point_count=21`.
- `fallback_mode=ros2_cli_action_send_goal`.
- `planned_waypoint_summary` or `planned_pose_summary`.
- `route_replay_material_ref` or `route_csv_ref`.
- `route_intent_summary`.
- `strict_no_motion=true`.
- `safe_to_control=false`.
- `publishes_cmd_vel=false`.
- `calls_base_manual=false`.
- `uses_base_uart=false`.
- `robot_control_executed=false`.
- `route_execution_success=false`.
- `delivery_success=false`.
- `hil_pass=false`.
- `next_evidence_required`.

## Strict No-Motion 禁止项

This sprint is strict no-motion and must explicitly preserve:

- no /cmd_vel.
- no `/api/base/manual`.
- no NavigateToPose.
- no controller/BT execution.
- no WAVE ROVER UART.
- no route execution.
- no base manual relay.
- no safe-to-control claim.
- no delivery claim.
- no HIL pass claim.

Required false fields:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Implementation Plan

1. Source evidence intake: locate the 21:57 accepted source artifact and record its relative path, source sprint, artifact hash if practical, `path_point_count=21`, frame/start/goal fields, fallback mode, and no-motion false fields.
2. Route intent ID: create a stable `route_intent_id` or `task_id`, preferably derived from the sprint timestamp and source artifact name, without implying route execution.
3. Waypoint/pose summary: extract the generated path points into a compact ordered summary with frame, count, first pose, last pose, and any available goal/start metadata.
4. Replay material: write either replay JSONL or `route.csv`; both are acceptable if quick. The material should preserve route order and be easy for later O6/O7 consumers to ingest.
5. Summary JSON: write `route_intent_summary.json` with source proof ref, route material refs, no-motion false fields, next evidence required, and rejected claims.
6. Verification: run local checks that artifacts exist, have expected keys, preserve `path_generated=true` as source evidence, and keep route/delivery/HIL fields false.
7. Closeout: update `tech-done.md` with actual files, validation output, failure定位, remaining risk, and an explicit statement that this is route-intent material only.

## Acceptance Commands For Algorithm

Algorithm must run and report the following commands after implementation.

Artifact key inspection:

```bash
rg -n "route_intent_id|task_id|source_path_proof_ref|path_generated=true|path_point_count=21|fallback_mode=ros2_cli_action_send_goal|route_execution_success=false|delivery_success=false|hil_pass=false|strict no-motion|next_evidence_required" \
  sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material
```

If implementation touches Python helper/tests:

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

If implementation is artifact-only, run a structured artifact validation command chosen by Algorithm and record it in `tech-done.md`; examples include `python3 -m json.tool` on summary JSON and `wc -l` / header inspection for JSONL or CSV.

Scoped diff check:

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material
```

## Product Acceptance Gate

Accept as useful sprint progress only if one of these is true:

- Preferred: this sprint contains a JSON summary plus replay JSONL or `route.csv` with `route_intent_id` / `task_id`, source path proof ref, planned pose/waypoint summary, no-motion false fields, and next evidence required.
- Acceptable blocked: the blocker is narrower than “need route material” and identifies source artifact missing, schema drift, extraction failure, or writer failure with an exact next command.

Do not accept:

- O5 support-only/wrapper/readiness material.
- O6/O7 standalone surface/checklist/handoff.
- Repeating 21:57 final without new route-intent artifact.
- Claiming route execution, NavigateToPose, controller/BT, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART, delivery, HIL, safe-to-control, or production evidence.
- Any no-motion violation.

## OKR Success / Non-Success口径

Success for this sprint:

- A fixed-route / route-intent material packet exists and is internally consistent.
- Next evidence required is concrete enough to route the following sprint to route execution, delivery/operator acceptance, HIL, or production readback.
- Strict no-motion evidence remains clean.

OKR percentage result for normal success:

- Keep O5 about `85%`.
- Keep O1 about `94%`.
- Keep O6/O7 about `93%`.
- Do not archive KR: `不归档`.
- Record as O3/O1 supporting evidence only.

Non-success:

- If artifacts are missing or only repeat old final wording, send back to `robot-algorithm-engineer` for repair.
- If source artifact cannot be parsed, close only with a narrow parser/schema blocker and next command.
- If implementation accidentally claims route execution or delivery, Product must reject and request correction.

## Risks

- Source path proof may not expose every pose field needed for rich fixed-route semantics.
- A route-intent packet can still be too weak for execution if it lacks frame, timestamp, start, goal, or route order.
- `path_generated=true` remains source evidence only; it is not route execution.
- There is still no NavigateToPose, controller/BT, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART, route execution, delivery/operator acceptance, current live HIL, safe-to-control proof, true mobile/browser acceptance, or production external evidence.

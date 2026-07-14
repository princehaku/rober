# Final - O3 CLI Full Path Pose Export

## Acceptance Result

Product accepts this sprint as O3/O1 strict no-motion helper/export readiness plus historic artifact fail-closed proof.

- Sprint: `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_cli_full_path_pose_export_readiness_only`
- Product status: accepted with material boundary
- Direction judgment: continue O3/O1 strict no-motion; pause O5 support-only; do not create O6/O7 surface work until it consumes this or stronger mission material.
- OKR decision: O5 约 `85%`，O1 约 `94%`，O6/O7 约 `93%`，KR `不归档`.

## User Value And Product North Star

本轮用户价值是让后续 no-motion path capture 能直接输出 structured path poses，减少从 CLI 日志尾部人工补材料的风险。产品北极星继续是普通手机用户一键发车后得到可验证送达或失败结果；本 sprint 只完成路线执行前的 helper/export readiness，不是路线执行或送达闭环。

## Evidence Accepted

- Summary schema: `trashbot.cli_full_path_pose_export_summary.v1`.
- Future helper/export readiness: `cli_fallback_structured_path_pose_export_ready=true`.
- Sample parser proof: `path_structured_pose_count=2`, `path_preview_point_count=2`, `path_preview_frame_id=map`.
- Source artifact boundary: `historic_authoritative_path_point_count=21`.
- Historic materialized count: `historic_stdout_tail_structured_pose_count=14`.
- Historic missing lower bound: `historic_minimum_unmaterialized_path_pose_count=7`.
- Narrowed blocker: `historic_stdout_tail_truncated_full_pose_replay_unavailable=true`.
- Required next evidence: rerun strict no-motion live capture with updated helper to generate `path_structured_pose_count=21`.

## Rejected Claims And Safety Boundary

This sprint is not route execution, not NavigateToPose, not controller/BT execution, not `/cmd_vel`, not `/api/base/manual`, not WAVE ROVER UART, not delivery/operator acceptance, not HIL, not safe-to-control, and not production external evidence.

Safety fields remain fixed:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## OKR Mapping And Direction Judgment

- Continue: O3/O1 strict no-motion path-material lane, because the fixed-route chain still needs full structured path poses before replay or execution evidence can be evaluated.
- Pause: O5 support-only readiness/checklist/wrapper work, because O5 remains blocked on real external production evidence and stays about `85%`.
- Keep flat: O1 remains about `94%`; O6/O7 remain about `93%`.
- Do not archive KR: this is helper/export readiness and historic artifact fail-closed proof, not mission completion, route execution, delivery, HIL, safe-to-control, or production acceptance.
- Historical KR records remain in `OKR.md` and `docs/process/okr_progress_log.md`; this sprint adds a current progress note only.

## KR Breakdown And Archive Decision

- Current KR delta: future CLI fallback artifacts can carry structured poses when the full CLI output is available.
- Current KR blocker: old 21:57 artifact cannot be upgraded into full 21-pose structured material because only 14 complete stdout-tail pose blocks were saved.
- Archive decision: KR `不归档`; no current KR has crossed route execution, delivery, HIL, safe-to-control, or production evidence.
- Historical record location: `OKR.md` 4.1 current progress and `docs/process/okr_progress_log.md` 2026-07-13 series.

## Core Lever And Next Work

本轮核心抓手是 `robot-algorithm-engineer` 产出的 CLI stdout path-pose parser/export contract and historic fail-closed artifact. 下一轮优先级是 `robot-algorithm-engineer` 用更新后的 helper 重新跑 strict no-motion `ComputePathToPose` live capture，目标生成包含 `path_structured_pose_count=21` 的新 artifact。

Acceptance for that next sprint should still require no `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART, and all motion/control/delivery/HIL/safe-to-control fields false.

## Verification

Product acceptance verification:

- `python3 -m json.tool .../cli_full_path_pose_export_summary.json >/tmp/product_cli_full_path_pose_export_summary.pretty.json`: passed.
- Structured assertion check: printed `product_acceptance_cli_export_ok`.
- Anchor `rg`: hit helper readiness, historic fail-closed boundary, next `path_structured_pose_count=21`, O5/O1 percentages, KR archive decision, and false safety fields.
- Scoped `git diff --check`: no whitespace errors.

Algorithm verification accepted from `tech-done.md`:

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`: passed.
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`: `Ran 140 tests in 2.303s`, `OK`.
- Summary invariant check printed `cli_full_path_pose_export_summary_ok`.
- Implementation scoped `git diff --check`: passed.

## Remaining Risks

- The current sprint did not rerun a true-board live no-motion capture after helper changes, so there is not yet a new full 21 structured poses artifact.
- The old 21:57 source remains partial and cannot prove full 21-point replay.
- There is no route execution, no controller/BT run, no robot motion, no WAVE ROVER UART use, no delivery/operator acceptance, no current live HIL, no safe-to-control evidence, and no production external evidence.
- O5 still needs real external production evidence; O6/O7 need future consumer work against stronger mission material.

## Sprint Documents Updated

- Created `side2side_check.md`.
- Created `final.md`.
- Updated `OKR.md`.
- Updated `docs/process/okr_progress_log.md`.

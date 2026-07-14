# Side2Side Check - O3 CLI Full Path Pose Export

## Acceptance Result

Product accepts this sprint as O3/O1 strict no-motion helper/export readiness plus historic artifact fail-closed proof.

- Sprint: `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_cli_full_path_pose_export_readiness_only`
- Direction judgment: continue O3/O1 strict no-motion toward structured path material; keep O5 support-only work paused until real external production evidence exists.
- OKR decision: O5 约 `85%`，O1 约 `94%`，O6/O7 约 `93%`，KR `不归档`.

## User Value And Product North Star

用户价值是把 fixed-route 证据链从“只能读旧日志尾部”推进到“未来 live capture 可以直接导出 structured path poses”。产品北极星仍是普通手机用户一键发车后得到可验证送达或失败结果；本轮只是路线执行前的材料层修复，不是发车、路线执行或送达。

## Evidence Checked

| Check | Evidence | Product judgment |
| --- | --- | --- |
| Future CLI fallback export contract | `cli_fallback_structured_path_pose_export_ready=true` | Accept as helper readiness |
| Sample structured parse | `path_structured_pose_count=2`, `path_preview_frame_id=map` | Accept as parser/export proof only |
| Historic 21:57 replay boundary | `historic_authoritative_path_point_count=21`, `historic_stdout_tail_structured_pose_count=14`, `historic_minimum_unmaterialized_path_pose_count=7` | Accept fail-closed; do not fabricate missing poses |
| Historic truncation blocker | `historic_stdout_tail_truncated_full_pose_replay_unavailable=true` | Accept as narrowed next blocker |
| Next required artifact | rerun strict no-motion capture to produce `path_structured_pose_count=21` | Required before full structured route material claim |
| Safety invariant | `safe_to_control=false`, `route_execution_success=false`, `delivery_success=false`, `hil_pass=false` | Required and satisfied |

## Rejected Claims

This sprint is not route execution, not NavigateToPose, not controller/BT execution, not `/cmd_vel`, not `/api/base/manual`, not WAVE ROVER UART, not delivery/operator acceptance, not HIL, not safe-to-control, and not production external evidence.

Required false fields remain:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## OKR Mapping

- Continue: O3/O1 strict no-motion path-material lane, because it removes the export blocker that prevented full fixed-route replay material.
- Keep flat: O5 约 `85%`、O1 约 `94%`、O6/O7 约 `93%`; this sprint has no new live same-run full structured path material, route execution, delivery, HIL, or production evidence.
- Do not archive: KR `不归档`; this is helper/export readiness and historic artifact fail-closed proof only.
- Historical record: current progress is recorded in `OKR.md` 4.1 and detailed history in `docs/process/okr_progress_log.md`.

## Priority And Acceptance Criteria

Next priority is for `robot-algorithm-engineer` to rerun strict no-motion `ComputePathToPose` live capture with the updated helper. Acceptance for the next sprint should require a new artifact with `path_structured_pose_count=21`, false safety fields, and no motion/control path. Only after that can fixed-route replay move from partial material to full structured path material.

## Remaining Risks

- The old 21:57 artifact is still partial because saved stdout tail contains only 14 complete pose blocks.
- There is no route execution, no controller/BT run, no robot motion, no WAVE ROVER UART use, no delivery/operator acceptance, no current live HIL, and no safe-to-control evidence.
- O5 still needs real external production evidence; O6/O7 need future consumers of stronger mission material instead of surface/readback-only work.

# O6/O7 Localization Path Material Readback Pre-start

## Sprint Type

sprint_type: epic

## Context

O5 is still the lowest active Objective at about `85%`, but `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` already locked O5 behind `okr_credit_allowed=false` until real external production evidence appears. The current workspace still has no verified public HTTPS/TLS, 4G/SIM, production DB/queue, worker cutover, OSS/CDN live traffic, or real phone/browser material.

O1 is about `90%`, but the last three O1 runs have consumed historical same-run field material. `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/final.md` says the next valid O1 lift needs current same-run `feedback_T1001.log`, motion command record, operator/external observation, HIL acceptance, and current Nav2 path generation or route execution proof. Those current live/HIL artifacts are not present in this workspace.

This sprint therefore routes to O6/O7 to consume the latest O1 material delta: `localization_path_material_bridge` from `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json`. The goal is to make O6 archive/readback and O7 consumer/UI aware of the same-run localization/path readback, while keeping the proof boundary explicit: same-run localization was observed, same-run path generation failed, and this is not route execution success.

## Objective Routing

- Lowest active Objective: O5 `~85%`.
- O5 decision: not targeted because current run lacks real external production evidence; another local/support packet would repeat the same blocker and should not count toward OKR.
- Next lower Objective: O1 `~90%`.
- O1 decision: not targeted directly because current live/HIL material is unavailable; repeating historical material inside O1 would consume the same lane again.
- Targeted Objectives: O6/O7 `~91%`, as a cross-owner material-consumption sprint that brings the latest O1 localization/path delta into archive/readback and operator display.

## Owners

- `robot-algorithm-engineer`: add Algorithm manifest contract for `trashbot.localization_path_material_readback.v1`.
- `robot-software-engineer`: add O6 archive/readback/include support for the new material.
- `full-stack-software-engineer`: add O7 consumer contract/UI/test support for the new material.

## Evidence Boundaries

- Must keep `delivery_success=false`, `safe_to_control=false`, `primary_actions_enabled=false`, `robot_control_executed=false`, `route_execution_success=false`, `nav2_route_execution_success=false`, and `hil_pass=false`.
- Must preserve `same_run_path_generation_succeeded=false`, `same_run_path_generated=false`, `same_run_path_point_count=0`, and `same_run_path_proven=false`.
- June 11 clean-baseline path proof can only be shown as `cross_run_clean_baseline_*` comparator and must not override same-run false fields.


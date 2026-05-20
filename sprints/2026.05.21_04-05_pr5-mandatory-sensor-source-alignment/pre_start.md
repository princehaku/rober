# PR5 Mandatory Sensor Source Alignment Pre-start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_04-05_pr5-mandatory-sensor-source-alignment`
- Target capability: `pr5_mandatory_sensor_source_alignment`
- Evidence boundary: `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`
- Preserved states: `source=software_proof`, `hardware_material_pending`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning scope: create planning docs only. This step does not modify product code, test code, `OKR.md`, `docs/process/okr_progress_log.md`, or existing sprint files.

## User Value And Product North Star

The product north star remains a low-cost ROS2 trash delivery robot that ordinary phone users can operate without ROS2, SSH, serial tools, or hardware knowledge. This sprint advances that north star by removing ambiguity from mandatory sensing assumptions: any 2D LiDAR / ToF / monocular camera baseline must be traceable to local vendor-source boundaries and must stay separate from real procurement, wiring, calibration, HIL, field pass, or delivery proof.

The user value is practical review closure hygiene for PR #5 thread `PRRT_kwDOSWB9286CJ3tX`: an Engineer can implement an auditable source-alignment gate and downstream read-only surfaces that answer the review request without pretending real hardware materials exist.

## Required Evidence Inputs

- `OKR.md` 4.1 shows Objective 5 is the lowest Objective at about 68%, but this Docker-only host lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, and true phone/browser external proof.
- `OKR.md` 4.1 shows Objective 1 is next lowest at about 81%. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`, and the live review requirement asks for mandatory sensor assumptions to cite local vendor source.
- Latest sprint `2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff` closed as conservative software proof and explicitly said not to add another wrapper around the same missing field proof.
- `/Users/m4/.codex/automations/skill-progression-map/memory.md` records repeated stop rules: do not recycle blocked O5 external proof, O1 real hardware proof, or route/elevator real-material absence as a new name-only blocker.
- `docs/process/okr_progress_log.md` records that recent O2/O3/O4 field-evidence rungs only created metadata/software-proof handoffs; they do not prove real field rerun, HIL, true phone/browser proof, or delivery success.
- GitHub evidence supplied by the main session: PR #5 has unresolved thread `PRRT_kwDOSWB9286CJ3tX` requiring mandatory sensor assumptions to cite local vendor source. PR #6 has no review threads and is docs-only.

## Why This Sprint

Objective 5 remains numerically lowest, but the next meaningful O5 movement needs real external proof that is not available on this Docker-only host. Continuing another local O5 guard would repeat recent metadata/fail-closed work.

Objective 1 is the lowest actionable Objective because PR #5 has a concrete unresolved review thread and the requested action is source-alignment work that can be implemented and verified locally. This sprint still must not claim HIL, real 2D LiDAR / ToF procurement, installation, calibration, field pass, or reviewer resolution.

The sprint is epic because the implementation should span four disjoint owner surfaces: hardware source-alignment PC gate, Robot diagnostics safe alias, mobile read-only visibility, and Autonomy/Nav2 assumption documentation. That split lets the team move in parallel without overlapping file ownership.

## Owners And Parallel Plan

- Hardware Infra Engineer: owns the canonical source-alignment PC gate and product hardware boundary update.
- Robot Platform Engineer: owns Robot diagnostics safe alias for the alignment summary.
- User Touchpoint Full-Stack Engineer: owns the read-only mobile/web panel and phone-safe copy.
- Autonomy Algorithm Engineer: owns Nav2/fixed-route sensing-assumption boundary docs so route/SLAM wording cannot imply unproven sensor readiness.
- Product Manager / OKR Owner: owns this sprint planning and later conservative closeout, including `OKR.md` and progress log only after implementation lands.

## Risks, Blockers, And Evidence Gaps

- O5 cannot increase without real external cloud/mobile proof: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser evidence.
- O1 cannot increase on percentage until real 2D LiDAR / ToF SKU/source/receipt/procurement, mounting, wiring, power, calibration, HIL-entry, WAVE ROVER/UART/HIL, or reviewer resolution exists.
- `docs/vendor/VENDOR_INDEX.md` and the local vendor files are source-boundary evidence only. They do not prove that project 2D LiDAR or ToF hardware exists on the robot.
- PR #5 comment id `3269642220` is a reply artifact, not reviewer resolution.
- PR #6 is README/docs-only and must not be used as runtime, hardware, HIL, phone/browser, or O5 external proof.

## Sprint Documents To Create

- `pre_start.md`: this start record, evidence basis, owner split, and blocker boundary.
- `prd.md`: user value, OKR mapping, KR breakdown, priority, acceptance, and non-claims.
- `tech-plan.md`: implementation owner split, 文件范围, 验收命令, interface boundaries, and OKR 最低优先级核对.

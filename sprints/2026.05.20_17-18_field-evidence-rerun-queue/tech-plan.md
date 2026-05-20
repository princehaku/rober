# Field Evidence Rerun Queue Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.20_17-18_field-evidence-rerun-queue`
- Target capability: `field_evidence_rerun_queue`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_queue_gate`
- Required preserved states: `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers; no engineering code is implemented by this planning handoff.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, lower than Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint is not targeting Objective 5 directly.
3. Reason: Objective 5 currently needs real external proof that this Docker-only host does not have: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or real phone/browser external proof. Continuing local O5 metadata depth would repeat a blocked path and must not be used to claim O5 progress.
4. Next lowest actionable Objective: Objective 1 is about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending and manual reply `3269642220` is not hardware proof. The host lacks WAVE ROVER/UART/HIL and real 2D LiDAR/ToF material.
5. Chosen sprint target: O2/O3/O4 field-evidence rerun queue. The previous `field_evidence_rerun_handoff_intake` created owner-safe intake but still lacks real task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor/human assistance evidence, dropoff/cancel completion, delivery result, and real phone/browser evidence. A controlled rerun queue candidate is the next actionable software-proof step without weakening evidence boundaries.

## Evidence Inputs

- `OKR.md` 4.1 snapshot at 2026-05-20 16:25 Asia/Shanghai.
- `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/final.md`.
- Live GitHub PR #5 evidence: merged 2026-05-14; thread `PRRT_kwDOSWB9286CJ3tX` still `is_resolved=false`; review concerns included mandatory sensor baseline/vendor-source gaps and lowest-objective consistency.
- Live GitHub PR #6 evidence: merged 2026-05-20; README product narrative rewrite; testing was documentation diff/status only with no code/runtime/hardware tests.
- `docs/product/mobile_user_flow.md` phone-safe constraints: primary actions remain fail-closed unless command-safety and legacy gates allow them; read-only evidence panels must not expose raw control, credentials, local paths, complete artifacts, or success claims.

## Architecture And Contract

The implementation should add one metadata-only contract family:

- Artifact family: `field_evidence_rerun_queue`
- Suggested schema: `trashbot.field_evidence_rerun_queue.v1`
- Suggested summary schema: `trashbot.field_evidence_rerun_queue_summary.v1`
- Suggested Robot safe alias: `robot_diagnostics_field_evidence_rerun_queue_summary`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_queue_gate`

Expected minimum output fields:

- `schema`
- `schema_version`
- `source=software_proof`
- `queue_status`
- `safe_evidence_ref`
- `source_handoff_intake_schema`
- `source_handoff_intake_status`
- `same_evidence_ref_status`
- `blocker_summary`
- `next_required_evidence`
- `owner_handoff`
- `safe_copy`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `evidence_boundary=software_proof_docker_field_evidence_rerun_queue_gate`

The queue candidate may say that a controlled field rerun is ready to schedule only as metadata. It must not enable control, Start Delivery, Confirm Dropoff, Cancel, ACK/cursor fetches, or robot command side effects.

## Parallel Worker Plan

### Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical queue artifact.

Allowed file range for implementation:

- `pc-tools/evidence/field_evidence_rerun_queue.py`
- focused tests under `tests/` for the new PC gate
- evidence fixture/sample files only if needed for the new gate
- relevant docs under `docs/` describing the evidence contract
- current sprint implementation docs after code lands

Implementation requirements:

- Consume the previous `field_evidence_rerun_handoff_intake` artifact or safe summary.
- Validate same safe `evidence_ref`.
- Emit queue status, blockers, required field rerun materials, and owner handoff.
- Fail closed on missing handoff intake, schema mismatch, unsafe evidence ref, missing required state, or success/control claims.
- Preserve `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_queue.py
python3 -m unittest tests.test_field_evidence_rerun_queue
python3 pc-tools/evidence/field_evidence_rerun_queue.py --help
rg -n "field_evidence_rerun_queue|software_proof_docker_field_evidence_rerun_queue_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence tests docs sprints/2026.05.20_17-18_field-evidence-rerun-queue
git diff --check -- pc-tools/evidence/field_evidence_rerun_queue.py tests docs sprints/2026.05.20_17-18_field-evidence-rerun-queue
```

### Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range for implementation:

- Robot diagnostics/operator gateway files that already host safe aliases
- focused diagnostics tests under `tests/`
- relevant docs under `docs/`
- current sprint implementation docs after code lands

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_queue_summary` as a safe alias.
- Prefer canonical queue summary and reject raw/unsafe artifact material.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Preserve the same `software_proof_docker_field_evidence_rerun_queue_gate` boundary.
- Keep all existing diagnostics aliases compatible.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/operator_gateway_diagnostics.py
python3 -m unittest tests.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_rerun_queue_summary|field_evidence_rerun_queue|software_proof_docker_field_evidence_rerun_queue_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools tests docs sprints/2026.05.20_17-18_field-evidence-rerun-queue
git diff --check -- pc-tools tests docs sprints/2026.05.20_17-18_field-evidence-rerun-queue
```

### Worker 3: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel.

Allowed file range for implementation:

- `mobile/web/app.js`
- mobile fixtures under `mobile/fixtures/` or `mobile/web/fixtures/`
- focused mobile tests under `tests/`
- relevant mobile/product docs under `docs/`
- current sprint implementation docs after code lands

Implementation requirements:

- Add a read-only “现场证据复跑队列” panel.
- Prefer `robot_diagnostics_field_evidence_rerun_queue_summary`; fall back only to safe compatible summary fields already present in status/diagnostics payloads.
- Show queue status, safe `evidence_ref`, blocker summary, next required evidence, owner handoff, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, or robot command requests from the panel.
- Keep existing Start Delivery, Confirm Dropoff, and Cancel gating unchanged.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest tests.test_mobile_web_entrypoint
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/dev/null
rg -n "field_evidence_rerun_queue|software_proof_docker_field_evidence_rerun_queue_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑队列" mobile tests docs sprints/2026.05.20_17-18_field-evidence-rerun-queue
git diff --check -- mobile tests docs sprints/2026.05.20_17-18_field-evidence-rerun-queue
```

## Product Closeout Plan

Product closeout runs only after the three Engineer workers return changed files, validation snippets, failures if any, and remaining risk.

Closeout tasks:

- Update `sprints/2026.05.20_17-18_field-evidence-rerun-queue/tech-done.md`.
- Update `sprints/2026.05.20_17-18_field-evidence-rerun-queue/side2side_check.md`.
- Update `sprints/2026.05.20_17-18_field-evidence-rerun-queue/final.md`.
- Update `OKR.md` conservatively.
- Update `docs/process/okr_progress_log.md`.
- Confirm relevant `docs/` pages reflect any engineering changes.
- Confirm code technical comments added by Engineering are Chinese and meet the project comment-density rule where code was touched.

Product closeout acceptance commands:

```bash
test -f sprints/2026.05.20_17-18_field-evidence-rerun-queue/tech-done.md
test -f sprints/2026.05.20_17-18_field-evidence-rerun-queue/side2side_check.md
test -f sprints/2026.05.20_17-18_field-evidence-rerun-queue/final.md
rg -n "field_evidence_rerun_queue|software_proof_docker_field_evidence_rerun_queue_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_17-18_field-evidence-rerun-queue
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.20_17-18_field-evidence-rerun-queue
```

## Boundaries And Non-Claims

The implementation must not claim:

- real route/elevator field pass
- real Nav2/fixed-route runtime pass
- real task record
- real phone/browser validation
- real PWA prompt/userChoice
- WAVE ROVER/UART/HIL
- delivery success
- dropoff completion
- cancel completion
- O5 external proof
- public HTTPS/TLS proof
- 4G/SIM proof
- OSS/CDN live traffic proof
- production DB/queue or worker/cutover proof
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved

Manual reply `3269642220` must remain a published software-proof GitHub reply only.

## Planning Validation Commands

The planning handoff itself must pass:

```bash
test -f sprints/2026.05.20_17-18_field-evidence-rerun-queue/pre_start.md
test -f sprints/2026.05.20_17-18_field-evidence-rerun-queue/prd.md
test -f sprints/2026.05.20_17-18_field-evidence-rerun-queue/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_rerun_queue|software_proof_docker_field_evidence_rerun_queue_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" sprints/2026.05.20_17-18_field-evidence-rerun-queue
git diff --check -- sprints/2026.05.20_17-18_field-evidence-rerun-queue
```

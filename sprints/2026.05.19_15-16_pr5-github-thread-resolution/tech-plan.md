# Sprint 2026.05.19_15-16 PR5 GitHub Thread Resolution - Tech Plan

## OKR Lowest Priority Check

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 at about 68%.
2. This sprint does not target O5 because the latest OKR snapshot requires real external materials before further O5 completion movement.
3. Next lower Objective is Objective 1 at about 81%. This sprint targets Objective 1 evidence hygiene through PR #5 review-thread state, but does not claim real HIL or sensor material progress.
4. Objective 4 is kept as a read-only visibility side effect; no real phone/browser acceptance is claimed.

## Implementation Plan

1. Hardware worker verifies current mainline evidence:
   - `docs/vendor/VENDOR_INDEX.md`
   - `docs/product/production_hardware_boundary.md`
   - `OKR.md`
   - `pc-tools/evidence/pr5_review_thread_closeout_gate.py`
2. Main session resolves only the two ready GitHub review threads:
   - `PRRT_kwDOSWB9286CJ3tQ`
   - `PRRT_kwDOSWB9286CJ3tU`
3. Main session leaves `PRRT_kwDOSWB9286CJ3tX` unresolved because it is blocked by real 2D LiDAR / ToF materials.
4. Product worker updates:
   - `sprints/2026.05.19_15-16_pr5-github-thread-resolution/tech-done.md`
   - `sprints/2026.05.19_15-16_pr5-github-thread-resolution/side2side_check.md`
   - `sprints/2026.05.19_15-16_pr5-github-thread-resolution/final.md`
   - `OKR.md`
   - `docs/process/okr_progress_log.md`

## File Scope

Hardware worker may modify only this sprint folder if needed for its result note. It should not modify product code unless the gate fails.

Product worker may modify only:

- `sprints/2026.05.19_15-16_pr5-github-thread-resolution/**`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Acceptance Commands

Hardware worker:

```bash
test -f docs/vendor/VENDOR_INDEX.md
python3 -m py_compile pc-tools/evidence/pr5_review_thread_closeout_gate.py
python3 -m unittest tests/test_pr5_review_thread_closeout_gate.py
python3 pc-tools/evidence/pr5_review_thread_closeout_gate.py --output-dir sprints/2026.05.19_15-16_pr5-github-thread-resolution/evidence
rg -n "ready_to_close_on_mainline_docs|blocked_pending_real_materials|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.19_15-16_pr5-github-thread-resolution/evidence docs/product/production_hardware_boundary.md OKR.md
git diff --check -- pc-tools/evidence tests docs/product sprints/2026.05.19_15-16_pr5-github-thread-resolution
```

Product worker:

```bash
test -f sprints/2026.05.19_15-16_pr5-github-thread-resolution/tech-done.md
test -f sprints/2026.05.19_15-16_pr5-github-thread-resolution/side2side_check.md
test -f sprints/2026.05.19_15-16_pr5-github-thread-resolution/final.md
rg -n "Objective 5|Objective 1|PR #5|PRRT_kwDOSWB9286CJ3tQ|PRRT_kwDOSWB9286CJ3tU|PRRT_kwDOSWB9286CJ3tX|resolved|unresolved|blocked_pending_real_materials|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_15-16_pr5-github-thread-resolution
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_15-16_pr5-github-thread-resolution
```

## Risk Boundary

This sprint is GitHub review-state closeout plus repo evidence recording. It is not real 2D LiDAR / ToF procurement, install, wiring, calibration, HIL entry, WAVE ROVER UART proof, route/elevator field pass, real phone/browser acceptance, O5 external proof, dropoff/cancel completion, or delivery success.


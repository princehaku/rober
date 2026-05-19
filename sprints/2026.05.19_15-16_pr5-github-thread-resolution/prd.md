# Sprint 2026.05.19_15-16 PR5 GitHub Thread Resolution - PRD

## 1. User Value

The team needs PR/review feedback to match the repo evidence. If PR #5 review threads remain open after the repo has produced explicit ready-to-close decisions, sprint routing keeps re-reading stale review blockers. If a thread is still blocked by real materials, it must stay open so nobody mistakes documentation closeout for real 2D LiDAR / ToF, WAVE ROVER, HIL, or field evidence.

## 2. OKR Mapping

- Objective 5 remains the lowest numeric objective at about 68%, but is not locally actionable without real external proof.
- Objective 1 is the next actionable evidence hygiene lane because PR #5 review feedback is about hardware boundary and vendor/source attribution.
- Objective 4 is secondarily affected because mobile/product surfaces already display PR #5 closeout status, but this sprint is not real phone/browser acceptance.

## 3. Requirements

1. Re-run or verify `pr5_review_thread_closeout` against current mainline docs.
2. Resolve only GitHub PR #5 threads whose repo decision is `ready_to_close_on_mainline_docs`.
3. Keep the mandatory sensor real-material thread unresolved while it remains `blocked_pending_real_materials`.
4. Update sprint closeout and OKR/progress log with exact evidence boundary:
   - `software_proof`
   - `not_proven`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
5. Do not increase Objective 1, 4, or 5 percentages without real materials.

## 4. Acceptance

- GitHub PR #5 P1 hardware-boundary thread is resolved.
- GitHub PR #5 P2 OKR narrative/table thread is resolved.
- GitHub PR #5 P2 mandatory sensor citation/material thread remains unresolved and explicitly blocked on real materials.
- Sprint docs record commands, thread IDs, and the remaining real-material gap.


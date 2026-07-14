# Tech Plan - O5 Cloud External Evidence Review Decision

## Owner

Primary owner: `full-stack-software-engineer`

Rationale: the task spans `pc-tools/evidence` and the user/product-facing cloud relay contract. File scope is coupled around one O5 evidence contract, so a single owner should implement and validate it end-to-end.

## File Scope

Allowed implementation files:

- `pc-tools/evidence/cloud_external_evidence_review_decision.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- optional narrow interface doc under `docs/interfaces/` if needed
- `sprints/2026.07.13_22-20_o5_cloud_external_review_decision/tech-done.md`

Do not modify hardware, launch, Nav2, WAVE ROVER, UART, route execution, O7 UI, or unrelated historical sprint files.

## Implementation Plan

1. Add the missing review-decision CLI under `pc-tools/evidence/`.
2. Reuse existing fixture schema names and docs terminology:
   - `trashbot.external_evidence_intake`
   - `software_proof_docker_external_evidence_intake_gate`
   - `software_proof_docker_cloud_external_evidence_review_decision_gate`
   - `accepted_external_evidence_not_proven`
   - `needs_external_evidence_backfill_not_proven`
   - `rejected_unsafe_external_evidence_not_proven`
   - `blocked_missing_external_evidence_intake_not_proven`
   - `external_evidence_ref_mismatch_not_proven`
3. Keep outputs sanitized: no raw URLs, credentials, bearer tokens, local paths, DB/queue URLs, OSS secrets, response bodies, ROS/control paths, serial paths, or success/control claims.
4. Add relay helpers and CLI/preflight/cutover packet consumption for the review-decision artifact as a separate O5 source slot.
5. Update tests for the CLI and relay packet consumption.
6. Update docs and `tech-done.md` with actual changes, verification, and residual risk.

## Acceptance Commands

The owner must run these commands and paste key results into `tech-done.md`:

```bash
python3 -m py_compile pc-tools/evidence/cloud_external_evidence_review_decision.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
python3 pc-tools/evidence/cloud_external_evidence_review_decision.py --intake-json pc-tools/evidence/fixtures/cloud_external_evidence_review_decision/accepted_intake.json --evidence-ref external_evidence_ref_20260524_0001 --output /tmp/cloud_external_evidence_review_decision.json --summary-output /tmp/cloud_external_evidence_review_decision_summary.json
python3 -m json.tool /tmp/cloud_external_evidence_review_decision.json >/dev/null
python3 -m json.tool /tmp/cloud_external_evidence_review_decision_summary.json >/dev/null
rg -n "cloud_external_evidence_review_decision|software_proof_docker_cloud_external_evidence_review_decision_gate|accepted_external_evidence_not_proven" pc-tools/evidence onboard/src/ros2_trashbot_behavior docs/product sprints/2026.07.13_22-20_o5_cloud_external_review_decision
git diff --check -- pc-tools/evidence onboard/src/ros2_trashbot_behavior docs/product sprints/2026.07.13_22-20_o5_cloud_external_review_decision
```

## OKR Lowest Priority Check

Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about `85%`.

This sprint targets Objective 5 directly. It avoids repeating the latest O5 `blocked_http_status_not_success_class` blocker by not re-running the CDN/TLS probe. It instead closes a missing local review-decision executable and packet-consumption gap that can later accept stronger real external evidence.

This sprint is not expected to raise O5 percentage unless the owner actually consumes new success-class external production evidence. With current local-only evidence, closeout should stay flat and mark KR as `不归档`.

## Risk Boundary

This sprint must not claim:

- production cloud readiness
- public HTTPS/TLS success
- OSS/CDN live traffic
- production DB/queue
- worker cutover
- 4G/SIM
- real phone/browser proof
- route execution
- delivery/operator acceptance
- HIL
- safe-to-control

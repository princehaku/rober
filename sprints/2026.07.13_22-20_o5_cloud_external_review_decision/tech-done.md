# Tech Done - O5 Cloud External Evidence Review Decision

## Sprint Type

- sprint_type: epic
- Completed at: 2026-07-13 22:37 CST
- Owner: `full-stack-software-engineer`
- Proof boundary:
  - `software_proof_o5_cloud_external_evidence_review_decision_only`
  - `software_proof_docker_cloud_external_evidence_review_decision_gate`
  - `software_proof_docker_cloud_external_evidence_review_decision_gate` consumed by O5 cutover readiness packet

## Actual Changes

- Added `pc-tools/evidence/cloud_external_evidence_review_decision.py`.
  - Consumes sanitized `trashbot.external_evidence_intake` JSON and writes artifact schema `trashbot.cloud_external_evidence_review_decision.v1`.
  - Writes summary schema `trashbot.cloud_external_evidence_review_decision_summary.v1`.
  - Emits deterministic statuses:
    - `accepted_external_evidence_not_proven`
    - `needs_external_evidence_backfill_not_proven`
    - `rejected_unsafe_external_evidence_not_proven`
    - `blocked_missing_external_evidence_intake_not_proven`
    - `external_evidence_ref_mismatch_not_proven`
  - Keeps `production_ready=false`, `delivery_success=false`, `safe_to_control=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`, and `okr_credit_allowed=false`.

- Updated `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`.
  - Added constants, validator, and summary helper for `cloud_external_evidence_review_decision`.
  - Added direct preflight consumption via `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ARTIFACT` and `--cloud-external-evidence-review-decision-artifact`.
  - Added `cloud_external_evidence_review_decision` as an independent source slot in `trashbot.cloud_production_cutover_readiness_packet.v1`.
  - Kept the packet support-only: `production_ready=false`, `okr_credit_allowed=false`, `support_only_reason=no_real_production_external_evidence`, `proof_scope_class=software_proof_support_only`.

- Updated `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`.
  - Added a targeted regression for accepted review decision consumption in preflight and cutover packet.
  - Added fail-closed coverage for unsafe intake content without leaking URL/token/control-path markers.
  - Updated packet source slot count from 9 to 10.

- Updated product docs:
  - `docs/product/cloud_4g_infrastructure.md`
  - `docs/product/remote_4g_mvp.md`
  - Documented artifact schemas, CLI command, env/arg consumption, and support-only proof boundary.

## Interface Impact

- New CLI:

```bash
python3 pc-tools/evidence/cloud_external_evidence_review_decision.py \
  --intake-json <trashbot.external_evidence_intake.json> \
  --evidence-ref <expected_safe_evidence_ref> \
  --output <artifact.json> \
  --summary-output <summary.json>
```

- New relay env/arg:
  - `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ARTIFACT`
  - `--cloud-external-evidence-review-decision-artifact`

- O5 cutover readiness packet now has a `cloud_external_evidence_review_decision` artifact status slot. Accepted review material can become `software_proof_ready` inside that slot, but the packet remains `blocked_not_production_ready`.

## Verification Results

```bash
python3 -m py_compile pc-tools/evidence/cloud_external_evidence_review_decision.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

Result: passed.

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

Result: passed.

Key output:

```text
Ran 196 tests in 87.313s
OK
```

```bash
python3 pc-tools/evidence/cloud_external_evidence_review_decision.py --intake-json pc-tools/evidence/fixtures/cloud_external_evidence_review_decision/accepted_intake.json --evidence-ref external_evidence_ref_20260524_0001 --output /tmp/cloud_external_evidence_review_decision.json --summary-output /tmp/cloud_external_evidence_review_decision_summary.json
python3 -m json.tool /tmp/cloud_external_evidence_review_decision.json >/dev/null
python3 -m json.tool /tmp/cloud_external_evidence_review_decision_summary.json >/dev/null
```

Result: passed. Accepted fixture emitted `review_decision=accepted_external_evidence_not_proven`, `production_ready=false`, and `safe_to_control=false`.

Additional fixture smoke:

```text
needs_backfill -> needs_external_evidence_backfill_not_proven
mismatch -> external_evidence_ref_mismatch_not_proven
unsafe -> rejected_unsafe_external_evidence_not_proven
```

```bash
rg -n "cloud_external_evidence_review_decision|software_proof_docker_cloud_external_evidence_review_decision_gate|accepted_external_evidence_not_proven" pc-tools/evidence onboard/src/ros2_trashbot_behavior docs/product sprints/2026.07.13_22-20_o5_cloud_external_review_decision
```

Result: passed. Anchors found in the new CLI, relay contract, tests, docs, and sprint plan.

```bash
git diff --check -- pc-tools/evidence onboard/src/ros2_trashbot_behavior docs/product sprints/2026.07.13_22-20_o5_cloud_external_review_decision
```

Result: passed with no whitespace errors.

## Failure Location And Fix

- Initial targeted test passed, but the unit test printed the CLI summary JSON twice because it called the CLI `main()` directly.
- Fixed by wrapping the two CLI calls in `mock.patch("sys.stdout", new_callable=io.StringIO)` so the full required unittest output stays clean.
- Also tightened missing/unreadable intake handling so it emits `blocked_missing_external_evidence_intake_not_proven` instead of the unsafe-content state.

## Remaining Risk

- This is local/software-only review material. It does not prove production cloud, real public HTTPS/TLS, OSS/CDN live traffic, production DB/queue, worker cutover, 4G/SIM, true phone/browser acceptance, verified terminal result, route execution, delivery, HIL, or safe-to-control.
- O5 should remain about `85%`; no KR should be archived from this sprint alone.
- Next O5 progress still requires success-class real external evidence or a real production evidence packet that passes the same fail-closed review boundary.

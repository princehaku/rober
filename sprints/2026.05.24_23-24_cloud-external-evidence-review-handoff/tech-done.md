# Tech Done: cloud external evidence review handoff

- sprint_type: epic
- target capability: `cloud_external_evidence_review_handoff`
- upstream capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_gate`
- closeout result: `software_proof`, `not_proven`, `no OKR percentage lift`
- completed_at: 2026-05-24 23:17 Asia/Shanghai

## Actual Changes

Task A User Touchpoint Full-Stack Engineer completed the read-only phone/support handoff surface:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff.json`
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`

Task A added a `cloud_external_evidence_review_handoff` panel and fixture that consume `robot_diagnostics_cloud_external_evidence_review_handoff_summary`, show source review decision metadata, owner/support/reviewer handoff route, next required evidence, `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, and false-state flags. Start Delivery, Confirm Dropoff, Cancel, ACK/cursor mutation, artifact upload/download, raw diagnostics fetch, and robot-control paths remain disabled or absent.

Task B Robot Platform Engineer completed the Robot diagnostics safe alias:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Task B added `robot_diagnostics_cloud_external_evidence_review_handoff_summary` as a safe read-only diagnostics alias for sanitized handoff metadata. It preserves `cloud_external_evidence_review_decision`, `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.

## Planning Deviation

`tech-plan.md` named `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py` for Task B. During implementation, Robot corrected the target to `operator_gateway_diagnostics.py` because the existing safe alias family and diagnostics filtering live there. Product accepts this deviation because it matches the established runtime contract, avoids changing command/control paths, and keeps the result metadata-only.

## Validation Results

Task A worker validation reported:

```text
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff.json >/tmp/cloud_external_evidence_review_handoff_fixture.json
passed

python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_external_evidence_review_handoff
Ran 2 tests in 0.043s
OK

required rg
passed

scoped git diff --check
passed
```

Task B worker validation reported:

```text
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k cloud_external_evidence_review_handoff
Ran 1 test in 0.019s
OK

required rg
passed

scoped git diff --check
passed
```

Product closeout rerun:

```text
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff.json >/tmp/cloud_external_evidence_review_handoff_fixture.json
passed

python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_external_evidence_review_handoff
passed

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k cloud_external_evidence_review_handoff
passed

required rg
passed

scoped git diff --check
passed
```

## Evidence Boundary

This sprint is only `software_proof_docker_cloud_external_evidence_review_handoff_gate`. It is not true phone/browser proof, not O5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not verified terminal result, not HIL, not WAVE ROVER/UART proof, not route/elevator field pass, not PR #5 resolved, and not delivery success.

`PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless fresh live GitHub evidence proves otherwise. No fresh evidence was supplied during this closeout.

## Remaining Risks

- Objective 5 remains about 68%; no OKR percentage lift.
- Real public ingress/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, and field delivery proof are still missing.
- Objective 1 remains blocked on real 2D LiDAR / ToF materials, WAVE ROVER/UART/HIL evidence, and PR #5 reviewer resolution.
- Product did not run broad regression, Docker build, real phone/browser, real cloud, hardware, route/elevator, or delivery-success validation.

# O6 Worker Report - route_bag_evidence intake

## Worker

- role: `robot-software-engineer`
- sprint: `2026.07.09_17-00_o6_o7_route_bag_evidence_intake`
- report_time: `2026-07-09 17:36:22 CST`

## Actual changes

- Added O6 readback schema `trashbot.o6.route_bag_evidence.v1` for source schema `trashbot.route_bag_evidence.v1`.
- Added proof scope `software_proof_route_bag_evidence_intake_only` and `include=route_bag_evidence` allowlist support.
- Wired `route_bag_evidence` through field-evidence ingest, artifact-bundle ingest, archive task detail, `field_evidence`, `artifact_bundle`, consumer detail aliases, and explicit consumer include readback.
- Added fail-closed summaries for missing evidence, bad schema, bad proof_scope, dangerous true claims, path/root/token/raw/base64/credential URL, and unsafe topic text.
- Kept all safety fields false: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `robot_control_executed=false`.
- Updated O6 API docs with route bag evidence schema, fields, readback surfaces, and fail-closed rules.

## Changed files

- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`
- `/Users/m1/apps/rober/sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md`

## Validation

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - Result: passed.
  - Log: `Ran 158 tests in 56.274s OK`.
- `rg -n "route_bag_evidence|software_proof_route_bag_evidence_intake_only|include=route_bag_evidence|safe_to_control|delivery_success" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md`
  - Result: passed.
  - Log: `672` matching lines; output redirected to `/tmp/o6_route_bag_rg.txt` after the terminal-truncated full run confirmed exit code `0`.
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/artifacts/o6_worker_report.md`
  - Result: passed.
  - Log: no whitespace errors.

## Failure fixes during validation

- Fixed O6 re-sanitize path so already stored `trashbot.o6.route_bag_evidence.v1` readback is accepted and does not become `route_bag_evidence_schema_unsupported`.
- Fixed ready status handling so `local_mock_only` and `not_proven` remain boundary reasons without downgrading `ready_not_route_execution_proof`.
- Added safe-value key exceptions for `topic_count` and `sample_topic_names`; values remain sanitized short topic labels and `/cmd_vel` remains blocked.
- Fixed test task ids so sensitive marker cases keep `token` only inside the route bag evidence subpacket, where O6 should produce a blocked summary instead of rejecting the whole bundle.

## Remaining risks

- This is local/mock O6 archive/readback proof only; it does not prove production cloud, OSS/CDN, live Nav2 route execution, raw DB3 storage, robot movement, operator delivery confirmation, or delivery success.
- `sample_topic_names` are sanitized short labels; O6 intentionally does not return ROS message payloads, absolute DB3 paths, roots, credentials, raw bytes, or base64.
- Coordination needed with `robot-algorithm-engineer` for source generator field parity and `full-stack-software-engineer` for O7 display/consumer readiness.

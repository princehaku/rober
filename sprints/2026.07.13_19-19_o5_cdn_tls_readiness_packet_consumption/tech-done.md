# Tech Done - O5 CDN/TLS Readiness Packet Consumption

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/`
- Owner: `robot-software-engineer`
- Proof boundary: `software_proof_o5_cdn_tls_external_evidence_readiness_packet_consumption_only`
- Target Objective: O5 cloud relay productionization

## Actual Changes

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - Added `trashbot.o5.cdn_tls_external_evidence.v1` summary validation through `cdn_tls_external_evidence_artifact_summary`.
  - Added source slot `cdn_tls_external_evidence` to `trashbot.cloud_production_cutover_readiness_packet.v1`.
  - Added env/CLI entry points: `TRASHBOT_REMOTE_CLOUD_CDN_TLS_EXTERNAL_EVIDENCE_ARTIFACT` and `--cdn-tls-external-evidence-artifact`.
  - Kept 4xx material fail-closed with `blocked_http_status_not_success_class`; future 2xx/3xx material can only make the section `software_proof_ready`.
  - Preserved fixed false fields: `production_ready=false`, `okr_credit_allowed=false`, `delivery_success=false`, `safe_to_control=false`, `robot_control_executed=false`, `route_execution_success=false`, and `hil_pass=false`.
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - Added tests for consuming the 13:13 sanitized artifact, packet slot readback, future success-class bounded behavior, and hostile artifact fail-closed redaction.
  - Updated the existing cutover packet source-slot expectation from 8 to 9.
- `docs/interfaces/o5_cdn_tls_external_evidence_probe.md`
  - Documented packet/preflight consumption contract, env/CLI names, proof boundary, and 4xx fail-closed behavior.
- `docs/product/cloud_4g_infrastructure.md`
  - Documented the new `cdn_tls_external_evidence` packet slot and env/CLI usage.

## Verification Results

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

Result: passed with no output.

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

Result: `Ran 192 tests in 83.412s` and `OK`.

```bash
python3 -m json.tool sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/artifacts/cdn_tls_external_evidence_summary.json >/dev/null
```

Result: passed with no output.

```bash
rg -n "cdn_tls_external_evidence|TRASHBOT_REMOTE_CLOUD_CDN_TLS_EXTERNAL_EVIDENCE_ARTIFACT|blocked_http_status_not_success_class|software_proof_o5_cdn_tls_external_evidence_readiness_packet_consumption_only|safe_to_control=false|delivery_success=false" onboard/src/ros2_trashbot_behavior docs sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/tech-done.md
```

Result: passed with exit code 0. Output is intentionally large because `safe_to_control=false|delivery_success=false` matches existing fail-closed docs and behavior code; key new hits include this sprint `tech-done.md`, `docs/interfaces/o5_cdn_tls_external_evidence_probe.md`, `docs/product/cloud_4g_infrastructure.md`, and `remote_cloud_relay.py`.

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/cloud_4g_infrastructure.md docs/interfaces/o5_cdn_tls_external_evidence_probe.md sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption
```

Result: passed with no output.

Process note: the initial pre-doc anchor `rg` failed with `No such file or directory` only because `tech-done.md` had not been created yet. After this file was created, the exact command above passed.

## Acceptance Boundary

Accepted:

- The 13:13 sanitized CDN/TLS artifact is machine-read by O5 readiness logic.
- `cloud_production_cutover_readiness_packet` now has an independent `cdn_tls_external_evidence` source slot.
- 4xx artifact status remains `blocked_not_proven` and does not grant OKR credit.
- Future success-class artifact is bounded to section-level software proof only.

Rejected:

- Not production cloud ready.
- Not OSS object upload or CDN origin fetch.
- Not production DB/queue or worker cutover.
- Not 4G/SIM.
- Not real phone/browser proof.
- Not route execution, delivery success, HIL, or safe-to-control.

## Remaining Risk

- O5 remains blocked on success-class external CDN/TLS or stronger production evidence. The consumed 13:13 artifact still has `http_status_class=4xx`.
- This sprint did not rerun the CDN/TLS probe and did not change CDN origin/path configuration.
- No Hardware, Algorithm, or Full-stack implementation is required for this packet-consumption step; Product still needs to keep O5 percentage flat unless stronger production evidence appears.

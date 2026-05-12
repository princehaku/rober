# Sprint 2026.05.12_23-24 Remote Transaction Isolation Gate - Side2Side Check

## Status

- Stage: side2side_check
- Product Owner: `product-okr-owner`
- Main Objective: O6 4G cloud relay + OSS/CDN data path productization
- Evidence boundary: `software_proof_docker_transaction_isolation_gate`
- Acceptance result: accepted as Docker/local software proof; not production ready.

## User Value And North Star

North star: ordinary phone users should be able to start and understand a trash delivery without knowing ROS2, command queues, ACK cursors, or cloud internals.

This sprint improves a productionization prerequisite rather than a visible UX flow. It proves, in a Docker/local gate, that concurrent command/status/ACK writes for one robot do not let a later ACK move cursor past an unfinished command. That reduces the chance that future phone/cloud flows mislead the user about command progress.

## OKR Mapping

- O6 KR1: `trashbot.remote.v1` command/status/ACK envelope remains protected; Task B confirmed metadata does not drive robot action.
- O6 KR5: phone-safe summaries avoid credentials, DB/queue URLs, local paths, ROS topics, `/cmd_vel`, serial, baudrate, and hardware details.
- O6 KR6: transaction isolation risk is now visible in artifact, preflight, phone readiness, and diagnostics.
- O5: no progress increase; this only supplies O6 support metadata to phone-facing surfaces.
- O1/O2/O3/O4: no progress increase; no hardware, Nav2/fixed-route, camera, HIL, or real delivery evidence was produced.

## Side By Side Acceptance

| Requirement | Evidence | Product Decision |
| --- | --- | --- |
| Artifact gate exists for transaction isolation | Task A added `trashbot.transaction_isolation_drill`; CLI output reported `ok=true` and `transaction_isolation_status=passed` | Accept |
| Cursor cannot skip unfinished command | Task A scenario keeps cursor at `cmd-before-transaction-a` while a later command terminal ACK exists | Accept as Docker/local proof |
| ACK is not delivery success | CLI reported `delivery_success=false`; docs and phone copy keep ACK as command envelope evidence | Accept |
| Preflight consumes the artifact | Preflight output reported `transaction_isolation=pass`, `production_ready=False`, `overall_status=blocked` | Accept |
| Robot compatibility is preserved | Task B targeted tests `Ran 40 tests in 19.857s OK`; no production `remote_bridge.py` change required | Accept |
| Product docs and interface docs exist | Path check confirms all referenced docs exist | Accept |

## Evidence Boundary

Accepted boundary is exactly `software_proof_docker_transaction_isolation_gate`.

This sprint does not prove real production DB/queue, multi-instance consistency, real production transaction isolation, real cloud, real 4G/SIM, HTTPS/TLS public ingress, OSS/CDN live traffic, production operations, real phone device behavior, Nav2/fixed-route, WAVE ROVER, HIL, or real delivery.

## Remaining Risks

- `production_ready=false` remains correct.
- `overall_status=blocked` remains correct until real production DB/queue, cloud/4G, and operations evidence exist.
- O6 can move only modestly because this is a local gate, not a production transaction system.

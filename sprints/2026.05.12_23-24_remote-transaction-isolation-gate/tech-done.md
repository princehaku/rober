# Tech Done - Remote Transaction Isolation Gate

## Status

- Stage: tech-done
- Product Owner: `product-okr-owner`
- Task A Owner: `full-stack-software-engineer`
- Task B Owner: `robot-software-engineer`
- Evidence target: `software_proof_docker_transaction_isolation_gate`
- Product boundary: Docker/local software proof only; `production_ready=false` and `overall_status=blocked`.

## Actual Changes - Task A

- `remote_cloud_relay.py`
  - Added `trashbot.transaction_isolation_drill` artifact builder, checksum validator, phone-safe summary helper, CLI writer, and preflight consumer.
  - Drill scenario uses one robot with interleaved command/status/ACK writes: command A remains non-terminal, command B receives terminal ACK, status writes interleave with ACK writes, ACK cursor stays before unfinished command A, and ACK never becomes delivery success.
  - Preflight now reports `transaction_isolation=pass` when the artifact is valid and keeps `production_ready=false`.
- `operator_gateway_http.py`
  - Added `/api/status.phone_readiness.transaction_isolation` from the same phone-safe summary helper.
  - Added `/api/diagnostics.transaction_isolation` in the HTTP diagnostics wrapper so support sees the same summary as status.
- `operator_gateway_diagnostics.py`
  - Added top-level diagnostics `transaction_isolation` summary for configured artifact refs or `TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT`.
- Tests under `src/ros2_trashbot_behavior/test/`
  - Added artifact generation, invalid/stale/failed/hostile artifact handling, preflight consumption, status payload, and diagnostics payload assertions.
- Product docs
  - Updated O6 proof ladder, remote MVP CLI/preflight notes, and phone-safe field contract.

## Actual Changes - Task B

- `test_remote_bridge.py`
  - Added remote bridge compatibility coverage for transaction isolation metadata in cloud/status/diagnostics style payloads.
  - Verified metadata-only blocked responses do not trigger local robot action, do not ACK, and do not advance or persist cursor state.
  - Verified ACK remains command envelope evidence only and is not treated as delivery success.
- `docs/interfaces/ros_contracts.md`
  - Documented that transaction isolation metadata is phone/operator support metadata and can be ignored by older robot clients.
- `remote_bridge.py`
  - No production change was required; existing worker behavior already consumes only the command envelope.

## Validation - Task A

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py

Ran 125 tests in 26.988s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py

exit 0
```

```text
PYTHONPATH=src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-transaction-isolation-artifact /tmp/trashbot_transaction_isolation_drill.json

ok=true
transaction_isolation_status=passed
evidence_boundary=software_proof_docker_transaction_isolation_gate
cursor_after_interleaving=cmd-before-transaction-a
delivery_success=false
production_ready=false
```

```text
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT=/tmp/trashbot_transaction_isolation_drill.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight

software_proof_ready=True
production_ready=False
transaction_isolation=pass
evidence_boundary=software_proof_docker_transaction_isolation_gate
overall_status=blocked
```

```text
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  docs/product/mobile_user_flow.md \
  sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-done.md

exit 0
```

## Validation - Task B

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py

Ran 40 tests in 19.857s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py

exit 0
```

```text
git diff --check -- \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  docs/interfaces/ros_contracts.md \
  sprints/2026.05.12_23-24_remote-transaction-isolation-gate/tech-done.md

exit 0
```

## Product Acceptance Notes

- User value: future 4G/cloud command flow now has a local gate for the specific risk where later ACKs could otherwise appear to skip an unfinished command.
- OKR mapping: O6 KR1/KR5/KR6 advanced through artifact, preflight, phone readiness, diagnostics, and robot compatibility fence. O5 only receives supporting O6 summary material and does not increase.
- Core acceptance: `transaction_isolation=pass`, `evidence_boundary=software_proof_docker_transaction_isolation_gate`, `production_ready=false`, `overall_status=blocked`, and `delivery_success=false` are all preserved.

## Remaining Risk

- This is Docker/local software proof only.
- It does not prove real production DB/queue, multi-instance consistency, real production transaction isolation, real production queue ordering, real cloud, real 4G/SIM, HTTPS/TLS public ingress, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER, HIL, or real delivery success.
- ACK remains command accepted/processing evidence only; phone copy and diagnostics keep that boundary explicit.

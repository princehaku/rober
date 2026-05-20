# Cloud Command Sequence Regression Guard PRD

## User Value

When the cloud control plane serves an older queued command after a newer command has already reached a terminal ACK, the robot must fail closed. The phone should show that the cloud queue is out of order and that the robot did not execute the stale command again.

## OKR Mapping

- Primary: Objective 5 KR1 and KR6, command/status/ACK control-plane safety and graceful degradation.
- Secondary: Objective 4 KR4/KR5, phone-safe diagnostics and user-readable recovery copy.

This sprint does not increase Objective 5 progress because it is local Docker software proof, not real production queue ordering, production DB/queue, 4G/SIM, HTTPS/TLS, OSS/CDN live traffic, or true phone/browser proof.

## Problem Evidence

- `OKR.md` 4.1 still lists Objective 5 at about 68% with missing queue ordering and external cloud proof.
- `docs/product/remote_4g_mvp.md` already documents queue ordering as a known local drill and states production queue ordering is not proven.
- Recent guards cover duplicate ID, ID conflict, auth failure, and media degradation, but they do not cover an older queue sequence being served under a new command id.

## Requirements

1. Robot bridge accepts optional command queue sequence metadata and tracks the latest terminal sequence after successful ACK post.
2. If a new unexpired command has a lower/equal sequence than the latest terminal sequence and a different command id, the bridge rejects it before backend execution.
3. Operator status, ACK result, diagnostics/readiness, and mobile/web show `degradation_state=command_sequence_regression`.
4. Phone-facing copy must say this is not delivery success and must keep primary actions disabled.
5. Commands without sequence metadata preserve existing opaque cursor behavior.

## Non-goals

- No production DB/queue implementation.
- No real queue ordering proof.
- No real cloud/4G/phone/HIL validation.
- No hardware, route/elevator, or delivery-success claim.

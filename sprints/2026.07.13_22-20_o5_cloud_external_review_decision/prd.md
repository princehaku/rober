# PRD - O5 Cloud External Evidence Review Decision

## Problem

Objective 5 is lowest at about `85%`, but recent O5 work is blocked on real external production evidence. The repo documents a `cloud_external_evidence_review_decision` step after `external_evidence_intake`, yet that step has no executable tool and is not consumed by the current O5 cutover readiness packet.

Without this step, future public HTTPS/TLS, OSS/CDN, production DB/queue, worker cutover, 4G/SIM, and true phone/browser evidence has no local fail-closed review artifact before it enters product-facing diagnostics.

## User Value

The immediate user value is not a visible delivery feature. It is an operator-safe intake path that lets future real production evidence be reviewed without leaking URLs, credentials, response bodies, local paths, control endpoints, or hardware claims.

This keeps the product honest: external materials can be accepted for later review, marked as backfill-needed, rejected as unsafe, or blocked for missing intake. None of those states may be treated as production readiness.

## Scope

In scope:

- Add an executable `pc-tools/evidence/cloud_external_evidence_review_decision.py`.
- Support existing fixtures for accepted, backfill-needed, mismatch, and unsafe intake.
- Emit artifact and summary JSON with deterministic status and safe fields.
- Add O5 relay/readiness consumption for the review-decision artifact as a separate source slot.
- Add tests and update O5 product/interface docs.
- Update this sprint's `tech-done.md`.

Out of scope:

- Re-probing the public CDN/TLS endpoint.
- Connecting to production cloud, production DB/queue, real OSS/CDN, 4G/SIM, or real phone/browser.
- Any `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, HIL, route execution, or delivery action.
- O6/O7 UI wrapper expansion unless a narrow test helper needs to read the summary.

## Acceptance Criteria

- The CLI can consume `accepted_intake.json`, `needs_backfill_intake.json`, `mismatch_intake.json`, and `unsafe_intake.json`.
- The CLI writes both artifact and summary JSON.
- Accepted fixture returns `accepted_external_evidence_not_proven`; incomplete fixture returns `needs_external_evidence_backfill_not_proven`; evidence-ref mismatch returns `external_evidence_ref_mismatch_not_proven`; unsafe content returns `rejected_unsafe_external_evidence_not_proven`.
- All outputs keep fixed false fields and `production_ready=false`.
- O5 cutover readiness packet exposes `cloud_external_evidence_review_decision` as an independent artifact status without marking the packet production-ready.
- Tests prove safe redaction/fail-closed behavior and packet consumption.

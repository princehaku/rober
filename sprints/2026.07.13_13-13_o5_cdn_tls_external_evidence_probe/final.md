# Final - O5 CDN/TLS External Evidence Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Final status: accepted fail-closed O5 external CDN/TLS evidence probe

## Actual Changes Accepted

Product accepts the implementation artifacts as a bounded O5 fail-closed external evidence probe:

- `onboard/scripts/o5_cdn_tls_external_evidence_probe.py`
- `onboard/tests/test_o5_cdn_tls_external_evidence_probe.py`
- `docs/interfaces/o5_cdn_tls_external_evidence_probe.md`
- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/artifacts/cdn_tls_external_evidence_summary.json`
- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/tech-done.md`

Product closeout added:

- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/side2side_check.md`
- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/final.md`
- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/artifacts/product_acceptance_cdn_tls_external_evidence.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Product Acceptance Decision

Accepted as: fail-closed O5 CDN/TLS external evidence probe with useful TLS/certificate observation.

Rejected as: O5 OKR-lifting production proof.

The artifact records `schema=trashbot.o5.cdn_tls_external_evidence.v1`, `evidence_key=cdn_tls_external_evidence`, `probe_attempted=true`, `external_request_attempted=true`, `tls_handshake_observed=true`, `certificate_valid_for_host=true`, `http_method=HEAD`, and `http_status_class=4xx`. Because the outcome is `cdn_tls_external_evidence_status=blocked_http_status_not_success_class` and `accepted_claim=none`, Product does not raise O5 and does not archive the KR.

## OKR And KR Result

- O5 remains about `85%`.
- O1 remains about `94%`.
- O6/O7 remain about `93%`.
- KR archival: `不归档`.
- Direction: continue O5 only with successful external CDN/TLS/public ingress or stronger production evidence; otherwise pivot to explicit operator-approved current live HIL/current route evidence.

## Rejected Claims

This sprint does not prove production cloud ready, OSS object upload, CDN origin fetch, production DB/queue, production worker cutover, 4G/SIM, real phone/browser, route execution, delivery, HIL, or safe-to-control.

Safety and mission fields remain fixed: `delivery_success=false`, `safe_to_control=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`.

## Verification Result

Implementation verification from `tech-done.md` passed:

- `python3 -m py_compile onboard/scripts/o5_cdn_tls_external_evidence_probe.py`
- `python3 -m unittest onboard.tests.test_o5_cdn_tls_external_evidence_probe`, `Ran 6 tests in 0.006s OK`
- probe command wrote the sanitized artifact
- JSON tool passed for `cdn_tls_external_evidence_summary.json`
- anchor `rg` passed
- scoped `git diff --check` passed
- artifact leak scan passed for complete URL, default host string, token/cookie marker, raw header marker, traceback marker, and local absolute path

Product validation passed after this closeout:

- JSON tool passed for implementation and product acceptance artifacts.
- Structure assertions passed with `product_cdn_tls_acceptance_ok`.
- Anchor `rg` found the required O5, `cdn_tls_external_evidence`, `blocked_http_status_not_success_class`, TLS/cert, `http_status_class=4xx`, `accepted_claim=none`, false safety fields, and `不归档` wording.
- Scoped `git diff --check` passed.

## Remaining Risk And Next Recommendation

Remaining blocker: `blocked_http_status_not_success_class`. TLS and certificate validation were observed, but the external endpoint returned `4xx`, so the sprint is useful diagnosis, not production readiness.

Next recommendation: rerun the sanitized probe against the intended public CDN endpoint once it can return a success HTTP class, then separately collect OSS upload/origin fetch, production DB/queue, worker cutover, 4G/SIM, and real phone/browser evidence before raising O5 or archiving KR4.

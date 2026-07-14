# Tech Done - O5 CDN/TLS External Evidence Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/`
- Owner: `robot-software-engineer`
- Evidence key: `cdn_tls_external_evidence`
- Status: implementation complete, pending Product acceptance closeout

## Actual Changes

- Added `onboard/scripts/o5_cdn_tls_external_evidence_probe.py`, a stdlib HTTPS probe CLI that defaults to the O5 KR4 public CDN target assembled in memory and supports `ROBER_CDN_PROBE_BASE_URL` override.
- Added `onboard/tests/test_o5_cdn_tls_external_evidence_probe.py` covering successful HEAD probe, bounded GET fallback, non-success HTTP fail-closed handling, TLS failure sanitization, unsafe input rejection, and CLI JSON output.
- Added `docs/interfaces/o5_cdn_tls_external_evidence_probe.md` documenting the sanitized artifact contract and rejected claims.
- Generated `artifacts/cdn_tls_external_evidence_summary.json` from one default real external probe run.

## Verification Results

- `python3 -m py_compile onboard/scripts/o5_cdn_tls_external_evidence_probe.py`: passed.
- `python3 -m unittest onboard.tests.test_o5_cdn_tls_external_evidence_probe`: passed, `Ran 6 tests in 0.006s OK`.
- `python3 onboard/scripts/o5_cdn_tls_external_evidence_probe.py --output sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/artifacts/cdn_tls_external_evidence_summary.json`: passed and wrote sanitized artifact.
- `python3 -m json.tool sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/artifacts/cdn_tls_external_evidence_summary.json >/dev/null`: passed.
- `rg -n "cdn_tls_external_evidence|next_live_command|delivery_success=false|safe_to_control=false" ...`: passed; anchors found in script, tests, docs, sprint docs, and artifact.
- `git diff --check -- onboard/scripts/o5_cdn_tls_external_evidence_probe.py onboard/tests/test_o5_cdn_tls_external_evidence_probe.py docs/interfaces/o5_cdn_tls_external_evidence_probe.md sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe`: passed.
- Targeted leak scan of the artifact found no complete URL, default host string, token/cookie marker, raw header marker, traceback marker, or local absolute path.

## Failure Positioning

- Default real probe status: `blocked_http_status_not_success_class`.
- Evidence observed: `probe_attempted=true`, `external_request_attempted=true`, `tls_handshake_observed=true`, `certificate_valid_for_host=true`, `http_method=HEAD`, `http_status_class=4xx`, `elapsed_ms_bucket=lt_250ms`, `content_length_bucket=1b_1kb`.
- Safe blocker: HTTPS/TLS and certificate validation were observed, but the CDN endpoint returned a non-success HTTP class, so this run does not set `accepted_claim=o5_cdn_tls_external_evidence_delta`.
- The artifact keeps only `target_source=okr_kr4_default`, `scheme=https`, and a host hash prefix; it does not persist the full target or target path.

## Remaining Risk

- This sprint only proves a narrow O5 CDN/TLS external evidence delta when the external probe reaches a sanitized status class.
- It does not prove production cloud ready, OSS object upload, CDN origin fetch, production DB/queue, 4G/SIM, real phone/browser, route execution, delivery success, HIL, or safe-to-control.
- Safety invariants remain fixed: `delivery_success=false`, `safe_to_control=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`.

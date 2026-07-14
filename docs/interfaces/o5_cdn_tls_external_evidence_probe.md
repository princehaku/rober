# O5 CDN/TLS External Evidence Probe

## Scope

`onboard/scripts/o5_cdn_tls_external_evidence_probe.py` runs a real external HTTPS probe for the O5 public CDN/TLS evidence gap. The default target is the O5 KR4 public CDN base URL assembled inside the script; operators may override it with `ROBER_CDN_PROBE_BASE_URL`.

This is an external reachability and TLS evidence tool only. It does not prove production cloud readiness, OSS upload, CDN origin fetch, production DB/queue, worker cutover, 4G/SIM, real phone/browser validation, route execution, delivery, HIL, or safe-to-control.

## Artifact Contract

The JSON artifact schema is `trashbot.o5.cdn_tls_external_evidence.v1` and the evidence key is `cdn_tls_external_evidence`.

Persisted fields are intentionally narrow:

- `target_source`
- `target_host_hash_prefix`
- `scheme`
- `probe_attempted`
- `external_request_attempted`
- `tls_handshake_observed`
- `certificate_valid_for_host`
- `http_method`
- `http_status_class`
- `elapsed_ms_bucket`
- `content_length_bucket`
- `blocked_reasons`
- `next_live_command`
- fixed false invariants such as `delivery_success=false` and `safe_to_control=false`

The artifact must not persist a complete URL, URL path, query string, token, cookie, response body, raw headers, raw traceback, or local absolute path. Host identity is represented only by `target_host_hash_prefix`.

## Fail-Closed Rules

The probe rejects unsafe input before network I/O when the target is non-HTTPS, uses userinfo, has query or fragment material, uses a non-default HTTPS port, points at localhost/private hosts, or contains sensitive markers.

Network and TLS failures are reported as safe reason codes such as:

- `dns_failed`
- `http_timeout`
- `network_unavailable`
- `tls_failed`
- `tls_certificate_invalid`
- `http_status_not_success_class`

Blocked artifacts still keep `delivery_success=false`, `safe_to_control=false`, `robot_control_executed=false`, `route_execution_success=false`, and `hil_pass=false`.

## Readiness Packet Consumption

`remote_cloud_relay.py` now exposes a packet/preflight consumer for the sanitized artifact:

- Environment variable: `TRASHBOT_REMOTE_CLOUD_CDN_TLS_EXTERNAL_EVIDENCE_ARTIFACT`
- CLI flag: `--cdn-tls-external-evidence-artifact`
- Cutover packet source slot: `cdn_tls_external_evidence`
- Consumer proof boundary: `software_proof_o5_cdn_tls_external_evidence_readiness_packet_consumption_only`

The consumer accepts `schema=trashbot.o5.cdn_tls_external_evidence.v1` and `evidence_key=cdn_tls_external_evidence`, verifies all fixed false fields, verifies redaction flags, and only forwards safe facts such as TLS handshake observed, certificate-valid-for-host, HTTP method/class, accepted claim, and host-hash-prefix presence.

The 13:13 artifact with `http_status_class=4xx`, `cdn_tls_external_evidence_status=blocked_http_status_not_success_class`, and `accepted_claim=none` is consumed but remains `blocked_not_proven` inside `trashbot.cloud_production_cutover_readiness_packet.v1`. A future 2xx/3xx artifact with `accepted_claim=o5_cdn_tls_external_evidence_delta` may make only the `cdn_tls_external_evidence` section `software_proof_ready`; the packet itself must still keep `production_ready=false`, `okr_credit_allowed=false`, `delivery_success=false`, and `safe_to_control=false`.

## Operator Command

Use the normal sprint command and pass an output path:

```bash
python3 onboard/scripts/o5_cdn_tls_external_evidence_probe.py --output <sanitized_artifact_path>
```

To test a staging or replacement public CDN endpoint, set `ROBER_CDN_PROBE_BASE_URL` in the environment. Do not paste secret-bearing URLs into sprint docs or artifacts.

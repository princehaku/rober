# Tech Plan - O5 CDN/TLS External Evidence Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target Objective: O5
- Proof target: `cdn_tls_external_evidence`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 / Objective 列表中最低完成度 Objective 是 O5，当前约 `85%`。
2. 本 sprint 针对最低 Objective：是，直接针对 O5 的真实公网 HTTPS/TLS、OSS/CDN live traffic 和 external production evidence 缺口中的 CDN/TLS 子缺口。
3. 非重复理由：最近两轮 `2026.07.13_11-13_o6_o7_label_query_filters` 与 `2026.07.13_12-13_o6_archive_task_query_filters` 都是 O6/O7 local/mock query filter contract hardening；本 sprint 不继续做 O6 query/readback wrapper，而是要求 `robot-software-engineer` 发起真实外部 CDN/TLS probe。若 probe 失败，必须 fail closed 并给 `next_live_command`，不得包装成 support-only 进度。

## Implementation Owner And Routing

Owner: `robot-software-engineer`

Reason: probe 属于 ROS2/cloud relay 软件链路和 artifact/preflight 合同，不涉及 WAVE ROVER、ESP32、UART、电压、引脚或机械尺寸；不需要 Hardware owner。O6/O7 只可能在后续消费 sanitized summary，本 sprint 不改 O6/O7。

## Proposed File Scope For Implementation

Implementation should stay narrowly scoped. Suggested files:

- `onboard/scripts/o5_cdn_tls_external_evidence_probe.py`
- `onboard/tests/test_o5_cdn_tls_external_evidence_probe.py`
- `docs/interfaces/o5_cdn_tls_external_evidence_probe.md`
- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/tech-done.md`
- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/side2side_check.md`
- `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/final.md`

Do not modify unrelated O6 query filter code unless implementation proves an existing shared helper must be reused.

## Technical Approach

1. Build a small CLI probe using Python standard library networking and TLS primitives where practical.
2. Default target comes from O5 KR4 public CDN base URL in `OKR.md`; allow `ROBER_CDN_PROBE_BASE_URL` override.
3. Require HTTPS for accepted success; reject non-HTTPS or unsafe targets before network I/O.
4. Prefer `HEAD`; optionally bounded `GET` only if CDN rejects `HEAD`. Never persist response body.
5. Emit JSON artifact under sprint artifacts or caller-provided output path.
6. Artifact schema should include:
   - `schema=trashbot.o5.cdn_tls_external_evidence.v1`
   - `evidence_key=cdn_tls_external_evidence`
   - `probe_attempted`
   - `external_request_attempted`
   - `target_source=okr_kr4_default|env_override`
   - `target_host_hash_prefix`
   - `scheme=https`
   - `tls_handshake_observed`
   - `certificate_valid_for_host`
   - `http_status_class`
   - `elapsed_ms_bucket`
   - `content_length_bucket`
   - `blocked_reasons`
   - `next_live_command`
   - `delivery_success=false`
   - `safe_to_control=false`
   - `robot_control_executed=false`
   - `route_execution_success=false`
   - `hil_pass=false`
7. Redaction guard must reject or strip:
   - full URL
   - path/query
   - bearer/token/cookie/credential strings
   - response body
   - raw response headers
   - raw traceback
   - local absolute paths
8. Fail closed:
   - DNS, TCP, TLS, timeout, unsafe URL, non-HTTPS and unexpected HTTP outcomes must produce `cdn_tls_external_evidence_status=blocked_*` and safe `blocked_reasons`.
   - A failed probe must still write a sanitized artifact when possible.

## Product Acceptance Gate

Accepted as O5 progress only when all are true:

- An external CDN/TLS probe was actually attempted against the OKR default target or env override.
- Artifact includes `cdn_tls_external_evidence`.
- Artifact includes `next_live_command`.
- Artifact includes `delivery_success=false` and `safe_to_control=false`.
- Artifact does not include complete URL, path/query, token, response body, credentials, cookie, raw header, traceback or local absolute path.
- Verification commands pass.

Accepted claim if successful:

- O5 CDN/TLS external evidence delta.

Rejected claims even if successful:

- production cloud ready.
- OSS object upload.
- CDN origin fetch.
- production DB/queue.
- production worker/cutover.
- 4G/SIM.
- real phone/browser.
- route execution.
- delivery success.
- HIL.
- safe-to-control.

## Future Engineer Acceptance Commands

The implementation owner should run a focused version of:

```bash
python3 -m py_compile onboard/scripts/o5_cdn_tls_external_evidence_probe.py
python3 -m unittest onboard.tests.test_o5_cdn_tls_external_evidence_probe
ROBER_CDN_PROBE_BASE_URL="<env-or-default-not-recorded>" python3 onboard/scripts/o5_cdn_tls_external_evidence_probe.py --output sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/artifacts/cdn_tls_external_evidence_summary.json
rg -n "cdn_tls_external_evidence|next_live_command|delivery_success=false|safe_to_control=false" sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe onboard/scripts/o5_cdn_tls_external_evidence_probe.py onboard/tests/test_o5_cdn_tls_external_evidence_probe.py
git diff --check -- onboard/scripts/o5_cdn_tls_external_evidence_probe.py onboard/tests/test_o5_cdn_tls_external_evidence_probe.py docs/interfaces/o5_cdn_tls_external_evidence_probe.md sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe
```

The command string above intentionally uses a placeholder and must not be copied into artifacts with a complete URL or credential.

## Planning Acceptance Commands

This planning sprint must pass:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|CDN/TLS|external evidence|cdn_tls_external_evidence|robot-software-engineer|next_live_command|delivery_success=false|safe_to_control=false" sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe

git diff --check -- sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe
```

## Risks And Follow-Up

- If external network is blocked, the sprint should finish fail-closed with sanitized blocker and `next_live_command`, not claim progress.
- If CDN returns a non-success HTTP status but TLS succeeds, Product must classify the exact narrow evidence and avoid over-claiming.
- If any artifact persists full URL, path, body, token or credential material, Product must reject and send `robot-software-engineer` back to repair redaction before acceptance.
- Docs sync is required in the implementation phase; this planning-only turn is intentionally limited to the three requested sprint files.

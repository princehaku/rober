# Full-Stack Owner Note: Operator Report PC Proxy Retest

## Sprint / Scope

- sprint: `sprints/2026.06.04_17-18_runtime-material-epic/`
- owner: `full-stack-software-engineer`
- role: User Touchpoint Full-Stack Engineer
- evidence_type: `robot_runtime_material` + `software_guard`
- target: verify PC same-origin `/api/o7/direct-upper/operator-report` can write through to the real upper API `http://192.168.1.11:8787`.
- safety_scope: non-motion verification only; did not call `/api/base/manual`, `/api/base/stop`, serial motion, or `/cmd_vel`.

## User Journey Impact

- PC operator report is no longer blocked by the old `upper_http_405` wrapper failure.
- Operator can submit a report through the PC same-origin API and then read the same `evidence_ref` back from the real upper API artifact.
- The response still keeps the product boundary visible: `safe_to_control=false`, `robot_control_executed=false`, no robot ACK, no `T=1001`, no HIL, and no delivery success.

## Verification Commands And Results

### Real upper 8787 direct POST

Command:

```bash
curl -sS -i --max-time 8 -X POST 'http://192.168.1.11:8787/api/operator/report' \
  -H 'Content-Type: application/json' \
  --data '{"evidence_ref":"2026.06.04_17-18_operator_report_pc_proxy_retest_direct","note":"full-stack direct upper retest after robot software deploy; no motion","operator_confirmed":true}'
```

Key output:

```text
HTTP/1.1 200 OK
schema=trashbot.upper_robot_api.v1.operator_report_result
endpoint=/api/operator/report
operator_report_status=unsafe_or_incomplete
artifact.path=runtime/operator_report_latest.json
artifact.write.ok=true
command_payload_summary.evidence_ref=2026.06.04_17-18_operator_report_pc_proxy_retest_direct
safe_to_control=false
robot_control_executed=false
sends_commands=false
sends_motion_commands=false
uses_base_uart=false
starts_ros2=false
```

### Real upper 8787 direct GET

Command:

```bash
curl -sS -i --max-time 8 'http://192.168.1.11:8787/api/operator/report'
```

Key output:

```text
HTTP/1.1 200 OK
schema=trashbot.upper_robot_api.v1.operator_report_latest_result
artifact.status=loaded
latest_result.command_payload_summary.evidence_ref=2026.06.04_17-18_operator_report_pc_proxy_retest_direct
latest_result.operator_report_status=unsafe_or_incomplete
safe_to_control=false
robot_control_executed=false
delivery_success=false
```

### PC workstation tests

Command:

```bash
cd pc-tools/workstation && npm test -- --run
```

Output:

```text
Test Files  3 passed (3)
Tests  97 passed (97)
Duration  18.42s
```

### PC same-origin API startup

Command:

```bash
cd pc-tools/workstation && TMPDIR=/tmp PORT=18787 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
```

Output:

```text
pc-tools workstation API listening on http://127.0.0.1:18787
```

The API process was stopped after the smoke test.

### PC same-origin proxy POST

Command:

```bash
curl -sS -i --max-time 10 -X POST 'http://127.0.0.1:18787/api/o7/direct-upper/operator-report' \
  -H 'Content-Type: application/json' \
  --data '{"evidence_ref":"2026.06.04_17-18_operator_report_pc_same_origin_retest","note":"PC same-origin proxy retest against real upper 8787; no motion; confirm wrapper not upper_http_405","operator_confirmed":true}'
```

Key output:

```text
HTTP/1.1 200 OK
schema=trashbot.pc_tools_workstation.o7_direct_upper_operator_report.v1
accepted_by_workstation=true
upper_request.path=/api/operator/report
upper_request.method=POST
upper_request.executed=true
upper_request.ok=true
upper_request.http_status=200
upper_request.failure_reason=
failure_reason=none
fail_closed=false
command_payload_summary.evidence_ref=2026.06.04_17-18_operator_report_pc_same_origin_retest
robot_ack_connected=false
t1001_observed=false
safe_to_control=false
robot_control_executed=false
sends_commands=false
```

This confirms the PC wrapper is no longer returning `upper_http_405`.

### Real upper readback after PC proxy POST

Command:

```bash
curl -sS -i --max-time 8 'http://192.168.1.11:8787/api/operator/report'
```

Key output:

```text
HTTP/1.1 200 OK
schema=trashbot.upper_robot_api.v1.operator_report_latest_result
artifact.status=loaded
artifact.bytes_read=3456
latest_result.command_payload_summary.evidence_ref=2026.06.04_17-18_operator_report_pc_same_origin_retest
latest_result.command_payload_summary.report_note=PC same-origin proxy retest against real upper 8787; no motion; confirm wrapper not upper_http_405
latest_result.operator_report_status=unsafe_or_incomplete
latest_result.safe_to_control=false
latest_result.robot_control_executed=false
latest_result.sends_commands=false
latest_result.uses_base_uart=false
latest_result.starts_ros2=false
```

## Failure Localization

- No active failure observed for the requested path.
- The previous `upper_http_405` blocker is resolved for real upper `8787` and PC same-origin `/api/o7/direct-upper/operator-report`.
- The report remains `unsafe_or_incomplete` because this non-motion retest intentionally did not provide physical clearance, emergency stop readiness, observed motion, observed stop, or field/HIL material.

## Remaining Risk

- This retest does not prove PC WASD control, base motion, stop execution, robot ACK, fresh `T=1001`, `/odom`, `/imu/data`, `/battery`, SLAM map lifecycle, localization, Nav2, elevator runtime, or delivery success.
- `operator_report` is human/operator material only. It does not replace `/api/base/status`, `/api/base/stop`, feedback samples, HIL, or field video.
- PC API startup still needs `TMPDIR=/tmp` in this WSL/mixed mount environment to avoid the known `tsx` temp IPC issue.

## Changed Files

- `sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/full-stack-software-engineer-operator-report-retest.md`


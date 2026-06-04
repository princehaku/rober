# Robot Software Owner Note: Operator Report Runtime Deploy

## Sprint / Evidence

- sprint: `sprints/2026.06.04_17-18_runtime-material-epic/`
- owner: `robot-software-engineer`
- evidence_type: `robot_runtime_material`
- deployment_target: `root@192.168.1.11:37878:/root/rober/onboard/scripts/upper_robot_api.py`
- safety_scope: non-motion upper API deploy only; no `/api/base/manual`, no serial motion command, no ROS `/cmd_vel`.

## Local Change Review

- Reviewed local `onboard/scripts/upper_robot_api.py`.
  - `POST /api/operator/report` and `GET /api/operator/report` are registered in `create_app()`.
  - `--operator-report-artifact-path` is present in argparse, so `--help` exits before server startup.
  - Operator report guard flags keep `safe_to_control=false`, `robot_control_executed=false`, `delivery_success=false`.
- Reviewed local `onboard/scripts/test_upper_robot_api.py`.
  - Includes class-level artifact persistence/readback tests.
  - Includes aiohttp route smoke proving POST/GET are not 405 when aiohttp test client is available.
- Reviewed local `docs/interfaces/o7_upper_robot_api.md`.
  - Documents the operator report evidence contract, artifact path, POST/GET semantics, and non-motion boundary.

## Deployment Actions

Pre-deploy command:

```bash
ssh root@192.168.1.11 -p 37878 'set -eu; test -f /root/rober/onboard/scripts/upper_robot_api.py; ps -ef | grep upper_robot_api.py | grep -v grep || true; python3 /root/rober/onboard/scripts/upper_robot_api.py --help | head -20'
```

Key output:

```text
root 24105 1 ... python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12
usage: upper_robot_api.py [-h] [--host HOST] [--port PORT] ...
```

Pre-deploy live probe:

```bash
ssh root@192.168.1.11 -p 37878 'curl -sS -i --max-time 5 http://127.0.0.1:8787/health'
```

Result: `HTTP/1.1 200 OK`; response kept `safe_to_control=false`, `delivery_success=false`, `robot_control_executed=false`.

```bash
ssh root@192.168.1.11 -p 37878 'curl -sS -i --max-time 5 -X POST http://127.0.0.1:8787/api/operator/report -H "Content-Type: application/json" --data "{\"evidence_ref\":\"pre_deploy_operator_report_probe\",\"note\":\"pre deploy check\",\"operator_confirmed\":true}"'
```

Result: `HTTP/1.1 405 Method Not Allowed`; this confirmed the old 8787 runtime still had the route blocker before deploy.

Backup and deploy:

```text
backup=/root/rober/onboard/scripts/upper_robot_api.py.20260604_181656.bak
backup_stat=/root/rober/onboard/scripts/upper_robot_api.py.20260604_181656.bak 108291 bytes mode=755 mtime=2026-06-04 14:23:17.793620748 +0800
```

- Uploaded local script to `/root/rober/onboard/scripts/upper_robot_api.py.codex_tmp_operator_report`.
- Ran remote `python3 -m py_compile` on the temporary file before replacement.
- Replaced target script only after compile passed.

Remote target after deploy:

```text
068208c7376d45a82e3e9d7fc1e4688eb77dddfa281ae034b4ab43e6834f09e8  /root/rober/onboard/scripts/upper_robot_api.py
target_stat=/root/rober/onboard/scripts/upper_robot_api.py 120620 bytes mode=755 mtime=2026-06-04 18:17:35.480673272 +0800
```

Restart action:

- Stopped only the matched upper API process: `old_pids=24105`.
- Started only `python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`.
- New process: `new_pid=30042`.

Restart log:

```text
{"event": "upper_robot_api_started", "host": "0.0.0.0", "port": 8787}
```

Post-deploy command:

```bash
ssh root@192.168.1.11 -p 37878 'ps -ef | grep upper_robot_api.py | grep -v grep || true; python3 /root/rober/onboard/scripts/upper_robot_api.py --help | head -20'
```

Key output:

```text
root 30042 1 ... python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12
usage: upper_robot_api.py [-h] [--host HOST] [--port PORT] ...
                          [--operator-report-artifact-path OPERATOR_REPORT_ARTIFACT_PATH]
```

## Remote Runtime Verification

`GET /health`:

```bash
ssh root@192.168.1.11 -p 37878 'curl -sS -i --max-time 5 http://127.0.0.1:8787/health'
```

Result: `HTTP/1.1 200 OK`.

Key response fields:

```json
{
  "status": "ready",
  "safe_to_control": false,
  "delivery_success": false,
  "primary_actions_enabled": false,
  "robot_control_executed": false,
  "cloud_relay": false
}
```

`POST /api/operator/report`:

```bash
ssh root@192.168.1.11 -p 37878 'curl -sS -i --max-time 5 -X POST http://127.0.0.1:8787/api/operator/report -H "Content-Type: application/json" --data "{\"evidence_ref\":\"2026.06.04_17-18_operator_report_deploy_retest\",\"note\":\"remote 8787 operator report deploy retest no motion\",\"operator_confirmed\":true}"'
```

Result: `HTTP/1.1 200 OK`, no longer 405.

Key response fields:

```json
{
  "endpoint": "/api/operator/report",
  "operator_report_status": "unsafe_or_incomplete",
  "command_payload_summary": {
    "evidence_ref": "2026.06.04_17-18_operator_report_deploy_retest",
    "report_note": "remote 8787 operator report deploy retest no motion"
  },
  "artifact": {
    "path": "runtime/operator_report_latest.json",
    "write": {
      "ok": true,
      "method": "atomic_replace"
    }
  },
  "safe_to_control": false,
  "robot_control_executed": false,
  "delivery_success": false,
  "sends_commands": false,
  "sends_motion_commands": false,
  "uses_base_uart": false,
  "starts_ros2": false
}
```

`operator_confirmed=true` was included because this deploy task required that request shape. The current API contract intentionally does not treat it as a motion preflight field; missing `operator_present`, `physical_clearance_confirmed`, and `emergency_stop_ready` keep `operator_report_status=unsafe_or_incomplete`.

`GET /api/operator/report`:

```bash
ssh root@192.168.1.11 -p 37878 'curl -sS -i --max-time 5 http://127.0.0.1:8787/api/operator/report'
```

Result: `HTTP/1.1 200 OK`, no longer 405.

Key readback fields:

```json
{
  "artifact": {
    "status": "loaded",
    "bytes_read": 3299
  },
  "latest_result": {
    "operator_report": {
      "evidence_ref": "2026.06.04_17-18_operator_report_deploy_retest",
      "operator_notes": "remote 8787 operator report deploy retest no motion"
    },
    "operator_report_status": "unsafe_or_incomplete",
    "safe_to_control": false,
    "robot_control_executed": false,
    "delivery_success": false,
    "sends_commands": false,
    "uses_base_uart": false,
    "starts_ros2": false
  },
  "safe_to_control": false,
  "robot_control_executed": false,
  "delivery_success": false
}
```

## Failure定位

- No deploy or restart failure observed.
- Root cause of the pre-deploy 405 was stale deployed runtime: the remote help output before deploy did not include `--operator-report-artifact-path`, while the post-deploy help output does.

## Remaining Risk

- This is `robot_runtime_material` for the real 8787 upper API route only.
- It is not HIL, not PC browser end-to-end proof, not base movement proof, not `T=1001` feedback proof, and not delivery success.
- `runtime/operator_report_latest.json` is a relative path under the service process working directory. It was writable in this run, but this note does not prove long-term log retention or production archive ingestion.

## Coordination

- Product / OKR Owner: can treat the specific `upper_http_405` blocker as resolved for real 8787 runtime; do not count as HIL or delivery progress.
- Hardware Infra Engineer: no action needed for this non-motion deploy; future HIL still owns stop-first, clearance, E-stop, and `T=1001` material.
- Robot Algorithm Engineer: no coordination needed.
- Full-Stack Engineer: should now retest PC same-origin `/api/o7/direct-upper/operator-report` against this upper runtime and confirm UI readback.

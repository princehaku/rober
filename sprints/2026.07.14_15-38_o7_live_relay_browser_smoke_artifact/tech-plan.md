# Tech Plan - O7 Live Relay Browser Smoke Artifact

## Plan Status

- sprint_type: epic
- Sprint: `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/`
- Owner: `full-stack-software-engineer`
- Product decision: `调整`
- Proof boundary: `software_proof_o7_live_relay_browser_smoke_artifact_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 Objective 5，O5 当前约 85%。O1 约 94%，O6/O7 约 93%。
2. 本 sprint 不直接继续 O5 production/cloud lane；它针对 O7/O5 supporting evidence。
3. 不直接做 O5 的理由：O5 production/cloud success evidence 当前不可用；最近关闭的 O5 CLI export refresh 已证明继续 CLI export/readiness packet/terminal-result/readback/export wrapper 只会产生 support-only 材料；`field_execution_pack` inventory/pivot 也已经以 `blocked_missing_new_field_execution_material` 收口。为了避免重复消费同一 blocker，本轮转向 live relay + browser smoke artifact，要求真实启动本机 workstation server 并跑 live HTTP 或 live browser smoke。

## 技术目标

Build a live relay browser smoke artifact for the existing PC/O7 operator console path. This is not another wrapper: the accepted artifact must prove a live loopback server process was started and queried through real HTTP sockets.

Minimum target:

- Start `pc-tools/workstation` Node/Express server on loopback.
- Query live endpoints with real HTTP:
  - `/api/health`
  - `/api/o7/operator-console`
  - `/api/o7/cloud-operator-console-probe?baseUrl=<same-live-loopback-server>`
- Write `artifacts/o7_live_relay_browser_smoke_artifact.json`.
- Keep all safety and mission-success fields fixed false:
  - `delivery_success=false`
  - `safe_to_control=false`
  - `route_execution_success=false`
  - `hil_pass=false`
  - `robot_control_executed=false`
  - `connects_cloud_production=false`

## 文件范围

Implementation owner may modify:

- `pc-tools/workstation/src/server/`
- `pc-tools/workstation/test/`
- `pc-tools/workstation/package.json` only if a smoke script command is added.
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/tech-done.md`
- `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/`

Do not modify:

- `OKR.md` during implementation.
- `docs/process/okr_progress_log.md` during implementation.
- Existing closed sprint final/side2side/tech-done files.
- Robot control, hardware, Nav2, UART, WAVE ROVER, route execution, HIL, or production cloud credentials.

## 接口影响

Preferred implementation should reuse existing endpoints and avoid adding new runtime API. Existing useful endpoints:

- `GET /api/health`
- `GET /api/o7/operator-console`
- `GET /api/o7/cloud-operator-console-probe?baseUrl=<local-loopback-url>`

If a helper is needed, keep it as a smoke/artifact generator rather than a new product panel. Acceptable helper behavior:

- Start server with `HOST=127.0.0.1` and a deterministic port such as `17001`, or choose the next free loopback port and record it.
- Poll `/api/health` until ready.
- Fetch O7 operator console and cloud operator console probe via live HTTP.
- Validate schemas and false fields.
- Stop the server cleanly.
- Write the artifact under this sprint only.

## Artifact Contract

Required artifact shape:

```json
{
  "schema": "trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1",
  "proof_boundary": "software_proof_o7_live_relay_browser_smoke_artifact_only",
  "artifact_status": "live_relay_browser_smoke_ready_not_delivery_proof",
  "endpoint_transport": "live_loopback_http_socket",
  "server_started": true,
  "http_smoke_executed": true,
  "browser_smoke_status": "live_browser_executed",
  "delivery_success": false,
  "safe_to_control": false,
  "route_execution_success": false,
  "hil_pass": false,
  "robot_control_executed": false,
  "connects_cloud_production": false
}
```

If live browser automation is not available, `browser_smoke_status` may be `not_run_http_only_minimum`, but `endpoint_transport` must still be `live_loopback_http_socket`.

## 验收命令

Implementation owner must run:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
```

Implementation owner must also run a live HTTP smoke. Preferred command if a script is added:

```bash
cd pc-tools/workstation && npm run smoke:o7-live-relay-browser -- --artifact ../../sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/o7_live_relay_browser_smoke_artifact.json
```

Fallback manual smoke if no script is added:

```bash
cd pc-tools/workstation
HOST=127.0.0.1 PORT=17001 npm run api
curl -fsS http://127.0.0.1:17001/api/health
curl -fsS http://127.0.0.1:17001/api/o7/operator-console
curl -fsS 'http://127.0.0.1:17001/api/o7/cloud-operator-console-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A17001'
```

Implementation owner must assert artifact anchors:

```bash
rg -n "trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1|software_proof_o7_live_relay_browser_smoke_artifact_only|live relay|browser smoke|endpoint_transport=live_loopback_http_socket|server_started=true|http_smoke_executed=true|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false" pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact
```

Planning-stage validation for this Product plan:

```bash
test -f sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/pre_start.md && test -f sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/prd.md && test -f sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/tech-plan.md
rg -n 'sprint_type: epic|OKR 最低优先级核对|Objective 5|O5.*85|live relay|browser smoke|not another wrapper|software_proof|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false' sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact
git diff --check -- sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact
```

## Owner Prompt for Implementation

Use `full-stack-software-engineer` as the single implementation owner.

Task:

- Implement live relay browser smoke artifact generation for the existing PC/O7 operator console path.
- Do not create another UI panel.
- Do not create jsdom-only browser proof.
- Use real loopback HTTP against a started workstation server.
- Keep proof boundary `software_proof_o7_live_relay_browser_smoke_artifact_only`.

Output requirements:

1. Actual changed files.
2. Validation command outputs.
3. Failure root cause if any.
4. Remaining risks.

## 验收判断

Accept only if:

- A sprint artifact exists and records live loopback HTTP transport.
- `/api/health`, `/api/o7/operator-console`, and `/api/o7/cloud-operator-console-probe` were queried from a live server.
- Artifact schema and proof boundary match this plan.
- Fixed false fields remain false.
- Tests/build/lint/scoped diff check pass, or failures are repaired and re-run.

Reject if:

- Evidence is only unit test, fixture, jsdom, snapshot, status panel, readback wrapper, or CLI export.
- Artifact claims route execution, delivery success, HIL pass, safe-to-control, production cloud connected, real DB/queue/OSS/CDN connected, or robot control side effects.
- Implementation touches hardware/Nav2/control paths without a new plan and owner split.

## 风险和剩余阻塞

- This remains `software_proof`; it does not prove production cloud, public HTTPS/TLS, 4G/SIM, DB/queue, OSS/CDN, real phone/browser production path, route execution, delivery/operator acceptance, HIL, or safe-to-control.
- If live browser runtime cannot run in the environment, live HTTP smoke is enough for this sprint only; final must explicitly state the browser gap.
- O5 will remain about 85% unless this sprint unexpectedly consumes success-class external production evidence, which is not expected.

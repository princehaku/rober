# Tech Plan - O7 Live Relay Headless Browser Smoke

## Plan Status

- sprint_type: epic
- Sprint: `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/`
- Owner: `full-stack-software-engineer`
- Owner model: default single owner closeout, no parallel.
- Product decision: `调整`
- Proof boundary: `software_proof_o7_live_relay_headless_browser_smoke_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 Objective 5，O5 当前约 85%。O1 约 94%，O6/O7 约 93%。
2. 本 sprint 针对最低 Objective 5 的 browser evidence 缺口：上一轮 live relay HTTP smoke 已完成，但 `browser_smoke_status=not_run_http_only_minimum`，所以本轮补真实 `headless Chrome` browser smoke against live relay。它仍是 O7/O5 supporting evidence。
3. 本轮仍然 support-only：本机环境没有可见 O5 production/cloud、OSS/CDN、4G/SIM、tunnel 凭据入口，不能产出 success-class production evidence。计划明确不重复 HTTP-only smoke，不提升 OKR 百分比，不归档 KR，除非实施阶段意外取得 success-class production/cloud 或 same-window live route/HIL/delivery/operator evidence。

## 技术目标

Build a headless Chrome browser smoke artifact against the existing PC/O7 live relay endpoints. The accepted artifact must prove a real browser process loaded JSON contracts from a live loopback workstation server.

Minimum target:

- Start `pc-tools/workstation` live loopback server.
- Use real `headless Chrome` to load:
  - `/api/health`
  - `/api/o7/operator-console`
  - `/api/o7/cloud-operator-console-probe?baseUrl=<same-live-loopback-server>`
- Parse loaded JSON for schema/status and fixed false fields.
- Write `artifacts/o7_live_relay_headless_browser_smoke.json`.
- Keep all mission and safety fields fixed false:
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
- `docs/product/pc_tools_workstation.md` only if workstation usage changes.
- `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/tech-done.md`
- `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/`

Do not modify during implementation:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- Existing closed sprint files
- Robot control, hardware, Nav2, UART, WAVE ROVER, route execution, HIL, production cloud credentials, OSS/CDN credentials, 4G/SIM or tunnel configuration

## 接口影响

Preferred implementation should reuse existing endpoints and avoid adding product runtime API:

- `GET /api/health`
- `GET /api/o7/operator-console`
- `GET /api/o7/cloud-operator-console-probe?baseUrl=<local-loopback-url>`

Acceptable helper behavior:

- Start server with `HOST=127.0.0.1` and a deterministic port such as `17002`, or choose the next free loopback port and record it.
- Poll `/api/health` until ready.
- Launch `headless Chrome` against each target URL.
- Read the browser-loaded body as JSON.
- Validate schemas and fixed false fields.
- Stop the server and browser process cleanly.
- Write the artifact under this sprint only.

## Artifact Contract

Required artifact shape:

```json
{
  "schema": "trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1",
  "proof_boundary": "software_proof_o7_live_relay_headless_browser_smoke_only",
  "artifact_status": "headless_browser_smoke_ready_not_delivery_proof",
  "endpoint_transport": "live_loopback_http_socket",
  "browser_runtime": "headless_chrome",
  "browser_smoke_status": "live_headless_chrome_executed",
  "server_started": true,
  "http_smoke_executed": true,
  "headless_browser_smoke_executed": true,
  "delivery_success": false,
  "safe_to_control": false,
  "route_execution_success": false,
  "hil_pass": false,
  "robot_control_executed": false,
  "connects_cloud_production": false
}
```

`browser_smoke_status=not_run_http_only_minimum` is explicitly rejected for this sprint completion. If Chrome cannot run, implementation must fail closed and document the blocker rather than accepting HTTP-only evidence.

## 验收命令

Implementation owner must run:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
```

Implementation owner must also run a live headless browser smoke. Preferred command if a script is added:

```bash
cd pc-tools/workstation && npm run smoke:o7-live-relay-headless-browser -- --artifact ../../sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/o7_live_relay_headless_browser_smoke.json
```

Fallback manual shape if no script is added:

```bash
cd pc-tools/workstation
HOST=127.0.0.1 PORT=17002 npm run api
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless=new --disable-gpu --dump-dom http://127.0.0.1:17002/api/health
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless=new --disable-gpu --dump-dom http://127.0.0.1:17002/api/o7/operator-console
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless=new --disable-gpu --dump-dom 'http://127.0.0.1:17002/api/o7/cloud-operator-console-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A17002'
```

Implementation owner must assert artifact anchors:

```bash
rg -n "trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1|software_proof_o7_live_relay_headless_browser_smoke_only|headless Chrome|browser_smoke_status=live_headless_chrome_executed|headless_browser_smoke_executed=true|endpoint_transport=live_loopback_http_socket|server_started=true|http_smoke_executed=true|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false" pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke
```

Planning-stage validation for this Product plan:

```bash
test -f sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/pre_start.md && test -f sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/prd.md && test -f sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|约 85%|headless Chrome|browser_smoke_status|not_run_http_only_minimum|software_proof_o7_live_relay_headless_browser_smoke_only|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false" sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke
git diff --check -- sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke
```

## Owner Prompt for Implementation

Use `full-stack-software-engineer` as the single implementation owner.

Task:

- Implement headless Chrome browser smoke artifact generation against the existing PC/O7 live relay endpoints.
- Do not create another UI panel.
- Do not create jsdom-only browser proof.
- Do not accept HTTP-only evidence for this sprint.
- Use real headless Chrome against a started workstation loopback server.
- Keep proof boundary `software_proof_o7_live_relay_headless_browser_smoke_only`.

Output requirements:

1. Actual changed files.
2. Validation command outputs.
3. Failure root cause if any.
4. Remaining risks.

## 验收判断

Accept only if:

- A sprint artifact exists and records `browser_runtime=headless_chrome`.
- `browser_smoke_status=live_headless_chrome_executed`.
- `/api/health`, `/api/o7/operator-console`, and `/api/o7/cloud-operator-console-probe` were loaded by a real headless Chrome process from a live server.
- Artifact schema and proof boundary match this plan.
- Fixed false fields remain false.
- Tests/build/lint/scoped diff check pass, or failures are repaired and re-run.

Reject if:

- Evidence is only unit test, fixture, jsdom, snapshot, status panel, readback wrapper, CLI export, curl-only, or HTTP-only.
- Artifact keeps `browser_smoke_status=not_run_http_only_minimum` as the final state.
- Artifact claims route execution, delivery success, HIL pass, safe-to-control, production cloud connected, real DB/queue/OSS/CDN connected, or robot control side effects.
- Implementation touches hardware/Nav2/control paths without a new plan and owner split.

## 风险和剩余阻塞

- This remains `software_proof`; it does not prove production cloud, public HTTPS/TLS, 4G/SIM, DB/queue, OSS/CDN, real phone/browser production path, route execution, delivery/operator acceptance, HIL, or safe-to-control.
- If local Chrome is absent or cannot run headless, implementation should record a blocker and return fail-closed; Product should not accept an HTTP-only downgrade as completion.
- O5 will remain about 85% unless this sprint unexpectedly consumes success-class external production evidence, which is not expected.

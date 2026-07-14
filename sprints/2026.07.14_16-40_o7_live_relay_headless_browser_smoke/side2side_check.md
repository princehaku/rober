# Side2Side Check - O7 Live Relay Headless Browser Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/`
- Product closeout time: 2026-07-14 16-40 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Product status: `accepted_support_only_no_okr_lift`
- Proof boundary: `software_proof_o7_live_relay_headless_browser_smoke_only`

## 用户价值和产品北极星

产品北极星仍是普通手机/PC 用户可以可验证地发起、观察和复验垃圾投递任务。本轮用户价值是把上一轮 live HTTP-only smoke 推进为真实本机 `headless_chrome` browser runtime 对 live loopback relay contract 的复验材料，而不是再做一个 status panel、jsdom artifact、CLI export 或 readback wrapper。

Product 接受本 sprint 为 O7/O5 supporting headless Chrome live relay software proof only。它证明本机真实 Chrome headless 进程加载了 live relay JSON contract；不证明 production cloud、真实手机/browser production proof、public HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、route execution、delivery/operator acceptance、HIL、safe-to-control 或 robot control。

## Side-by-side Acceptance

| Item | Planned acceptance | Observed artifact | Product judgment |
| --- | --- | --- | --- |
| Artifact schema | `trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1` | Matched | Accept |
| Proof boundary | `software_proof_o7_live_relay_headless_browser_smoke_only` | Matched | Accept support-only |
| Artifact status | `headless_browser_smoke_ready_not_delivery_proof` | Matched | Accept |
| Endpoint transport | `live_loopback_http_socket` | Matched | Accept |
| Browser runtime | `headless_chrome` | Matched | Accept |
| Browser smoke status | `live_headless_chrome_executed` | Matched | Accept |
| Server and smoke booleans | `server_started=true`, `http_smoke_executed=true`, `headless_browser_smoke_executed=true` | Matched | Accept |
| `/api/health` schema | `trashbot.pc_tools_workstation.health.v1` | Matched | Accept |
| `/api/o7/operator-console` schema | `trashbot.o7.operator_console.v1` | Matched | Accept |
| `/api/o7/cloud-operator-console-probe` schema | `trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1` | Matched | Accept |
| Probe status | `loaded_fail_closed_contract` | Matched | Accept |
| Fixed false fields | `delivery_success=false`, `safe_to_control=false`, `route_execution_success=false`, `hil_pass=false`, `robot_control_executed=false`, `connects_cloud_production=false` | Matched | Accept |

## Compared With Previous Sprint

Previous sprint `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/final.md` accepted only live HTTP socket proof: `browser_smoke_status=not_run_http_only_minimum` and `browser_runtime=not_configured_in_workstation_package`.

This sprint is stronger because it uses a real `headless_chrome` process and records `browser_smoke_status=live_headless_chrome_executed`. It is still support-only because the endpoint is local loopback and every delivery/control/HIL/production field remains false.

## OKR Mapping And Direction

- Direction judgment: `继续但不计分`. The sprint closes the exact browser automation gap from 15:38, but it does not cross the O5 production/cloud or mission execution gate.
- O5 remains about `85%`.
- O1 remains about `94%`.
- O6/O7 remains about `93%`.
- KR archival: `不归档`.

## Rejected Claims

This sprint does not prove production cloud, real phone/browser production proof, public HTTPS/TLS, 4G/SIM, production DB/queue, OSS/CDN, route execution, delivery/operator acceptance, real delivery success, HIL, safe-to-control, robot control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or robot movement.

## Next Required Evidence

Next run should not repeat HTTP-only smoke, headless browser smoke, jsdom artifact, CLI export, readiness packet, terminal-result/readback/export wrappers, voice/offline smoke, or route readiness/precheck. The next scoring move requires success-class O5 production/cloud evidence or explicit same-window live route execution + terminal result + operator/dropoff + HIL/safe-to-control evidence.

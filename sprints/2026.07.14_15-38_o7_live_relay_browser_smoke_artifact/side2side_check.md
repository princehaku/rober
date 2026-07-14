# Side2Side Check - O7 Live Relay Browser Smoke Artifact

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/`
- Check time: 2026-07-14 15:38 CST closeout
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Product status: `accepted_support_only_no_okr_lift`
- Proof boundary: `software_proof_o7_live_relay_browser_smoke_artifact_only`

## 用户价值和产品北极星

北极星仍是普通用户通过手机/PC 入口可验证地完成垃圾投递闭环。本轮没有证明送达闭环，但把 O7 operator console 的复验方式从 jsdom/test stub 推进到本机 live loopback HTTP socket：现场 owner 可以运行 `npm run smoke:o7-live-relay-browser`，启动 workstation server，并用真实 HTTP 访问 operator console/probe endpoints 生成 artifact。

本轮强于 `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/` 的 jsdom-only browser artifact，因为 transport 从 `vitest_fetch_stub_no_socket` 升级为 `endpoint_transport=live_loopback_http_socket`。但它仍不是 browser automation，因为 `browser_smoke_status=not_run_http_only_minimum`，且 artifact 明确记录 browser automation was not run。

## Side-by-side Acceptance

| 验收项 | 计划要求 | 本轮观察 | Product 判断 |
| --- | --- | --- | --- |
| Live server | 启动本机 workstation server | `server_started=true`，`server_base_url=http://127.0.0.1:17001` | Accept |
| Transport | 真实 loopback HTTP 或更强 browser | `endpoint_transport=live_loopback_http_socket` | Accept as live HTTP minimum |
| HTTP smoke | 访问 health、operator console、cloud probe | `http_smoke_executed=true`，三个 endpoint 均 HTTP 200 | Accept |
| Browser runtime | 可选 live browser；不可用时必须明示 | `browser_smoke_status=not_run_http_only_minimum`，`browser_runtime=not_configured_in_workstation_package` | Accept with browser gap |
| Operator contract | O7 operator console schema | `operator_console_schema=trashbot.o7.operator_console.v1` | Accept |
| Cloud probe contract | O7 cloud operator probe schema/status | `cloud_operator_console_probe_schema=trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1`，`probe_status=loaded_fail_closed_contract` | Accept |
| Safety false fields | Dangerous fields must stay false | `delivery_success=false`、`safe_to_control=false`、`route_execution_success=false`、`hil_pass=false`、`robot_control_executed=false`、`connects_cloud_production=false` | Accept |

## OKR 映射和方向判断

- Product direction: `调整`，不继续 O5 CLI/export/readiness/terminal-result wrapper；接受一个更强的 O7/O5 supporting smoke artifact。
- O5 remains about `85%` because this is not success-class production/cloud evidence.
- O1 remains about `94%` because this does not touch live WAVE ROVER HIL, route execution, or safe-to-control.
- O6/O7 remains about `93%` because this is support-only live loopback HTTP proof, not production cloud, real browser automation, delivery, or operator acceptance.
- KR archival: `不归档`.

## Accepted Claims

- Accepted as `software_proof_o7_live_relay_browser_smoke_artifact_only`.
- Accepted as stronger than jsdom-only O7 operator dropoff browser artifact because it uses `live_loopback_http_socket`.
- Accepted as live HTTP minimum for O7 operator console/probe fail-closed contract.
- Accepted validation evidence: live smoke command passed, `python3 -m json.tool` passed, `npm run test` passed with 3 files / 525 tests, `npm run build` passed with existing Vite large chunk warning, `npm run lint` passed, required `rg` and scoped `git diff --check` passed.

## Rejected Claims

This sprint is not browser automation, production cloud, public HTTPS/TLS, 4G/SIM, production DB/queue, OSS/CDN, route execution, delivery/operator acceptance, HIL, safe-to-control, robot control proof, real phone/browser production proof, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or robot movement.

Fixed false fields remain accepted and required:

- `delivery_success=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## 需要补齐的证据链

- Real browser automation against the live workstation runtime, if the workstation package later configures Playwright or equivalent.
- Success-class O5 production/cloud evidence: public HTTPS/TLS success, production DB/queue, worker cutover, OSS/CDN live traffic, 4G/SIM, or true phone/browser production proof.
- Explicit same-window live route/HIL/delivery/operator evidence before any route execution, delivery success, HIL, or safe-to-control claim.

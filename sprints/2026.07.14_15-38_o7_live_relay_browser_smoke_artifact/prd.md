# PRD - O7 Live Relay Browser Smoke Artifact

## 背景和问题

O5 当前约 85%，是最低 Objective，但最近 O5/O6/O7 已经连续产出 CLI export、readiness packet、terminal-result/readback/export、voice/offline smoke、route readiness precheck 等 support-only 材料。继续做类似 wrapper 会重复消费同一个 blocker：没有真实 production/cloud success evidence，也没有 live route/HIL/delivery/operator evidence。

PC/O7 工作站已有 operator console、cloud operator console probe 和 selected-task consumer-read 能力。已有 `o7_operator_dropoff_browser_artifact` 证明了测试内 UI/DOM artifact，但其 transport 是 `vitest_fetch_stub_no_socket`，不等于现场 owner 可以启动本机服务后复验的 live relay/browser smoke。

本轮产品目标是把 O7 operator console 复验方式从测试内 stub 推进到 live relay smoke artifact：真实启动本机 workstation server，真实 HTTP 访问 operator console/probe endpoints，保存 artifact，供后续普通用户/现场 owner 复验。

## 用户价值和产品北极星

目标用户是不会 ROS2、不会读测试 fixture 的现场 owner 或普通操作者。TA 需要知道 PC/O7 operator console 当前是否能通过一个真实本机服务入口被访问，并且所有危险能力是否继续 fail closed。

北极星是普通用户通过手机/PC 入口可验证地完成垃圾投递闭环。本轮只推进用户触点侧的 live-smoke 可复验性，不把它包装成送达、云端生产或机器人控制完成。

## OKR 映射和方向判断

- Objective 5: O5 当前约 85%，最低。生产云、4G/SIM、production DB/queue、OSS/CDN success-class evidence 当前不可用。
- Objective 7 / O7: 当前约 93%。本轮消费 O7 PC workstation live relay/browser 证据，作为支持 O5/O7 后续现场复验的材料。
- Direction: `调整`。不继续 O5 wrapper；转向可复验 live HTTP/browser artifact。
- Scoring: 默认不提升 OKR 百分比，不归档 KR。只有真实 production/cloud success、same-window live route execution、delivery/operator acceptance、HIL 或 safe-to-control 证据出现时才重新评估。

## 产品需求

### 必须实现

1. 启动本机 `pc-tools/workstation` Node/Express server，记录启动命令、host、port、PID 或等效进程标识。
2. 对 live server 执行真实 HTTP smoke，至少访问：
   - `GET /api/health`
   - `GET /api/o7/operator-console`
   - `GET /api/o7/cloud-operator-console-probe?baseUrl=<same-live-loopback-server>`
3. 生成 sprint artifact：
   - `schema=trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1`
   - `proof_boundary=software_proof_o7_live_relay_browser_smoke_artifact_only`
   - `endpoint_transport=live_loopback_http_socket`
   - `server_started=true`
   - `http_smoke_executed=true`
   - `browser_smoke_status=live_browser_executed|not_run_http_only_minimum`
4. Artifact 必须保留 fixed false fields：
   - `delivery_success=false`
   - `safe_to_control=false`
   - `route_execution_success=false`
   - `hil_pass=false`
   - `robot_control_executed=false`
   - `connects_cloud_production=false`
5. Artifact 必须写入 blocked/not-proven：
   - not production cloud
   - not real phone/browser production proof
   - not route execution
   - not delivery success
   - not HIL
   - not safe-to-control

### 可以实现

- 如果工程环境已有 Playwright 或可用 live browser runtime，可以访问 live workstation UI 并点击 O7 probe 入口，保存浏览器层 smoke summary。
- 如果没有 browser runtime，最低限度 live HTTP smoke 仍可接受，但必须明确 `browser_smoke_status=not_run_http_only_minimum`。

### 明确不做

- 不新增 UI panel。
- 不做静态 jsdom-only DOM artifact。
- 不重复 CLI export、readiness packet、terminal-result/readback/export wrapper、voice/offline smoke 或 route readiness precheck。
- 不连接公网云、production DB/queue、OSS/CDN、4G/SIM。
- 不发送 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或任何机器人控制命令。

## 验收口径

本轮验收必须看到一个 live relay/browser smoke artifact。最低可接受证据：

```text
schema=trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1
proof_boundary=software_proof_o7_live_relay_browser_smoke_artifact_only
endpoint_transport=live_loopback_http_socket
server_started=true
http_smoke_executed=true
operator_console_schema=trashbot.o7.operator_console.v1
cloud_operator_console_probe_schema=trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1
probe_status=loaded_fail_closed_contract
delivery_success=false
safe_to_control=false
route_execution_success=false
hil_pass=false
```

Rejected evidence:

- `endpoint_transport=vitest_fetch_stub_no_socket`
- jsdom-only artifact
- snapshot-only UI text
- server not started
- only unit tests without live HTTP
- any artifact claiming delivery success, route execution success, HIL pass, safe-to-control, production cloud connected, or robot command side effect

## 对应责任 Engineer

- Primary: `full-stack-software-engineer`
- Consultation only: `robot-software-engineer` if a Robot/API relay fact must be clarified.
- No Hardware/Algorithm owner in this sprint, because no `/cmd_vel`, UART, HIL, Nav2, route execution, map, scan, TF, or camera hardware path is in scope.

## 风险和剩余证据链

- This is still `software_proof`; it does not close O5 production/cloud success.
- A loopback server can prove route reachability and fail-closed contracts, but not real 4G/SIM, public HTTPS/TLS, production DB/queue, or OSS/CDN.
- Live HTTP smoke can be accepted without live browser only as a minimum. The final closeout must state whether browser runtime was actually executed.
- Future countable evidence still needs one of: success-class O5 production/cloud evidence, same-window live route execution result, same-task delivery/operator acceptance, current live HIL pass, or safe-to-control evidence.

## 已完成 KR 历史记录位置

No KR moves to history in this planning step. Relevant support-only historical records remain in:

- `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/final.md`
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md`
- `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/final.md`
- `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/final.md`

## 需要创建或更新的 sprint 文档

- This planning step creates `pre_start.md`, `prd.md`, and `tech-plan.md`.
- Implementation must create `tech-done.md`.
- Product acceptance must create `side2side_check.md` and `final.md`.

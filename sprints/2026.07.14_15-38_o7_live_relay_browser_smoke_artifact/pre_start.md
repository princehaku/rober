# Pre Start - O7 Live Relay Browser Smoke Artifact

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/`
- Start time: 2026-07-14 15:38 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Supporting owner: `robot-software-engineer` only if the live HTTP smoke needs Robot/API relay facts beyond the PC workstation.
- Product status: `planned`

## 用户价值和产品北极星

北极星仍是让普通用户可以通过手机/PC 操作入口可验证地发起、观察和复验送垃圾任务，而不是让工程同学继续阅读一串 support-only packet。当前缺口不是又一个状态面板，而是让现场 owner 能在本机启动真实 PC/O7 workstation relay/server，用真实 HTTP 或 live browser 访问路径复验 O7 operator console 的 fail-closed contract，并留下一个可复验 artifact。

这能服务普通用户路径的下一步：现场 owner 不需要翻测试 fixture 或 jsdom 日志，只要启动本机工作站服务、访问固定 URL、保存 smoke artifact，就能知道当前 PC/O7 入口能否通过 live relay/browser 链路读取安全 console contract。

## OKR 映射和方向判断

- 当前最低 Objective 是 Objective 5，O5 当前约 85%。O1 约 94%，O6/O7 约 93%。
- 最近关闭 sprint `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/` 已明确 O5 CLI export refresh 是 support-only，不能重复 CLI export、readiness packet、terminal-result/readback/export wrapper、voice/offline smoke 或 route readiness precheck。
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/` 已消费 `field_execution_pack` inventory/pivot，并以 `blocked_missing_new_field_execution_material` 收口；不能原样重复材料盘点。
- 本轮方向判断：`调整`。O5 是最低，但 production/cloud success evidence 当前不可用；为避免连续消费 O5 wrapper，本轮转向 O7/O5 supporting evidence，要求生成 live relay browser smoke artifact。
- 本轮不是 O5 production/cloud success、不是 route execution、不是 delivery success、不是 HIL，也不应提升 OKR 百分比，除非 implementation 后出现真实 success-class external evidence。

## KR 拆解、更新或历史归档

- 当前 KR 不归档：O5 production/cloud success evidence 仍缺；O6/O7 live operator/browser 证据仍不是 production cloud 或 delivery success；O1/O3 live route/HIL 证据仍缺。
- 本轮 KR 拆解只新增一个 supporting evidence 抓手：把 PC/O7 operator console 从测试内 stub artifact 推进到 live loopback HTTP 或 live browser smoke artifact。
- 已完成 KR 历史记录不移动：最近 O5 CLI export refresh、O7 operator dropoff browser artifact、voice runtime preflight/offline smoke 均保留在各自 sprint final/tech-done 里，继续作为 support-only 历史证据，不进入当前 KR 完成区。

## 本轮核心抓手

核心抓手是 `live relay` + `browser smoke` 的可复验 artifact，而不是新增 UI panel 或静态 DOM 证明。

最低可接受实现是 live HTTP smoke：

1. 启动 `pc-tools/workstation` 本机 Node/Express server。
2. 通过真实 loopback socket 访问 `/api/health`、`/api/o7/operator-console` 和 `/api/o7/cloud-operator-console-probe?baseUrl=<same-live-loopback-server>`。
3. 生成 sprint artifact，记录监听地址、HTTP status、schema、probe status、固定 false fields、proof boundary 和命令摘要。

如果 runtime 支持浏览器层，则再用 live browser 访问同一 live server；但不能用 jsdom-only DOM artifact 替代 live HTTP。

## 需要做什么

- 由 `full-stack-software-engineer` 单线闭环实现 smoke artifact 生成和验证。
- 优先复用现有 `pc-tools/workstation` Node/Express endpoints：`/api/health`、`/api/o7/operator-console`、`/api/o7/cloud-operator-console-probe`。
- 生成 artifact 建议路径：`sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/o7_live_relay_browser_smoke_artifact.json`。
- 完成后更新本 sprint `tech-done.md`；若实现改变 PC workstation 行为或 docs 状态，同步更新 `docs/product/pc_tools_workstation.md`。

## 优先级和验收口径

- Priority: P0 for the next implementable O7/O5 supporting evidence lane, because O5 is lowest but O5 production/cloud success evidence is unavailable.
- Acceptance: artifact must prove `endpoint_transport=live_loopback_http_socket` or stronger live browser transport.
- Acceptance: artifact must include `schema=trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1`.
- Acceptance: artifact must include real HTTP response observations from the live server, not fixture-only or jsdom-only events.
- Acceptance: artifact must keep `delivery_success=false`, `safe_to_control=false`, `route_execution_success=false`, and `hil_pass=false`.
- Rejection: another readback/status panel, CLI export, readiness packet, terminal-result wrapper, voice/offline smoke, route readiness precheck, or static browser artifact without live server access.

## 风险、阻塞和证据链

- O5 production/cloud success evidence is still unavailable, so this sprint remains `software_proof` unless new external material appears.
- If port binding fails on the default workstation port, implementation may choose a deterministic alternate loopback port and record it in the artifact.
- If live browser automation is unavailable, minimum live HTTP smoke is acceptable, but the artifact must explicitly say `browser_runtime=not_run_http_only_minimum`.
- This is not another wrapper: the artifact is accepted only if it proves a live loopback server path was started and queried by real HTTP.

Fixed false fields for this sprint:

- `delivery_success=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## 需要创建或更新的 sprint 文档

- Planning now: `pre_start.md`, `prd.md`, `tech-plan.md`.
- Implementation later: `tech-done.md`.
- Acceptance later: `side2side_check.md`, `final.md`.

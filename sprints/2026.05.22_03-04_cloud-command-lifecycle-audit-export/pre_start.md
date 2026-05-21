# Cloud Command Lifecycle Audit Export Pre-start

Run time: 2026-05-22 03:04 Asia/Shanghai

## Sprint Declaration

- sprint_type: epic
- capability: `cloud_command_lifecycle_audit_export`
- evidence_boundary: `software_proof_docker_cloud_command_lifecycle_audit_export_gate`
- target status: `not_proven`
- fixed safety fields: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`
- latest prior sprint: `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack`

## User Value And Product North Star

本轮用户价值是让 support / field owner 在真实 O5 外部材料缺失时，仍能用同一条 phone-safe command lifecycle timeline 复盘命令卡在哪里：enqueue、robot poll / next-command、ACK lookup、accepted / processing、terminal-result pending 都要串到同一个 safe `command_id` / `evidence_ref` 上。

产品北极星仍是低成本 ROS2 自主垃圾投递机器人：普通手机用户不需要懂 ROS2、SSH、串口、云队列或 ACK 语义，也能看到安全状态；support 能复制一段安全摘要去追 verified terminal delivery / dropoff / cancel result。本轮不追求真实云证明或真实送达，只补齐一个可审计、可复制、fail-closed 的 O5 command lifecycle audit/export 功能。

## Evidence Read Before Start

- `OKR.md` 4.1 当前显示 Objective 5 最低，约 68%；Objective 1 约 81%；Objective 2/3/4 约 99%。
- 最新 sprint `sprints/2026.05.22_02-03_field-evidence-material-blocker-escalation-pack/final.md` 已把缺真实 O5 external proof、O1 PR #5 hardware/HIL materials、O2/O3/O4 route/elevator/phone field materials 统一升级为 blocker escalation pack，并明确 no real materials supplied。
- 近期 O5 已完成 `cloud_ack_accepted_result_pending_guard` 和 `cloud_terminal_result_verification_guard`，但仍缺可复制、可审计的 command lifecycle timeline/export，把 command enqueue、robot poll/next-command、ACK lookup/accepted/processing、terminal-result pending 串成同一条 safe `command_id` / `evidence_ref` 证据链。
- GitHub PR #5 live review thread evidence：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved/material pending；comment `3269642220` 是 software-proof reply publication，不是 reviewer resolution。
- PR #6 是 README docs-only，不提供 runtime、hardware、cloud、phone proof。
- 当前主机只有 Docker，没有真实硬件、真实串口、真实手机、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、verified terminal delivery/dropoff/cancel result。
- `docs/product/remote_4g_mvp.md` 已定义 phone app/web -> cloud API -> robot outbound polling -> behavior 的 4G 控制面，并明确 terminal-result pending guard 不能证明 delivery success。
- `docs/product/mobile_user_flow.md` 已要求 mobile/web 对 pending ACK、accepted-result-pending、terminal-result-verification-pending 保持 Start Delivery / Confirm Dropoff / Cancel disabled。

## Why This Is The Next Sprint

Objective 5 仍是最低项，但上一轮已经把缺真实外部材料升级成 blocker escalation pack。继续做另一个材料缺失 wrapper 会重复消费同一 blocker；本轮改为补一个具体 O5 功能：把 command 生命周期的安全状态跨 Robot/API 与 mobile/web 对齐，形成可复制 audit/export summary，帮助 support 用同一 `command_id` / `evidence_ref` 追 verified terminal result。

本 sprint 不提高真实 proof 百分比，因为没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实手机/browser、verified terminal delivery/dropoff/cancel result。它只提升 Docker/local software proof 的可审计性和支持交接能力。

## Scope Boundary

In scope:

- Robot/API 暴露 phone-safe command lifecycle audit/export summary。
- Mobile/web 增加只读 lifecycle panel、fixture 与 copy/export 行为。
- Hardware read-only consultation 防止 O1/HIL/PR #5 overclaim。
- Product closeout 后续更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`。

Out of scope:

- 不改真实云、DB/queue、OSS/CDN、TLS、公网入口、4G/SIM 或生产部署。
- 不运行真实硬件、真实串口、WAVE ROVER、HIL、真实手机/browser 或 route/elevator field run。
- 不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- 不关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`，不把 comment `3269642220` 写成 reviewer resolution。
- 不声明 verified terminal delivery/dropoff/cancel result、dropoff completion、cancel completion、delivery success 或真实 O5 external proof。

## Owners

- Robot Platform Engineer：实现 Robot/API diagnostics/status safe summary 与接口文档，保持控制面 fail-closed。
- User Touchpoint Full-Stack Engineer：实现 mobile/web 只读 panel、fixture、样式与产品文档同步，提供 safe copy/export。
- Hardware Infra Engineer：read-only consultation；必须读 `docs/vendor/VENDOR_INDEX.md`，确认本轮不构成 O1/HIL/PR #5 hardware material proof。
- Product Manager / OKR Owner：后续 closeout，更新 OKR/progress log/sprint 收口文档，核对文档同步与证据边界。

## Risks And Blockers To Preserve

- O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 和 verified terminal delivery/dropoff/cancel result。
- O1 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry，缺 WAVE ROVER powered bench/UART/HIL logs；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending。
- O2/O3/O4 仍缺真实 task record、Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser 证据和 route/elevator field pass。
- 本轮所有输出必须保持 `software_proof_docker_cloud_command_lifecycle_audit_export_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。


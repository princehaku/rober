# Cloud Command Lifecycle Acceptance Mobile Export Panel Pre-Start

Run time: 2026-05-24 08:01 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

本轮继续围绕产品北极星：普通手机用户和支持人员不用 SSH、ROS2、串口或云后台知识，也能看到一次云命令生命周期验收包的安全解释、当前阻塞原因和下一步证据需求。

用户价值不是让手机端发起新控制，而是把上一轮只读 HTTP export 变成手机/支持视图可消费的 read-only 面板：当命令已经 accepted/processing 但 verified terminal result 仍缺失时，用户触点能解释为什么 Start Delivery、Confirm Dropoff、Cancel 必须继续禁用。

## OKR 映射

- 目标 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，当前约 68%，仍是最低 Objective。
- 关联 Objective 4：手机端可理解的支持视图，但本轮不作为 Objective 4 真实手机验收，也不是 true phone/browser proof。
- 不改变 Objective 1/2/3：本轮不触碰 WAVE ROVER、UART、HIL、Nav2/fixed-route、route/elevator field pass 或 delivery success。

## 证据基础

- live `OKR.md` 4.1 最新 sprint 是 `2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export`，Objective 5 仍最低，约 68%；Objective 1 约 81%，Objective 2/3/4 约 99%。
- 上轮已完成 `cloud_command_lifecycle_replay_acceptance_packet_http_export`，独立 cloud relay 暴露只读 HTTP GET route `/api/support/cloud-command-lifecycle-replay-acceptance-packet-export`，边界为 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`，no OKR percentage lift。
- 上轮 final 明确仍缺真实公网 HTTPS/TLS、4G/SIM、真实手机/browser、OSS/CDN live traffic、production DB/queue、worker/cutover、HIL、WAVE ROVER/UART、verified terminal result 和 delivery success。
- PR #5 live review threads 中 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，要求 vendor sources for mandatory 2D LiDAR / ToF assumptions and real materials；PR #7 open 但没有 review threads。
- Automation memory 04:26 已过时，live repo 07-08 sprint 和 `OKR.md` 作为本轮 source of truth。

## 本轮核心抓手

能力名：`cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`

本轮将现有 HTTP support export 的安全验收包数据消费到 `mobile/web` 的只读 phone/support-facing panel 或 support export view。面板只展示 safe fields、safe copy、owner handoff、next required evidence、accepted/processing ACK 语义和阻塞边界；不新增控制动作，不回放命令，不请求 ACK/cursor，不上传材料，不触发 GitHub action。

目标 evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate
```

## 需要做什么

1. Full-Stack：在 `mobile/web` 增加只读面板，消费 existing HTTP export/support packet data 或同源 fixture/status summary，显示 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
2. Robot：只读核对 HTTP export 与 Robot diagnostics safe alias 的字段兼容性，确认不会把 support export 接成控制面；仅在缺关键 summary alias 时才允许补最小兼容。
3. Product：实施完成后收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，保守写明 no OKR percentage lift。

## 优先级和验收口径

- P0：手机/支持视图必须展示 `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`，并保留 `software_proof_docker`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- P0：主操作 Start Delivery、Confirm Dropoff、Cancel 不得因该面板启用；面板不得 fetch raw diagnostics、raw materials、ACK/cursor route、command route 或 replay route。
- P0：明确写出 not true phone/browser proof、不是 public HTTPS/TLS、不是 4G/SIM、不是 OSS/CDN live traffic、不是 production DB/queue、不是 HIL、不是 PR #5 resolution、不是 delivery success。
- P1：复用现有 `mobile/web` 面板和 fixture 命名风格，避免新增宽泛测试；验证只跑 fenced checks。
- P2：文档同步 `docs/product/mobile_user_flow.md`，必要时同步 `docs/product/remote_4g_mvp.md`。

## 对应责任 Engineer

- `full-stack-software-engineer`：主责 `mobile/web` panel、fixture、targeted mobile test、相关 product docs。
- `robot-software-engineer`：并行只读咨询和兼容性核对；仅在 safe alias 缺失时补最小字段。
- `product-okr-owner`：完成后负责 sprint closeout、OKR 保守更新和进度日志。

## 风险、阻塞和需要补齐的证据链

- 本机没有真实硬件，只有 Docker；本轮只能形成 `software_proof_docker` / local fixture proof。
- 缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover，所以不能提升 Objective 5 百分比。
- 缺真实手机设备/browser、production app、PWA prompt/userChoice，所以不是 Objective 4 true phone/browser proof。
- 缺 HIL、WAVE ROVER/UART、Nav2/fixed-route runtime、route/elevator field pass、verified terminal delivery/dropoff/cancel result 和 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；本轮不解决 2D LiDAR / ToF vendor material review。

## 需要创建或更新的 sprint 文档

本轮 planning 阶段创建：

- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/pre_start.md`
- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/prd.md`
- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/tech-plan.md`

实施完成后由对应 owner 更新：

- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/tech-done.md`
- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/side2side_check.md`
- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

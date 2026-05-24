# Cloud Command Lifecycle Acceptance Support Handoff Bundle Pre-Start

Run time: 2026-05-24 09:00 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

本轮继续围绕产品北极星：普通手机用户、field owner 和支持人员不用 SSH、ROS2、串口、云后台或 GitHub review 知识，也能拿到一份只读、脱敏、可复制/下载的 support handoff bundle，用来收集下一轮真实公网、真实手机、真实云资源或真实 terminal result 材料。

用户价值不是让手机端或支持包发起控制，而是把上一轮 mobile export panel / HTTP export 中已经安全展示的 pending-safe command/evidence、accepted-processing-only、terminal-result-pending、owner handoff、next-required-evidence 汇总成一个可交接包。这个包帮助后续收集 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/terminal result 材料，但本轮仍是 Docker/local `software_proof`。

## OKR 映射

- 目标 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，当前约 68%，仍是最低 Objective。
- 关联 Objective 4：手机/支持触点可读、可复制、可下载的交接体验，但本轮是 not true phone/browser proof。
- 不改变 Objective 1/2/3：本轮不触碰 WAVE ROVER、UART、HIL、Nav2/fixed-route、route/elevator field pass、verified terminal result 或 delivery success。

## 证据基础

- live `OKR.md` 4.1 最新 sprint 是 `2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel`，Objective 5 最低约 68%。
- 最新 final 的能力边界是 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`；剩余真实缺口包含 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result、HIL、WAVE ROVER/UART、route/elevator field pass、delivery success。
- Live GitHub PR #5 evidence：PR #5 merged/closed；review threads Q `PRRT_kwDOSWB9286CJ3tQ` and U `PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。Published reply says local vendor sources are attribution only and still miss real 2D LiDAR/ToF SKU/source/receipt, wiring/power/calibration, HIL entry, Nav2/SLAM field pass。
- Live PR #7 is open but has no review threads。
- Host has Docker only, no real hardware；本轮不得宣称 true phone/browser proof、real external cloud proof、HIL、WAVE ROVER/UART proof 或 delivery success。

## 本轮核心抓手

能力名：

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle
```

目标 evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate
```

本轮把 mobile export panel / HTTP export 已经安全归一的 support data 转成 support handoff bundle。Bundle 必须只读、脱敏、可复制/下载，且必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`not true phone/browser proof`、`no OKR percentage lift`。

## 需要做什么

1. Full-Stack：在 `mobile/web` 增加 support handoff bundle panel / fixture / targeted tests，并同步必要的 product docs；bundle 只能消费 safe summary，不得 fetch raw diagnostics、raw materials、ACK/cursor、command、replay/resubmit、GitHub mutation 或 control route。
2. Robot：并行核对 HTTP export / Robot diagnostics 是否已有足够 support bundle summary 或兼容字段；若缺失，补最小 safe summary / compatibility fields，否则只读咨询并写入证据。
3. Product：实施完成后收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，保守写明 Objective 5 保持约 68%，no OKR percentage lift。

## 优先级和验收口径

- P0：support handoff bundle 必须包含 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle`、`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate`、pending-safe command/evidence、`accepted_processing_only_not_delivery_success`、`terminal_result_pending`、owner handoff、next required evidence、redaction status。
- P0：必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，并明确 `not true phone/browser proof`、`no OKR percentage lift`。
- P0：bundle 不得让 Start Delivery、Confirm Dropoff、Cancel 或任何 control path 变为可用；不得自动回放、重发、post ACK、mutate cursor、上传材料或触发 GitHub action。
- P1：bundle 文案中文优先，支持 field owner / support / reviewer 直接复制或下载，用于后续补真实 public HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/terminal result 材料。
- P2：Product closeout 必须保留 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`，不能把 vendor attribution reply 写成硬件材料完成。

## 对应责任 Engineer

- `full-stack-software-engineer`：主责 mobile/web support handoff bundle panel、fixture、targeted tests、相关 product docs。
- `robot-software-engineer`：并行主责 Robot/API safe summary compatibility；优先只读，必要时最小补字段。
- `product-okr-owner`：实施完成后负责 sprint closeout、OKR 保守更新和进度日志。

## 风险、阻塞和需要补齐的证据链

- 本机只有 Docker，没有真实硬件；本轮只能形成 Docker/local `software_proof`。
- Objective 5 仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、多实例/queue ordering/cutover proof，因此不能提升 OKR 百分比。
- Objective 4 仍缺真实 iPhone/Android browser/device、production app、真实 PWA prompt/userChoice，因此本轮 not true phone/browser proof。
- Objective 1 仍缺 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF SKU/source/receipt、安装、接线、电源、标定；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`。
- Objective 2/3 仍缺 route/elevator field pass、Nav2/fixed-route runtime、真实 task record、verified terminal delivery/dropoff/cancel result 和 delivery success。

## 需要创建或更新的 sprint 文档

本轮 planning 阶段创建：

- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/pre_start.md`
- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/prd.md`
- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/tech-plan.md`

实施完成后由对应 owner 更新：

- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/tech-done.md`
- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/side2side_check.md`
- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

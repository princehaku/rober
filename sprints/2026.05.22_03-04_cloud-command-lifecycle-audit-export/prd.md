# Cloud Command Lifecycle Audit Export PRD

Run time: 2026-05-22 03:04 Asia/Shanghai

## Product Goal

新增 `cloud_command_lifecycle_audit_export`：当 O5 仍缺真实外部 proof 时，Robot/API 与 mobile/web 提供同一条 phone-safe command lifecycle audit/export summary，让 support / field owner 能复制 safe timeline，并用同一 `command_id` / `evidence_ref` 去追 verified terminal delivery、dropoff 或 cancel result。

这不是材料缺失 wrapper，也不是 delivery result。它是 O5 command lifecycle 的可审计证据链：command enqueue -> robot poll / next-command -> ACK lookup -> accepted / processing -> terminal-result pending。

## User Value And North Star

普通手机用户只需要知道当前命令还在处理中、还没有 verified terminal result，主操作不能继续；support 需要一个可复制的安全摘要，说明命令在哪个生命周期阶段、对应哪个 safe `command_id` / `evidence_ref`、下一步该找谁补结果材料。

北极星仍是普通手机用户可用的低成本 ROS2 垃圾投递机器人。本轮只降低远程控制和售后诊断的理解成本，不证明真实云、真实手机、真实路线、电梯、HIL 或真实送达。

## OKR Mapping

- Objective 5：主目标。补齐云中转 command/status/ack 产品化中的 audit/export 缺口，让 terminal-result pending 状态可被 phone-safe 复盘和复制。
- Objective 4：次级影响。Mobile/web 增加只读 panel，让普通用户与 support 看到中文优先、fail-closed 的生命周期摘要。
- Objective 1：只做边界防护。Hardware consultation 防止把 PR #5 `PRRT_kwDOSWB9286CJ3tX`、HIL、WAVE ROVER 或传感器材料写成已解决。
- Objective 2/3：不直接推进。Route/elevator/terminal delivery result 仍需真实 field materials，本轮只为追结果提供同一 safe evidence chain。

## KR Breakdown

- KR5-A：Robot/API diagnostics/status 暴露 `cloud_command_lifecycle_audit_export` safe summary，包含 safe `command_id`、safe `evidence_ref`、timeline stages、current lifecycle state、terminal result status、next required evidence、copy/export safe text。
- KR5-B：Summary 必须保持 `software_proof_docker_cloud_command_lifecycle_audit_export_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- KR5-C：Mobile/web 增加只读 lifecycle audit/export panel，展示并复制 safe timeline，不调用 command、ACK、cursor、diagnostics fetch 或 raw artifact route。
- KR5-D：文档同步更新 `docs/interfaces/operator_gateway_diagnostics.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md`，明确本轮不是真实 external cloud proof、不是 terminal delivery result、不是 delivery success。
- KR5-E：Product closeout 后续保守更新 `OKR.md` 与 `docs/process/okr_progress_log.md`；没有真实外部材料时，Objective 5 不因本轮提高真实 proof 百分比。

## Core Lever

核心抓手是把已有 O5 command-safety guard 从“单点状态说明”升级为“同一 command lifecycle timeline/export”。Robot 负责生成安全摘要，mobile/web 负责只读展示和复制，Hardware 负责防止 PR #5/O1 过度声明，Product 负责收口时不把 software proof 写成真实 proof。

## Requirements

### Robot/API

- 输出 schema 建议：`trashbot.cloud_command_lifecycle_audit_export_summary.v1`。
- capability 必须为 `cloud_command_lifecycle_audit_export`。
- evidence boundary 必须为 `software_proof_docker_cloud_command_lifecycle_audit_export_gate`。
- 必须能表达生命周期阶段：
  - command enqueued
  - robot polled next command
  - ACK lookup pending / accepted
  - accepted / processing
  - terminal result pending / missing verified terminal result
- 必须绑定同一 safe `command_id` / `evidence_ref`，并提供 phone-safe `copy_export_text`。
- 必须 fail closed：缺字段、状态冲突、terminal result 未 verified、raw artifact 缺失时均保持 `not_proven` 和 primary actions disabled。

### Mobile/web

- 增加只读 panel，优先消费 Robot diagnostics safe alias；也可消费兼容 nested diagnostics/status summary。
- 展示：lifecycle state、safe command id、safe evidence ref、timeline stages、terminal result status、next required evidence、safe copy/export text、证据边界和固定安全字段。
- Copy/export 只能复制 backend 提供的 phone-safe whitelist 文本；没有 safe copy 时禁用 copy 并显示 blocked/not_proven。
- Start Delivery、Confirm Dropoff、Cancel 保持 disabled；panel 不触发命令、ACK、cursor、diagnostics fetch、raw artifact download 或自动 replay/resubmit。

### Hardware Boundary

- Hardware 只做 read-only consultation。
- 必须读 `docs/vendor/VENDOR_INDEX.md`。
- 本轮不得写成 WAVE ROVER/UART/HIL、2D LiDAR/ToF source/procurement/install/calibration、PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved、route/elevator field pass 或 delivery success。

## Priority And Acceptance

Priority P0:

- Robot/API 与 mobile/web 使用同一 capability、schema/boundary、safe `command_id` / `evidence_ref`、fixed safety fields。
- `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 在 Robot summary、mobile fixture、docs、sprint closeout 中一致。
- Copy/export 必须 phone-safe，不含 credential、Authorization header、signed URL、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、local path、traceback、raw JSON 或完整 artifact。

Priority P1:

- 面板中文优先，说明“命令已接收/处理中，但缺 verified terminal result”。
- 支持 missing summary 的 blocked/not_proven fallback。
- Product closeout 明确 Objective 5 不提高真实 proof 百分比。

## Responsibility

- Robot Platform Engineer：Robot/API diagnostics/status safe summary、接口文档、单元测试。
- User Touchpoint Full-Stack Engineer：mobile/web panel、fixture、样式、entrypoint 测试、mobile product docs。
- Hardware Infra Engineer：read-only boundary consultation，避免 HIL/PR #5/material overclaim。
- Product Manager / OKR Owner：更新 OKR/progress log 与 sprint closeout，确认 docs 同步和证据边界。

## Risks And Evidence Gaps

- 真实 O5 证据仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal delivery/dropoff/cancel result。
- 真实 O1 证据仍缺：PR #5 `PRRT_kwDOSWB9286CJ3tX` 的 2D LiDAR / ToF 真实来源、采购、安装、标定、HIL-entry 和 WAVE ROVER powered bench/UART/HIL logs。
- 真实 O2/O3/O4 证据仍缺：route/elevator field pass、Nav2/fixed-route runtime、task record、dropoff/cancel completion、delivery result、真实手机/browser。
- PR #6 是 README docs-only，不提供 runtime/hardware/cloud/phone proof。

## Sprint Docs To Create Or Update

Planning phase creates:

- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/pre_start.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/prd.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-plan.md`

Implementation/closeout phase must later update:

- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/tech-done.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/side2side_check.md`
- `sprints/2026.05.22_03-04_cloud-command-lifecycle-audit-export/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`


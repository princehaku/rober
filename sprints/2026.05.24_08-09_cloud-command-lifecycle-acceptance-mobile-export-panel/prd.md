# Cloud Command Lifecycle Acceptance Mobile Export Panel PRD

Run time: 2026-05-24 08:01 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

普通手机用户和支持人员需要一个不误导的解释面：命令已进入云命令生命周期 support packet，但仍没有 verified terminal result 时，页面必须直接告诉他们为什么主操作不能继续、下一步该补什么证据、以及这不是送达成功。

产品北极星保持不变：`rober` 是面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。当前 O5 的产品化抓手是让云中转和支持导出材料能被用户触点安全消费，而不是把本地 Docker proof 叙述成真实云、真实手机或真实交付。

## 问题陈述

上轮 `cloud_command_lifecycle_replay_acceptance_packet_http_export` 已提供只读 GET route：

```text
GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export
```

但该 support export 仍停留在 HTTP/API 层。普通用户或 field owner 仍需要在手机/支持视图中看到同一份 safe packet 的关键状态，包括 `accepted_processing_only_not_delivery_success`、`terminal_result_pending`、`owner_handoff`、`next_required_evidence` 和 false-state flags。

## 本轮能力

能力名：

```text
cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel
```

Evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate
```

本轮在 `mobile/web` 增加 read-only phone/support-facing export panel。它可以消费现有 HTTP export/support packet data、Robot diagnostics compatible summary 或同源 fixture，但只能展示 safe fields，不得产生控制、副作用或成功判断。

## OKR 映射

- Objective 5：直接推进最低 Objective 的 support/API-to-phone surface，可提升云命令生命周期 support handoff 的可读性和可复盘性。
- Objective 4：只作为手机界面可解释性的辅助，不计为 true phone/browser proof。
- Objective 1/2/3：不触碰硬件协议、任务状态机、导航路线或电梯实跑。

## KR 拆解或更新

- O5 KR1：保留 commands/status/ack 的安全语义，手机面板只读消费 ACK/terminal-result support packet，不暴露 `/cmd_vel` 或机器人直连控制。
- O5 KR2：继续沿用 cloud relay support surface 和 4G 架构文档，不把本地 HTTP export 当 production cloud hosting。
- O5 KR5：继续保持凭证和敏感字段 redaction；面板不得展示 bearer token、Authorization header、signed URL、DB/queue endpoint、OSS AK/SK、root password、local path、traceback、serial/UART detail 或 WAVE ROVER detail。
- O5 KR6：把缺 verified terminal result 的 graceful degradation 显示到手机/支持视图中，明确等待结果或联系支持，而不是继续主操作。

本轮不更新 OKR 百分比目标；若实施只获得 local/Docker proof，closeout 必须写明 no OKR percentage lift。

## 范围

### In Scope

- `mobile/web/app.js` 增加只读 mobile export panel。
- `mobile/web/fixtures/` 增加或复用 acceptance packet mobile export fixture。
- `mobile/web/test_mobile_web_entrypoint.py` 增加 targeted assertions。
- `docs/product/mobile_user_flow.md` 同步面板、边界和禁用规则。
- `docs/product/remote_4g_mvp.md` 仅在需要时补充 mobile consumption of HTTP export 的边界。
- Robot 只读核对 `cloud_command_lifecycle_replay_acceptance_packet_http_export` 与 diagnostics safe alias 兼容性。

### Out of Scope

- 不新增 POST/command/ACK/cursor/replay/resubmit/material upload/GitHub mutation。
- 不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- 不做真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- 不做真实手机/browser、production app、PWA prompt/userChoice 验收。
- 不做 HIL、WAVE ROVER/UART、Nav2/fixed-route runtime、route/elevator field pass。
- 不解决 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
- 不声明 verified terminal result、dropoff completion、cancel completion 或 delivery success。

## 验收口径

### P0

- 页面能显示 `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel` 的安全摘要。
- 明确展示或可测试定位：
  - `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`
  - `accepted_processing_only_not_delivery_success`
  - `terminal_result_pending`
  - `not_proven`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `safe_to_control=false`
- 面板缺失、unsafe copy、success wording、raw material 或 false-state flags 不齐时 fail closed。
- Start Delivery、Confirm Dropoff、Cancel 保持 disabled。

### P1

- Copy/export 文案只能来自 backend-provided safe copy 或 sanitized fixture fields；否则显示 blocked/unavailable。
- 文案中文优先，解释下一步证据：等待 verified terminal result、联系 support、补真实公网/4G/DB/queue/OSS/CDN 或现场材料。
- `docs/product/mobile_user_flow.md` 和必要的 O5 docs 与实现保持同步。

### P2

- 支持 field owner / support / reviewer 能看懂同一 safe `evidence_ref` 和 safe command id 的下一步，但不暴露 raw command、ACK payload、cursor 或完整 artifact。

## Owner 和优先级

- P0 implementation owner：`full-stack-software-engineer`。
- P0 compatibility consultation owner：`robot-software-engineer`。
- P0 closeout owner：`product-okr-owner`。

优先级顺序：先保证 false-state flags 和禁用主操作，再补 UI copy 和 docs，同步完成 targeted validation；不做 broad test sweep。

## 风险、阻塞和证据链

- 本轮可交付的是 `software_proof_docker` only；not true phone/browser proof。
- 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover，因此不能称为 O5 external proof。
- 没有 HIL、WAVE ROVER/UART、Nav2/fixed-route runtime、route/elevator field pass、verified terminal result 或 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`；本轮只保留可见 blocker，不关闭该 review thread。

## 完成定义

- Full-Stack 返回实际改动文件、targeted validation output、失败定位和剩余风险。
- Robot 返回只读核对结论或最小兼容改动、验证输出和边界风险。
- Product 收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，并写明 no OKR percentage lift。

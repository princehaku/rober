# Cloud Command Lifecycle Acceptance Mobile Export Panel Tech Plan

Run time: 2026-05-24 08:01 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 技术目标

实现 `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`：在 `mobile/web` 增加只读 phone/support-facing panel，消费上一轮 HTTP export/support packet data 或同源 safe fixture/status summary，让用户触点能解释 command lifecycle acceptance packet 的阻塞状态和下一步证据需求。

目标 evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate
```

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 是否针对该最低 Objective：是。本轮把 Objective 5 的 `cloud_command_lifecycle_replay_acceptance_packet_http_export` 继续推进到手机/支持视图消费面。
3. 为什么仍计划 no OKR percentage lift：本轮只是 Docker/local `mobile/web` read-only panel proof，缺真实公网 HTTPS/TLS、4G/SIM、真实手机/browser、OSS/CDN live traffic、production DB/queue、worker/cutover、verified terminal result、HIL、WAVE ROVER/UART、Nav2/fixed-route runtime、route/elevator field pass 和 delivery success。

## Evidence and PR Review Basis

- live `OKR.md` 4.1 最新 sprint：`2026.05.24_07-08_cloud-command-lifecycle-acceptance-http-export`。
- 上轮能力：`cloud_command_lifecycle_replay_acceptance_packet_http_export`。
- 上轮 route：`GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export`。
- 上轮边界：`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`。
- 上轮结论：Objective 5 保持约 68%，no OKR percentage lift；Objective 4 明确 is not true phone/browser proof。
- PR #5 live review：`PRRT_kwDOSWB9286CJ3tQ` resolved；`PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`，要求 vendor sources for mandatory 2D LiDAR / ToF assumptions and real materials。
- PR #7：open but no review threads。
- Automation memory 04:26 stale；本轮以 live repo 07-08 `OKR.md` 和 sprint docs 为 source of truth。

## Owner Split and File Ranges

### Task A - Full-Stack Mobile Export Panel

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet.json`，仅在复用现有 acceptance packet fixture 更合适时可改。
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`，仅在需要补 HTTP export mobile consumption 边界时可改。
- 本 sprint `tech-done.md` 中 Task A 结果段。

要求：

- 增加只读 panel，能力名必须包含 `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`。
- 优先消费 `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_summary`；可 fallback 到 `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_summary`、现有 `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary`、HTTP export compatible payload 或 fixture safe fields。
- 显示 safe command id、safe `evidence_ref`、acceptance packet status、ACK semantics、terminal result status、owner handoff、next required evidence、redaction status、evidence boundary 和 safe copy。
- 保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- Copy button 只能使用 backend-provided `safe_copy` / `support_acceptance_copy` / sanitized support copy；缺失或 unsafe 时显示 blocked/unavailable。
- 不 fetch raw diagnostics、raw materials、command routes、ACK/cursor routes、review routes、material routes、GitHub mutation routes、replay/resubmit routes 或任何控制路径。
- 不启用 Start Delivery、Confirm Dropoff、Cancel。
- 不引入 broad tests；只补 targeted mobile entrypoint assertions。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel
rg -n "cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate|accepted_processing_only_not_delivery_success|terminal_result_pending|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof" mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/tech-done.md
```

### Task B - Robot Read-Only Compatibility Consultation

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/` 中与 `cloud_command_lifecycle_replay_acceptance_packet_http_export` 或 `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary` 直接相关的文件，仅在 mobile panel 无法安全消费必要字段时才改。
- `docs/product/remote_4g_mvp.md`，仅在需要补 Robot/API support export to mobile boundary 时可改。
- 本 sprint `tech-done.md` 中 Task B 结果段。

优先只读要求：

- 核对 HTTP export payload 是否已含 safe command id、safe evidence ref、ACK semantics、terminal result status、owner handoff、next required evidence、redaction status 和 false-state flags。
- 确认 support export 仍 read-only：不 replay/resubmit command、不 post ACK、不 mutate cursor/state、不上传材料、不触发 GitHub action、不控制 Nav2、不触碰 WAVE ROVER/UART、不写 delivery success。
- 确认 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending` 不被本轮 O5 mobile panel 改写。
- 若 changed files none，必须在 `tech-done.md` 写清只读核对证据。

验收命令：

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet_http_export|cloud_command_lifecycle_replay_acceptance_packet|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary|delivery_success|primary_actions_enabled|safe_to_control|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/tech-done.md
```

### Task C - Product Closeout and OKR Update

Owner：`product-okr-owner`

允许改动：

- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/tech-done.md`
- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/side2side_check.md`
- `sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 Task A / Task B 实际改动、验证输出、失败定位和剩余风险。
- 如果只有 Docker/local mobile panel proof，Objective 5 保持约 68%，写明 no OKR percentage lift。
- 必须写明 not true phone/browser proof、not public HTTPS/TLS、not 4G/SIM、not OSS/CDN live traffic、not production DB/queue、not worker/cutover、not HIL、not WAVE ROVER/UART proof、not PR #5 resolved、not delivery success。
- `OKR.md` 必须继续保留 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。

验收命令：

```bash
test -f sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/tech-done.md && test -f sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/side2side_check.md && test -f sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate|Objective 5|not true phone/browser proof|no OKR percentage lift|not delivery success|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel OKR.md docs/process/okr_progress_log.md
```

## 并行启动要求

本轮是 2+ owner Epic sprint，文件范围互不重叠，必须并行派发 2-3 个子 agent：

- `full-stack-software-engineer` 负责 mobile/web implementation、fixture、targeted test 和 product docs。
- `robot-software-engineer` 并行做 read-only compatibility consultation；只有发现字段缺口才做最小 Robot/API safe alias 改动。
- `product-okr-owner` 等 Task A / B 返回后做 closeout 和 OKR 保守更新。

主节点不得自己写产品代码、测试代码或运行实现验证命令；实现、测试、修复和 fenced validation 必须由对应子 agent 执行。主节点只做派发、等待、证据核对、sprint 文档收口和最终汇总。

## 接口影响

本轮默认不新增后端 route；消费既有 route：

```text
GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export
```

允许的 mobile panel data shape：

- `schema`
- `schema_version`
- `capability=cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`
- `source_capability=cloud_command_lifecycle_replay_acceptance_packet_http_export`
- `evidence_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`
- `source_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`
- `safe_command_id`
- `safe_evidence_ref`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `terminal_result_status=terminal_result_pending`
- `owner_handoff`
- `next_required_evidence`
- `redaction_status=passed`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `safe_copy` / `support_acceptance_copy`

响应和 fixture 不得包含：

- bearer token、Authorization header、signed URL、credential-bearing URL。
- DB/queue endpoint、OSS AK/SK、root password。
- local state path、traceback、raw artifact path、checksums、complete artifacts。
- ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER details。
- raw command replay material、raw ACK mutation material、raw GitHub mutation payload。
- success wording、`delivery_success=true`、`primary_actions_enabled=true`、`safe_to_control=true`。

## 验证围栏

只跑 fenced validation：

- `node --check` for changed JS。
- fixture `python3 -m json.tool`。
- targeted `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`。
- required `rg` markers。
- scoped `git diff --check` for touched files。

不跑 broad test sweep，不跑 Docker build，不跑 ROS2/HIL/硬件 smoke，除非 targeted validation 暴露接口破坏且需要 owner 重试。

## 风险与阻塞

- `software_proof_docker` only；not true phone/browser proof。
- 不是 public HTTPS/TLS、不是 4G/SIM、不是 OSS/CDN live traffic、不是 production DB/queue、不是 worker/cutover。
- 不是 HIL、不是 WAVE ROVER/UART proof、不是 Nav2/fixed-route runtime pass、不是 route/elevator field pass。
- 不是 verified terminal delivery/dropoff/cancel result、不是 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`；本轮不是 PR #5 resolution。

## 完成定义

- Task A / B / C 结果写入 `tech-done.md`。
- `side2side_check.md` 对照 PRD P0/P1/P2 验收。
- `final.md` 写清 Objective 5 movement、no OKR percentage lift、证据边界和剩余外部缺口。
- 如实现阶段有 durable change，按用户要求提交并推送远程；planning-only 阶段只提交/推送由后续执行 owner 决定。

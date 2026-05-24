# Cloud Command Lifecycle Acceptance Support Handoff Bundle Tech Plan

Run time: 2026-05-24 09:00 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 技术目标

实现 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle`：把上一轮 mobile export panel / HTTP export 的 pending-safe command/evidence、accepted-processing-only、terminal-result-pending、owner handoff、next-required-evidence 转成只读、脱敏、可复制/下载的 support handoff bundle。

目标 evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate
```

本轮必须保留 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，并明确 not true phone/browser proof、no OKR percentage lift。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 是否针对该最低 Objective：是。本轮继续 Objective 5 的 cloud command lifecycle support/export ladder，把 mobile export panel 的安全解释进一步产品化为 support handoff bundle。
3. 为什么仍计划 no OKR percentage lift：本轮仍是 Docker/local `software_proof`，缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result、HIL、WAVE ROVER/UART、route/elevator field pass 和 delivery success。

## Evidence and PR Review Basis

- live `OKR.md` 4.1 最新 sprint：`2026.05.24_08-09_cloud-command-lifecycle-acceptance-mobile-export-panel`。
- 最新 final 的能力边界：`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`。
- 最新 final 的剩余真实缺口：public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result、HIL、WAVE ROVER/UART、route/elevator field pass、delivery success。
- Live GitHub PR #5：merged/closed；Q `PRRT_kwDOSWB9286CJ3tQ` and U `PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
- PR #5 published reply：local vendor sources are attribution only and still miss real 2D LiDAR/ToF SKU/source/receipt, wiring/power/calibration, HIL entry, Nav2/SLAM field pass。
- Live PR #7：open but no review threads。
- Host has Docker only, no real hardware。

## Owner Split and File Ranges

### Task A - Full-Stack Support Handoff Bundle Panel

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle.json`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel.json`，仅在复用上一轮 fixture 更合适时可最小调整。
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`
- 本 sprint `tech-done.md` 中 Task A 结果段。

要求：

- 增加只读 support handoff bundle panel / copy-download affordance，能力名必须包含 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle`。
- 优先消费 `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_summary`；可 fallback 到 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_summary`、上一轮 mobile export panel summary、HTTP export compatible payload 或 fixture safe fields。
- Bundle 显示 safe command id、safe `evidence_ref`、accepted/processing ACK semantics、terminal result status、owner handoff、support route、reviewer route、next required evidence、redaction status、evidence boundary 和 safe copy/download text。
- 保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`not true phone/browser proof`、`no OKR percentage lift`。
- Copy/download 只能使用 backend-provided `safe_copy` / `support_handoff_copy` / sanitized support copy；缺失或 unsafe 时显示 blocked/unavailable。
- 不 fetch raw diagnostics、raw materials、command routes、ACK/cursor routes、review routes、material routes、GitHub mutation routes、replay/resubmit routes 或任何控制路径。
- 不启用 Start Delivery、Confirm Dropoff、Cancel。
- 不引入 broad tests；只补 targeted mobile entrypoint assertions。

验收命令：

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate|accepted_processing_only_not_delivery_success|terminal_result_pending|owner_handoff|next_required_evidence|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle.json docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle.json docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/tech-done.md
```

### Task B - Robot/API Support Bundle Compatibility

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/` 中与 `cloud_command_lifecycle_replay_acceptance_packet_http_export`、`cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel` 或 Robot diagnostics safe summary 直接相关的文件，仅在 support handoff bundle 无法安全消费必要字段时才改。
- `docs/product/remote_4g_mvp.md`，仅在需要补 Robot/API support bundle boundary 时可改。
- 本 sprint `tech-done.md` 中 Task B 结果段。

优先只读要求：

- 核对 HTTP export / diagnostics payload 是否已含 pending-safe command id、safe evidence ref、ACK semantics、terminal result status、owner handoff、next required evidence、redaction status 和 false-state flags。
- 确认 support handoff bundle 仍 read-only：不 replay/resubmit command、不 post ACK、不 mutate cursor/state、不上传材料、不触发 GitHub action、不控制 Nav2、不触碰 WAVE ROVER/UART、不写 delivery success。
- 确认 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending` 不被本轮 O5 bundle 改写。
- 若 changed files none，必须在 `tech-done.md` 写清只读核对证据。

验收命令：

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet_http_export|cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel|cloud_command_lifecycle_replay_acceptance_packet|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet|delivery_success|primary_actions_enabled|safe_to_control|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/tech-done.md
```

### Task C - Product Closeout and Conservative OKR Update

Owner：`product-okr-owner`

允许改动：

- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/tech-done.md`
- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/side2side_check.md`
- `sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 Task A / Task B 实际改动、验证输出、失败定位和剩余风险。
- 如果只有 Docker/local support handoff bundle proof，Objective 5 保持约 68%，写明 no OKR percentage lift。
- 必须写明 not true phone/browser proof、not public HTTPS/TLS、not 4G/SIM、not OSS/CDN live traffic、not production DB/queue、not worker/cutover、not HIL、not WAVE ROVER/UART proof、not PR #5 resolved、not delivery success。
- `OKR.md` 必须继续保留 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。

验收命令：

```bash
test -f sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/tech-done.md && test -f sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/side2side_check.md && test -f sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate|Objective 5|not true phone/browser proof|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery success" sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_09-10_cloud-command-lifecycle-acceptance-support-handoff-bundle OKR.md docs/process/okr_progress_log.md
```

## 并行启动要求

本轮是 2+ owner Epic sprint，Task A 与 Task B 文件范围基本互不重叠，必须并行派发 2 个 Engineer 子 agent；Task C 在 A/B 返回后由 Product closeout：

- `full-stack-software-engineer` 负责 mobile/web implementation、fixture、targeted test、copy/download affordance 和 product docs。
- `robot-software-engineer` 并行做 Robot/API safe summary compatibility；只有发现字段缺口才做最小 Robot/API safe alias 改动。
- `product-okr-owner` 等 Task A / B 返回后做 closeout 和 OKR 保守更新。

主节点不得自己写产品代码、测试代码或运行实现验证命令；实现、测试、修复和 fenced validation 必须由对应子 agent 执行。主节点只做派发、等待、证据核对、sprint 文档收口和最终汇总。

## 接口影响

本轮默认不新增控制 route；允许消费既有 read-only support route：

```text
GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export
```

允许的 support handoff bundle data shape：

- `schema`
- `schema_version`
- `capability=cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle`
- `source_capability=cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel`
- `evidence_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate`
- `source_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`
- `safe_command_id`
- `safe_evidence_ref`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `terminal_result_status=terminal_result_pending`
- `owner_handoff`
- `support_route`
- `reviewer_route`
- `next_required_evidence`
- `redaction_status=passed`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `not_true_phone_browser_proof=true`
- `no_okr_percentage_lift=true`
- `safe_copy` / `support_handoff_copy` / `download_text`

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
- targeted `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle`。
- Robot/API targeted `py_compile` and unittest only if Task B changes or confirms compatibility through existing files。
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
- 如实现阶段有 durable change，按用户要求提交并推送远程；planning-only 阶段只创建 planning docs，不修改 `OKR.md` 或产品代码。

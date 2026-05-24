# Cloud Command Lifecycle Acceptance Support Handoff Bundle PRD

Run time: 2026-05-24 09:00 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

普通手机用户、field owner 和支持人员需要一份可直接复制/下载的安全交接包：当命令生命周期已经进入 accepted/processing、terminal result 仍 pending、owner handoff 已形成但真实外部材料仍缺失时，交接包必须明确告诉下一位执行者要补什么证据、哪些状态仍未证明、哪些操作仍不能启用。

产品北极星保持不变：`rober` 是面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。当前 Objective 5 的产品化抓手是让云中转支持材料从“可查看”进一步变成“可交接、可复盘、可指导真实材料收集”，不是把 Docker/local proof 叙述成真实云、真实手机或真实交付。

## 问题陈述

上一轮 `cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel` 已经把 HTTP export 的安全字段展示到 mobile/support surface，但它仍偏向页面解释。后续要推进真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/terminal result 材料时，需要一个 bundle 把可复制/下载内容、owner/support/reviewer 路由、next-required-evidence 和 false-state flags 统一起来。

## 本轮能力

能力名：

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle
```

Evidence boundary：

```text
software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate
```

本轮新增只读 support handoff bundle。它可以消费上一轮 mobile export panel / HTTP export / Robot diagnostics safe summary，但只能输出 safe fields 和 backend/sanitized safe copy。它不得新增控制、副作用、成功判断或外部材料上传。

## OKR 映射

- Objective 5：直接针对最低 Objective，推进 cloud command lifecycle support handoff 的可交接性，帮助下一轮真实外部材料收集。
- Objective 4：作为手机/支持触点可解释性的辅助，但 not true phone/browser proof。
- Objective 1：保留 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`，不把 vendor-source attribution reply 当硬件材料完成。
- Objective 2/3：不触碰任务状态机、导航路线、电梯实跑、terminal result 或 delivery result。

## KR 拆解或更新

- O5 KR1：bundle 继续遵守 `trashbot.remote.v1` commands/status/ack 安全语义，只读消费 ACK/terminal-result support packet，不暴露 `/cmd_vel` 或机器人直连控制。
- O5 KR2：bundle 写清它依赖 local/Docker cloud relay support surface，不代表 production cloud hosting、public HTTPS/TLS 或 worker/cutover。
- O5 KR5：bundle 必须脱敏，禁止 bearer token、Authorization header、signed URL、DB/queue endpoint、OSS AK/SK、root password、local path、traceback、serial/UART detail、WAVE ROVER detail、complete artifact、checksum。
- O5 KR6：bundle 把 graceful degradation 和 next required evidence 转成可交接清单，明确 `accepted_processing_only_not_delivery_success`、`terminal_result_pending` 和 `delivery_success=false`。

本轮不更新 OKR 百分比目标；若实施只获得 local/Docker proof，closeout 必须写明 Objective 5 保持约 68%，no OKR percentage lift。

## 范围

### In Scope

- `mobile/web/app.js` 增加只读 support handoff bundle panel / copy-download affordance。
- `mobile/web/fixtures/` 增加 support handoff bundle fixture。
- `mobile/web/test_mobile_web_entrypoint.py` 增加 targeted assertions。
- `docs/product/mobile_user_flow.md` 同步 bundle、禁用主操作、copy/download 边界。
- `docs/product/remote_4g_mvp.md` 同步 support handoff bundle 与 HTTP export / Robot diagnostics 边界。
- Robot/API 只读核对或最小补充 safe support bundle summary / compatibility fields。

### Out of Scope

- 不新增 POST/command/ACK/cursor/replay/resubmit/material upload/GitHub mutation。
- 不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- 不做真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- 不做真实手机/browser、production app、PWA prompt/userChoice 验收。
- 不做 HIL、WAVE ROVER/UART、2D LiDAR / ToF procurement/install/calibration、Nav2/fixed-route runtime、route/elevator field pass。
- 不解决 PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。
- 不声明 verified terminal result、dropoff completion、cancel completion、delivery_success=true 或 delivery success。

## 验收口径

### P0

- Bundle 能显示或导出 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle` 的安全摘要。
- 明确展示或可测试定位：
  - `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate`
  - `accepted_processing_only_not_delivery_success`
  - `terminal_result_pending`
  - `owner_handoff`
  - `next_required_evidence`
  - `not_proven`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `safe_to_control=false`
  - `not true phone/browser proof`
  - `no OKR percentage lift`
- Start Delivery、Confirm Dropoff、Cancel 保持 disabled。
- Missing safe IDs、unsafe copy、success wording、raw material 或 false-state flags 不齐时 fail closed。

### P1

- Copy/download 内容只能来自 backend-provided safe copy 或 sanitized fixture fields；否则显示 blocked/unavailable。
- Bundle 清单必须指向下一步真实证据：public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result。
- 文案中文优先，面向 field owner / support / reviewer 可执行。

### P2

- Bundle 可保留同一 safe `evidence_ref`、safe command id 和 owner/support/reviewer route，但不得暴露 raw command、ACK payload、cursor、完整 artifact、GitHub mutation payload 或硬件细节。

## Owner 和优先级

- P0 implementation owner：`full-stack-software-engineer`。
- P0 Robot/API compatibility owner：`robot-software-engineer`。
- P0 closeout owner：`product-okr-owner`。

优先级顺序：先保证 bundle 安全字段、false-state flags 和禁用主操作，再做 copy/download、UI copy 和 docs；验证只跑 fenced checks。

## 风险、阻塞和证据链

- 本轮可交付的是 `software_proof_docker` only；not true phone/browser proof。
- 没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover，因此不能称为 O5 external proof。
- 没有 HIL、WAVE ROVER/UART、Nav2/fixed-route runtime、route/elevator field pass、verified terminal result 或 delivery success。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`；published reply 只说明本地 vendor sources 是 attribution only，仍缺真实 2D LiDAR/ToF SKU/source/receipt、wiring/power/calibration、HIL entry、Nav2/SLAM field pass。

## 完成定义

- Full-Stack 返回实际改动文件、targeted validation output、失败定位和剩余风险。
- Robot 返回只读核对结论或最小兼容改动、验证输出和边界风险。
- Product 收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，并写明 Objective 5 保持约 68%，no OKR percentage lift。

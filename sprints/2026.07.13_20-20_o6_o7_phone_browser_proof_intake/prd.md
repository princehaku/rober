# PRD - O6/O7 Phone Browser Proof Intake

## Product Goal

把同一 `task_id` 的 phone/browser terminal-material 安全摘要接入 O6/O7 主证据链，让运营人员能看到手机/浏览器验收材料是否已被收件、是否和任务一致、还缺什么材料。该能力只作为 `software_proof_o6_o7_phone_browser_terminal_material_intake_only`，不声明真实手机验收完成。

## Problem

O7 18:17 已能导出 selected-task mission evidence bundle，但 bundle 只是读取和导出已有 O6 detail。当前缺口是：当现场或准现场拿到 phone/browser 材料时，没有一个非重复的 selected-task intake/readback path 把 `true_phone_browser_evidence`、`diagnostics_mobile_safe_summary` 和 terminal-result 材料状态写回同一任务证据链。

如果继续做 O5 CDN/TLS readiness packet、O7 bundle export、query/readback、inference request、mission event append 或 delivery-result intake，会重复最近已经完成的 support-only wrapper。最新 O5 仍是 `blocked_http_status_not_success_class`，没有可消费的 success-class production evidence。

## Scope

In scope:

- O6 local/mock archive 新增 `phone_browser_terminal_material` 安全 section 或等价 consumer detail alias。
- O7 selected-task 主路径新增 phone/browser proof intake action 和 receipt 展示。
- 仅接受本机回环 O6 base URL。
- 安全字段只保留 material names、safe refs、同一 `task_id`、terminal result type、accepted/missing/rejected counts、blocked reasons、next required evidence。
- 文档同步到 O6/O7 interface 与 product docs。

Out of scope:

- 真实手机设备测试、真实浏览器远程调试、真实 PWA install/userChoice。
- 生产 cloud、production DB/queue、OSS/CDN upload/origin fetch、4G/SIM。
- 真实 route execution、delivery/operator acceptance、HIL、safe-to-control。
- 重新执行 O5 CDN/TLS probe 或 readiness packet consumption。

## Functional Requirements

1. O6 archive/readback
   - 新 section 建议：`phone_browser_terminal_material`。
   - 接受 selected task 的 `task_id` / `robot_id`，并校验安全 `safe_evidence_ref`。
   - 材料名白名单至少覆盖 `true_phone_browser_evidence`、`diagnostics_mobile_safe_summary`、`terminal_result_summary`。
   - 回读必须固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。
   - 任意 raw URL、cookie、Authorization、token、local path、screenshot body、DOM dump、traceback、`/cmd_vel`、serial/UART、WAVE ROVER、`delivery_success=true` 均 fail closed。

2. O7 selected-task intake
   - 新 endpoint 建议：`POST /api/o7/consumer-read/tasks/:taskId/phone-browser-proof/intake?baseUrl=<local-loopback-url>`。
   - Body 只允许安全材料摘要，不接受 raw artifact body。
   - Adapter 必须校验 path/body task id 一致、baseUrl local-loopback-only、dangerous true fields、safe refs 和 material allowlist。
   - 成功 receipt 建议 schema：`trashbot.pc_tools_workstation.o7_phone_browser_proof_intake_result.v1`。
   - Receipt status 只允许 `local_mock_phone_browser_material_written`、`local_mock_phone_browser_material_updated` 或 `fail_closed`。

3. O7 readback/display
   - Selected task detail 加载后展示 phone/browser material status、accepted/missing/rejected material names、same-task identity 和 next required evidence。
   - UI 不显示真实 token、URL query、local path、raw screenshot、DOM dump 或完整 artifact。
   - 该 action 不启用 start delivery、confirm dropoff、cancel、ACK、control、Nav2 或任何 primary action。

## Product Acceptance Criteria

- O6 targeted unit tests pass.
- O7 workstation test/build/lint pass.
- `rg` anchors 命中 endpoint/schema/proof boundary/false fields/docs/tech-done。
- Hostile payload fail-closed：非回环 URL、task mismatch、dangerous true、raw URL/token/local path/raw body 均不能写入成功 receipt。
- 成功 receipt 和 O6 readback 均包含 `software_proof_o6_o7_phone_browser_terminal_material_intake_only` 或同等 proof boundary。
- Product closeout 必须保持 O5/O1/O6/O7 主百分比不调整，除非后续真实 phone/browser + production/cloud/route/delivery/HIL 证据另行到位。

## OKR Mapping And Direction Judgment

- O5 是当前最低 Objective，约 `85%`，但最新 blocker 是 `blocked_http_status_not_success_class`。本 sprint 不继续 O5，是有证据的调整。
- O6/O7 约 `93%`。本 sprint 选择 distinct same-task evidence intake path，方向判断为继续 O6/O7 证据链，但不归档 KR。
- 若 Engineer 只能产出 local/mock receipt，本轮仍是 support-only software proof；如果未来接入真实手机/browser、公网云、生产 DB/queue 或 route delivery evidence，再重新评估 OKR 提升。

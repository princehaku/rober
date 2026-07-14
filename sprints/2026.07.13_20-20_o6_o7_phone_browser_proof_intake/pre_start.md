# Pre Start - O6/O7 Phone Browser Proof Intake

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/`
- started_at: 2026-07-13 20:20 CST
- Product owner: `product-okr-owner`
- Primary implementation owner: `full-stack-software-engineer`
- Supporting implementation owner: `robot-software-engineer`
- Target Objective: O6/O7 same-task mission evidence consumption, with O5 blocker explicitly skipped
- Direction judgment: adjust away from repeated O5 CDN/TLS readiness work and add a distinct phone/browser terminal-material intake path

## User Value And Product North Star

普通手机用户最终要看到的是同一任务里的可解释送达证据：任务、路线、终态、手机/浏览器验收材料和安全摘要能串起来，而不是工程人员反复导出 local/mock 包装物。产品北极星仍是普通用户把垃圾交给小车后，通过手机和云端控制面安全完成固定路线送达，并能在失败时看到可信证据链。

本 sprint 只计划 O6/O7 对 `true_phone_browser_evidence` / phone-browser terminal material 的安全 intake/readback，不发送 `/cmd_vel`、不调用 `/api/base/manual`、不触发 NavigateToPose、不访问 WAVE ROVER UART。任何输出都必须固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`。

## Recent Evidence Reviewed

- `sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/final.md`：O5 readiness packet 已消费 13:13 CDN/TLS artifact，但源证据仍是 `blocked_http_status_not_success_class` / `http_status_class=4xx` / `accepted_claim=none`，O5 继续约 `85%`，KR `不归档`。
- `sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/tech-done.md`：实现只新增 O5 packet source slot 和 env/CLI consumption，明确不是 production cloud、OSS/CDN origin fetch、4G/SIM、real phone/browser、route execution、delivery、HIL 或 safe-to-control。
- `sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export/final.md`：O7 mission evidence bundle export 已接受为 `software_proof_o7_o6_mission_evidence_bundle_export_only`，但仍是 local/mock bundle receipt，不证明真实 phone/browser、delivery 或 production cloud。
- `sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export/tech-done.md`：O7 已能导出 selected-task safe bundle summary；继续做 bundle/readback/export 会重复 support-only wrapper。

## Non-Repeating Blocker Reason

本轮不继续 O5 同一 blocker，原因：

- 最新 O5 仍 blocked 在 `blocked_http_status_not_success_class`，没有 success-class public endpoint、production DB/queue、worker cutover、OSS/CDN origin fetch/upload、4G/SIM 或 real phone/browser 新材料。
- 继续 CDN/TLS probe、readiness packet consumption 或 packet/readback wrapper 只会重复 `software_proof` 支撑层，不会让 O5 从约 `85%` 前进。
- O1/O3 当前 live HIL / route execution 需要 explicit operator approval；本自动化默认不能发 motion/control 命令。
- O7 最新链路已经完成 query filters、inference request、mission event append、delivery result intake 和 mission evidence bundle export；本轮只接受一个新的 distinct evidence path。

因此本 sprint 选择 phone/browser terminal-material intake：让同一 `task_id` 安全接收和回读手机/浏览器验收材料摘要。该抓手不是 closeout，也不是主百分比提升；若没有真实设备/公网/生产链路证据，仍保持 `software_proof_o6_o7_phone_browser_terminal_material_intake_only`。

## Needed Work

`robot-software-engineer` 需要补 O6 archive/consumer contract：

- 在 O6 local/mock archive 中新增或规范化 `phone_browser_terminal_material` section。
- 支持从 `field_evidence_manifest` 或 `artifact_bundle` 中消费安全的 `true_phone_browser_evidence`、`diagnostics_mobile_safe_summary`、`terminal_result_type`、`safe_evidence_ref` 和同一 `task_id`。
- 只回读 basename/ref/count/status/blocked reasons/next evidence；不得回显 raw screenshot、DOM dump、完整 URL、token、cookie、本地路径、traceback 或设备指纹。

`full-stack-software-engineer` 需要补 O7 selected-task intake/readback：

- 在 O7 consumer-read primary path 增加 selected-task phone/browser proof intake action。
- Adapter 只允许 local-loopback O6 baseUrl，并只把安全摘要转发到 O6。
- UI/receipt 显示 `phone_browser_terminal_material_written/readback`、`same_task_id_consumed`、`safe_evidence_ref`、accepted/missing materials 和 fixed false fields。
- 没有 selected task、task mismatch、非回环 URL、dangerous true 或 unsafe text 时 fail closed。

## Acceptance Boundary

接受为：

- O6/O7 phone-browser terminal-material local/mock intake/readback software proof。
- 同一 `task_id` 的手机/浏览器验收材料摘要进入 O6 archive，并能被 O7 selected-task 主路径回读。
- fixed false fields 明确存在：`safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。

拒绝为：

- real phone/browser proof。
- production cloud、production DB/queue、OSS/CDN live traffic、4G/SIM。
- route execution、delivery/operator acceptance、真实 delivery success、HIL 或 safe-to-control。
- O5 external evidence success 或 O5 percentage lift。

## KR And History Decision

- O5 继续约 `85%`，本轮不推进同一 CDN/TLS blocker。
- O1 继续约 `94%`，本轮没有 explicit operator-approved live HIL 或 route execution。
- O6/O7 继续约 `93%`，本 sprint 预计只形成 distinct software proof，不归档 KR。
- 已完成 KR 不移动；本轮只在后续 closeout 有真实证据时再判断历史归档。

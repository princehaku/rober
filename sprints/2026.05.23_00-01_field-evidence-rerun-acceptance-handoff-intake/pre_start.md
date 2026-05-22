# Field Evidence Rerun Acceptance Handoff Intake Pre-Start

Run time: 2026-05-23 00:01 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake`

Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate`

## 开工证据

- Automation 上轮已完成并推送 `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/`，能力为 `field_evidence_rerun_execution_result_acceptance_review_handoff`，证据边界为 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`。
- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%。但同一节和第 6 节均要求：没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result materials 时，不继续叠加本地 O5 metadata depth。本机当前只有 Docker/local 证据，不可提升 O5。
- Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF materials、operator HIL report 和 PR #5 reviewer resolution。GitHub PR #5 live thread evidence：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`。
- 最近 final 明确要求现场 owner 仍需提供同一 safe `evidence_ref` 的真实 task record、Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result、真实手机/browser evidence。
- 本轮不是再做 acceptance review handoff，也不是声明真实材料已到位；本轮只消费上一轮 safe handoff summary，并接收 field owner/support 的 safe acknowledgement/intake packet，输出 fail-closed 的 acceptance handoff intake artifact/summary。

## 用户价值和产品北极星

用户价值：field owner / support 在收到上一轮 acceptance review handoff 后，需要一个安全回执入口，说明是否已收到交接、是否附带同一 safe `evidence_ref` 的真实材料索引、哪些材料仍缺、哪些 claim 仍禁止。普通手机用户只能看到只读 intake 状态和禁用主操作，避免把“收到回执”误解为真实送达或可继续控制。

产品北极星：`rober` 要成为低成本、手机可用、证据可复盘的 ROS2 垃圾投递机器人。`field_evidence_rerun_execution_result_acceptance_handoff_intake` 的价值是把真实材料回填入口接上，不是替代真实 route/elevator field pass、true phone/browser proof、dropoff/cancel completion、delivery success、Objective 5 external proof、Objective 1 HIL 或 PR #5 resolution。

## 本轮核心抓手

本轮实现 `field_evidence_rerun_execution_result_acceptance_handoff_intake`：消费上一轮 `field_evidence_rerun_execution_result_acceptance_review_handoff` 的 safe summary，再接收 field owner/support 的 safe acknowledgement/intake packet，生成 PC gate artifact、Robot diagnostics safe alias、mobile/web read-only panel 和 Product closeout。

Intake artifact 必须包含：

- capability、schema、evidence boundary 和 `source=software_proof`。
- 上一轮 handoff capability 与 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`。
- same safe `evidence_ref`，但不暴露 raw artifact、local path、checksum、traceback、credentials 或敏感材料。
- field owner/support acknowledgement status、intake status、accepted safe material refs、missing required materials、rejected unsafe materials、next evidence request。
- required real-material checklist：真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result、真实手机/browser evidence。
- hard boundary：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## OKR 映射

- Objective 2：把送达任务、电梯 assisted delivery 的现场复跑执行结果验收交接推进到 owner/support safe intake，方便后续按同一 `evidence_ref` 回填真实任务材料。
- Objective 3：把真实 Nav2/fixed-route runtime log 与 route completion signal 放入 intake required checklist，但不声明真实路线通过。
- Objective 4：让 mobile/web 只读展示 intake status、缺口、next step 和安全边界，不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- Objective 5：仍是最低约 68%，但缺真实 external proof；本轮不做 O5 external proof，不产生 Objective 5 completion lift。
- Objective 1：约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；本轮不处理真实硬件材料 closure，不产生 HIL 或 reviewer resolution。

## 本轮范围边界

In scope:

- 规划 A/B/C/D 四个任务，后续由对应 Engineer / Product owner 执行和收口。
- A Autonomy：新增 PC-only handoff intake gate、focused tests、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- B Robot：新增 Robot diagnostics safe alias、diagnostics focused tests、`docs/interfaces/ros_runtime_contracts.md`。
- C Full-Stack：新增 `mobile/web` read-only panel/fixture/focused tests、`docs/product/mobile_user_flow.md`。
- D Product：A/B/C 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

Out of scope:

- 不声明真实 route/elevator field pass。
- 不声明真实手机/browser、真实 iPhone/Android device behavior、PWA prompt/userChoice 或 production app proof。
- 不声明 delivery success、dropoff completion、cancel completion 或 verified terminal result。
- 不声明 Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不声明 Objective 1 HIL、真实 WAVE ROVER/UART、真实 `/odom`、`/imu/data`、`/battery` 或 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution。

## Owner 和启动规则

- A Autonomy Algorithm Engineer：PC-only acceptance handoff intake gate、focused tests、evidence docs。
- B Robot Platform Engineer：Robot diagnostics safe alias、focused tests、runtime contract docs。
- C User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、focused tests、mobile flow docs。
- D Product Manager / OKR Owner：只在 A/B/C 完成后做 sprint closeout、OKR 和 progress log。

本 sprint 是跨 owner Epic。`tech-plan.md` 完成后必须并行启动 A/B/C 三个 Engineer worker；D Product 只做收口，不得抢先写 implementation closeout 或更新 OKR。

## 风险、阻塞和证据缺口

- O5 仍缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result materials。
- O1 仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、采购/安装/接线/电源/标定、operator HIL report、PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- O2/O3/O4 仍缺真实 same-safe-`evidence_ref` field materials：真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser evidence。
- 本轮只能形成 `software_proof` handoff intake artifact。所有 summary 和 UI 必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 需要创建或更新的 sprint 文档

本规划任务创建：

- `sprints/2026.05.23_00-01_field-evidence-rerun-acceptance-handoff-intake/pre_start.md`
- `sprints/2026.05.23_00-01_field-evidence-rerun-acceptance-handoff-intake/prd.md`
- `sprints/2026.05.23_00-01_field-evidence-rerun-acceptance-handoff-intake/tech-plan.md`

A/B/C 实现完成后，D 必须创建或更新：

- `sprints/2026.05.23_00-01_field-evidence-rerun-acceptance-handoff-intake/tech-done.md`
- `sprints/2026.05.23_00-01_field-evidence-rerun-acceptance-handoff-intake/side2side_check.md`
- `sprints/2026.05.23_00-01_field-evidence-rerun-acceptance-handoff-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

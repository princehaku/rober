# Sprint 2026.05.19_10-11 Hardware Real Material Escalation Request - PRD

## 1. 用户价值和产品北极星

本轮产品目标是把 Objective 1 的真实硬件材料缺口从“散落在 OKR、PR #5 review 和 sprint final 里的风险说明”升级为可执行、可复盘、可交接的 `hardware_real_material_escalation_request` 链路。

面向用户和现场 owner 的价值：

- 知道下一步必须补齐哪些真实材料，才能推进 WAVE ROVER/UART/HIL 与 2D LiDAR / ToF baseline。
- 在手机端和 diagnostics 中看到同一份 phone-safe 缺口摘要，不需要 SSH、ROS2、串口工具或阅读 raw artifact。
- 明确当前只是 `software_proof` / `not_proven`，避免把 Docker 本地证明误解成真实硬件或 delivery success。

产品北极星：普通手机用户最终能用低成本机器人完成送垃圾任务；为了做到可量产、可售后、可验证，硬件 baseline 必须有真实来源、采购、安装、接线、供电、标定和 HIL-entry 证据，而不是靠 PRD 或本地 mock 推进。

## 2. OKR 映射

| Objective | 映射 | 本轮是否提高完成度 |
| --- | --- | --- |
| Objective 5 | 当前约 68%，仍缺真实 external proof。 | 否。本轮不碰 O5 completion，不证明公网、4G、OSS/CDN、DB/queue 或 production cutover。 |
| Objective 1 | 当前约 81%，缺 WAVE ROVER/UART/HIL 与 PR #5 2D LiDAR / ToF 真实材料。 | 仅推进可执行材料升级请求；不提高真实 HIL 或硬件完成度。 |
| Objective 4 | 当前约 99%，手机端要能解释硬件材料缺口和低成本量产边界。 | 仅新增只读 phone-safe 可见性；不证明真实手机或 production app。 |
| Objective 2 / Objective 3 | PR #4 route/elevator 现场材料仍缺。 | 否。本轮避免第三次消费同一 route/elevator material blocker。 |

## 3. KR 拆解或更新

### KR-A：Hardware PC gate

作为 Hardware Engineer，我需要一个 `hardware_real_material_escalation_request` PC gate，读取安全输入并产出材料升级请求 summary。它必须列出：

- WAVE ROVER/UART/HIL 必需材料。
- PR #5 2D LiDAR / ToF 必需材料。
- `docs/vendor/VENDOR_INDEX.md` 作为本地 vendor/source 边界。
- 当前 missing/rejected/next_required_evidence。
- owner handoff 和 rerun command。
- `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

验收口径：缺输入、弱 schema、unsafe copy、HIL success claim、field pass claim、delivery success claim、Objective 5 external proof claim 都必须 fail closed。

### KR-B：Robot diagnostics safe alias

作为 Robot Platform Engineer，我需要 diagnostics 只读暴露 `robot_diagnostics_hardware_real_material_escalation_request_summary`，让 operator gateway 可安全展示材料请求。

验收口径：diagnostics 只接受 summary-only safe fields，不读取 raw material、不打开串口、不调用硬件、不改变任务状态；缺 summary 时 fail closed 到 `not_proven`。

### KR-C：mobile/web read-only panel

作为 User Touchpoint Full-Stack Engineer，我需要 mobile/web 展示“硬件真实材料升级请求”只读 panel，让现场 owner 通过手机理解当前缺口。

验收口径：panel 只展示 safe status、safe evidence ref、missing materials、next required evidence、owner handoff、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。它不能触发 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、diagnostics fetch 或任何 robot command。

### KR-D：Product closeout

作为 Product OKR Owner，我需要在实现后更新 sprint closeout、OKR evidence boundary 和 progress log。

验收口径：最终说明 Objective 5 不提高、Objective 1 只得到 software-proof escalation 可执行性、Objective 4 只得到只读可见性；不得把 PRD、panel、diagnostics summary 写成真实硬件进展。

## 4. 本轮核心抓手

`hardware_real_material_escalation_request` 是本轮唯一核心抓手。它不是采购系统、不是 HIL runner、不是 sensor driver、不是 route/elevator replay，也不是 O5 cloud probe。

它要回答一个具体问题：如果要让 Objective 1 从 81% 继续前进，现场 owner 现在必须提交哪些真实材料，提交后由谁复核，复核失败时下一步是什么。

## 5. 需要做什么

1. Hardware：新增 PC gate、tests、interface doc，并同步 `docs/product/production_hardware_boundary.md`。
2. Robot：新增 diagnostics safe alias、tests、interface doc。
3. Full-Stack：新增 mobile/web read-only panel、fixtures、targeted tests，并同步 `docs/product/mobile_user_flow.md`。
4. Product：完成 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 收口。

## 6. 优先级和验收口径

优先级：

1. 先保证 Hardware gate 的 evidence boundary 正确，尤其是 PR #5 传感器材料和 WAVE ROVER/UART/HIL 材料边界。
2. 再保证 Robot diagnostics 只读安全，不把 summary 变成控制通道。
3. 再保证 mobile/web phone-safe 可见性，不影响主操作 gating。
4. 最后 Product closeout 只记录 software-proof 可执行性，不上调 O5 或真实 HIL 进度。

全局验收口径：

- 必须包含 `hardware_real_material_escalation_request`。
- 必须包含 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须显式提到 Objective 5、Objective 1、PR #5、PR #4。
- 必须显式说明本轮不是 HIL，不证明真实 2D LiDAR / ToF，不提高 O5。
- 必须由 `hardware-engineer`、`robot-software-engineer`、`full-stack-software-engineer` 并行交付，Product closeout 收口。

## 7. 风险、阻塞和证据链

- 当前主机只有 Docker，没有真实 WAVE ROVER、UART、2D LiDAR、ToF、手机设备、4G、OSS/CDN 或 production DB/queue。
- 本轮即使全部验证通过，也只能证明 repo 的 software-proof chain 工作，不能证明真实硬件、真实手机、真实 route/elevator、真实云或真实 delivery。
- 真实材料缺口仍需现场 owner 提供：SKU/source/receipt/procurement、安装/接线/供电、标定、HIL-entry、WAVE ROVER feedback、同一 evidence_ref 的 operator HIL report。
- 若 Engineer 在实现中发现 docs/vendor 缺少传感器来源，只能标为 `hardware_material_pending` / `not_proven`，不能补猜测。

## 8. 需要创建或更新的 sprint 文档

本阶段已创建 PRD。实现后必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

Product closeout 必须再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。任何代码或接口变更必须同步更新对应 `docs/` 文档。

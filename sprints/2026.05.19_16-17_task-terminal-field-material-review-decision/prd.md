# Sprint 2026.05.19_16-17 Task Terminal Field Material Review Decision - PRD

## 1. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给小车后，小车可验证地完成固定路线 / 电梯 assisted delivery / 投放或人工取走 / 返回或等待下一任务，而不是只完成本地 demo。

本轮用户价值不是新增控制能力，而是把现场材料回填后的“材料是否足够”翻译成用户和现场 owner 能理解的复核决策：哪些材料已 accepted，哪些 missing，哪些 rejected，谁负责下一步，下一次 rerun 必须补齐哪些证据。这样可以减少现场复测反复沟通，避免把 incomplete materials 误写成 delivery success。

## 2. OKR 映射

- Objective 5：当前约 68%，最低，但本轮不推进 completion。原因是缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实 external proof。
- Objective 1：当前约 81%，不推进 completion。PR #5 剩余 `PRRT_kwDOSWB9286CJ3tX` 仍缺真实 2D LiDAR / ToF vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- Objective 2：支撑送垃圾 terminal action 的现场材料复核闭环，但仍是 `software_proof` / `not_proven`。
- Objective 3：支撑 route/elevator/Nav2 materials 的缺口复核和 rerun guidance，但不声明真实 route/elevator field pass。
- Objective 4：支撑手机端只读展示 review decision，让普通用户和现场 owner 看懂下一步材料要求，但不证明真实手机/browser acceptance。

## 3. KR 拆解或更新

本轮不直接提高 OKR 百分比，只新增下一轮可执行 KR evidence rung：

- KR-A：Robot diagnostics 能输出 `robot_diagnostics_task_terminal_field_material_review_decision_summary`，并把 returned/missing materials 转成 accepted/missing/rejected/material review decision。
- KR-B：mobile/web 能展示只读“现场材料复核决策”panel，显示 review decision、blocked materials、owner_handoff、next_required_evidence、rerun guidance，并保持所有 primary actions disabled。
- KR-C：Autonomy/PC gate 能对 route/elevator/Nav2 相关字段做 fail-closed review decision，不把 missing 或 accepted metadata 写成真实 Nav2/fixed-route complete。
- KR-D：Product closeout 后只记录主链路 evidence hygiene，不把 `software_proof` 写成 O5/O1/O2/O3/O4 的真实通过。

## 4. 本轮核心抓手

核心抓手是 `task_terminal_field_material_review_decision`：

1. 输入：上一轮 `task_terminal_field_material_intake` summary / artifact 中的 returned materials、missing materials、safe `evidence_ref`、phone-safe copy 和 boundary flags。
2. 转换：按同一 safe `evidence_ref` 把 materials 分类为 `accepted`、`missing`、`rejected`，并输出 blocker summary。
3. 决策：生成 `review_decision`、`owner_handoff`、`next_required_evidence` 和 rerun guidance。
4. 展示：Robot diagnostics 和 mobile/web 只读显示，不触发任何控制动作。

## 5. 需要做什么

- Robot：新增 diagnostics safe alias，输出 `robot_diagnostics_task_terminal_field_material_review_decision_summary`。
- Full-Stack：新增 mobile/web 只读 panel，更新 fixture、测试和 `docs/product/mobile_user_flow.md`。
- Autonomy：新增或复用 PC/evidence gate，把 route/elevator/Nav2 materials 的 review decision 规则落到可测试 CLI，并更新 `pc-tools/README.md`。
- Product：实现完成后核对三方验证、更新 sprint closeout、`OKR.md` 和 progress log；本 planning 阶段不得预生成 `tech-done.md` / `side2side_check.md` / `final.md`。

## 6. 优先级和验收口径

P0：

- `task_terminal_field_material_review_decision` 缺输入、坏 schema、unsafe copy、raw path、credential、checksum、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER detail、success wording、HIL/pass wording、field-pass wording 必须 fail closed。
- 输出必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- mobile/web Start Delivery、Confirm Dropoff、Cancel gating 不得变化。

P1：

- review decision 至少能表达：ready for owner handoff but not proven、missing required materials、rejected unsafe materials、evidence_ref mismatch、unsupported input。
- owner_handoff 必须限定到 Robot、Full-Stack、Autonomy、Product closeout 或现场 owner，不得生成模糊责任人。
- next_required_evidence 必须具体列出真实 task record、dropoff/cancel terminal material、route/elevator field material、Nav2/fixed-route runtime log、route completion signal、door/floor/human assistance record、真实手机/browser evidence 等缺口。

## 7. 对应责任 Engineer

- `robot-software-engineer`：Robot diagnostics summary、接口文档和单元测试。
- `full-stack-software-engineer`：mobile/web panel、fixture、UI 测试和产品流程文档。
- `autonomy-engineer`：PC/evidence gate、route/elevator/Nav2 字段复核、测试和 README。
- `product-okr-owner`：阶段验收、OKR 边界、sprint closeout 和 progress log。

## 8. 风险、阻塞和证据链

- O5 真实外部材料仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- O1 真实硬件材料仍缺：2D LiDAR / ToF vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；PR #5 `PRRT_kwDOSWB9286CJ3tX` 不能关闭。
- PR #4 route/elevator 主链仍缺真实 route/elevator field pass、真实 task record、真实 route completion signal、真实电梯门状态、真实楼层确认、人工协助记录和真实 delivery result。
- Docker-only 主机只能产生 software-proof review decision，不能产生真实手机、真实 Nav2、真实 WAVE ROVER、HIL 或 delivery success。

## 9. 需要创建或更新的 sprint 文档

本 planning 阶段只创建：

- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/pre_start.md`
- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/prd.md`
- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/tech-plan.md`

实现和验收完成后再由 Product closeout 更新：

- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/tech-done.md`
- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/side2side_check.md`
- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

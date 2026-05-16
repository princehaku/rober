# Sprint 2026.05.16_08-09 Mobile Field Material Review Decision - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 fresh Epic sprint：`sprints/2026.05.16_08-09_mobile-field-material-review-decision/`。

本轮不继续推进 Objective 5。本机没有真实硬件，只有docker；当前 `OKR.md` 4.1 显示 Objective 5 约 66% 数值最低，但第 6 节明确要求只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料时才继续 O5 completion。继续堆本地 O5 metadata 会重复消费同一外部材料 blocker。

本轮主线改推 Objective 2 / Objective 3：把上一轮 `mobile_field_material_intake` 转成 `mobile_field_material_review_decision`，让现场材料 intake 输出变成 phone-safe 的 review decision、blocker、next-required-evidence 和 owner handoff。Objective 4 只作为手机入口支撑，不把本轮写成真实手机通过、真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。

## 2. 背景证据

- CEO 要求：根据近期 PR 和评审建议下一步 OKR；每条建议基于具体证据；用 team 继续完成 OKR；重新在功能往前走；测试只做围栏；优先推进 OKR 完成度低的部分；本机没有真实硬件，只有docker；最后提交并推送。
- 当前 `OKR.md` 4.1：Objective 5 约 66% 为数值最低，但主要缺口是公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 等真实外部材料。
- 当前 `OKR.md` 第 6 节：外部材料仍不可用时，不要重复本地 O5 metadata depth；最高可行动作是用 `mobile_field_material_intake` 采集真实手机/PWA observation 或 Objective 2 / Objective 3 的 route/elevator 现场材料。
- 最新 sprint `sprints/2026.05.16_07-08_mobile-field-material-intake/final.md`：已完成 `software_proof_docker_mobile_field_material_intake_gate`，形成 phone-safe material intake surface、Robot diagnostics metadata-only consumer 和 pc-tools fail-closed gate。
- 最新 sprint 剩余风险：仍缺真实手机/PWA observation、真实 route/elevator field materials、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result 材料。
- 近期本地提交：`6a4f135 Add mobile field material intake gate`、`1130759 Add mobile route elevator device precheck`、`4254bc9 Add mobile route elevator handoff browser proof`、`25a6883 Add elevator route evidence reconciliation gate`。
- PR/评审证据边界：`gh` CLI 不可用，本轮“PR/评审”只采用本地 sprint final / tech-done、`OKR.md`、recent git log、repo docs / acceptance / review 文档作为证据。

## 3. 用户价值和产品北极星

用户价值：现场操作者不需要读 raw artifact、ROS topic、串口日志或云凭证，就能看到本次材料是否足够进入下一步、卡在哪个 blocker、下一份必须补什么证据、交给哪个 owner 继续处理。

产品北极星：普通手机用户和现场支持人员可以用手机完成“材料准备 -> 决策复核 -> 下一步交接”的闭环，逐步逼近真实送达 / 电梯 / fixed route 现场证据；系统保持 fail-closed，不把 review decision 误写成真实现场通过。

## 4. 本轮核心抓手

核心抓手是 `mobile_field_material_review_decision`：

- 输入：上一轮 `mobile_field_material_intake` summary / artifact。
- 输出：phone-safe review decision、blocker classification、next-required-evidence、owner handoff、same `evidence_ref` status、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- 证据边界：`software_proof_docker_mobile_field_material_review_decision_gate`。
- 业务边界：只做现场材料复核和下一步分派，不证明真实手机、真实电梯、真实 Nav2/fixed-route、真实投放、真实 cancel/dropoff completion、delivery success、HIL 或 Objective 5 external proof。

## 5. Owner 和协作方式

- A Full-stack：`full-stack-software-engineer`，负责 `mobile/web` 的只读 review decision panel 和 phone-safe copy/export。
- B Robot：`robot-software-engineer`，负责 operator diagnostics metadata-only consumer 和 ROS contract 文档。
- C Autonomy：`autonomy-engineer`，负责 pc-tools review decision gate，将 intake 结果转成 next-required-evidence / blocker / owner handoff。
- D Product closeout：`product-okr-owner`，负责 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 收口；本 planning 阶段不更新 OKR。

## 6. 风险、阻塞和证据链缺口

- Objective 5 仍被真实外部材料阻塞：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- Objective 2 / Objective 3 仍缺真实 route/elevator field materials、真实 Nav2/fixed-route runtime log、同一 `evidence_ref` task record/completion signal、dropoff/cancel completion 或 delivery result。
- Objective 4 仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 本轮所有结果必须保留 `software_proof`、`metadata-only`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false` 边界。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段本轮只创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后再由 Product closeout 更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

OKR 收口和 `OKR.md` 更新必须等 Full-stack / Robot / Autonomy 实现与验证完成后再做。

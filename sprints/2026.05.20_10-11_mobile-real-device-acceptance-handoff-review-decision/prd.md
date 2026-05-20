# Sprint 2026.05.20_10-11 Mobile Real Device Acceptance Handoff Review Decision - PRD

## 1. 用户价值和产品北极星

上一轮 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` 解决的是“现场 owner 是否收到 handoff、还缺什么、下一步谁处理”。但对普通手机用户和售后诊断来说，只看到 intake 还不够：必须知道当前材料能否进入下一步、是否缺关键证据、是否被拒绝、是否被真实环境 blocker 卡住，以及谁负责重跑。

本轮产品目标是新增 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision` software-proof rung：把 handoff intake 的状态复核成 `accepted`、`missing`、`rejected`、`blocked` 四类结论，并输出 next owner、rerun guidance、missing/rejected material summary、evidence boundary 和 `not_proven`。它服务手机用户体验与现场验收材料链，但不声称真实手机/browser 通过。

产品北极星：手机端是普通用户唯一入口，所有任务状态、验收状态和失败原因都必须中文优先、可解释、可复跑、可售后诊断，并在证据不足时 fail closed。本轮不得把 review decision、handoff intake、ACK、completion signal、diagnostics summary 或 phone panel 写成真实手机验收、production app、O5 external proof、HIL、route/elevator pass、dropoff/cancel completion 或 delivery success。

## 2. OKR 映射

主目标：Objective 4，建立手机用户体验与低成本量产边界。

关联 KR：

- Objective 4 KR1：手机端最小流程需要持续解释确认、状态、异常和人工处理。
- Objective 4 KR4：远程诊断最小数据包需要包含最近任务状态、失败原因、关键日志和现场证据引用。
- Objective 4 KR5：普通用户不接触命令行，也能知道失败时该怎么做。
- Objective 4 KR7：手机端 UI 必须可直接使用、文案中文优先、主路径清晰。

不计入本轮完成度提升的目标：

- Objective 5：当前约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 和真实手机/browser；不能用本地 handoff review decision metadata 提升云中转完成度。
- Objective 1：当前约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；Q/U 已 resolved 但 X 仍等真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，不能用 review decision wrapper 提升硬件协议可信度。
- Objective 2 / Objective 3：没有真实 route/elevator field pass、Nav2/fixed-route runtime、dropoff/cancel completion 或 delivery result，本轮不写成送达闭环或导航闭环完成。

## 3. KR 拆解或更新

本轮只拆 Objective 4 的执行型 KR，不预设 OKR 百分比提高：

- KR-A：Robot diagnostics 能输出 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision` safe summary，包含 source handoff intake、review decision、accepted material summary、missing material summary、rejected material summary、blocked reason、next owner、rerun guidance、same safe `evidence_ref` 和 fail-closed flags。
- KR-B：mobile/web 能展示只读 “现场验收交接复核决策” panel，让现场 owner 和普通用户看到当前材料是 accepted、missing、rejected 还是 blocked，以及下一步要补什么。
- KR-C：PC/operator diagnostics 消费同一 summary，不读取 raw artifacts、ACK payload、cursor、local path、credentials、checksum 或 complete artifact。
- KR-D：Start Delivery、Confirm Dropoff、Cancel 继续不受 review decision metadata 影响，所有 primary actions 仍由原有 command safety gates 控制。
- KR-E：docs/product 与 docs/interfaces 在实现阶段同步更新，明确该 review decision 不是真实手机验收、真实 field pass、HIL、delivery success 或 O5 external proof。

## 4. 本轮核心抓手

从上一轮 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` 派生 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision`：

- `accepted`：材料格式与同一 safe `evidence_ref` 对齐，可进入下一 owner 处理；仍是 `not_proven`，不等于真实手机通过。
- `missing`：缺真实手机/browser、PWA prompt/userChoice、production app、route/elevator field material、dropoff/cancel material、O5 external proof 或 O1 hardware material 中的关键项。
- `rejected`：材料含 unsafe copy、raw artifact、credentials、local path、checksum、success/control wording、HIL/pass 误称或 schema mismatch。
- `blocked`：当前依赖真实外部/硬件/手机/现场材料，Docker-only host 无法补齐，只能给出 next owner 和 rerun guidance。

核心证据边界固定为 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate`。

## 5. 需要做什么

Robot Platform Engineer 后续需要做：

- 新增或扩展 diagnostics safe summary，字段名围绕 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision`。
- 从上一轮 handoff intake summary 读取 source status，并派生 review decision。
- 输出 phone-safe fields：source handoff intake status、review decision、accepted materials、missing materials、rejected materials、blocked reason、next owner、rerun guidance、same safe `evidence_ref`、evidence boundary、`software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 更新接口文档，说明该 summary 是 metadata-only、read-only、fail-closed。

User Touchpoint Full-Stack Engineer 后续需要做：

- 在 `mobile/web` 增加只读 “现场验收交接复核决策” panel。
- 消费 Robot diagnostics safe summary，不读取 raw artifact、ACK payload、cursor、local path、credentials、checksum 或 complete artifact。
- 增加 fixture 与 targeted tests，覆盖 accepted / missing / rejected / blocked、缺字段、unsafe copy、fail-closed flags、copy/export whitelist 和 action gating 不变。
- 更新 `docs/product/mobile_user_flow.md`，说明手机端如何解释 handoff review decision。

Product Owner 后续需要做：

- 实现阶段结束后补齐 `tech-done.md`、`side2side_check.md`、`final.md`。
- 根据真实结果保守更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 核对 Objective 5 不因本地 metadata 提升，Objective 1 不因 PR #5 wrapper 提升，`PRRT_kwDOSWB9286CJ3tX` 不被写成 resolved。

## 6. 优先级和验收口径

P0：

- Robot、PC/operator diagnostics 与 mobile/web 都围绕 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision` 使用同一 evidence boundary。
- 两侧都保留 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- review decision 必须只允许 `accepted`、`missing`、`rejected`、`blocked`，缺 source intake、safe `evidence_ref` 或 fail-closed flags 时必须 blocked / not_proven。
- Start Delivery、Confirm Dropoff、Cancel gating 不改变。

P1：

- copy/export 只输出 safe metadata。
- rerun guidance 必须是现场 owner 可执行摘要，不包含 shell 注入式原始命令、凭证、路径、raw JSON 或 complete artifacts。
- 文档同步更新并明确证据边界。

P2：

- 展示顺序与现有 mobile/web 第一屏 evidence panels 保持一致，不新增 landing page，不新增控制入口。

验收口径：

- target unit tests / py_compile / node syntax check / required `rg` / scoped `git diff --check` 通过。
- 只允许 software-proof、metadata-only 结论；不得把本轮写成真实手机验收完成、O5 external proof、O1 hardware proof、HIL、真实 route/elevator field pass、dropoff/cancel completion 或 delivery success。

## 7. 对应责任 Engineer

- Robot Platform Engineer：Robot diagnostics review decision summary、behavior-side tests、`docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：mobile/web panel、fixtures、front-end tests、`docs/product/mobile_user_flow.md`。
- Product Owner：sprint closeout、OKR 边界、progress log、阶段验收。

## 8. 风险、阻塞和需要补齐的证据链

- 如果没有真实手机设备、本轮仍只能是 `software_proof`，不能提高 Objective 4 百分比。
- 如果没有真实 O5 external proof，Objective 5 继续保持约 68%，不能推进 completion。
- 如果没有 PR #5 真实 sensor source/material 或 WAVE ROVER/UART/HIL，Objective 1 继续保持约 81%，`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved。
- 如果没有真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery result，Objective 2 / Objective 3 不能写成真实闭环完成。

## 9. 需要创建或更新的 sprint 文档

本阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现阶段必须补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

closeout 阶段按实际结果再决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`；没有真实外部/硬件/手机材料时，OKR 百分比应保守不提高。

# Sprint 2026.05.17_17-18 Route Task Result Review Dispatch - PRD

sprint_type: epic

## 1. 产品问题

上一轮 `route_task_field_retest_result_backfill_review_decision` 已经把回填结果转成 accepted / missing / rejected review decision，但它还没有形成现场可直接执行的派发闭环。现场支持下一步需要的是 owner work order：谁补哪类材料、callback packet 必须带哪些字段、哪些命令要重跑、哪些材料已接受不应重复采集、哪些材料被 rejected 必须退回重做。

本轮要规划 `route_task_field_retest_result_review_dispatch`，接在 review decision 后面，把材料复核决策转成现场证据 dispatch / owner work order / callback packet requirements。

## 2. 用户价值和产品北极星

用户价值：

- 现场支持人员拿到派发包后，可以按 material category 和 owner work order 补齐真实 route/elevator 结果材料。
- Engineer 不再重新解读上一轮 review decision；每个缺口都有 owner、required evidence、callback packet requirements 和 rerun commands。
- 手机或 diagnostics 只展示 phone-safe 只读状态，不暴露 raw JSON、ROS topic、串口、local path、checksum 或控制授权。

产品北极星：

把 `rober` 做成低成本、可复核、可交付的 ROS2 垃圾投递机器人。当前最需要的不是继续包装 Objective 5 external proof blocker，而是让 Objective 2 / Objective 3 的 route/elevator field materials 可以从本地软件复核走向真实现场补料。

## 3. 背景证据

- `OKR.md` 4.1 当前 Objective 5 约 68%，数值最低；但 `OKR.md` 第 6 节要求只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof 才继续推进 O5 completion。本机只有 Docker，不具备这些材料。
- 最新 final 显示 `route_task_field_retest_result_backfill_review_decision` 已完成，Objective 2 / Objective 3 到约 97%，但真实 route/elevator field pass、真实 Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 仍缺。
- PR #4 把 elevator-assisted delivery 变成主链，route/elevator result materials 不应停在 review decision。
- PR #5 review comments 已暴露硬件边界、lowest objective narrative 和 mandatory sensor source citation 问题；近期已多次消费该 blocker，本轮不再包装同一 PR #5 hardware/source/config blocker。
- 本轮证据边界必须保持 `software_proof_docker_route_task_field_retest_result_review_dispatch_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. OKR 映射

Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。

- 本轮把 door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 的 accepted/missing/rejected 决策转成现场 owner work orders。

Objective 3：可验证导航与固定路线能力。

- 本轮把 Nav2/fixed-route runtime log、route completion signal、task record 的复核结果转成 rerun commands 与 callback packet requirements，并强制 `same_evidence_ref_required=true`。

Objective 4：手机用户体验与低成本量产边界。

- 本轮要求 mobile/web 只读展示 dispatch 状态、owner handoff、next required evidence 和 blocked copy，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

Objective 5：云中转 + OSS/CDN 数据通路产品化。

- 本轮不推进 Objective 5。没有真实 external proof 时，任何 Docker-only dispatch gate 都不能证明公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。

## 5. KR 拆解或更新

KR1：PC review dispatch gate。

- 输入：上一轮 `trashbot.route_task_field_retest_result_backfill_review_decision.v1` artifact 或 compatible summary。
- 输出：`trashbot.route_task_field_retest_result_review_dispatch.v1` artifact 与 summary。
- 必须包含：source review decision、safe `evidence_ref`、accepted / missing / rejected material categories、owner work orders、callback packet requirements、rerun commands、`same_evidence_ref_required=true`、`safe_copy`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

KR2：Robot diagnostics metadata-only consumer。

- 支持 file/env/top-level/nested summary。
- 对 unsupported schema/boundary、unsafe copy、success claim、`delivery_success=true`、`primary_actions_enabled=true`、`same_evidence_ref_required=false` fail closed。
- 不改变 task_orchestrator、action server、Start、Confirm Dropoff、Cancel 控制语义。

KR3：Mobile/web 只读 panel。

- 新增“路线任务现场派发”或同等中文 panel。
- 展示 dispatch status、accepted/missing/rejected categories、owner work orders、callback packet requirements、rerun command summary、safe evidence ref、not proven 和 boundary flags。
- copy/export 只使用白名单字段；缺 `safe_copy` 时显示 `blocked copy unavailable`。

KR4：Product closeout。

- 根据工程结果更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 若实现确实落地且验证通过，再保守更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- Product 必须确保相关 `docs/` 同步反映 dispatch surface，且不能把本轮写成真实 field pass 或 Objective 5 external proof。

## 6. 本轮核心抓手

把上一轮 review decision 的“复核决策”升级为“现场派发”。工程输出必须回答：

- 哪些 material categories accepted，不要重复采。
- 哪些 material categories missing，谁补、补什么。
- 哪些 material categories rejected，为什么退回、如何重跑。
- callback packet 必须包含哪些 phone-safe 字段。
- 所有材料是否继续绑定同一 `evidence_ref`。

## 7. 范围

本轮做：

- PC software proof dispatch gate。
- Robot diagnostics metadata-only consumer。
- `mobile/web` read-only dispatch panel。
- 相关接口与产品文档同步。
- sprint closeout 与 OKR 证据边界准备。

本轮不做：

- 不接入真实 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
- 不证明真实 route/elevator field pass、HIL、真实手机/browser、O5 external proof、dropoff success、cancel success 或 delivery success。
- 不修 PR #5 硬件材料 blocker，不新增 2D LiDAR / ToF hardware facts。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

## 8. 优先级和验收口径

P0：

- `software_proof_docker_route_task_field_retest_result_review_dispatch_gate` 出现在 PC artifact、Robot diagnostics summary、mobile/web copy 和 sprint closeout 中。
- 所有输出保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- dispatch 覆盖 accepted / missing / rejected material categories、owner work orders、callback packet requirements、rerun commands、`same_evidence_ref_required=true` 和 `safe_copy`。
- Robot diagnostics 与 mobile/web 只读展示，不能改变控制授权。
- 通过小围栏验证：`py_compile`、focused unittest、CLI `--help`、`node --check`、required `rg`、scoped `git diff --check`。

P1：

- 同一 `evidence_ref` mismatch、unsupported schema、unsupported boundary、unsafe copy、success phrasing、`delivery_success=true`、`primary_actions_enabled=true` 或 `same_evidence_ref_required=false` 被拒绝。
- mobile copy 中文优先，不能出现真实完成、真实送达、真实 HIL、真实手机通过或 Objective 5 production proof 暗示。

## 9. 对应责任 Engineer

- `autonomy-engineer`：PC dispatch gate、schema、focused unittest、CLI help、evidence contract docs。
- `robot-software-engineer`：diagnostics consumer、diagnostics tests、ROS contract docs。
- `full-stack-software-engineer`：mobile/web panel、fixture、mobile tests、`docs/product/mobile_user_flow.md`。
- `product-okr-owner`：sprint docs、OKR mapping、side-by-side check、final closeout。

## 10. 风险、阻塞和需要补齐的证据链

- Objective 5 仍最低，但缺真实 external proof，本轮不能提升 O5。
- 本轮只处理 Docker/local software proof，不补齐真实路线、真实电梯、真实 Nav2/fixed-route、真实 task record、真实 completion signal、真实 dropoff/cancel completion 或 delivery result。
- PR #5 hardware blocker 仍存在，但真实 sensor/source/procurement/install/calibration/HIL-entry 材料不可得，本轮不继续消费。
- 若工程实现只新增 UI 文案而没有 dispatch schema、fail-closed 和 rerun/callback requirements，不能视为完成。

## 11. 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口阶段必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

# Sprint 2026.05.16_08-09 Mobile Field Material Review Decision - PRD

sprint_type: epic

## 1. 产品目标

将上一轮 `mobile_field_material_intake` 从“收材料”推进到“复核决策”。现场人员提交或准备的材料不能停留在 checklist 层，需要被转换成明确、phone-safe、可执行的下一步：

- review decision：当前材料是否可进入下一轮现场运行准备，还是 blocked。
- blocker：缺真实手机/PWA、缺 route/elevator field material、缺 Nav2/fixed-route runtime log、缺 task record/completion signal、缺 dropoff/cancel completion 或 delivery result。
- next-required-evidence：下一份必须补齐的证据清单。
- owner handoff：交给 Full-stack、Robot、Autonomy 或 Product closeout 的下一步。

本轮产品目标服务 Objective 2 / Objective 3 的送达、电梯和 fixed route 现场材料链；Objective 4 只提供手机入口；Objective 5 暂停，因为本机没有真实硬件，只有docker，且缺真实外部 O5 材料。

## 2. 用户价值和产品北极星

用户价值：普通现场操作者只需要打开手机页面，就能知道“这批材料是否够、缺什么、交给谁、下一步怎么补”，不用读 raw JSON、ROS2 topic、串口、云配置或本地 artifact。

产品北极星：把 rober 做成普通手机用户可以理解和操作的低成本 ROS2 自主垃圾投递机器人；在真实硬件和真实外部云材料缺失时，仍通过严格的 software proof 把现场证据链一步步变得可复核、可交接、可执行。

## 3. OKR 映射

- Objective 2：本轮主服务对象。review decision 必须围绕 route/elevator 送达材料、dropoff/cancel completion、delivery result、人工接管原因和同一 `evidence_ref` 补证链。
- Objective 3：本轮主服务对象。review decision 必须指出 Nav2/fixed-route runtime log、路线采集、关键帧或 task record/completion signal 的缺口。
- Objective 4：支撑对象。手机端只显示 phone-safe review decision 和 owner handoff；不启用 Start / Confirm Dropoff / Cancel，不声称真实手机设备验收。
- Objective 5：本轮不推进。Objective 5 约 66% 数值最低，但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；不能用本地 review decision 代替 O5 external proof。

## 4. KR 拆解

KR-A Full-stack：手机端能显示 `mobile_field_material_review_decision` 只读面板。

- 显示 review decision、safe `evidence_ref`、blocker、next-required-evidence、owner handoff、not_proven、evidence boundary。
- 支持 whitelist-only copy/export，禁止 raw artifact、本地路径、凭证、ROS topic、`/cmd_vel`、串口/UART、baudrate、WAVE ROVER、DB/queue URL、OSS AK/SK、traceback、checksum。
- Start Delivery、Confirm Dropoff、Cancel 授权逻辑不变。

KR-B Robot：operator diagnostics 能暴露 metadata-only review decision consumer。

- 支持 explicit ref / env var / diagnostics source 读取 `mobile_field_material_review_decision` 或 summary。
- 输出仅作为 `/api/diagnostics` / phone readiness metadata；不触发 command、ACK、cursor、persistence、HIL、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。
- 文档同步更新 `docs/interfaces/ros_contracts.md`。

KR-C Autonomy：pc-tools gate 能把 intake 结果转成 review decision artifact。

- 输入上一轮 intake artifact / summary。
- 输出 `schema=trashbot.mobile_field_material_review_decision.v1`。
- 输出 `evidence_boundary=software_proof_docker_mobile_field_material_review_decision_gate`。
- 对 missing / placeholder / mismatch / unsafe success claim fail closed。
- 生成 blocker、next-required-evidence、owner handoff、operator next steps。

KR-D Product closeout：实现完成后真实收口。

- 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
- 明确 Objective 5 不上调，Objective 2 / Objective 3 是否可保守上调取决于实现验证结果和证据边界。
- 提交并推送实现结果。

## 5. 范围边界

必须做：

- 建立 `mobile_field_material_review_decision` 的 PC gate、Robot diagnostics consumer 和 mobile read-only surface。
- 保持 phone-safe copy、metadata-only、fail-closed。
- 保持 same `evidence_ref` 语义和 next-required-evidence / owner handoff 可执行。
- 同步更新相关 `docs/` 文档，由对应 Engineer 在实现任务里完成。

明确不做：

- 不证明真实手机/PWA observation。
- 不证明真实 route/elevator field pass。
- 不证明真实 Nav2/fixed-route runtime。
- 不证明真实 dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 `T=1001` feedback。
- 不推进 Objective 5 external proof。
- 不改变 Start Delivery、Confirm Dropoff、Cancel 授权条件。

## 6. 优先级和验收口径

P0：证据边界正确。所有 surface 必须包含 `software_proof_docker_mobile_field_material_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

P0：review decision 可执行。输出必须明确 blocker、next-required-evidence 和 owner handoff，不能只给泛泛建议。

P0：手机安全。mobile copy/export 必须 whitelist-only，不泄露 raw artifact、路径、凭证、ROS/hardware/cloud 敏感词或成功误导文案。

P1：围栏验证。只跑 tech-plan 中列出的 targeted unittest、`py_compile`、`node --check`、required `rg` 和 scoped `git diff --check`。

P1：文档同步。功能实现后，相关 `docs/product/`、`docs/interfaces/`、`docs/navigation/` 必须反映当前状态。

## 7. 责任 Engineer

- A Full-stack：`full-stack-software-engineer`
- B Robot：`robot-software-engineer`
- C Autonomy：`autonomy-engineer`
- D Product closeout：`product-okr-owner`

## 8. 风险、阻塞和需要补齐的证据链

- 真实外部 O5 证据缺失，本轮不能上调 Objective 5。
- 真实硬件、真实 WAVE ROVER/UART/HIL 缺失，本轮不能上调 Objective 1。
- Objective 2 / Objective 3 的真实世界证据仍待补齐：真实电梯门状态、真实楼层确认、人工协助现场记录、Nav2/fixed-route runtime log、同一 `evidence_ref` task record/completion signal、dropoff/cancel completion 和 delivery result。
- Objective 4 的真实手机证据仍待补齐：真实 iPhone/Android、production app、真实 PWA prompt/user choice。

## 9. 成功判定

本轮成功不等于真实送达成功。本轮成功定义为：

1. `mobile_field_material_review_decision` 在 PC gate、Robot diagnostics、mobile PWA 三处形成一致的 phone-safe review decision。
2. 每个 blocker 都能导向具体 next-required-evidence 和 owner handoff。
3. 全部验证围栏通过。
4. sprint closeout 能清楚说明本轮只完成 `software_proof_docker_mobile_field_material_review_decision_gate`。

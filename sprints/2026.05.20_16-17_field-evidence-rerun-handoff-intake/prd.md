# Sprint 2026.05.20_16-17 Field Evidence Rerun Handoff Intake - PRD

## 1. 用户价值和产品北极星

北极星：让普通手机用户可以把垃圾交给小车，小车沿固定路线完成送达、电梯 assisted delivery、投放或人工取走；当证据不足时，用户和现场 owner 能清楚看到缺口、责任人和下一步回填材料。

本轮 PRD 的用户价值是把“现场证据复跑复核交接”推进到“交接回执入口”。上一轮 `field_evidence_rerun_callback_review_handoff` 已经把 review decision 交给现场 owner，但如果没有回执 intake，工程链路仍停在“已交接但未确认 owner 是否接收、材料是否可复跑”的状态。本轮要把 owner-safe handoff intake packet 变成 PC artifact/summary、Robot diagnostics safe alias 和 mobile/web 只读 panel。

## 2. 背景证据

- `OKR.md` 4.1：Objective 5 约 68% 是当前数值最低，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- `OKR.md` 4.1：Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；manual reply comment `3269642220` 不是硬件 proof。
- 最近 sprint chain：`field_evidence_rerun_material_dispatch -> field_evidence_rerun_callback_intake -> field_evidence_rerun_callback_review_decision -> field_evidence_rerun_callback_review_handoff`。
- 最近 sprint 边界：全部为 `software_proof` / `not_proven` / `safe_to_control=false` / `delivery_success=false` / `primary_actions_enabled=false`。
- 本机环境：没有真实硬件，只有 Docker；不能声称 HIL、真实 route/elevator field pass、真实 phone/browser 或 O5 external proof。

## 3. OKR 映射

### 主推进 Objective 2 / 3 / 4

- Objective 2：现场复跑交接回执必须覆盖送达任务、电梯 assisted delivery、门状态、楼层确认、人工协助、dropoff/cancel completion 和 delivery result 的材料状态。
- Objective 3：交接回执必须覆盖真实 Nav2/fixed-route runtime log、route completion signal、field task record、same safe `evidence_ref` 的一致性要求。
- Objective 4：手机端只读 panel 必须让现场支持和普通用户看到回执状态、缺失证据、下一步 owner 和风险边界；不得暴露 raw JSON、ROS topic、串口、WAVE ROVER 参数或控制授权。

### 不推进 Objective 5 的理由

Objective 5 是当前最低 Objective，但当前缺口是外部真实 proof，不是 repo 内再做一个本地 metadata wrapper 可以解决：

- 真实公网 HTTPS/TLS
- 真实 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- worker/cutover
- 真实手机/browser external proof

因此本轮只在 tech-plan 的 OKR 最低优先级核对中记录 Objective 5，不用 O5 作为主 sprint。

### 不推进 Objective 1 的理由

Objective 1 仍需要真实 WAVE ROVER/UART/HIL 和 PR #5 material closure：

- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending。
- reply comment `3269642220` 只是 `software_proof` / `not_proven` reply，不是硬件 proof。
- 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 仍缺真实 WAVE ROVER feedback、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。

## 4. KR 拆解或更新

| KR | 本轮抓手 | 验收边界 |
| --- | --- | --- |
| O2 KR4 / KR5 / KR6 / KR7 | `field_evidence_rerun_handoff_intake` 接收 owner-safe handoff 回执，归类缺失/接收/阻塞材料 | 只证明回执 intake software proof，不证明真实电梯、真实送达、dropoff/cancel completion 或 delivery success |
| O3 KR3 / KR4 / KR5 | 回执必须保留 same safe `evidence_ref`、route completion signal、runtime log、field task record 要求 | 不证明真实路线实跑、Nav2/fixed-route runtime 或上车复账 |
| O4 KR5 / KR6 / KR7 | mobile/web 新增只读“现场证据复跑交接回执”panel | Start/Confirm/Cancel gating 不变；不证明真实手机/browser |
| O1 KR1-KR5 | 不更新进度；只在风险中保留 PR #5 blocker | 不得写成 hardware proof |
| O5 KR1-KR6 | 不更新进度；只在最低优先级核对中记录外部 proof blocker | 不得写成 external cloud proof |

## 5. 本轮核心抓手

新增 `field_evidence_rerun_handoff_intake` 作为 field evidence rerun 链路的下一环：

1. PC gate 消费上一轮 `field_evidence_rerun_callback_review_handoff` summary 和 owner-safe handoff intake packet。
2. PC gate 输出 artifact/summary，明确 intake status、safe `evidence_ref`、missing/rejected/accepted handoff refs、owner next steps、rerun guidance 和 proof boundary。
3. Robot diagnostics 提供 safe alias `robot_diagnostics_field_evidence_rerun_handoff_intake_summary`，metadata-only / fail-closed。
4. mobile/web 展示只读“现场证据复跑交接回执”panel，保持 primary action gating 不变。
5. Product closeout 更新 sprint 文档、`OKR.md` 和 `docs/process/okr_progress_log.md`，保守保持 OKR 百分比和证据边界。

## 6. 范围边界

### In Scope

- 新 PC evidence gate、测试、README 和 evidence contract。
- 新 Robot diagnostics safe alias、测试和 ROS runtime contract。
- 新 mobile/web 只读 panel、fixture、entrypoint test 和 mobile user flow 文档。
- Product closeout 文档、OKR 和 progress log。

### Out of Scope

- 不改真实控制链路，不启用 Start/Confirm/Cancel。
- 不新增 O5 云端命令、DB/queue、OSS/CDN、公网 TLS、4G/SIM 或 worker/cutover proof。
- 不新增真实硬件、串口、WAVE ROVER、2D LiDAR、ToF、HIL 或 vendor/source proof。
- 不声称真实 route/elevator field pass、真实 phone/browser、真实 PWA prompt/userChoice、dropoff/cancel completion 或 delivery success。

## 7. 优先级和验收口径

P0：Autonomy PC gate 必须先定义 artifact/summary contract，并用测试证明 fail-closed、same safe `evidence_ref` 和 proof boundary。

P0：Robot diagnostics safe alias 必须只消费 safe summary，缺字段或 unsafe success claim 时 fail closed。

P0：mobile/web panel 必须只读展示 safe fields，不能改变 Start Delivery / Confirm Dropoff / Cancel gating。

P0：Product closeout 必须保守更新 `OKR.md` 和 progress log，明确 Objective 5 / Objective 1 不提升，O2/O3/O4 仍是 `not_proven` software proof。

P1：所有 docs 更新必须同步到对应 `docs/interfaces/`、`docs/product/` 和 sprint closeout。

## 8. 对应责任 Engineer

- `autonomy-engineer`：PC evidence gate、artifact/summary schema、tests、PC README、evidence contracts。
- `robot-software-engineer`：Robot diagnostics safe alias、diagnostics tests、ROS runtime contracts。
- `full-stack-software-engineer`：mobile/web 只读 panel、fixture、entrypoint tests、mobile user flow。
- `product-okr-owner`：`tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 9. 风险、阻塞和需要补齐的证据链

- 真实 field evidence 仍未提供：真实 task record、真实 route completion signal、真实 Nav2/fixed-route runtime log、真实电梯门状态、真实楼层确认、人工协助记录、真实 dropoff/cancel completion、真实 delivery result、真实 route/elevator field pass。
- 真实手机/browser 仍未提供：真实 iPhone/Android behavior、production app、真实 PWA prompt/userChoice、true phone/browser acceptance。
- O5 external proof 仍未提供：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- O1 / PR #5 hardware proof 仍未提供：PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved/material pending；reply comment `3269642220` 不是 hardware proof。
- 如果 implementation worker 发现上一轮 handoff summary 字段与当前设计不一致，必须先 fail closed 并在 `tech-done.md` 记录偏差，不得临时放宽 contract。

## 10. 需要创建或更新的 Sprint 文档

- 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施完成后更新：`tech-done.md`、`side2side_check.md`、`final.md`。
- Product closeout 更新：`OKR.md`、`docs/process/okr_progress_log.md`。

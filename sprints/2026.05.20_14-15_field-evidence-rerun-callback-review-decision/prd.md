# Sprint 2026.05.20_14-15 Field Evidence Rerun Callback Review Decision - PRD

## 1. 产品目标

`field_evidence_rerun_callback_review_decision` 要把上一轮 `field_evidence_rerun_callback_intake` 的输出推进到复核决策：系统读取 callback-intake summary，将每类现场材料转成明确的 `accepted`、`missing`、`rejected` 或 `blocked` review decision，并给出 owner handoff、next required evidence 和 rerun guidance。

本轮仍是 Docker-only software proof。目标不是证明真实路线、电梯、手机或云端通过，而是让现场材料回填后有明确复核结论，避免现场 owner、Robot diagnostics、mobile/web 只看到入口状态却不知道下一步怎么补。

## 2. 用户价值和产品北极星

产品北极星：普通手机用户不用理解 ROS2、串口、GitHub review thread 或现场日志命令，也能知道小车送垃圾任务现在缺哪类真实证据、由谁补、补完后是否可进入下一步复跑。

本轮用户价值：

- 现场 owner 可以看到 callback packet 被复核后的明确结论，而不只是 intake 分类。
- 工程和产品可以按 owner handoff 推动下一步真实材料回填或复跑。
- 手机端只读显示 review decision、next required evidence 和 rerun guidance，不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- 全链路保持 `not_proven`，避免把本地 review decision 误写成真实 route/elevator field pass、真实手机/browser、HIL、delivery success 或 O5 external proof。

## 3. OKR 映射

### Objective 5

Objective 5 仍是最低约 68%，但本轮不直接推进。O5 当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；这些都不在本机 Docker 环境内。本轮不得把 `software_proof_docker_field_evidence_rerun_callback_review_decision_gate` 写成 O5 external proof。

### Objective 1

Objective 1 约 81%。PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved，manual reply `3269642220` 也不是真实硬件 proof。本轮只允许在风险和缺口中引用该状态，不提升 Objective 1。

### Objective 2 / Objective 3 / Objective 4

本轮面向 O2/O3/O4 的真实现场材料闭环中间层：

- O2：把电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result 的 intake 状态转成 review decision。
- O3：把 route completion signal、field task record、Nav2/fixed-route runtime log 和 same `evidence_ref` 的 intake 状态转成 review decision。
- O4：把真实手机/browser evidence 的 intake 状态转成 phone-safe review decision，并在 mobile/web 只读展示。

若没有真实材料，本轮不提高 O2/O3/O4 百分比，只形成 callback review decision software proof。

## 4. KR 拆解或更新

| KR | 本轮判定 |
| --- | --- |
| O2 KR4 / KR5 / KR6 / KR7 | review decision 必须覆盖失败、人工协助、电梯门/楼层、dropoff/cancel 和 delivery result 材料要求，但不宣称真实完成。 |
| O3 KR3 / KR4 / KR5 | review decision 必须校验 Nav2/fixed-route runtime log、route completion signal、field task record 和 same `evidence_ref`，但不宣称路线实跑。 |
| O4 KR5 / KR6 / KR7 | mobile/web 只读 panel 必须让普通用户看懂复核结论、下一步材料和 owner handoff；不展示 raw JSON、ROS topic 或控制授权。 |
| O5 KR1-KR6 | 本轮不更新；缺真实外部材料。 |
| O1 KR1-KR5 | 本轮不更新；`PRRT_kwDOSWB9286CJ3tX` 仍需真实硬件材料。 |

## 5. 范围

### In Scope

- PC gate：`field_evidence_rerun_callback_review_decision.py` 只读读取上一轮 callback-intake artifact / summary。
- Review decision：将 intake 分类转成 `accepted`、`missing`、`rejected` 或 `blocked`，并输出 blocker summary、owner handoff、next required evidence、rerun guidance。
- 安全字段固定为 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot diagnostics safe alias：`robot_diagnostics_field_evidence_rerun_callback_review_decision_summary`。
- mobile/web 只读 panel：展示 review decision、safe `evidence_ref`、owner handoff、next required evidence、rerun guidance、evidence boundary。
- docs 同步：PC README、evidence contracts、ROS contracts、mobile user flow。
- Product closeout：实现后更新 sprint closeout、OKR 和 progress log。

### Out of Scope

- 不接入真实 robot command、ACK、cursor、Start Delivery、Confirm Dropoff、Cancel 或 Nav2 runtime。
- 不关闭 PR #5 thread `PRRT_kwDOSWB9286CJ3tX`。
- 不宣称真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF 材料或真实手机/browser。
- 不新增 O5 external proof、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不展示 raw JSON、raw artifact、local path、checksum、credentials、ROS topic、serial/UART、WAVE ROVER details 或 success/control copy。

## 6. 验收口径

本轮完成必须同时满足：

1. Autonomy PC gate 能读取 callback-intake output，并在缺输入、坏 JSON、unsupported schema、same `evidence_ref` 不一致、unsafe copy 或 success/control flag 出现时 fail closed。
2. Autonomy PC gate 能输出 `trashbot.field_evidence_rerun_callback_review_decision.v1` 和 `trashbot.field_evidence_rerun_callback_review_decision_summary.v1`。
3. Review decision 必须包含 `review_decision`、`owner_handoff`、`next_required_evidence`、`rerun_guidance`、blocker summary 和 proof boundary。
4. Robot diagnostics safe alias 只读暴露 `robot_diagnostics_field_evidence_rerun_callback_review_decision_summary`，且不触发任何控制路径。
5. mobile/web 只读 panel 能显示 review decision、owner handoff、next required evidence、rerun guidance，且 Start Delivery / Confirm Dropoff / Cancel gating 不变。
6. 文档同步说明这只是 `software_proof_docker_field_evidence_rerun_callback_review_decision_gate`，不是真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。
7. Product closeout 若无真实材料，保持 Objective 5 约 68%、Objective 1 约 81%，并保守记录 O2/O3/O4 不因本地 proof 提升。

## 7. 责任 Engineer

| 优先级 | Owner | 验收关注 |
| --- | --- | --- |
| P0 | Autonomy Algorithm Engineer | review-decision gate schema、fail-closed、PC docs/tests。 |
| P0 | Robot Platform Engineer | diagnostics safe alias、blocked default summary、ROS contract、安全边界。 |
| P0 | User Touchpoint Full-Stack Engineer | mobile/web 只读 panel、fixture/tests、用户可理解文案、控制 gating 不变。 |
| P1 | Product Manager / OKR Owner | sprint closeout、OKR/progress log、证据边界和百分比保守性。 |

## 8. 风险、阻塞和证据链

- 真实现场材料未出现时，最多证明 callback review decision gate 可读、可判定、可 fail closed。
- 如果 callback-intake output 声称 success、control authorization、HIL pass、real phone pass 或 O5 external proof，但缺真实材料引用，必须 rejected 或 blocked。
- 如果 callback-intake output 的 `evidence_ref` 与 dispatch package 不一致，必须 rejected 或 missing same-evidence-ref reconciliation。
- 如果现场 owner 只提交文字说明，没有 route completion signal、field task record、Nav2/fixed-route runtime log、电梯 summaries、dropoff/cancel completion、delivery result 或真实手机/browser evidence，应进入 missing，并给出 rerun guidance。

## 9. 需要创建或更新的 sprint 文档

本 planning task 创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现收口阶段创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

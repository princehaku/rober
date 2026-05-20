# Sprint 2026.05.20_13-14 Field Evidence Rerun Callback Intake - PRD

## 1. 产品目标

`field_evidence_rerun_callback_intake` 要把上一轮 `field_evidence_rerun_material_dispatch` 的派发结果推进到回执校验：现场 owner 按 dispatch package 提交 callback packet 后，系统只读校验材料是否满足 requirements，并输出 accepted / missing / rejected / blocked 的 intake summary。

本轮仍是 Docker-only software proof，目标不是证明真实送达，而是让现场证据回填进入统一入口，减少 route/elevator/mobile 现场材料在 PC、Robot diagnostics 和 mobile/web 三处不一致的问题。

## 2. 用户价值和产品北极星

产品北极星：普通手机用户不用理解 ROS2、串口、GitHub review thread 或现场日志命令，也能知道小车送垃圾任务现在缺哪类真实证据、由谁补、补完后是否已被系统接受。

本轮用户价值：

- 现场 owner 可以按照上一轮派发包提交 callback packet。
- 工程和产品可以看到每类材料是 accepted、missing、rejected 还是 blocked。
- 手机端只读显示下一步材料要求，不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- 保持 `not_proven`，避免把本地 intake 误写成真实路线、电梯、手机或云端通过。

## 3. OKR 映射

### Objective 5

Objective 5 仍是最低约 68%，但本轮不直接推进。原因是 O5 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；本机只有 Docker。本轮不得把 `software_proof_docker_field_evidence_rerun_callback_intake_gate` 写成 O5 external proof。

### Objective 1

Objective 1 约 81%。PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；Q/U resolved 不代表 X resolved，latest manual reply `3269642220` 也不是真实硬件 proof。本轮只允许在风险和缺口中引用该状态，不提升 Objective 1。

### Objective 2 / Objective 3 / Objective 4

本轮面向 O2/O3/O4 的真实现场材料闭环前置工作：

- O2：校验真实电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result 是否回填。
- O3：校验真实 route completion signal、field task record、Nav2/fixed-route runtime log 是否回填。
- O4：校验真实手机/browser evidence 是否回填，并在 mobile/web 只读展示 intake 状态。

若没有真实材料，本轮不提高 O2/O3/O4 百分比，只形成 callback intake software proof。

## 4. KR 拆解或更新

| KR | 本轮判定 |
| --- | --- |
| O2 KR4 / KR5 / KR6 / KR7 | callback intake summary 必须覆盖失败、人工协助、电梯门/楼层、dropoff/cancel 和 delivery result 材料要求，但不宣称真实完成。 |
| O3 KR3 / KR4 / KR5 | intake 必须校验 Nav2/fixed-route runtime log、route completion signal、field task record 和 same `evidence_ref`，但不宣称路线实跑。 |
| O4 KR5 / KR6 / KR7 | mobile/web 只读 panel 必须让普通用户看懂下一步证据状态；不展示 raw JSON、ROS topic 或控制授权。 |
| O5 KR1-KR6 | 本轮不更新；缺真实外部材料。 |
| O1 KR1-KR5 | 本轮不更新；`PRRT_kwDOSWB9286CJ3tX` 仍需真实硬件材料。 |

## 5. 范围

### In Scope

- PC gate：`field_evidence_rerun_callback_intake.py` 只读读取 dispatch summary 和 callback packet。
- Callback packet 校验 accepted / missing / rejected / blocked。
- 安全字段固定为 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot diagnostics safe alias：`robot_diagnostics_field_evidence_rerun_callback_intake_summary`。
- mobile/web 只读 panel：展示 intake status、safe `evidence_ref`、material classes、accepted/missing/rejected/blocked、next required evidence、evidence boundary。
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

1. Autonomy PC gate 能在 callback packet 缺失、字段缺失、schema 不支持、same evidence ref 不匹配、unsafe copy 或 success/control flag 出现时 fail closed。
2. Autonomy PC gate 能输出 `trashbot.field_evidence_rerun_callback_intake.v1` 和 `trashbot.field_evidence_rerun_callback_intake_summary.v1`。
3. Robot diagnostics safe alias 只读暴露 `robot_diagnostics_field_evidence_rerun_callback_intake_summary`，且不触发任何控制路径。
4. mobile/web 只读 panel 能显示 accepted / missing / rejected / blocked 状态，且 Start Delivery / Confirm Dropoff / Cancel gating 不变。
5. 文档同步说明这只是 `software_proof_docker_field_evidence_rerun_callback_intake_gate`，不是真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。
6. Product closeout 若无真实材料，保持 Objective 5 约 68%、Objective 1 约 81%，并保守记录 O2/O3/O4 不因本地 proof 提升。

## 7. 责任 Engineer

| 优先级 | Owner | 验收关注 |
| --- | --- | --- |
| P0 | Autonomy Algorithm Engineer | intake gate schema、callback packet 校验、fail-closed、PC docs/tests。 |
| P0 | Robot Platform Engineer | diagnostics safe alias、blocked default summary、ROS contract、安全边界。 |
| P0 | User Touchpoint Full-Stack Engineer | mobile/web 只读 panel、fixture/tests、用户可理解文案、控制 gating 不变。 |
| P1 | Product Manager / OKR Owner | sprint closeout、OKR/progress log、证据边界和百分比保守性。 |

## 8. 风险、阻塞和证据链

- 真实现场材料未出现时，最多证明 callback intake gate 可读、可判定、可 fail closed。
- 如果 callback packet 声称 success、control authorization、HIL pass、real phone pass 或 O5 external proof，但缺真实材料引用，必须 rejected 或 blocked。
- 如果 callback packet 的 `evidence_ref` 与 dispatch package 不一致，必须 rejected 或 missing same-evidence-ref reconciliation。
- 如果现场 owner 只提交文字说明，没有 route completion signal、field task record、Nav2/fixed-route runtime log、电梯 summaries、dropoff/cancel completion、delivery result 或真实手机/browser evidence，应进入 missing。

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

# Sprint 2026.05.16_09-10 Mobile Field Material Retest Request - Side2Side Check

sprint_type: epic

## 1. 用户价值核对

产品北极星仍是让普通手机用户把垃圾交给低成本 ROS2 小车后，可以沿固定路线 / 电梯 assisted delivery 可验证地完成送达；失败时能知道缺什么证据、下一次怎么补，而不是依赖工程师口头解释。

本轮把 PR / 评审链路里的 `mobile_field_material_review_decision` 继续推进为 `mobile_field_material_retest_request`。现场人员现在可以从 PC gate、Robot diagnostics metadata 和 mobile/web 只读 panel 看到下一次 route/elevator field retest 要补采的材料：真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion material、owner handoff 和 same `evidence_ref` 要求。

## 2. OKR 映射核对

- Objective 2：本轮支持把送垃圾任务 + 电梯 assisted delivery 的缺口转成可执行 retest request，因此可保守上调。
- Objective 3：本轮支持把固定路线/Nav2 现场复测材料按 same `evidence_ref` 组织成下一次复测请求，因此可保守上调。
- Objective 4：本轮新增手机只读 request panel，现场人员能 phone-safe 查看复测请求，因此可保守上调。
- Objective 1：本轮未补真实 WAVE ROVER、UART、Orange Pi、`T=1001` feedback 或 HIL，不能上调。
- Objective 5：本机只有docker，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration，不能上调。

## 3. 验收口径核对

通过项：

- PC gate 输出 `trashbot.mobile_field_material_retest_request.v1` / summary-compatible request，并保持 `software_proof_docker_mobile_field_material_retest_request_gate`。
- Robot diagnostics 只做 metadata-only consumer，不触发 command、ACK、cursor、persistence、Nav2/fixed-route、HIL、dropoff/cancel completion 或 delivery success。
- mobile/web 只读展示 retest request，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 未改变。
- 三个 worker 都返回针对性验证通过证据。
- Sprint closeout 已同步 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

不通过 / 不纳入本轮证明：

- 不证明真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success、HIL、真实 WAVE ROVER/UART 或 Objective 5 external proof。
- 状态必须继续写为 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. 剩余证据链

下一步如果要继续推进 Objective 2 / Objective 3，必须让现场人员基于本轮 retest request 补真实材料：真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 Nav2/fixed-route runtime log、同一 `evidence_ref` 的真实 task record/completion signal、真实 dropoff/cancel completion 或 delivery result。

下一步如果要推进 Objective 5，必须拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 之一；本地 metadata、browser proof 或 mobile summary 不能替代。

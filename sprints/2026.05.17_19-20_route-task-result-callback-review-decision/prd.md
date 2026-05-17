# Sprint 2026.05.17_19-20 Route Task Result Callback Review Decision - PRD

sprint_type: epic

## 1. 用户价值

现场支持人员已经能把 callback packet 回填到系统，但仍需要一个明确的复核决策层：哪些 accepted updates 可以进入结果复核，哪些 missing updates 必须回填，哪些 rejected updates 需要重新派发或重跑。

本轮把这个决策层产品化，减少 route/elevator 现场材料在 callback intake 之后继续靠口头判断。

## 2. OKR 映射

- Objective 2：送垃圾任务 + 电梯 assisted delivery 主链。review decision 把电梯门状态、楼层确认、人工协助记录等材料从摄取结果转成下一步 owner 行动。
- Objective 3：可验证导航与固定路线。review decision 把 Nav2/fixed-route runtime log、route completion signal、task record 等结果材料的 accepted/missing/rejected 状态转成复跑和复核依据。
- Objective 5：当前最低但本轮不推进；缺真实外部材料，本轮不能制造 O5 progress。

## 3. 需求

新增 `route_task_field_retest_result_callback_review_decision` 软件 proof gate：

- 输入上一轮 `route_task_field_retest_result_callback_intake` artifact 或 summary。
- 校验 schema、boundary、`safe_evidence_ref`、`same_evidence_ref_required`、safe copy、accepted/missing/rejected updates、owner follow-up。
- 输出 review decision：`ready_for_result_review`、`needs_material_backfill`、`needs_callback_rerun`、`evidence_ref_mismatch_rerun`、`rejected_unsafe_callback`。
- 输出 owner handoff、next required evidence、rerun commands 和 phone-safe summary。
- Robot diagnostics 和 mobile/web 只读消费 summary，不改变 Start / Confirm / Cancel / ACK / Nav2 / HIL 控制语义。

## 4. 验收口径

- PC gate 能对 ready / missing / rejected / mismatch safe fixtures 做 fail-closed 判定。
- Robot diagnostics 支持 file/env/top-level/nested summary，并对 unsupported/unsafe/missing fail closed。
- mobile/web 展示 callback review decision、material status、owner handoff、next evidence、safe evidence ref 和 boundary flags。
- 所有输出保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 验证只做围栏命令：py_compile、focused unittest、node syntax、required `rg`、scoped `git diff --check`。

## 5. 非目标

- 不证明真实电梯、真实 Nav2/fixed-route、真实 delivery success、真实 phone/browser、HIL、WAVE ROVER/UART 或 O5 external proof。
- 不修改主行为控制路径，不扩大手机端控制按钮权限。
- 不处理 PR #5 真实硬件采购、安装、接线、电源、标定或 HIL-entry。

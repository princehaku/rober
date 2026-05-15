# Sprint 2026.05.15_12-13 Elevator Field Run Review Decision - PRD

sprint_type: epic

## 1. 用户价值

现场同学拿到电梯现场材料校验结果后，不应该再读 raw JSON 或猜下一步。系统要把“缺门状态、楼层确认未回填、人工协助记录仍是模板、`evidence_ref` 不一致、摘要不安全、越界成功声明”等机器状态，整理成普通支持人员能执行的复核决策和复跑清单。

## 2. OKR 对齐

- 主目标：Objective 2，尤其 KR6/KR7 的电梯 assisted delivery 失败原因、人工接管、可回放 `evidence_ref` 和手机端解释。
- 支撑目标：Objective 3，Nav2/fixed-route runtime log 必须继续作为同一 `evidence_ref` 的复核材料，不能脱离任务记录和 completion signal。
- 不推进 Objective 5：本轮没有真实公网、4G、OSS/CDN、DB/queue 或 worker/migration 材料。

## 3. 核心需求

1. 新增 `trashbot.elevator_field_run_review.v1` artifact。
2. 输出 `trashbot.elevator_field_run_review_summary.v1`，供 Robot diagnostics 和 mobile 只读消费。
3. 输入只接受上一轮 `trashbot.elevator_field_run_material_validation.v1` 或 summary 支持的安全字段。
4. 根据 validation 输出生成 review decision：
   - `ready_for_controlled_elevator_field_rehearsal_not_proven`
   - `blocked_missing_materials`
   - `blocked_template_materials`
   - `blocked_evidence_ref_mismatch`
   - `blocked_unsafe_copy`
   - `blocked_success_claim`
   - `blocked_invalid_validation`
5. 输出 operator next steps、commands to rerun、capture checklist、phone-safe summary、not_proven、`delivery_success=false`、`primary_actions_enabled=false`。
6. 任何 raw artifact、内部路径、ROS topic、串口/UART、WAVE ROVER、credential、delivery success、dropoff success、cancel completed、`hil_pass` 文案必须 fail closed 或被安全降级。

## 4. 验收口径

- Autonomy：CLI `--help`、py_compile、focused unittest、required rg、scoped diff check 通过。
- Robot：diagnostics 可从 explicit ref 或环境变量读取 review artifact/summary；focused diagnostics unittest、py_compile、required rg、scoped diff check 通过。
- Full-stack：mobile fixture 中可展示 review summary；Start/Confirm/Cancel gating 不变；mobile unittest、py_compile、`node --check`、required rg、scoped diff check 通过。
- Product：closeout 文档、`OKR.md`、`docs/process/okr_progress_log.md` 更新，且不把本轮写成真实现场、HIL、delivery success 或 O5 external proof。

## 5. 非目标

- 不做真实电梯门识别、真实楼层 OCR、真实喇叭/TTS、真实 Nav2/fixed-route 实跑、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion 或 delivery success。
- 不做 O5 外部云/4G/OSS/CDN/DB/queue proof。
- 不新增大范围测试，只保留本轮功能围栏。

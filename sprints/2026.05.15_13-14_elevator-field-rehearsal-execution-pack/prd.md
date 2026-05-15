# Sprint 2026.05.15_13-14 Elevator Field Rehearsal Execution Pack - PRD

sprint_type: epic

## 1. 用户价值

现场同学看到“电梯现场复核决策”后，还需要一个可以直接照着执行的演练包：哪些材料必须采、首跑命令是什么、复跑命令是什么、哪些字段必须沿用同一 `evidence_ref`、哪些结论仍然不能宣称成功。系统要把 review decision 继续整理成执行清单，而不是让人回到 raw JSON 里拼步骤。

## 2. OKR 对齐

- 主目标：Objective 2，尤其 KR6/KR7 的电梯 assisted delivery 现场步骤、人工协助、失败原因、人工接管和可回放 `evidence_ref`。
- 支撑目标：Objective 3，Nav2/fixed-route runtime log 必须继续作为同一 `evidence_ref` 的执行包材料，不能脱离 task record、completion signal 和 diagnostics/mobile safe summary。
- 不推进 Objective 5：本轮没有真实公网、4G、OSS/CDN、DB/queue 或 worker/migration 材料。

## 3. 核心需求

1. 新增 `trashbot.elevator_field_run_execution_pack.v1` artifact。
2. 输出 `trashbot.elevator_field_run_execution_pack_summary.v1`，供 Robot diagnostics 和 mobile 只读消费。
3. 输入只接受上一轮 `trashbot.elevator_field_run_review.v1` 或 `trashbot.elevator_field_run_review_summary.v1` 的安全字段。
4. 将 review decision 转为现场执行包：
   - `execution_pack_verdict`
   - `controlled_rehearsal_manifest`
   - `required_material_templates`
   - `first_run_commands`
   - `rerun_commands`
   - `capture_checklist`
   - `operator_handoff`
5. 输出 not_proven、`delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true` 和 phone-safe summary。
6. 任何 raw artifact、内部路径、ROS topic、serial/UART、WAVE ROVER、credential、delivery success、dropoff success、cancel completed、`hil_pass` 文案必须 fail closed 或被安全降级。

## 4. 验收口径

- Autonomy：CLI `--help`、py_compile、focused unittest、required rg、scoped diff check 通过。
- Robot：diagnostics 可从 explicit ref 或环境变量读取 execution pack artifact/summary；focused diagnostics unittest、py_compile、required rg、scoped diff check 通过。
- Full-stack：mobile fixture 中可展示 execution pack summary；Start/Confirm/Cancel gating 不变；mobile unittest、py_compile、`node --check`、required rg、scoped diff check 通过。
- Product：closeout 文档、`OKR.md`、`docs/process/okr_progress_log.md` 更新，且不把本轮写成真实现场、HIL、delivery success 或 O5 external proof。

## 5. 非目标

- 不做真实电梯门识别、真实楼层 OCR、真实喇叭/TTS、真实 Nav2/fixed-route 实跑、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion 或 delivery success。
- 不做 O5 外部云/4G/OSS/CDN/DB/queue proof。
- 不新增大范围测试，只保留本轮功能围栏。

# Sprint 2026.05.15_11-12 Elevator Field Material Validation - PRD

sprint_type: epic

## 1. 用户价值

普通用户不需要理解 ROS2、串口、Nav2 或 raw JSON。支持人员在下一次受控楼宇实测前，应能看到一份安全摘要：电梯门状态、楼层确认、人工协助、路线运行日志、task record 和完成信号哪些已经回填、哪些还是模板、哪些 `evidence_ref` 不一致、哪些文案不能给手机用户看。

## 2. OKR 对齐

- 主目标：Objective 2，尤其 KR6/KR7 的电梯 assisted delivery 状态链、失败原因、人工接管和可回放 evidence_ref。
- 支撑目标：Objective 3，现场路线运行日志和 fixed-route/Nav2 runtime 材料要进入同一 evidence_ref 校验。
- 不推进 Objective 5：本轮没有真实公网、4G、OSS/CDN、DB/queue 或 worker/migration 材料。

## 3. 核心需求

1. 生成 `trashbot.elevator_field_run_material_validation.v1` artifact。
2. 输出 `trashbot.elevator_field_run_material_validation_summary.v1` 供 Robot diagnostics 和 mobile 只读消费。
3. 校验同一 `evidence_ref` 下的最小材料：
   - elevator door state material
   - target floor confirmation material
   - human assistance/operator note material
   - Nav2/fixed-route runtime log material
   - task record material
   - completion signal material
   - diagnostics/mobile safe summary material
4. 任何材料缺失、模板未替换、坏 JSON、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true` 或 `delivery_success=true` 都必须 fail closed。
5. 所有输出必须明确 `software_proof_docker_elevator_field_material_validation_gate`，并保留真实电梯、HIL、真实路线、真实投放、真实送达和 O5 external proof 的 `not_proven`。

## 4. 验收口径

- Autonomy：CLI `--help`、py_compile、focused unittest、required rg、scoped diff check 通过。
- Robot：diagnostics 可从 explicit ref 或环境变量读取 validation artifact/summary；focused diagnostics unittest、py_compile、required rg、scoped diff check 通过。
- Full-stack：mobile fixture 中可展示 validation summary；Start/Confirm/Cancel gating 不变；mobile unittest、py_compile、`node --check`、required rg、scoped diff check 通过。
- Product：closeout 文档、`OKR.md`、`docs/process/okr_progress_log.md` 更新，且不把本轮写成真实现场或 delivery success。

## 5. 非目标

- 不做真实电梯门识别、真实楼层 OCR、真实喇叭/TTS、真实 Nav2/fixed-route 实跑、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion 或 delivery success。
- 不做 O5 外部云/4G/OSS/CDN/DB/queue proof。
- 不新增大范围测试，只保留本轮功能围栏。

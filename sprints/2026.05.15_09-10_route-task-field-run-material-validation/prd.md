# Sprint 2026.05.15_09-10 Route Task Field Run Material Validation - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

上一轮已经能生成现场材料包，但现场同学仍需要知道材料目录里哪些文件只是模板、哪些已经回填、哪些字段会导致后续 intake/review fail closed。本轮把材料包推进为“材料校验结果”，让真实 route/task field run 前的准备状态能被 PC、Robot diagnostics 和手机只读界面一致看到。

北极星不变：普通手机用户交付垃圾后，小车可验证地沿固定路线完成投递。本轮不宣称投递成功，而是减少真实现场联跑前的材料遗漏和证据错配。

## 2. OKR 映射

- Objective 2：推进 KR4/KR5。材料校验把 task record、completion、operator notes、diagnostics 和 mobile summary 是否可用于下一步真实联跑前置检查出来。
- Objective 3：推进 KR2/KR3/KR5。材料校验把 route status、Nav2/fixed-route runtime log、same `evidence_ref`、关键缺口和重跑命令统一成可复盘 artifact。
- Objective 5：本轮不推进。没有真实外部云/4G/OSS/CDN/DB/queue 材料。

## 3. 核心需求

1. PC 工具必须读取 `trashbot.route_task_field_run_material_bundle.v1`，并验证 `--material-dir` 中的 route/task/completion/operator notes/diagnostics/mobile summary 材料状态。
2. 工具必须输出 `trashbot.route_task_field_run_material_validation.v1` 与 summary，边界固定为 `software_proof_docker_route_task_field_run_material_validation_gate`。
3. 工具必须 fail closed：缺文件、模板未替换、坏 JSON、schema/boundary 不支持、`evidence_ref` mismatch、unsafe copy、`delivery_success=true` 或 `primary_actions_enabled=true` 都不能通过。
4. Robot diagnostics 与 mobile 只读消费 validation summary，但不得放行任何控制动作。
5. 文档必须明确这是 Docker/local material validation，不是现场实跑、HIL 或 delivery success。

## 4. 验收口径

- Autonomy：CLI、targeted unittest、`py_compile`、`--help`、required `rg`、scoped diff check 通过。
- Robot：diagnostics summary、targeted diagnostics unittest、`py_compile`、required `rg`、scoped diff check 通过。
- Full-stack：mobile panel、fixture、entrypoint unittest、`node --check`、required `rg`、scoped diff check 通过。
- Product：closeout 文档、`OKR.md` 与 progress log 引用真实文件，边界语言不越界。

## 5. 非目标

不做真实硬件/HIL，不跑 Nav2 实机，不接入真实手机，不做 O5 外部云补证，不新增宽泛测试矩阵。

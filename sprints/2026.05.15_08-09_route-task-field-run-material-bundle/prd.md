# Sprint 2026.05.15_08-09 Route Task Field Run Material Bundle - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

现场同学目前已经能看到 evidence kit，但还需要手动创建材料目录、复制模板、记录 operator notes、准备 route/task/completion 回填文件。这个步骤如果仍靠口头说明，会继续阻塞真实 route/task field run。

本轮用户价值是把“下一次真实路线-任务联跑要准备什么”落成可执行 material bundle：一个目录、一组模板、一个 summary、明确 run/rerun commands 和缺口清单。现场同学拿到它后，可以按同一 `evidence_ref` 回填真实材料，而不是从多个 artifact 反推。

北极星仍是普通手机用户交付垃圾后，小车可验证地沿固定路线完成投递；本轮只推进现场实跑前的材料履约能力，不宣称真实送达。

## 2. OKR 映射

- Objective 2：支撑 KR4/KR5。material bundle 把任务状态、dropoff/cancel 材料、失败/恢复原因和 operator next steps 从 summary 转为可回填文件。
- Objective 3：支撑 KR2/KR3/KR5。material bundle 固化 fixed-route/task record/completion signal 的同一 `evidence_ref` 现场材料契约。
- Objective 5：不推进。没有真实公网、4G、OSS/CDN、production DB/queue 或 worker/migration 外部材料。

## 3. 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_field_run_material_bundle_gate`：

- 输入上一轮 `trashbot.route_task_field_run_evidence_kit.v1`。
- 输出 `trashbot.route_task_field_run_material_bundle.v1` summary。
- 可选写入 material directory scaffold。
- 强制 `delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true`。
- diagnostics/mobile 只消费 summary，不暴露 raw artifact、本机绝对路径、token、串口、UART、`/cmd_vel` 或硬件细节。

## 4. 需要做什么

1. PC 侧新增 material bundle CLI：读取 evidence kit，生成 summary；指定 `--material-dir` 时写入必要模板文件。
2. Robot diagnostics 只读消费 material bundle summary，支持 explicit ref 和环境变量路径，校验 schema/boundary，字段不合格时 fail closed。
3. `mobile/web` 展示“现场材料包”只读 panel，展示 safe `evidence_ref`、bundle status、template files、missing materials、operator next steps、boundary 和 not_proven。
4. Product 收口 OKR、progress log 和 sprint final，明确这只是 Docker/local software proof。

## 5. 验收口径

- 所有工程验证只跑围栏：`py_compile`、目标 unittest、`node --check`、required `rg` 和 scoped `git diff --check`。
- 不新增宽泛回归测试，不跑真实硬件，不把 Browser 不可用解释为产品证明失败。
- 任何输出都不能包含真实路径、凭证、raw artifact、硬件串口或成功暗示。

## 6. 风险与阻塞

- 没有真实硬件和真实路线环境，因此本轮不会提升 HIL、真实 Nav2/fixed-route 或 delivery success。
- 没有 O5 外部材料，因此 Objective 5 只能维持。
- material bundle 如果只生成 summary 而没有目录 scaffold，就没有足够功能增量；Autonomy task 必须实际支持写模板文件。

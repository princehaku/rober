# Sprint 2026.05.15_04-05 Route Task Field Run Reconciliation - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

上一轮已经把 route/task field-run review console 推进为现场执行包，但 execution pack 只能告诉现场人员要采什么、怎么重跑。本轮 PRD 要求新增“现场复账”能力：把 execution pack 与 field-run intake/review 材料放在同一 `evidence_ref` 下复核，输出可读 verdict、缺口、重跑建议和 phone-safe summary。

产品北极星仍是低成本 ROS2 垃圾投递机器人完成可验证的送达闭环。本轮不是送达闭环完成，而是为 Objective 2 / Objective 3 的真实 route/task field run 建立复账层，避免把材料齐不齐、ref 是否一致、是否可进入人工复核停留在口头判断。

## 2. OKR 映射

- Objective 2：推进 KR5“每次任务产出可复盘记录”。本轮要求把 task record、robot-side task evidence、dropoff/cancel completion、失败原因和 delivery success 的材料状态汇总为 reconciliation verdict，但不得把 verdict 写成真实 delivery success。
- Objective 3：推进 KR2/KR3/KR5“固定路线流程、dry-run/实跑边界、PC 调试与复核展示”。本轮要求把 execution pack、route status、Nav2/fixed-route runtime log、field-run intake/review 材料按同一 `evidence_ref` 复账。
- Objective 5：本轮不推进。O5 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料；Docker/local reconciliation 不能替代。

## 3. KR 拆解或更新

本轮规划阶段不修改 `OKR.md`，只为实现阶段定义可验收 KR 子项：

1. KR5/O2-O3 复账 artifact：输出 schema `trashbot.route_task_field_run_reconciliation.v1`，boundary `software_proof_docker_route_task_field_run_reconciliation_gate`。
2. KR5/O2-O3 同一 `evidence_ref` 复核：CLI 必须消费 `--execution-pack-json`、`--intake-json`、`--output`、可选 `--evidence-ref`，并固定 `same_evidence_ref_required=true`。
3. KR5/O2 材料状态：输出 `materials_status`，明确 task record、robot-side task evidence、dropoff/cancel completion、support-safe mobile summary 等材料的 present/missing/mismatch 状态。
4. KR2/KR3/O3 路线状态：输出 route status、Nav2/fixed-route runtime log、route collection/review 材料的 present/missing/mismatch 状态。
5. KR5/O2-O3 复账结论：输出 `reconciliation_verdict`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
6. KR4/O4 支援面：mobile/web 只读展示复账 summary，帮助手机端理解“下一步补证据”，但不改变 Start/Confirm/Cancel gating。

## 4. 本轮核心抓手

交付 `software_proof_docker_route_task_field_run_reconciliation_gate`，把 execution pack 变成现场材料复账 verdict：

- reconciliation CLI：读取 execution pack 与 intake/review JSON，输出统一复账 artifact。
- materials status：逐项标记 required materials 是否 present、missing、mismatch、unsafe 或 not_proven。
- same evidence ref gate：`evidence_ref` 缺失、不一致或被命令行 override 后仍不匹配时必须 blocked。
- phone-safe summary：只保留 safe evidence ref、复账结论、材料状态摘要、operator next steps、not_proven 和 evidence boundary。
- not_proven：固定包含真实 Nav2/fixed-route、真实路线采集、HIL、dropoff/cancel completion、delivery success、Objective 5 external proof。

## 5. 需要做什么

1. 新增 PC/evidence CLI，消费 execution pack 与 field-run intake/review 材料，生成 reconciliation artifact。
2. 新增 targeted unittest，覆盖 ready、missing material、evidence_ref mismatch、bad schema/boundary 和 unsafe summary。
3. diagnostics metadata-only 消费 reconciliation summary，并保持动作、ACK、cursor、terminal ACK、Nav2、HIL、delivery success 隔离。
4. mobile/web 增加只读“路线任务现场复账”panel，不读取 raw artifact、不暴露本机路径/凭证/ROS/hardware 细节。
5. 更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 和 sprint closeout 文档。

## 6. 优先级和验收口径

P0：

- CLI 能用 `--execution-pack-json`、`--intake-json`、`--output`、可选 `--evidence-ref` 生成 artifact。
- artifact 必须包含 `schema=trashbot.route_task_field_run_reconciliation.v1`、`evidence_boundary=software_proof_docker_route_task_field_run_reconciliation_gate`、`same_evidence_ref_required=true`、`reconciliation_verdict`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- evidence ref 不一致、缺材料、unsupported schema/boundary 或 unsafe summary 必须 blocked/not_proven。
- diagnostics/mobile 均 metadata-only/read-only，不触发 Start/Confirm/Cancel、collect/dropoff/cancel、ACK、cursor、terminal ACK、Nav2、HIL 或 delivery success。

P1：

- 文档把 execution pack -> intake/review -> reconciliation 的使用顺序、材料状态和重跑建议写清楚。
- mobile 文案中文优先，避免 raw artifact、本机路径、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、checksum、traceback、凭证或 Objective 5 external proof 泄漏。

验收口径：

- 通过 targeted py_compile、targeted unittest/sample drill、required `rg` 和 scoped `git diff --check`。
- 不跑真实硬件、不宣称 HIL、不宣称 delivery success。

## 7. 对应责任 Engineer

- `autonomy-engineer`：reconciliation CLI、targeted test、PC/tool 文档和 navigation 文档。
- `robot-software-engineer`：diagnostics metadata-only summary、接口文档和隔离测试。
- `full-stack-software-engineer`：mobile/web 只读面板、fixture、entrypoint 测试和产品文档。
- `product-okr-owner`：收口文档、OKR 口径和证据边界。
- `hardware-engineer`：本轮不主责；若后续执行阶段触及 WAVE ROVER、UART、串口、波特率、引脚、电压或机械安装，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。

## 8. 风险、阻塞和证据链

- 当前主机没有真实硬件，只有 Docker/local 软件环境；本轮只能形成 software proof。
- reconciliation verdict 只表示 execution pack 与 intake/review 材料在 Docker/local artifact 层可复账，不等于真实 Nav2/fixed-route 实跑。
- phone-safe summary 只用于支持人员和用户触点理解下一步，不是控制授权。
- Objective 5 不因本轮上调，除非后续拿到真实外部云/4G/OSS/CDN/DB/queue 材料。
- 真实 delivery success 必须来自真实路线任务完成、dropoff/cancel completion 和同一 `evidence_ref` 上车复账，不能由 reconciliation verdict、diagnostics summary 或 mobile panel 推导。

## 9. 需要创建或更新的 sprint 文档

本阶段创建：

- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/pre_start.md`
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/prd.md`
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/tech-plan.md`

实现后必须继续创建或更新：

- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/tech-done.md`
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/side2side_check.md`
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/final.md`

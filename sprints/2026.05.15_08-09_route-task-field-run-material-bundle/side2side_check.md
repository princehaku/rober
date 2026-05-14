# Sprint 2026.05.15_08-09 Route Task Field Run Material Bundle - Side2Side Check

sprint_type: epic

## 1. 用户价值对照

PRD 要求把上一轮 evidence kit 转成现场同学可执行的 material bundle：目录结构、模板文件、summary、run/rerun commands、缺口清单和 operator handoff。三位 Engineer 的完成结果满足这个方向：

- Autonomy 生成 `trashbot.route_task_field_run_material_bundle.v1` / summary，并支持 `--material-dir` 创建 route/task/completion/operator notes/diagnostics/mobile summary 模板。
- Robot diagnostics metadata-only 消费 bundle / summary，保留 fail-closed 边界。
- `mobile/web` 增加只读“路线现场材料包” panel，不改变 Start / Confirm / Cancel gating。

产品北极星仍是普通手机用户交付垃圾后，小车可验证地沿固定路线完成投递。本轮只把真实现场联跑前的材料交接链路做成软件 proof，不把材料准备写成真实送达。

## 2. OKR 映射对照

Objective 2：可送垃圾任务闭环从约 67% 保守上调到约 68%。理由是任务材料从 evidence kit 进一步变成可回填材料目录，覆盖 task record、completion、operator notes、diagnostics 与 mobile summary 的交接模板。

Objective 3：可验证导航与固定路线从约 67% 保守上调到约 68%。理由是 fixed-route / route-task 现场材料链从 summary 变成可执行 material bundle scaffold，支持下一次真实路线采集或 Nav2/fixed-route 实跑按同一 `evidence_ref` 回填。

Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料，不能把 Docker/local material bundle 计入 O5 外部 proof。

## 3. 验收口径对照

已满足：

- `schema=trashbot.route_task_field_run_material_bundle.v1` 与 summary schema 已落地。
- `evidence_boundary=software_proof_docker_route_task_field_run_material_bundle_gate` 已落地。
- `delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true` 边界保留。
- diagnostics 与 mobile 都只读消费，不触发 collect/dropoff/cancel、ACK、Nav2、HIL、dropoff/cancel completion 或 delivery success。
- 工程验证按围栏完成：py_compile、目标 unittest、CLI `--help`、`node --check`、required `rg`、scoped `git diff --check`。

未满足且本轮不应宣称：

- 真实 Nav2/fixed-route。
- 真实路线采集。
- WAVE ROVER、串口/UART、Orange Pi 或 HIL。
- 真实 dropoff/cancel completion、delivery success。
- 真实手机/browser 或 production app。
- Objective 5 外部云/4G/OSS/CDN/DB/queue proof。

## 4. 结论

本轮通过 Product 验收，状态为 software proof only。它把下一次现场执行需要的材料目录和只读交接面补齐，适合进入 OKR 4.1 和 progress log；但所有真实世界证明仍必须由后续现场材料、上车证据或外部云材料补齐。

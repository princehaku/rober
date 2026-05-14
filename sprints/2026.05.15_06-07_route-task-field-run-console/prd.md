# Sprint 2026.05.15_06-07 Route Task Field Run Console - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星：让不会 ROS2、串口或命令行的普通用户，最终可以只用手机完成送垃圾任务，并在任务失败时获得清楚、可操作、可复盘的解释。

本轮用户价值是服务真实 field-run 前的操作员入口：把上一轮 completion signal、route status、execution pack 和 task record 变成现场可执行的操作台。现场同学必须能看到要跑哪条路线、要采哪些材料、same `evidence_ref` 是否一致、dropoff/cancel completion 还缺什么、哪些证明仍是 `not_proven`。这比继续堆 metadata 更接近真实送达验收。

## 2. OKR 映射

- Objective 2：围绕送达任务闭环推进 KR4/KR5。field-run console 必须输出任务现场步骤、失败/恢复材料要求、dropoff/cancel completion 材料状态、`delivery_success=false` 和 operator next steps。
- Objective 3：围绕固定路线可验证能力推进 KR2/KR3/KR5。field-run console 必须读取 route status、execution pack、completion signal 和 task record，并用 same `evidence_ref` 给出可复核状态。
- Objective 4：仅作为只读支援。mobile/web 可展示 field-run summary，但不能暴露 raw artifact、不能解锁 Start/Confirm/Cancel、不能声称真实手机验收。
- Objective 5：不推进。没有真实外部云、4G、OSS/CDN、production DB/queue 或 worker/migration 材料，本轮不更新 O5。

## 3. KR 拆解或更新

本 planning 阶段不修改 `OKR.md`。实现和验收通过后，Product closeout 才能保守评估 O2/O3 是否上调。

建议本轮证据拆解：

- O2.KR4：console 输出必须明确 `dropoff_completion.status`、`cancel_completion.status`、failure/recovery reason、blocked reason 和现场人工处理建议。
- O2.KR5：console 输出必须包含 task record 摘要、状态转换摘要、现场材料采集清单、same `evidence_ref` 校验和 `delivery_success=false`。
- O3.KR2/KR3：console 必须支持 Docker/local fixed-route status、route execution pack、completion signal、task record 输入；缺 Nav2/硬件时仍能 fail closed。
- O3.KR5：PC/operator 是主入口；Robot diagnostics 和 mobile/web 只能消费 summary，不读取 raw artifact 或本机路径。

## 4. 本轮核心抓手

核心抓手：`route_task_field_run_console`，证据边界为 `software_proof_docker_route_task_field_run_console_gate`。

它必须至少产出三类结果：

- 现场操作步骤：从 preflight 到 route run、dropoff/cancel material capture、task record export、completion review 的顺序。
- 材料采集模板：列出 required files/fields、expected `evidence_ref`、operator notes、blocked reason、not_proven 列表。
- 只读 summary：给 Robot diagnostics 和 mobile/web 消费，保留 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven`、`same_evidence_ref_required=true`。

## 5. 需要做什么

1. Autonomy：实现 PC/evidence field-run console/CLI 或 API 入口，读取 execution pack、completion signal、route status 和 task record，输出 field-run plan、capture checklist、same `evidence_ref` verdict 和 summary。
2. Robot：在 diagnostics 层只读消费 field-run summary，明确它不是 command/status/ACK envelope，不触发 Nav2、dropoff、cancel、remote ACK、cursor advance、terminal ACK、WAVE ROVER、HIL 或 delivery success。
3. Full-stack：在 `mobile/web` 只读展示 field-run summary，保持 phone-safe；不得读取 raw artifact、本机路径、traceback、ROS topic、serial/UART、baudrate、WAVE ROVER、credentials、DB/queue 或 OSS/CDN 细节。
4. Product：收口 `tech-done.md`、`side2side_check.md`、`final.md`，核对 OKR 最低优先级、证据边界、docs 同步和 `OKR.md` 是否可保守更新。

## 6. 优先级和验收口径

P0：

- 输出必须包含 `software_proof_docker_route_task_field_run_console_gate`、`delivery_success=false`、`not_proven`、`same_evidence_ref_required=true`。
- 缺 execution pack、completion signal、route status、task record 或 `evidence_ref` mismatch 时必须 fail closed。
- Console 必须给出可执行现场步骤和采集模板，而不是只生成 summary metadata。

P1：

- Robot diagnostics 与 mobile/web 只能消费 summary，不改变动作按钮或任务状态机。
- 文档必须同步更新到相关 `docs/`，并明确本轮不是真实 Nav2/fixed-route、HIL 或 delivery success。
- 验证只跑围栏：targeted unittest、`py_compile`、`node --check`、required `rg`、scoped `git diff --check`。

验收口径：

- Autonomy CLI/API 样例能从 fixture 生成 field-run plan/checklist/summary。
- Robot diagnostics targeted unittest 证明 summary 是 metadata-only，不能触发动作。
- mobile/web targeted unittest 和 JS syntax check 证明只读展示、按钮 gating 不变、缺 summary 时 blocked/not_proven。
- Product closeout 检查 docs、OKR 边界和 required `rg`。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer (`autonomy-engineer`)：PC/evidence field-run console/CLI/API、fixture、targeted test、`docs/navigation/`。
- Robot Platform Engineer (`robot-software-engineer`)：diagnostics metadata-only summary、targeted test、`docs/interfaces/`。
- User Touchpoint Full-Stack Engineer (`full-stack-software-engineer`)：mobile/web 只读 summary、targeted test、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner (`product-okr-owner`)：sprint closeout、OKR/KR 边界、`OKR.md` 和 process log 更新；不写工程代码。

## 8. 风险、阻塞和需要补齐的证据链

风险：

- Field-run console 被误读为真实 field-run 结果；必须固定 `delivery_success=false` 和 `not_proven`。
- 只读 summary 被误用为 command envelope；Robot 与 Full-stack 必须 fail closed。
- Docker/local fixtures 可能让材料看起来完整，但没有真实路线采集、Nav2 runtime 或硬件运动，不能上升为真实送达。

仍需补齐的真实证据链：

- 真实 Nav2/fixed-route 运行。
- 真实路线采集和关键帧实景证据。
- 同一 `evidence_ref` 的上车材料与实机复账。
- 真实 dropoff completion、cancel completion、failure recovery 和 delivery success。
- WAVE ROVER、真实串口/UART、`T=1001` feedback、HIL。
- 真实手机设备/browser、production app、真实 PWA prompt/user choice。
- Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 9. 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `sprints/2026.05.15_06-07_route-task-field-run-console/pre_start.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/prd.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/tech-plan.md`

实现阶段完成后必须继续补齐：

- `sprints/2026.05.15_06-07_route-task-field-run-console/tech-done.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/side2side_check.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/final.md`

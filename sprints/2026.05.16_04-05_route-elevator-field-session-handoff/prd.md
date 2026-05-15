# Sprint 2026.05.16_04-05 Route Elevator Field Session Handoff - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：现场同学要能拿着同一份 `evidence_ref` 交接包去执行 route + elevator assisted delivery 现场 session，并知道缺什么材料、按什么顺序采集、哪些结果仍不能当成真实送达。普通手机用户侧只能看到安全、只读、中文优先的状态解释，不能被软件 proof 误导为“已可发车”。

产品北极星：低成本 ROS2 自主垃圾投递机器人必须从“本机软件能复账”走向“现场 session 可交接、可回填、可复盘”。本轮不追求新增控制能力，而是打通 O2/O3 真实现场材料进入闭环前的最后一层 handoff。

## 2. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮服务于 KR5、KR6、KR7，把电梯门状态、目标楼层确认、人工协助记录、任务记录、完成信号和失败原因纳入同一 handoff 链路。
- Objective 3：可验证导航与固定路线。本轮服务于 KR3、KR4、KR5，把 PC route debug console、route completion signal 和 elevator reconciliation 组织成下一次 Nav2/fixed-route runtime log 回填入口。
- Objective 4：手机用户体验与低成本量产边界。本轮只做只读解释性支撑，mobile/web 继续 fail-closed。
- Objective 5：本轮不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据，不更新 O5 completion。

## 3. KR 拆解或更新

本轮完成后，O2/O3 可获得一条新的 KR 支撑证据：

- KR-Handoff-1：`route_elevator_field_session_handoff` artifact 能引用 PC route debug console summary、route completion signal、elevator-route reconciliation summary，并强制同一 `evidence_ref`。
- KR-Handoff-2：handoff summary 输出现场采集清单，至少覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 和 diagnostics/mobile safe summary。
- KR-Handoff-3：Robot diagnostics 能 metadata-only 展示 handoff summary，缺失、坏 schema、unsafe copy、success claim、`primary_actions_enabled=true` 或 `delivery_success=true` 时 fail closed。
- KR-Handoff-4：mobile/web 能只读展示 handoff summary，并保持 Start / Confirm Dropoff / Cancel fail-closed。
- KR-Handoff-5：Product closeout 保持证据边界：`software_proof_docker_route_elevator_field_session_handoff_gate` 不能写成真实路线、真实电梯、HIL、dropoff/cancel completion 或 delivery success。

## 4. 本轮核心抓手

新增一个 route + elevator field session handoff gate，作为上一轮 PC console integration 与下一轮真实现场材料之间的交接层。它不是新的 runtime，不调用 ROS graph，不访问硬件，不发控制命令；它只把已有 summary 和后续现场必填材料组织成可验证、可传递、可安全展示的 package。

## 5. 需要做什么

### Autonomy Task A

新增 `route_elevator_field_session_handoff` CLI/schema/test/docs：

- 输入：PC route debug console JSON 或 summary、route completion signal JSON 或 summary、elevator-route reconciliation JSON 或 summary、显式 `--evidence-ref`、可选现场 session id/operator/location/time window。
- 输出 artifact：`schema=trashbot.route_elevator_field_session_handoff.v1`。
- 输出 summary：`schema=trashbot.route_elevator_field_session_handoff_summary.v1`。
- evidence boundary：`software_proof_docker_route_elevator_field_session_handoff_gate`。
- 必须输出：`same_evidence_ref_required=true`、`handoff_verdict`、`field_session_manifest`、`required_materials`、`operator_handoff`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false`、`delivery_success=false`。

### Robot Task B

Robot diagnostics metadata-only 消费 `route_elevator_field_session_handoff` summary：

- 只保留白名单字段。
- 缺失或 invalid 时显示 blocked/not_proven。
- 不触发 `/api/collect`、ACK、cursor、Nav2、dropoff/cancel 或 success claim。

### Full-stack Task C

mobile/web 只读展示 handoff summary：

- 显示 handoff verdict、safe `evidence_ref`、required materials、operator next steps、boundary、`not_proven`。
- 不 fetch raw artifact、不显示本机路径、不显示 raw ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、凭证、DB/queue/OSS/CDN 材料。
- Start / Confirm Dropoff / Cancel 继续沿用既有 `command_safety` 和 legacy gates，不能因为 handoff summary 变可用而启用。

### Product Closeout

工程验收通过后更新 sprint closeout 与 OKR：

- `tech-done.md`：记录三个 Engineer 的实际改动、验证结果、偏差和风险。
- `side2side_check.md`：对照 PRD 验收每条用户价值和证据边界。
- `final.md`：说明是否可保守推动 O2/O3，明确 O5 不因本轮上调。
- `OKR.md`：仅在软件 proof 真实落地后更新 Objective 2/3 支撑说明，保留真实现场缺口。
- `docs/process/okr_progress_log.md`：追加本轮进展和证据边界。

## 6. 优先级和验收口径

P0 必须完成：

- CLI/schema/test/docs 能生成 handoff artifact + summary。
- summary 能被 Robot diagnostics 和 mobile/web metadata-only 消费。
- 所有 surfaces 都保留 `primary_actions_enabled=false` 和 `delivery_success=false`。
- 必须出现 `software_proof_docker_route_elevator_field_session_handoff_gate`。
- 必须列出真实现场必缺材料，并以 `not_proven` 明确排除真实 Nav2/fixed-route、真实电梯、HIL、真实手机/browser、Objective 5 external proof 和 delivery success。

P1 可选但不阻塞：

- CLI 可接受 session operator/location/time window，并脱敏后进入 operator handoff。
- mobile/web 对 required materials 做更清晰的中文分组。

验收不通过条件：

- 任一输出把 handoff ready 写成 delivery success、dropoff/cancel completed、HIL、真实路线、电梯实景或 O5 external proof。
- 任一 surface 因 handoff summary 启用 Start / Confirm Dropoff / Cancel。
- 任一 summary 暴露 raw artifact、本机完整路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：Task A 主责，新 CLI/schema/test/docs 与 handoff summary contract。
- Robot Platform Engineer：Task B 主责，diagnostics metadata-only 消费与 fail-closed 行为。
- User Touchpoint Full-Stack Engineer：Task C 主责，mobile/web 只读展示与控制按钮 fail-closed。
- Product Manager / OKR Owner：Product Closeout 主责，验收、OKR、进度日志与 sprint 收口。

## 8. 风险、阻塞和需要补齐的证据链

风险：

- 继续停留在 Docker/local software proof，不能证明真实现场执行。
- 如果 schema 过宽，Robot/mobile 可能误展示 raw artifact 或成功语义。
- 如果只做 UI 展示，不生成 handoff artifact，现场同学仍无法按同一 `evidence_ref` 回填材料。

阻塞：

- 缺真实 Nav2/fixed-route runtime log。
- 缺真实 route completion signal 与 task record。
- 缺真实电梯门状态、目标楼层确认和人工协助记录。
- 缺真实 dropoff/cancel completion 与 delivery result。
- 缺 WAVE ROVER/UART/HIL 与真实手机/browser 证据。

本轮只补齐“现场 session handoff package”这一层，不补齐上述真实材料本身。

## 9. 需要创建或更新的 sprint 文档

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

工程完成后继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

# Sprint 2026.05.15_03-04 Route Task Field Run Execution Pack - Side2Side Check

sprint_type: epic

## 1. PRD 对照

| PRD 验收点 | 结果 | 证据 |
| --- | --- | --- |
| 输出 execution pack manifest | 通过 | Task A 输出 `schema=trashbot.route_task_field_run_execution_pack.v1` 和 `software_proof_docker_route_task_field_run_execution_pack_gate`。 |
| 固化同一 `evidence_ref` 要求 | 通过 | Artifact 输出 `same_evidence_ref_required=true`；缺失或不一致进入 blocked/not_proven。 |
| 输出现场材料模板和重跑清单 | 通过 | Task A 输出 required materials、first-run commands、rerun commands 和 operator next steps。 |
| Robot diagnostics metadata-only consumption | 通过 | Task B 支持 explicit ref 和 `TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK`，不触发 collect/dropoff/cancel、ACK、cursor、HIL 或 delivery success。 |
| Mobile 只读展示 | 通过 | Task C 新增“路线任务现场执行包”panel，缺 summary 时 blocked/not_proven，不 fetch raw artifact，不改变 Start/Confirm/Cancel gating。 |
| 不把 software proof 写成真实成功 | 通过 | Artifact、diagnostics、mobile 和 closeout 均保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 |

## 2. OKR 对照

- Objective 2：本轮把 task record、robot-side task evidence、dropoff/cancel completion 和失败复盘所需材料前移为执行包，只支持从约 62% 保守上调到约 63%。
- Objective 3：本轮把 route status、Nav2/fixed-route runtime log、review console 和现场执行材料纳入同一 `evidence_ref` 执行链，只支持从约 62% 保守上调到约 63%。
- Objective 5：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部证据，保持约 66%。

## 3. 证据边界

本轮通过的是 Docker/local software proof：

- `software_proof_docker_route_task_field_run_execution_pack_gate`
- PC/evidence execution pack artifact
- Robot diagnostics metadata-only summary
- Mobile read-only execution pack panel

本轮没有证明：

- 真实 Nav2/fixed-route
- 真实路线采集
- WAVE ROVER、真实串口/UART 或 HIL
- 同一 `evidence_ref` 上车复账
- dropoff/cancel completion
- delivery success
- Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration

## 4. 完成前反思

需求已满足：A/B/C 的实现与验证证据已进入 closeout，OKR 只做 O2/O3 保守上调，O5 未上调。

范围已控制：Task D 只更新 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint 三份 closeout 文档，不回滚其他 worker 改动。

验证仍有缺口：本轮 validation 只覆盖软件 artifact、diagnostics、mobile read-only panel 和文档边界；真实现场运行材料仍需下一轮采集。

# Sprint 2026.05.15_11-12 Elevator Field Material Validation - Side2Side Check

sprint_type: epic

## 1. PRD 对照

| PRD 要求 | 结果 | 证据 |
| --- | --- | --- |
| 生成 `trashbot.elevator_field_run_material_validation.v1` artifact | 已完成 | Task A 新增 `pc-tools/evidence/elevator_field_run_material_validation.py` 和测试。 |
| 输出 `trashbot.elevator_field_run_material_validation_summary.v1` | 已完成 | Task A summary 输出，Task B diagnostics 与 Task C mobile 均只读消费。 |
| 校验 door state、target floor、human assistance、runtime log、task record、completion signal、diagnostics/mobile summary | 已完成 | Autonomy test `Ran 7 tests ... OK`，覆盖缺失/模板/坏 JSON/evidence_ref mismatch/unsafe copy/越界成功声明。 |
| Robot diagnostics 只读消费 artifact/summary | 已完成 | `operator_gateway_diagnostics.py` 暴露 `elevator_field_run_material_validation` / `_summary`，Robot test `Ran 75 tests ... OK`。 |
| Mobile 只读展示，不改变 Start/Confirm/Cancel gating | 已完成 | `mobile/web/app.js` 新增“电梯现场材料校验” panel，mobile test `Ran 42 tests ... OK`。 |
| Product closeout 不写成真实现场或 delivery success | 已完成 | `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout 均保留 `software_proof_docker_elevator_field_material_validation_gate`、`delivery_success=false` 和 `not_proven`。 |

## 2. 用户价值对照

- 对普通手机用户：新增 panel 只展示 phone-safe 材料校验状态，帮助理解现场实测还缺什么，不暴露 raw JSON、ROS topic、串口、token、本机路径或硬件调试细节。
- 对支持人员：Robot diagnostics 和 PC CLI 对齐同一 `evidence_ref`，能在下一次受控楼宇实测前提前发现缺材料、模板未替换、错配或 unsafe copy。
- 对产品验收：本轮把 Objective 2/O3 的现场材料缺口变成可机器校验的补证清单，但仍不把 Docker/local artifact 写成真实现场证明。

## 3. OKR 最低优先级核对回顾

- `OKR.md` 当前数值最低 Objective 仍是 Objective 5，约 66%。
- 本轮不针对 Objective 5 的理由仍成立：当前本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料。
- 因此本轮不继续堆本地 O5 metadata depth，也不因 `elevator_field_run_material_validation` 上调 Objective 5。
- 本轮针对 Objective 2/O3 的理由成立：最新电梯 assisted delivery 主链路已经进入默认 dry-run，本轮把下一次受控楼宇现场补证材料变成 fail-closed validation artifact、diagnostics summary 和 mobile read-only panel。

## 4. 边界核对

- 证据边界：`software_proof_docker_elevator_field_material_validation_gate`。
- 控制边界：`delivery_success=false`、`primary_actions_enabled=false`。
- 明确不证明真实电梯、真实 Nav2/fixed-route、真实路线采集、真实 WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。
- Browser render check 未运行，原因是 Browser runtime reported `Browser is not available: iab`。

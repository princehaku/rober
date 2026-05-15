# Sprint 2026.05.15_13-14 Elevator Field Rehearsal Execution Pack - Side2Side Check

sprint_type: epic

## 1. 对照结论

本 sprint 的 PRD 目标是把上一轮 `elevator_field_run_review` 复核决策整理成现场同学可执行的受控电梯演练执行包，并在 Robot diagnostics 与 mobile/web 中保持只读、安全、不可误宣称成功的展示链。工程 Task A/B/C 回传的证据满足该目标。

本轮验收结果归类为 `software_proof_docker_elevator_field_rehearsal_execution_pack_gate`。它不证明真实电梯、真实楼层确认、真实人工协助、真实喇叭/TTS、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 2. PRD 验收对照

| PRD 要求 | 本轮证据 | 验收判断 |
| --- | --- | --- |
| 新增 `trashbot.elevator_field_run_execution_pack.v1` artifact | Task A 新增 `pc-tools/evidence/elevator_field_run_execution_pack.py`，支持 `--review-json`、`--output`、`--once-json`，输出 pack/summary schema。 | 通过 |
| 输出 phone-safe summary 供 diagnostics/mobile 只读消费 | Task A 输出 summary；Task B 暴露 `elevator_field_run_execution_pack` / `_summary`；Task C 兼容 top-level、`phone_readiness`、diagnostics summary 和 nested diagnostics summary。 | 通过 |
| 固定 `same_evidence_ref_required=true`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | Task A 固定字段；Task B 只接受 JSON boolean `true`，字符串弱类型 fail closed；Task C UI 展示 false/not_proven 且不改变控制 gating。 | 通过 |
| unsafe copy / success claim fail closed | Task A 增加自由文本成功文案拦截；Task B 将 unsafe fields 标记为 fail closed；Task C 过滤 raw ROS topic、serial/UART、WAVE ROVER、credential、raw artifact 和 success phrasing。 | 通过 |
| 不改变 Start/Confirm/Cancel gating | Task B 不触发 collect/dropoff/cancel、ACK、Nav2、HIL；Task C 明确不调用 Start/Confirm/Cancel，也不主动 fetch diagnostics。 | 通过 |
| Product closeout 不虚增真实现场或 O5 external proof | `OKR.md` 与 progress log 保持 Objective 5 约 66%，并写明 not real Objective 5 external proof。 | 通过 |

## 3. 工程验证证据复核

- Task A Autonomy：py_compile passed；`test_elevator_field_run_execution_pack.py` `Ran 7 tests in 0.026s OK`；CLI `--help` passed；required `rg` passed；scoped diff check passed。
- Task B Robot：py_compile passed；`test_operator_gateway_diagnostics.py` 复核后 `Ran 79 tests in 0.078s OK`；required `rg` passed；scoped diff check passed。
- Task C Full-stack：`mobile/test_mobile_web_entrypoint.py` `Ran 44 tests in 0.119s OK`；py_compile passed；`node --check mobile/web/app.js` passed；required `rg` passed；scoped diff check passed。

## 4. OKR 和边界复核

- Objective 2 可保守上调：execution pack 将复核决策推进为受控现场演练 manifest、材料模板、first-run/rerun 命令和 operator handoff，直接服务 O2 KR6/KR7 的电梯 assisted delivery 现场补证。
- Objective 3 可保守上调：execution pack 继续要求 Nav2/fixed-route runtime log、task record、completion signal、diagnostics/mobile safe summary 使用同一 `evidence_ref`，强化固定路线现场复账材料链。
- Objective 5 不上调：本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实手机/生产云证据。

## 5. 风险和未完成事项

- 仍缺真实电梯门状态、目标楼层确认、人工协助记录、真实喇叭/TTS、真实 Nav2/fixed-route runtime、真实路线采集、WAVE ROVER/UART/HIL 和同一 `evidence_ref` 上车实机复账。
- 仍缺真实 dropoff completion、真实 cancel completion、delivery success、真实手机设备/browser、production app 和真实 PWA prompt/user choice。
- O5 external blocker 仍在：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 均未出现。

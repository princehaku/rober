# Field Evidence Rerun Execution Pack Side2Side Check

## Scope

- sprint_type: epic
- Sprint: `2026.05.20_18-19_field-evidence-rerun-execution-pack`
- Capability: `field_evidence_rerun_execution_pack`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_pack_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## User Value And Product North Star

本轮用户价值是把上一轮现场复跑队列转成 field owner 可执行的 execution pack：下一次真实路线/电梯复跑前，owner 可以按同一 safe `evidence_ref` 收集 task record、Nav2/fixed-route runtime log、route completion signal、电梯门/楼层/人工协助、dropoff/cancel completion、delivery result 和真实 phone/browser evidence。

产品北极星仍是普通手机用户可用的低成本 ROS2 垃圾投递机器人。本轮不证明真实送达，只证明 repo 已能生成、传递和展示安全的现场材料复跑执行包。

## OKR And KR Check

| Objective | Side2Side 结论 |
| --- | --- |
| Objective 5 | 仍约 68%；本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 phone/browser external proof。 |
| Objective 1 | 仍约 81%；本轮没有 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF materials，也没有解决 PR #5 `PRRT_kwDOSWB9286CJ3tX`。 |
| Objective 2 | 仍约 99%；execution pack 让 route/elevator 现场材料复跑更可执行，但没有真实 field rerun 或 delivery result。 |
| Objective 3 | 仍约 99%；material templates 明确真实 Nav2/fixed-route runtime log、route completion signal 和 task record 缺口，但没有路线实跑。 |
| Objective 4 | 仍约 99%；mobile/web 只读 panel 可见 execution pack，但不是真实 phone/browser 验收。 |

## Worker Evidence Integration

- Autonomy：新增 `pc-tools/evidence/field_evidence_rerun_execution_pack.py` 和 `tests/test_field_evidence_rerun_execution_pack.py`，消费 `field_evidence_rerun_queue` artifact/summary，输出 execution steps、material templates、owner handoff、fail/pass thresholds、backfill instructions；`py_compile`、5 tests、CLI help、required `rg`、scoped diff-check 通过。
- Robot：在 `onboard/src/ros2_trashbot_behavior/.../operator_gateway_diagnostics.py` 新增 `robot_diagnostics_field_evidence_rerun_execution_pack_summary` safe alias；diagnostics focused tests 报告 `Ran 234 tests OK`，required `rg`、scoped diff-check 通过。
- Full-Stack：在 `mobile/web` 新增“现场证据复跑执行包”只读 panel；`node --check`、mobile focused tests `Ran 175 tests OK`、fixture JSON、required `rg`、scoped diff-check 通过。
- Docs 同步：workers 已同步 `docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_runtime_contracts.md`、`docs/product/mobile_user_flow.md`；Product 同步 `docs/process/okr_progress_log.md`。

## Acceptance Result

- 验收口径满足：PC canonical artifact、Robot safe alias、mobile read-only panel 与 Product closeout 均保留 `software_proof_docker_field_evidence_rerun_execution_pack_gate`。
- 主操作安全满足：mobile panel 不触发 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、diagnostics fetch、queue scheduling、execution scheduling、automatic retry 或 robot command。
- 产品边界满足：本轮不写成真实现场复跑、真实 Nav2/fixed-route、真实 task record、route completion signal、真实电梯门/楼层/人工协助、dropoff/cancel completion、delivery result、真实 phone/browser、WAVE ROVER/UART/HIL、O5 external proof、PR #5 thread resolved 或 delivery success。

## PR And Review Evidence

- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending。
- GitHub comment `3269642220` 只是 published reply，不是 hardware proof，不是真实材料回填，也不是 reviewer resolved。
- PR #6 README docs-only，不包含 runtime、hardware、HIL、true phone/browser 或 O5 external tests。

## Remaining Evidence Needed

- 同一 safe `evidence_ref` 的真实 task record。
- 真实 Nav2/fixed-route runtime log 与 route completion signal。
- 真实电梯门状态、目标楼层确认、人工协助记录。
- 真实 dropoff completion、cancel completion 和 delivery result。
- 真实 iPhone/Android phone/browser evidence。
- 独立 O1：WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 独立 O5：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、外部 phone/browser proof。

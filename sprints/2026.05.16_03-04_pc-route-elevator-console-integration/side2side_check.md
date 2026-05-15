# Sprint 2026.05.16_03-04 PC Route Elevator Console Integration - Side2Side Check

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星仍是让普通手机用户交付垃圾后，小车能沿固定路线完成可验证、可复盘的低成本送达流程。本轮不是提升真实送达能力，而是把现场调试人员需要看的 PC route progress、recent task 与上一轮 elevator-route reconciliation 放到同一个只读复盘入口，减少真实联跑前的证据拼接成本。

## 2. OKR 映射

- Objective 3 主目标：PC route debug console 已能同屏展示 route progress、recent task 与 `route_elevator_reconciliation`，支撑固定路线/关键帧调试的可观测性。
- Objective 2 支撑：电梯 assisted delivery 的 phase evidence、route completion signal 和 operator next steps 可以通过同一个 PC console nested summary 被复核，但不证明真实电梯或真实送达。
- Objective 4 支撑：mobile PC route panel 可展示该 nested summary，普通现场人员能看到 blocked/not_proven 边界；不证明真实手机/browser。
- Objective 5 不推进：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据。

## 3. KR 拆解和本轮核心抓手

- KR3/O3：固定路线 dry-run 与调试入口从 route-only 推进到 route + elevator reconciliation 同屏复盘。
- KR5/O3：PC 关键帧调试页面/API 的最近任务状态现在可携带 nested elevator-route summary。
- KR6/KR7/O2：电梯证据链在 diagnostics 和 mobile 中保持 metadata-only，便于下一次同一 `evidence_ref` 现场材料复核。

核心抓手是 `software_proof_docker_pc_route_elevator_console_integration_gate`：父级 PC console boundary 保持 `software_proof_docker_pc_route_debug_console_gate`，新增 nested `route_elevator_reconciliation.evidence_boundary=software_proof_docker_pc_route_elevator_console_integration_gate`。

## 4. Side-by-side 验收

| 验收项 | 计划口径 | 实际结果 | 产品判断 |
| --- | --- | --- | --- |
| PC route console | 可选 `--elevator-route-reconciliation`，缺失 fail closed | Task A 已实现，`test_route_debug_web.py` `Ran 7 tests in 0.533s OK`，help/py_compile/rg/diff check 通过 | 通过 |
| Robot diagnostics | metadata-only 保留 `pc_route_debug_console.route_elevator_reconciliation` | Task B 已实现，`test_operator_gateway_diagnostics.py` `Ran 81 tests in 0.076s OK`，py_compile/rg/diff check 通过 | 通过 |
| Mobile PC route panel | 展示 nested route/elevator summary，不改变 Start/Confirm/Cancel gating | Task C 已实现，`mobile/test_mobile_web_entrypoint.py` `Ran 46 tests in 0.144s OK`，py_compile/node/rg/diff check 通过 | 通过 |
| 证据边界 | 保持 software proof，不写成真实运行 | 文档和 summary 均保留 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` | 通过 |

## 5. 优先级、责任 Engineer 和验收口径

- P0 Autonomy Algorithm Engineer：PC route debug console 集成 nested elevator-route reconciliation；验收为 CLI/help/API/HTML/unit/diff check。
- P0 Robot Platform Engineer：diagnostics metadata-only 透传 nested summary；验收为 diagnostics unit、py_compile、rg 和 diff check。
- P0 User Touchpoint Full-Stack Engineer：mobile PC route panel 展示 nested summary；验收为 mobile unit、node check、py_compile、rg 和 diff check。
- P0 Product Manager / OKR Owner：完成 `OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md` closeout。

## 6. 风险、阻塞和证据链缺口

本轮只证明本机 Docker/local PC route console、Robot diagnostics metadata-only consumption 和 mobile read-only panel 能一致展示 nested route/elevator reconciliation。它不证明真实 Nav2/fixed-route、真实路线采集、真实电梯、WAVE ROVER/UART/HIL、真实手机/browser、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

下一步若要继续推动 Objective 3/O2，必须补真实现场或上车材料：Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、真实楼层确认、人工协助记录、真实 dropoff/cancel completion 或 delivery success，并继续要求同一 `evidence_ref`。

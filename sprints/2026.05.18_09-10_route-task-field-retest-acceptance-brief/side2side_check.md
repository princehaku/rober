# Sprint 2026.05.18_09-10 Route Task Field Retest Acceptance Brief - Side2Side Check

## 1. 用户价值对照

本轮用户价值是让现场 operator / support user 在真实 route/elevator field materials 仍缺时，能通过 PC evidence gate、Robot diagnostics 和 mobile/web 看到同一份 acceptance brief。三方 worker 结果满足这个目标：

- PC 侧有顶层 `tests.test_route_task_field_retest_acceptance_brief` 验收入口。
- Robot 侧有 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` safe alias。
- mobile/web fixture 和 tests 证明 Robot alias 与主 acceptance brief 使用同一 phone-safe boundary/status whitelist。

这减少了现场复测前的两个主要误读：一是不同表面读取不同 key；二是把 acceptance brief 当成真实 route/elevator field pass。

## 2. OKR 映射对照

- Objective 2：本轮补齐 route/elevator assisted delivery 现场复测验收简报的一致读取入口，服务后续真实门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 与 delivery result 回填。
- Objective 3：本轮让 Nav2/fixed-route runtime log、route completion signal、task record 等 required evidence packet 可以通过统一 brief 进入现场复测验收口径。
- Objective 4：本轮让 mobile/web 只读消费 Robot diagnostics alias，不暴露 raw JSON、ROS topic、串口、WAVE ROVER、HIL、ACK、cursor 或 primary action。
- Objective 1：不推进。没有真实 WAVE ROVER/UART/HIL 证据，也没有 PR #5 真实 2D LiDAR / ToF 材料。
- Objective 5：不推进。没有公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser external proof。

## 3. 验收口径对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| PC acceptance brief gate 可用顶层 unittest 运行 | 通过 | `python3 -m unittest tests.test_route_task_field_retest_acceptance_brief` -> `Ran 5 tests in 0.029s OK` |
| Robot diagnostics 输出 safe alias | 通过 | diagnostics unittest -> `Ran 176 tests in 0.356s OK`，三个 alias 一致 |
| mobile/web 读取 Robot alias 且不放开主操作 | 通过 | mobile unittest -> `Ran 72 tests in 0.368s OK`，`node --check mobile/web/app.js` pass |
| 证据边界保持 software proof | 通过 | 三方均保留 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` |
| 不宣称真实 field/HIL/phone/O5 proof | 通过 | closeout 和 OKR 更新明确保守边界 |

## 4. Side-by-side 结论

本轮满足 PRD 中的 KR-A、KR-B、KR-C 和 KR-D。它是三端 contract consistency 的 software proof，不是用户可现场验收的真实送达闭环。

OKR 进度不应上调：Objective 2/3/4 已处于约 99%，本轮只是减少现场材料进入真实复测前的契约断点；没有新增真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 delivery result 或真实手机/browser。Objective 1 和 Objective 5 均没有新增真实材料。

# Sprint 2026.05.16_01-02 Elevator Evidence Driven Mainline - Side2Side Check

sprint_type: epic

## 1. 对照验收

| PRD / Tech Plan 验收点 | 收口判断 | 证据 |
| --- | --- | --- |
| 新 artifact/schema 固定为 Docker/local software proof | 通过 | Task A 输出 `trashbot.elevator_assist_rehearsal_evidence.v1`，固定 `software_proof_docker_elevator_evidence_driven_mainline_gate`、`source=software_proof`、`delivery_success=false`、`primary_actions_enabled=false`。 |
| Robot dry-run 支持缺失 artifact fallback | 通过 | Task B 回传：`elevator_assist_evidence_file` 缺失/空文件保持既有 dry-run fallback。 |
| Robot 非法 artifact fail closed | 通过 | Task B 回传：schema/boundary/boolean/source 不满足 contract 时 fail closed，并写入 failure/manual takeover。 |
| Robot artifact 通过时驱动 phase evidence 并提升 `evidence_ref` | 通过 | Task B 回传：按 `phase_evidence` 驱动 `machine.elevator_phase(...)`，artifact `evidence_ref` 提升到 task record 顶层 `evidence_ref/result_path`。 |
| Mobile panel 只读展示 evidence-driven elevator assist | 通过 | Task C 回传：展示 safe `evidence_ref`、phase evidence、failure/manual takeover、same evidence ref requirement 和 boundary。 |
| Start/Confirm/Cancel gating 不放行 | 通过 | Task C 回传：Start Delivery、Confirm Dropoff、Cancel gating 未改，`primary_actions_enabled=false`。 |
| 保持证据边界，不宣称真实送达 | 通过 | 三条工程线均固定 `delivery_success=false`、`not_proven`；本 closeout 明确 not real elevator/Nav2/HIL/delivery/O5 proof。 |

## 2. OKR 最低优先级复核

启动时和收口时，`OKR.md` 4.1 数值最低 Objective 仍是 Objective 5，约 66%。本 sprint 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，因此不应继续叠本地 O5 metadata，也不应上调 Objective 5。

本 sprint 选择 Objective 2/3/4 的理由仍成立：PR #4/#5 已把 elevator assisted delivery 设为 mandatory MVP，而上一轮 execution pack 仍缺真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime、同一 `evidence_ref` task record/completion signal、HIL、dropoff/cancel completion 和 delivery success。本轮把 execution pack 前移到 Robot 主链路可消费的 rehearsal evidence artifact，属于现场复账前的必要软件链路。

## 3. 验收边界

- 本轮证明：Docker/local `elevator_assist_rehearsal_evidence` artifact、Robot dry-run consumption、task record evidence anchor、mobile read-only panel 与 phone-safe copy boundary 可对齐。
- 本轮不证明：真实电梯、真实门状态、真实目标楼层、真实人工协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。
- 文档路径核对：本轮引用的 `docs/product/elevator_assisted_delivery.md`、`docs/product/mobile_user_flow.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md` 均存在。

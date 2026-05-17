# Sprint 2026.05.18_06-07 Route Task Material Callback Review Decision - PRD

sprint_type: epic

## 1. 用户价值

现场 owner 已经有 material pack 和 callback packet，但还缺一层“回执能不能进入下一步”的复核决策。如果没有该决策，accepted / missing / rejected materials 容易在聊天、表格和现场记录之间漂移，导致把不完整材料误当成 route/elevator field evidence。

本轮交付一个可机器校验、可诊断只读展示、可手机端查看的 review decision，让现场材料回执明确落到三类动作：

- `ready_for_controlled_field_rerun_not_proven`
- `needs_material_callback_backfill_not_proven`
- `blocked_material_callback_review_not_proven`

它服务“普通手机用户交垃圾后，小车沿固定路线、必要时借助电梯完成可靠投递”的证据链，但仍是 Docker/local software proof。

## 2. OKR 映射

- Objective 2：继续补 route/elevator assisted delivery 现场材料复核链，仍不证明真实送达或电梯通过。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 等回执材料的复核结果结构化，仍不证明真实路线实跑。
- Objective 4：让 mobile/web 只读展示复核决策，帮助非工程用户理解还缺什么，仍不证明真实手机设备验收。
- Objective 1：不推进；没有真实 WAVE ROVER/UART/HIL 材料。
- Objective 5：不推进；没有真实外部云/4G/OSS/CDN/DB/queue/worker/cutover 材料。

## 3. PR / Review 证据

- PR #4 明确电梯 assisted delivery 必达，因此现场材料链必须覆盖门状态、楼层确认、人工协助、Nav2/fixed-route runtime、task record、dropoff/cancel completion 和 delivery result。
- PR #5 review P1 指出 default hardware set 与 mandatory sensor baseline 不一致；P2 指出新 sensor assumption 缺本地 vendor source；这说明硬件材料不能继续靠默认叙述推进，必须保留真实 SKU/source/receipt/HIL-entry 缺口。
- 最近两轮 sprint 已经把 route/elevator material pack 和 callback packet 做成 software proof；下一步最小有效功能是 review decision，而不是重复生成 packet。

## 4. 验收口径

必须产出：

- `trashbot.route_task_field_retest_material_callback_review_decision.v1`
- `trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`
- `software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`

必须保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- same safe `evidence_ref`
- diagnostics/mobile metadata-only

验收失败条件：

- 把 review decision 写成 real route/elevator field pass。
- 因 review decision 存在而启用 Start / Confirm / Cancel / dispatch / callback / robot command。
- 接收 raw local path、serial/UART path、credentials、token、OSS/DB/queue secret、success claim 或 weakly typed safety flag。
- 复核逻辑不区分 accepted / missing / rejected materials。

## 5. 分工

- Autonomy：实现 PC gate 和 focused tests，更新 `docs/interfaces/evidence_contracts.md`。
- Robot：实现 diagnostics consumer 和 tests，更新 `docs/interfaces/ros_contracts.md`。
- Full-stack：实现 mobile/web panel 和 tests，更新 `docs/product/mobile_user_flow.md`。
- Product：收口 OKR、progress log 和 sprint 文档。

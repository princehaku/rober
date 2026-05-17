# Sprint 2026.05.17_13-14 Route Task Handoff Result Reconciliation Bridge - Side2Side Check

sprint_type: epic

## 1. 用户价值与产品北极星

北极星仍是让普通手机用户交给小车垃圾后，能获得可解释、可追溯、可恢复的送达体验。本轮没有试图证明真实送达，而是补上支持人员和现场复测链路的追溯缺口：result reconciliation 现在能显示该复账来自 review-result handoff derived result-intake，避免后续真实材料回填时靠人工口头说明来源。

## 2. OKR 映射

- Objective 2：PR #4 要求 elevator-assisted delivery 成为必须能力；本轮把 route/elevator review-result handoff 的来源谱系继续带到 result reconciliation，支持未来真实门状态、楼层确认、人工协助和 delivery result 复账。
- Objective 3：固定路线 / Nav2 的 runtime log、route completion signal、task record 等材料仍可沿同一 `evidence_ref` 追溯到 result-intake 和 upstream handoff，不被 reconciliation 阶段抹掉来源。
- Objective 5：不推进。O5 仍约 68% 且数值最低，但本机只有 Docker，缺真实 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、production worker/migration/cutover 或真实手机/browser 材料。

## 3. KR 拆解或更新

- Objective 2 KR5/KR6/KR7：补强任务记录、诊断和电梯 assisted delivery 证据链的同一 `evidence_ref` 复账能力。
- Objective 3 KR2/KR3/KR5：补强 fixed-route / Nav2 result materials 的可回放、可解释和 PC/Robot/mobile 共同展示能力。
- Objective 5 KR1-KR6：本轮无真实 external proof，不更新完成度。

## 4. 本轮核心抓手

核心抓手是 `route_task_field_retest_result_reconciliation` 的 safe lineage bridge：

- PC 从 result-intake `source_result` 摘要读取 lineage，不追 raw handoff artifact。
- Robot diagnostics metadata-only 透传 lineage，fail closed。
- Mobile result reconciliation panel 展示 safe lineage，copy/export whitelist-only。

## 5. 需要做什么

本轮 Task A/B/C 已完成。下一步不应继续包装相同 local metadata，而应补真实材料：

- O2/O3：真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result。
- O5：真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser。
- PR #5：真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。

## 6. 优先级与验收口径

验收口径通过：

- PC lineage 只来自 supported result-intake source metadata。
- Robot diagnostics 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Mobile copy/export 只包含白名单字段，Start Delivery / Confirm Dropoff / Cancel gating 不变。
- Product closeout 明确证据边界为 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`，不写成 field pass、HIL、真实手机/browser、delivery success 或 Objective 5 external proof。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：Task A，PC reconciliation lineage。
- Robot Platform Engineer：Task B，Robot diagnostics metadata-only consumer。
- User Touchpoint Full-Stack Engineer：Task C，mobile/web read-only lineage panel。
- Product Manager / OKR Owner：Task D，closeout、OKR、进度日志和证据边界。

## 8. 风险、阻塞和证据链缺口

- 真实现场材料仍未到位，本轮只能作为 software proof。
- PR #5 的真实硬件/source/material blocker 多轮未拿到，不应再消费为本地 metadata 包装。
- Objective 5 继续低于其他 Objective，但按 `OKR.md` 第 6 节 stop rule，缺真实外部材料前保持不变。

## 9. 需要更新的 sprint 文档

- `tech-done.md`：已记录 Task A/B/C/D 改动、验证和风险。
- `side2side_check.md`：已完成产品验收对照。
- `final.md`：已完成 sprint 收口和 OKR 更新结论。

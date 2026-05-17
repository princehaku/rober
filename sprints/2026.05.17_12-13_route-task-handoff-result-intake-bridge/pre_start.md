# Sprint 2026.05.17_12-13 Route Task Handoff Result Intake Bridge - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 Epic sprint：`route-task-handoff-result-intake-bridge`。

目标不是新增真实现场结论，而是修通上一轮 `route_task_field_retest_review_result_handoff` 到既有 `route_task_field_retest_result_intake` 的软件证据桥：result intake gate 必须能安全消费 review-result handoff artifact、summary、wrapper 和 nested JSON，并继续产出 `software_proof_docker_route_task_field_retest_result_intake_gate` 的 result intake artifact / summary。

本轮不写 `tech-done.md`、`side2side_check.md` 或 `final.md`。这些文件只在后续实现、验收和 closeout 完成后更新。

## 2. 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给小车后，小车沿固定路线或跨楼层 assisted delivery 完成送达，并且每次任务都有可复盘 evidence chain。

本轮用户价值是减少现场复测材料链的断点：上一轮 review-result handoff 已经把回执复核决策推到 result-intake 前，但 `pc-tools/evidence/route_task_field_retest_result_intake.py` 仍不能直接识别 `trashbot.route_task_field_retest_review_result_handoff.v1` 或 `trashbot.route_task_field_retest_review_result_handoff_summary.v1`。如果不补桥，后续真实材料回填后仍需要人工转换，容易丢失 same-`evidence_ref`、blocked reason、required materials 和 owner handoff。

## 3. 当前证据

- `OKR.md` 4.1 显示 Objective 5 约 68%，是数字最低 Objective。
- Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser，继续堆本地 Objective 5 metadata 不能形成真实 external proof。
- GitHub PR #5 暴露过 `docs/product/production_hardware_boundary.md` 默认硬件集与 `monocular + 2D LiDAR + ToF` mandatory baseline 的矛盾；近期硬件材料链仍缺真实 SKU/source/receipt/install/wiring/calibration/HIL-entry 材料。
- GitHub PR #4 已把电梯/跨楼层 assisted delivery 升级为主链必须能力，但真实 route/elevator field materials 仍缺。
- 上一轮 `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/final.md` 建议把 result handoff 推向真实材料 intake 后的 reconciliation / execution evidence。
- 只读排查确认 `route_task_field_retest_result_intake` 当前 SOURCE_SCHEMAS 支持 session handoff、result、intake，不支持 `route_task_field_retest_review_result_handoff` / `_summary`。

## 4. OKR 映射

- Objective 2：核心映射。把 route/elevator assisted delivery 的现场复测回执交接推进到 result intake，补齐后续 result reconciliation 的入口。
- Objective 3：核心映射。让 fixed-route / Nav2 field evidence chain 的 result handoff 能进入同一 `evidence_ref` 的 intake gate。
- Objective 4：间接映射。Robot diagnostics 和 mobile/web 只读 consumer 只验证可读，不新增 Start / Confirm Dropoff / Cancel 放行动作。
- Objective 5：不作为本轮主线。Objective 5 仍最低，但缺真实 external proof；本轮明确避免重复消费同一 Docker-only / O5 外部 blocker。

## 5. Blocker 重复消费核对

最近多轮已反复记录：

- Objective 5 外部证据 blocker：缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。
- PR #5 硬件材料 blocker：缺真实 2D LiDAR / ToF SKU、source、receipt、install、wiring、calibration、HIL-entry。

本轮不继续消费上述 blocker，而是转向不依赖外部云或真实硬件采购材料的 O2/O3 route-task result-intake 桥接缺口。该选择符合“同一 blocker 不重复堆 metadata”的红线。

## 6. 责任 Owner

- Product Manager / OKR Owner：本轮规划、验收口径、closeout 时 OKR 边界核对。
- Autonomy Algorithm Engineer：主责 PC result-intake gate 桥接、样例/测试和 result artifact 语义。
- Robot Platform Engineer：只读验证既有 Robot diagnostics consumer 能读取 result-intake 输出，不新增控制动作。
- User Touchpoint Full-Stack Engineer：只读验证既有 mobile/web result-intake consumer 能读取 result-intake 输出，不新增 primary action 放行。
- Hardware Infra Engineer：本轮只补 PR #5 事实边界，不改硬件配置，不写 vendor/source 结论。

## 7. 本轮边界

必须保持：

- `software_proof_docker_route_task_field_retest_result_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- same-`evidence_ref` required

不得宣称：

- 真实 route/elevator field pass。
- 真实 Nav2/fixed-route runtime pass。
- 真实电梯门状态或目标楼层确认。
- 真实 dropoff/cancel completion。
- 真实 delivery success。
- Objective 5 external proof。
- HIL、真实 WAVE ROVER、真实串口/UART 或真实 2D LiDAR / ToF 材料。

## 8. 需要创建或更新的 sprint 文档

本轮规划阶段创建：

- `sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/pre_start.md`
- `sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/prd.md`
- `sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/tech-plan.md`

后续实现完成后再由 closeout 更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

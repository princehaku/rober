# Sprint 2026.05.18_00-01 Route Task Result Callback Review Handoff - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：现场支持在 `route_task_field_retest_result_callback_review_decision` 之后，需要一个明确的 result review 前交接面：本次 review decision 是否可进入 result review、仍缺哪些材料、哪些 owner 需要补、哪些命令需要 rerun、哪些状态只能保持 blocked。没有这个 handoff，route/elevator 现场材料会停在“已经复核但还没交给下一步”的人工追踪状态。

产品北极星：低成本 ROS2 自主垃圾投递机器人闭环。当前 PRD 服务 PR #4 的 route/elevator field materials 回填链，把证据从 callback review decision 推进到 result review handoff；但本轮不证明真实送达、真实电梯、真实 Nav2、真实手机、HIL 或 Objective 5 external proof。

## 2. 证据来源

- `OKR.md` 4.1：Objective 5 约 68% 最低，但继续推进需要真实 external proof；Objective 1 约 81%，但仍缺真实 WAVE ROVER HIL packet；Objective 2 / Objective 3 / Objective 4 约 99%，仍缺真实 field evidence。
- PR #4：elevator-assisted delivery 是必达主线，route/elevator materials 必须可回填、可复核、可追责。
- PR #5 review comments：曾指出 production hardware boundary 默认硬件集与 2D LiDAR / ToF mandatory baseline 矛盾、OKR lowest-objective narrative drift、mandatory sensor assumptions 缺 vendor/source。当前真实 2D LiDAR / ToF 材料仍缺，本轮不包装硬件 blocker。
- `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/final.md`：上一轮已完成 callback review decision，输出复核决策、owner handoff、next required evidence 和 rerun path；下一步需要 result review 前的 handoff/status/owner follow-up/rerun package。
- 最近 HIL packet finals `21-22`、`22-23`、`23-24`：连续三轮围绕真实 WAVE ROVER HIL packet 所需材料做本地软件证明，剩余 blocker 均为真实硬件不可得；本机只有 Docker，不能继续消费同一 blocker。

## 3. OKR 映射

- Objective 2：主映射。result callback review handoff 让 elevator-assisted delivery 的 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 进入明确 handoff / rerun / owner follow-up 状态。
- Objective 3：主映射。handoff package 要求 Nav2/fixed-route runtime log、route completion signal 和 task record 与同一 `safe_evidence_ref` 对齐，避免 result review 使用错配材料。
- Objective 4：支援映射。手机端只读展示 status 和 next action，不改变 primary actions。
- Objective 5：明确不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1：明确不推进。真实 WAVE ROVER HIL packet blocker 已在最近三轮重复暴露，本轮不再本地包装。

## 4. KR 拆解或更新

本轮不直接更新 `OKR.md`，实现收口后由 Product closeout 根据 A/B/C 证据保守判断是否只记录 progress log 或微调 OKR。

本轮 KR 拆解：

- KR-O2-Callback-Handoff：把 callback review decision 转成 result review 前的 owner follow-up、handoff status 和 rerun package。
- KR-O3-Same-Evidence-Ref：所有 route/elevator result materials 必须保持同一 `safe_evidence_ref`，错配必须 rerun 或 blocked。
- KR-O4-Read-Only-Mobile：mobile/web 只能展示 handoff 状态、缺口、owner 和 rerun hints，不启用 Start Delivery、Confirm Dropoff、Cancel 或 ACK。
- KR-Boundary：所有输出必须保留 `software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 本轮核心抓手

`route_task_field_retest_result_callback_review_handoff` 是 result review 前的 handoff gate。它不做真实现场判断，而是把上一轮 review decision 转成下一步团队能执行的材料状态：

- `ready_for_result_review_handoff`
- `needs_owner_follow_up`
- `needs_callback_rerun`
- `evidence_ref_mismatch_rerun`
- `blocked_unsafe_review_handoff`

## 6. 需要做什么

Autonomy：

- 新增 PC evidence gate，读取 callback review decision artifact / summary。
- 输出 handoff artifact / summary，包含 status、owner follow-up、review-ready package、rerun package、next required evidence、boundary flags。
- 增加 focused test，覆盖 ready、missing owner follow-up、callback rerun、evidence ref mismatch、unsafe success claim。
- 更新 `docs/interfaces/evidence_contracts.md`。

Robot：

- 在 diagnostics 增加 metadata-only consumer。
- 只消费 safe summary，不读取 raw artifact、不改变 ROS2 action/task/control。
- focused test 覆盖 supported summary、missing summary、unsupported schema、unsafe flags。
- 更新 `docs/interfaces/ros_contracts.md`。

Full-stack：

- 在 `mobile/web` 增加只读 handoff panel。
- fixture 展示 handoff status、owner follow-up、rerun package、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- focused test 验证展示和 gating 不变。
- 更新 `docs/product/mobile_user_flow.md`。

Product：

- A/B/C 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 保持证据边界，不把本地 software proof 写成真实 field pass、HIL、手机或 O5 external proof。

## 7. 优先级和验收口径

P0：

- PC gate fail closed：缺 decision、unsupported schema、unsafe copy、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须失败。
- Robot diagnostics 只读：不改变 task_orchestrator、Nav2、Start、Dropoff、Cancel、ACK 或 HIL 控制路径。
- Mobile panel 只读：显示 handoff 状态但 primary actions 仍按既有 gating。
- 文档同步：`docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 必须更新。

P1：

- CLI / fixture 支持上一轮 artifact / summary 的 top-level 与 safe wrapper 输入。
- 输出包含 owner follow-up、rerun package、review-ready package 和 next required evidence。

验收口径：

- focused `py_compile`、focused `unittest`、`node --check`、required `rg` 和 scoped `git diff --check` 全部通过。
- planning docs required `rg` 能命中 `sprint_type: epic`、`route_task_field_retest_result_callback_review_handoff`、`OKR 最低优先级核对`、`Objective 5`、`Objective 1`、`PR #4`、`PR #5`、`software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不运行 broad full test；测试只围栏。

## 8. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC evidence gate + focused test + `docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：diagnostics metadata-only consumer + focused test + `docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel + fixture/test + `docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：closeout docs / OKR / progress log。

## 9. 风险、阻塞和证据链

- O5 风险：缺真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，本轮不推进。
- O1 风险：缺真实 WAVE ROVER HIL packet 和真实硬件，本轮不继续消费同一 blocker。
- O2/O3 风险：仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 completion signal、真实 door/floor/human assistance/dropoff/cancel/delivery result。
- O4 风险：mobile/web 是本地只读 panel，不是真实 iPhone/Android、production app 或 PWA prompt/user choice。
- PR #5 风险：真实 2D LiDAR / ToF 材料仍缺，不能把本轮写成硬件材料进展。

## 10. 范围外

- 不修改硬件 vendor 资料，不新增 2D LiDAR / ToF facts。
- 不修改真实 ROS2 control、Nav2 route execution、task action semantics 或 hardware launch 参数。
- 不实现 Objective 5 云端 external proof。
- 不声明 `hil_pass`、真实送达、真实手机通过或 delivery success。

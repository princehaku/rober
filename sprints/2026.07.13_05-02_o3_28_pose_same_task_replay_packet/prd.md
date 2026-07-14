# PRD - O3 28-Pose Same-Task Replay Packet

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- PRD status: ready for technical planning
- Proof boundary target: `software_proof_o3_o1_strict_no_motion_same_task_route_replay_packet_only`

## 用户价值和产品北极星

产品北极星是可验证的固定路线送垃圾闭环。本轮用户价值不是让车移动，而是让已捕获的 28-pose fixed-route material 进入同一任务的 replay/material packet，形成后续路线回放、消费者集成和受控 route execution 的输入凭证。

如果本轮成功，后续执行同学不需要重新判断 03:00 fresh path、04:02 consumer、CSV 和 JSONL 是否属于同一任务；packet 会把这些事实合并成可校验的同一 `task_id` 证据。

## OKR 映射和方向判断

- Objective 5 / O5：当前最低，约 `85%`，但被真实 external production evidence 锁住。本轮不做 O5 readiness/checklist/wrapper，不计 O5 增量。
- Objective 1 / O1：当前约 `94%`，主要缺 route execution success、delivery/operator acceptance、current live HIL 和 safe-to-control。本轮只补 no-motion route replay / material packet，不声明这些缺口已完成。
- 归档 Objective 3 / O3 临时激活 lane：04:02 已有 28-pose fixed-route consumer material；本轮继续推进 same-task replay/consumer integration。
- Objective 6 / O7：本轮不进入 O6 archive/readback 或 O7 UI 展示，除非后续单独开工。

方向判断：继续 O3/O1 strict no-motion evidence chain；暂停 O5 support-only；不调整当前 OKR 百分比；KR `不归档`。

## KR 拆解、更新或历史归档

本轮不新增已完成 KR，也不把任何 KR 移入历史区。原因：

- 04:02 material 已证明 fixed-route consumer 可消费 fresh 28-pose structured material，但仍不是 route execution。
- 本轮目标也仍是 software_proof / no-motion material packet，不满足 route execution、delivery、HIL、safe-to-control 或 production cloud 完成条件。
- 历史证据来源仍保留在 `OKR.md` Objective 1 Key Results 和 04:02 sprint closeout；本轮完成后应在后续 Product closeout 中再决定是否仅追加历史记录，不提前归档。

## 本轮核心抓手

把 04:02 的三个输出合并为 same-task route replay / material packet：

- `fixed_route_28_pose_consumer_summary.json`
- `fixed_route_28_pose_route.csv`
- `fixed_route_28_pose_replay.jsonl`

该 packet 必须证明：

- `route_csv` 与 `replay_jsonl` 都属于 `task_o3_28_pose_fixed_route_consumer_20260713_0402`。
- `route_intent_id` 保持 `route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`。
- 28 个 pose 的 order/source_index 连续且可被 replay consumer 顺序读取。
- 输出字段显式保留 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。

## 需求范围

必须做：

- 消费 04:02 summary、route_csv 和 replay_jsonl。
- 生成 same-task replay/material packet summary。
- 生成 replay packet JSONL 或等价 consumer integration artifact。
- 记录 row/event count、sha256 或等价 source fingerprint、first/last pose、frame set、task/route identity 和 no-motion boundary。
- 更新最小必要导航文档，说明 05:02 packet 是 04:02 material 的下一层，不是 route execution。
- 更新本 sprint `tech-done.md`。

不得做：

- 不运行 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不声明 route execution、fixed-route movement、delivery success、operator acceptance、HIL pass、safe-to-control 或 O5 production evidence。
- 不重复 helper/export/readiness/route-intent 包装。

## 优先级和验收口径

优先级：P0 for this automation run。理由是 O5 真实外部材料不可得，继续 O5 wrapper 会重复消费 blocker；04:02 已有可消费 28-pose material，本轮能产出更接近 route execution 的 same-task replay packet。

Product acceptance 必须同时满足：

- 有机器可读 packet summary。
- 有 `route_csv` 和 `replay_jsonl` consumption 证据，而不是只复制 04:02 summary。
- 有同一 `task_id`、同一 `route_intent_id`、28 pose count、row/event count readback。
- 有 explicit rejected claims。
- Safety fields 全部 false：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。

## 对应责任 Engineer

实现 owner：`robot-algorithm-engineer`。

建议单线闭环，不并行拆分。理由：文件范围集中在 Algorithm offline consumer、测试、导航文档和本 sprint artifacts，接口不需要跨团队实时协作。

## 风险、阻塞和需要补齐的证据链

- 当前证据链仍停在 no-motion software material，不证明真实路线执行。
- 04:02 source 是 28-pose，不是旧 21-pose target；本轮不得硬改或补造 21-pose。
- 如果 CSV/JSONL schema 与新 packet schema 不兼容，应扩展可变 pose count 和 material refs，而不是回退到旧 stdout-tail。
- 后续要提升主 OKR，需要受控 route execution evidence、delivery/operator acceptance、current live HIL 或真实 production cloud/readback。

## Sprint 文档更新要求

本 planning worker 创建：

- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/pre_start.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/prd.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/tech-plan.md`

后续 Algorithm worker 必须更新：

- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/tech-done.md`
- 必要 artifacts under `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/`

Product closeout 后再补：

- `side2side_check.md`
- `final.md`

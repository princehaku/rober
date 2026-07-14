# O5 External Evidence Or Field Execution Pivot PRD

## 背景

`OKR.md` 当前最低活跃 Objective 是 O5，约 `85%`。但最近 O5 sprint 已明确：没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser 时，`cloud_production_cutover_readiness_packet` 固定 `okr_credit_allowed=false`，继续做 readiness/support packet 不能提升主 OKR。

O1 当前约 `93%`，最近两轮已经消费 historical same-session wheel/PC command 材料。下一步必须 current live same-run HIL artifact；没有 current live 材料时继续包装历史材料也不能作为主要增量。

因此本 sprint 的产品目标是：把 hourly automation 的下一轮实现，从 O5/O1 blocker 包装切到新的现场执行材料链路。优先消费 O6/O7/O3 相关的路线、Nav2、送达、operator 或 production readback 材料，而不是新增 wrapper。

## 用户价值

普通用户价值不是“系统又多一个状态摘要”，而是未来能在手机或 PC 上看到：

- 本次任务是哪一个 `task_id`。
- 小车使用哪份地图和路线。
- Nav2 是否接受目标、是否终止、终止原因是什么。
- 是否有路线回放、关键帧、rosbag 或 replay JSONL。
- 是否有送达记录或 operator acceptance。
- 哪些证据仍缺，不能把软件 proof 当成真实送达。

## 产品北极星

北极星仍是低成本 ROS2 自主垃圾投递机器人：用户放入垃圾后，小车沿固定路线完成送达，并留下可复盘证据链。本轮 PRD 把下一步从“云控制面 readiness”调整为“现场执行证据 delta”，因为当前真正阻碍产品闭环的是缺新任务材料，而不是缺一个更好看的 readiness summary。

## OKR 映射和方向判断

- O5：继续作为最低 Objective 监控，但本轮没有真实 external production evidence，不做 O5 support-only 增量。
- O6：调整为本轮可推进承接方。若 Algorithm 产出新的 field execution pack，后续 O6 可归档和回读。
- O7：调整为后续消费方。若 O6/O7 后续展示新 pack，必须保持 observe-only、fail-closed，不自动声称 delivery success。
- O3：虽然在当前 OKR 中为软件侧归档 Objective，但 OKR 4.1 已把“现场 O3 验证 lane”临时激活。本轮可以把真实路线采集、固定路线回放、Nav2 result 或 replay material 当作现场材料来源。

方向判断：调整。O5 不降级，但本轮不再围绕 O5 support-only 做增量；改排能产生 `external_artifact_delta` 或 `field_execution_material_delta` 的路线。

## KR 拆解、更新或历史归档

本轮计划不归档 KR，不更新 `OKR.md`。

实现阶段若满足下列条件，Product closeout 才能考虑后续 OKR 调整：

- O5 增量条件：真实 external production evidence 到位，且 `okr_credit_allowed=true` 有证据支撑。
- O6/O7 增量条件：同一 `task_id` 消费新的现场执行材料，且不是仅把已有字段换名或重复展示。
- O3 临时验证条件：产出可追溯的 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result 或 operator record。

不满足时，收口必须写明 no KR archived / no OKR increase。

## 本轮核心抓手

定义并计划实现 `field_execution_pack`：

- 输入：新任务材料或明确的 source run artifact。
- 输出：安全摘要 JSON，包含 `task_id`、source run、material list、material freshness、field command evidence、route execution evidence、delivery/operator evidence、missing evidence、`okr_credit_allowed`、`support_only_reason`。
- fail-closed：缺新材料、task mismatch、危险 true、敏感 URL/token/path/raw payload 泄漏、把 comparator 当新材料时必须 blocked。

## 需要做什么

1. Algorithm owner 在实现前先 inventory 候选材料，确认是否有未被最近 sprint 消费的新 `task_id` 或 source run。
2. 若有新材料，在 `onboard/scripts/field_route_evidence_manifest.py` 增加 field execution pack 生成/消费入口。
3. 增加 targeted tests，覆盖 positive、新材料缺失、task mismatch、dangerous true、unsafe payload、historical comparator 不计分。
4. 同步 `docs/navigation/field_route_evidence_manifest.md`，写清该 pack 是现场执行材料合同，不是 production cloud 或 delivery success 的证明。
5. 更新本 sprint `tech-done.md`，记录实际改动、验证结果和剩余风险。

## 优先级和验收口径

优先级：P0。

验收口径：

- 必须优先寻找 O5 external production evidence；若没有，明确 O5 `okr_credit_allowed=false`。
- 必须消费新的现场或准现场材料，不能只新增 wrapper/display/status。
- Pack 输出中必须有 `task_id`、source run、present materials、missing materials、freshness 判断和 `next_required_evidence`。
- 不得把 historical comparator、readback-only、checklist-only 或 support packet 包装成主 OKR 增量。
- 如果无新材料，正确结果是 fail-closed 并保持 OKR flat。

## 对应责任 Engineer

主责：`robot-algorithm-engineer`。

协作边界：

- `robot-software-engineer` 本轮不主责，因为不应继续改 O5 relay readiness packet。
- `full-stack-software-engineer` 本轮不主责，因为展示新 surface 不能替代材料 delta。
- `rober-hardware-engineer` 本轮不主责，除非实现阶段触及 current live HIL/WAVE ROVER feedback。

## 风险、阻塞和需要补齐的证据链

- 缺真实 O5 external production evidence。
- 缺 current live same-run O1 HIL acceptance。
- 可能找不到新的现场材料；若如此必须 blocked，不得靠文档、wrapper 或 readback 提升。
- 后续 O6/O7 消费需要另开 implementation sprint 或在本 epic 后续阶段派发，不在本计划阶段完成。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

已完成 KR：无。

历史记录位置：本 sprint 计划阶段不更新历史区。

证据来源：

- `OKR.md` 4.1。
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`。
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/final.md`。
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/final.md`。

剩余风险：PRD 只定义方向和验收口径；没有实现前不改变 OKR。

## 需要创建或更新的 sprint 文档

计划阶段创建 `pre_start.md`、`prd.md`、`tech-plan.md`。

实现阶段必须追加 `tech-done.md`，验收阶段追加 `side2side_check.md` 和 `final.md`。

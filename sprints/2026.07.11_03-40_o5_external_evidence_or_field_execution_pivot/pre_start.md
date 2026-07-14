# O5 External Evidence Or Field Execution Pivot Pre-Start

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

用户价值：把下一轮 hourly automation 从 support-only readiness/readback 拉回真实任务材料链路。普通手机用户最终需要的是“发车后能沿固定路线送达并可复盘”，不是更多状态面板、handoff 或只读 wrapper。

产品北极星：`rober` 必须从“能看见软件证据”继续推进到“同一 `task_id` 下可验证地完成路线执行、送达记录、operator acceptance 或生产云回读”。本轮计划只启动能产生新材料的 sprint，不把风险边界本身包装成 OKR 交付。

## 开工依据

- 已读 `AGENTS.md`：Epic sprint 必须有 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`，且 `tech-plan.md` 必须包含 OKR 最低优先级核对。
- 已读 `OKR.md` 4.1：当前最低活跃 Objective 是 O5，约 `85%`；O1/O6/O7 均约 `93%`。
- 已读 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`：O5 readiness packet 固定 `okr_credit_allowed=false`，缺真实 external production evidence 时不能继续计主 OKR 增量。
- 已读 `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/final.md`：O6/O7 已消费 prior PC live Nav2 material，下一步必须接 live route execution、delivery record、operator confirmation 或 production cloud readback。
- 已读 `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/final.md` 和 `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/final.md`：O1 下一步必须 current live same-run HIL artifact，不应继续 historical same-session 包装。

## 上轮未完成项和重复 blocker 核对

O5 当前仍缺：

- 真实公网 HTTPS/TLS。
- 真实 4G/SIM outbound polling。
- production DB/queue。
- production worker cutover / drain。
- OSS/CDN live traffic。
- 真实 phone/browser acceptance。

这些材料当前环境没有提供。继续做 O5 readiness、support packet、probe-readback 或 cutover checklist 会再次消费同一 O5 blocker，且 `okr_credit_allowed=false`，不能提升主 OKR。

O1 最近两轮已围绕 historical same-session wheel/PC command 材料收口。下一步若没有 current live same-run `feedback_T1001.log`、motion command、external video、LiDAR delta、HIL acceptance record，就不能继续把 historical material 当作 O1 增量。

## 方向判断

方向：调整。

不是暂停 O5，而是把本轮 OKR 增量从 O5 support-only 改排到“可产生现场执行材料的最低可推进路线”。优先级如下：

1. 若实现阶段拿到真实 O5 external production evidence，则立即切回 O5，并用 `okr_credit_allowed=true` 的外部证据合同验收。
2. 当前没有 O5 external evidence 时，本 sprint 改排 O6/O7 + 现场 O3 验证 lane，要求消费新的 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record 或 operator confirmation 中至少一类材料。
3. 若实现阶段也找不到新现场材料，则 sprint 必须 fail closed，记录 `blocked_missing_new_field_execution_material`，不得用 wrapper/support surface 计分。

## 本轮核心抓手

本轮核心抓手是 `field_execution_pack` 计划：由 Algorithm owner 主责，在现有 field route evidence manifest 链路上定义并消费一份新的同任务现场执行材料包。该包必须回答：

- 本轮是否有新的 `task_id` 或新的 source run。
- 消费了哪些具体现场材料。
- 哪些材料是本轮新消费，哪些只是历史 comparator。
- 是否包含 live/field command、Nav2 result、delivery/operator 或 production readback。
- `okr_credit_allowed` 是否为 true；若不是，必须给出 `support_only_reason`。

## 优先级和验收口径

优先级：P0 epic planning，计划完成后进入 implementation dispatch。

计划阶段验收：

- 三份文档存在：`pre_start.md`、`prd.md`、`tech-plan.md`。
- `tech-plan.md` 包含 `OKR 最低优先级核对`、O5、`okr_credit_allowed`、`验收命令`、`文件范围`、`接口边界`。

实现阶段验收口径：

- 不能修改 O5 support-only packet 来制造增量。
- 必须产生或消费至少一类新现场材料：`task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record、operator confirmation 或 production readback。
- 若无新材料，必须 fail closed，明确不提升 OKR。
- 输出必须固定安全边界：不证明 delivery success、production cloud、HIL pass 或 safe-to-control，除非对应真实证据实际存在。

## 对应责任 Engineer

主责 Engineer：`robot-algorithm-engineer`。

理由：本轮核心不是云 cutover、PC UI 或硬件参数，而是把路线/现场执行材料收敛成可被 O6/O7 后续消费的同任务算法证据包。O6/O7/Full-stack 可在后续 sprint 消费该包；本轮先避免多 owner 并发写共享接口。

## 风险、阻塞和需要补齐的证据链

- O5 external production evidence 仍缺；本轮不应声称 O5 前进。
- O3 已归档为软件侧完成，但现场验证 lane 被 OKR 4.1 临时激活；如果没有新路线材料，本轮只能形成 fail-closed 计划，不能算现场成功。
- O6/O7 已有大量 readback/display 能力，继续展示同层材料不再提升主 OKR；必须消费新 material delta。
- 若实现阶段触及 WAVE ROVER、UART、速度映射或真实底盘反馈，必须按 `AGENTS.md` 再读 `docs/vendor/VENDOR_INDEX.md`。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

已完成 KR：本轮计划阶段不归档 KR。

历史记录位置：不移动 `OKR.md` 当前区或历史区。

证据来源：

- `OKR.md` 4.1 当前快照。
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`。
- `sprints/2026.07.11_00-34_o6_o7_pc_live_nav2_execution_material/final.md`。
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/final.md`。
- `sprints/2026.07.11_02-34_o1_same_session_pc_command_material/final.md`。

剩余风险：计划本身不产生现场材料；OKR 只有在下一步 owner 实现并通过材料 delta 验收后才可考虑调整。

## 需要创建或更新的 sprint 文档

本轮计划阶段创建：

- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/pre_start.md`
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/prd.md`
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/tech-plan.md`

实现和收口阶段后续需要创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

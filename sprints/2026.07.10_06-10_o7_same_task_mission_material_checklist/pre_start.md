# O7 Same-Task Mission Material Checklist Pre-Start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-10 06:10 CST。

本轮只创建规划文档，不进入实现；后续实现应由 `full-stack-software-engineer` 单线闭环完成。

## 用户价值和产品北极星

用户价值：让 PC 端运营人员在 O7 consumer detail 主路径里，直接看到同一 `task_id` mission material 还缺什么、下一步该补哪份证据，而不是在 O5 terminal result、O6 gate、route execution、delivery record 和 operator confirmation 之间人工对照。

产品北极星：普通手机用户最终能可验证地完成垃圾送达；PC 端当前服务于运营调试和证据复盘。本轮不宣称真实送达，只把已有 O6 `same_task_mission_evidence_gate` 缺口转换成 operator 可执行清单。

## OKR 映射和方向判断

- O7：继续，当前约 83%。本轮直接针对 PC 端运营调试平台，把 same-task mission gate 从只读摘要推进为 operator 可执行 material checklist。
- O5：暂停 local smoke 增量，当前约 84%。最近 `2026.07.10_05-10_o5_sqlite_shadow_same_task_gate` 已明确：继续 O5 只能接真实 production cloud、production DB/queue external probe 或 live endpoint evidence；没有这些材料时不再用 local shadow/smoke 提升百分比。
- O6：继续作为事实来源，但本轮不继续 wrapper/decoder，当前约 84%。O6 `same_task_mission_evidence_gate` 已有 readback 合同，O7 应消费它而不是要求 O6 再包装一层。
- O1：当前约 85%，仍依赖真实轮速非零反馈、HIL 和硬件材料，不作为本轮软件可推进最低项。

方向判断：调整执行抓手，从 O5/O6 local/mock 证明转向 O7 same-task mission material checklist。该调整符合最近收口建议：下一轮应消费真实或准现场 same-task mission materials，不继续 wrapper、decoder、handoff 或 review surface。

## 最近 sprint 证据核对

- `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/final.md`：O7 已能展示 gate 状态、terminal/cloud source、linked flags、blocked reasons 和 next required evidence，但仍不证明真实 production cloud、真实 live Nav2、真实 delivery record 或真实 operator confirmation。
- `sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/final.md`：O5 SQLite shadow restart/readback 已完成；下一轮如果没有真实外部材料，应转向 O7 same-task mission material checklist。

同一 blocker 核对：最近两轮不是 blocked 收口，但 05-10 已明确 local smoke 不能继续作为 O5 增量。本轮切换到 O7，不重复消费同一 local smoke / wrapper blocker。

## KR 拆解、更新和历史归档

本轮不修改 `OKR.md`，不归档 KR。规划结论如下：

- O7/KR3 历史路线回放：checklist 应指出 route execution material、route bag / pose progress / live Nav2 material 是否足以支撑同一任务复盘。
- O7/KR4 标注/数据训练：checklist 应指出 delivery record、operator confirmation 和 key evidence 是否足以进入后续标注或训练材料准备。
- O7/KR6 手控/自动寻路下发：checklist 必须保持观察模式，展示缺口，不启用手控、寻路或 primary actions。

已完成 KR 历史记录位置：本轮无新增完成或归档；既有归档 Objective 仍以 `OKR.md` 已归档 Objective 表和 `docs/process/okr_progress_log.md` 为准。

## 本轮核心抓手

把 O6 `same_task_mission_evidence_gate` 的 linked flags、blocked_reasons、next_required_evidence、terminal/cloud source、route execution / delivery / operator confirmation 缺口，派生为 O7 consumer detail 的 `same_task_mission_material_checklist` 或等价数据结构，并在 UI 中展示 operator 可执行清单。

核心原则：

- 只读消费 O6 consumer detail 主路径，不读取真实公网云，不发送控制命令。
- 所有状态 fail-closed；ready 也只能是 ready-not-success-proof。
- 必须固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- UI 文案必须帮助 operator 补证据，而不是制造“已完成送达”的错觉。

## 需要做什么

后续实现阶段由 `full-stack-software-engineer` 完成：

1. 在 `pc-tools/workstation` O7 consumer detail adapter 中派生 checklist。
2. 在 shared contract 中补充 checklist shape 或等价类型。
3. 在 O7 UI 中展示 checklist item、当前 material 状态、blocked reasons 和 next required evidence。
4. 增加 fixture / adapter / UI 测试，覆盖 ready-not-success、缺材料、危险 true、task mismatch 和 schema mismatch。
5. 同步更新 `docs/interfaces/o7_realtime_operator_console.md`。

## 优先级和验收口径

优先级：P0，因为 O7 是当前最低可推进 Objective，且该 checklist 直接承接最近 O5/O6 同 task gate 证据链。

规划验收口径：

- 本目录存在 `pre_start.md`、`prd.md`、`tech-plan.md`。
- `tech-plan.md` 含 `OKR 最低优先级核对`。
- 规划明确 `same_task_mission_material_checklist`、O7 workstation 验收命令和 `git diff --check`。

后续实现验收口径：

- `cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过。
- `git diff --check` 通过。
- O7 consumer detail 主路径能展示 checklist。
- 所有控制、成功、真实云连接字段保持 false。

## 对应责任 Engineer

- 规划 owner：`product-okr-owner`。
- 后续实现 owner：`full-stack-software-engineer`。
- O6 事实来源 owner：`robot-software-engineer` 仅在 O6 gate contract 被发现不清时只读补事实；本轮不计划改 O6。
- Algorithm / Hardware owner：本轮不参与，除非后续发现缺少 route execution material 的事实定义。

## 风险、阻塞和需要补齐的证据链

风险：

- O7 可能把 gate ready 误读成 delivery success；必须用 false fields 和 UI 文案压住。
- 如果 checklist 只展示已有 blocked reasons 而没有 operator 下一步，仍会退化成 support surface。
- 如果实现新增 wrapper 而不接 O7 consumer detail 主路径，不应计入 O7 主线进展。

需要补齐的证据链：

- 真实或准现场同一 `task_id` terminal/cloud result。
- live Nav2 route execution material。
- delivery record。
- operator confirmation。
- production cloud / DB / queue / OSS / CDN 真实 readback。

## 需要创建或更新的 sprint 文档

本规划任务只创建：

- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/pre_start.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/prd.md`
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/tech-plan.md`

后续实现完成后必须补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`


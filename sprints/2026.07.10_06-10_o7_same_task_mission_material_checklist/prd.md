# O7 Same-Task Mission Material Checklist PRD

## 背景

O6 已提供 `same_task_mission_evidence_gate`，O7 也能展示 gate 状态、terminal/cloud source、linked flags、blocked reasons 和 next required evidence。但当前运营人员仍需要人工判断这些字段分别对应哪份 mission material：terminal result、route execution、delivery record、operator confirmation、production cloud readback。

本 PRD 要求 O7 在 consumer detail 主路径中，把这些字段派生成 `same_task_mission_material_checklist` 或等价清单数据结构，并在 UI 中展示 operator 可执行清单。

## 用户价值和产品北极星

目标用户：PC 端运营调试人员和数据复盘人员。

用户价值：

- 一眼知道同一 `task_id` 的 mission material 哪些已存在、哪些 blocked。
- 看到下一步必须补哪份证据，而不是只看到 `blocked_not_proven`。
- 在不连接真实公网云、不发送机器人控制命令的前提下，为现场复跑和后续验收准备材料。

产品北极星：可验证地可靠交付垃圾。本轮产品价值是提升证据链可执行性，不是证明真实 delivery success。

## OKR 映射和方向判断

- O7 / KR3 历史路线回放：继续。checklist 要把 route execution / route bag / pose progress / live route material 的缺口变成可执行项。
- O7 / KR4 标注与训练数据：继续。checklist 要显示 delivery record、operator confirmation、关键 evidence 是否足以支持标注与训练材料准备。
- O7 / KR6 手控和自动寻路：继续但保持 disabled。checklist 可以提示 safe command / navigation material 缺口，但不得启用控制。
- O5 / O6：调整为上游事实来源。O5/O6 本轮不再靠 local smoke、wrapper 或 decoder 作为主要增量。

方向判断：继续 O7，调整抓手到 same-task mission material checklist。O5/O6 只作为 O7 的输入来源，不在本轮规划中新增后端合同。

## KR 拆解、更新或历史归档

本轮不归档 KR，不更新 `OKR.md`。后续实现若通过 O7 test/build/lint 且 UI 主路径展示 checklist，可在收口时考虑 O7 小幅推进；但仍不得标记 O7 KR 完成，因为真实 production cloud、真实媒体、真实 live route execution、delivery record、operator confirmation 和 delivery success 均未证明。

历史记录位置：如后续实现完成，应在本 sprint `final.md` 和 `docs/process/okr_progress_log.md` 收口记录中追加证据；本规划任务不修改这些文件。

## 范围

### In Scope

- O7 consumer detail 主路径派生 `same_task_mission_material_checklist` 或等价字段。
- 从 O6 `same_task_mission_evidence_gate` 消费：
  - linked flags
  - blocked_reasons
  - next_required_evidence
  - terminal/cloud source
  - source schema / source ref safe summary
  - route execution、delivery、operator confirmation 相关缺口
- O7 UI 展示 operator 可执行清单：
  - material item 名称
  - 当前状态：present / missing / blocked / not_proven / ready_not_success_proof
  - blocker
  - next required evidence
  - source summary
  - owner hint
- 同步更新 `docs/interfaces/o7_realtime_operator_console.md`。
- 增加测试覆盖 fail-closed 和 UI 展示。

### Out of Scope

- 不修改 O6 archive/readback contract。
- 不修改 Algorithm manifest。
- 不连接公网云、生产云、真实 OSS/CDN、真实 DB/queue。
- 不发送控制命令，不下发 Nav2 goal，不触发 TTS/ASR，不读串口，不读取硬件。
- 不把 checklist ready 解释为真实送达成功。

## 功能需求

### FR1 - Checklist 数据结构

O7 consumer detail 应新增 `same_task_mission_material_checklist` 或等价结构。建议字段：

- `schema=trashbot.pc_tools_workstation.o7_same_task_mission_material_checklist.v1`
- `task_id`
- `source_gate_schema`
- `source_gate_status`
- `overall_status`
- `items[]`
- `blocked_reasons[]`
- `next_required_evidence[]`
- `proof_status=not_proven`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

### FR2 - Checklist Items

至少包含以下 item：

- `same_task_identity`：同一 `task_id` 对齐。
- `terminal_cloud_result`：O5 terminal/cloud source 和 source schema。
- `route_execution_material`：live route execution / route execution readiness。
- `delivery_record`：delivery result / dropoff terminal material。
- `operator_confirmation`：operator confirmation / manual confirmation material。
- `route_pose_progress`：route bag / pose progress / route motion material。
- `production_cloud_readback`：production cloud / DB / queue / endpoint readback 缺口。
- `safety_invariants`：四个固定 false 字段和 observe-only 边界。

### FR3 - Fail-Closed 规则

以下情况必须 fail-closed，并保留 blocker：

- O6 gate 缺失。
- schema mismatch。
- task mismatch。
- unsafe ref、绝对路径、raw/base64、token、credential URL。
- 任一危险字段为 true。
- next_required_evidence 或 blocked_reasons 不是安全字符串数组。
- gate ready 但缺少 terminal/cloud source 或 route execution material summary。

### FR4 - UI 展示

O7 UI 必须在 consumer detail 主路径中展示 checklist。展示应面向 operator 下一步行动：

- 每个 item 清楚显示当前状态和下一步证据。
- blocked reasons 与 next required evidence 不应只堆 JSON；需要按 item 分组。
- UI 不提供 send、run、control、navigate、submit、TTS、stop、cancel 或 production cloud connect 操作。
- 如有按钮，只能是本地展开/折叠或复制非敏感 evidence key，不得触发后端写入或机器人动作。

### FR5 - 文档同步

更新 `docs/interfaces/o7_realtime_operator_console.md`：

- 增加 checklist contract 说明。
- 说明 source 是 O6 consumer detail 主路径的 `same_task_mission_evidence_gate`。
- 说明 fail-closed 与四个固定 false 字段。
- 说明不证明 production cloud、live route execution、delivery success 或 operator confirmation 已真实完成。

## 非功能需求

- 保持 additive，不破坏现有 O7 consumer detail、route replay、labeling、artifact readiness、same_task_mission_evidence_gate 展示。
- TypeScript 类型和 UI 测试应覆盖关键字段。
- 技术注释如需新增，必须使用中文，并解释为什么 fail-closed。
- 不输出敏感路径、token、credential-bearing URL、raw payload 或 base64。

## 优先级和验收口径

P0：

- O7 consumer detail 输出 checklist。
- UI 展示 checklist。
- 固定 false 字段存在且为 false。
- dangerous true / task mismatch / schema mismatch fail-closed。
- `cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过。
- `git diff --check` 通过。

P1：

- checklist item 支持 owner hint 和 next evidence 分组。
- 文档给出最小示例和边界说明。

## 对应责任 Engineer

主责：`full-stack-software-engineer`。

Product owner 后续只做验收和 OKR 收口，不改产品代码。

## 风险、阻塞和需要补齐的证据链

主要风险：

- checklist 被误读为任务成功；必须固定 not success 和 observe-only。
- O7 只做 UI 包装，没有形成 operator 下一步；验收时必须检查 item 是否包含 next required evidence。
- O6 gate 字段命名可能存在 source alias；实现需优先兼容既有主路径，不能要求 O6 再改。

需要补齐的真实证据链：

- production cloud endpoint / DB / queue readback。
- live Nav2 route execution。
- delivery record。
- operator confirmation。
- 真实关键帧媒体和长期路线验收。

## 需要创建或更新的 sprint 文档

本规划任务：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现任务：

- `tech-done.md`
- `side2side_check.md`
- `final.md`


# O6/O7 Same-Task Route Execution Material Packet PRD

## 用户价值和产品北极星

产品北极星：普通用户把垃圾交给机器人后，机器人能沿固定路线完成可验证、可复盘、可恢复的送达任务。

本轮用户价值不是新增一层状态面板，而是把“这次任务是否真的消费了 route execution 相关材料”变成 Algorithm -> O6 -> O7 都能读到的同一 `task_id` 证据包。运营人员需要看到 route materials、route execution result、pose progress、replay timeline 与缺失证据之间的关系，而不是只看到 checklist 已存在。

## 问题背景

- O5 已被 production evidence gate 卡住，没有真实 cloud/DB/queue/live endpoint 材料时不能继续计 OKR。
- O1 下一步必须接真实上车 run 材料，当前环境没有 `feedback_T1001.log`、motion command、operator report 和 HIL acceptance record。
- O6/O7 已有 `same_task_field_material_packet`，但它只证明同 task 准现场材料被消费，不证明 route execution result 或 delivery closure。
- 下一步必须从 field material packet 走向 route execution material packet，避免重复做 readback/checklist wrapper。

## OKR 对齐和方向判断

- O6：继续。把任务材料从 archive/readback 的 field packet 深化到 route execution packet，增强数据存档、查询和 consumer read API 的任务履约证据能力。
- O7：继续。让 PC 端围绕同一 `task_id` 展示 route execution material status、缺失项和下一条现场命令，提升运营调试和回放判断能力。
- O5：暂停本轮 OKR 计分推进。没有 production cloud / production DB-queue external probe / live endpoint evidence。
- O1：暂停本轮 OKR 计分推进。没有同一真实 run 的硬件/HIL 材料。
- 本轮不归档任何 KR；只规划下一阶段可实现的 O6/O7 证据链。

## 范围

### In Scope

- 定义 `same_task_route_execution_material_packet` 的产品验收口径。
- 要求 producer 消费同一 `task_id` 下已有/准现场 materials，而不是只复制 existing checklist。
- 要求 O6 作为合同源，提供 archive/readback/include/consumer detail 的安全摘要。
- 要求 O7 作为只读 consumer，展示 O6 顶层状态、material consumption、blocked reasons 和 next required evidence。
- 固定 false safety/delivery/control flags，防止软件 proof 被误读为真实送达或安全准入。

### Out of Scope

- 不实现真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic。
- 不宣称真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 不启用真实控制动作，不开放 primary action。
- 不修改本阶段允许范围外的代码、测试、OKR 或 closeout 文件。

## 接口验收口径

### Producer 必须证明

- 产出 schema：`trashbot.same_task_route_execution_material_packet.v1`。
- 同一 `task_id` 有效，并能关联已有 `same_task_field_material_packet`。
- 至少消费一类 route execution 相关材料，例如 route execution result JSON/JSONL、Nav2 goal/result、pose progress/replay summary、route bag semantic/pose progress replay。
- 只输出安全摘要：basename、count、size、sha256 prefix、status、blocked reason、sample ref summary。
- 不输出 raw ROS payload、base64、绝对路径、credential-like URL、token、traceback 或敏感 body。

### O6 必须证明

- 产出 schema：`trashbot.o6.same_task_route_execution_material_packet.v1`。
- 支持 field evidence ingest、artifact bundle、archive detail、consumer detail 顶层 alias 和 `include=same_task_route_execution_material_packet`。
- schema mismatch、task mismatch、unsafe text、dangerous true、raw/base64、absolute path、credential URL 均 fail-closed 到当前 section，不污染其它 evidence section。
- O6 顶层 status 是 O7 判断 readiness 的唯一来源。

### O7 必须证明

- 默认或显式 include 能拿到 O6 的 `same_task_route_execution_material_packet`。
- UI 展示 route execution material status、present/missing materials、blocked reasons、next required evidence 和 fixed false flags。
- Checklist 可引用该 packet，但验收不能只有 checklist item；必须显示 packet 自身的 O6 顶层状态和材料摘要。
- `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 始终可见或可追踪。

## 固定 false flags

本轮及实现阶段必须固定：

- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `hil_pass=false` 如涉及硬件安全语义
- `connects_cloud_production=false` 如涉及 cloud proof

任何 worker 不得把 `route_execution_material_consumed=true` 等同于 delivery success、safe-to-control、production proof 或 HIL pass。

## 优先级

P0：

- Producer -> O6 -> O7 三层围绕同一 `task_id` 消费 `same_task_route_execution_material_packet`。
- 安全摘要和 fail-closed 行为。
- 固定 false flags。
- 验证命令和 sprint `tech-done.md` 留证。

P1：

- O7 UI 展示顺序和 checklist 邻接位置。
- 与 `same_task_mission_evidence_gate`、`same_task_field_material_packet` 的互链说明。

P2：

- 更丰富的 route execution timeline 展示。不得阻塞 P0 验收。

## 需要补齐的证据链

- 同一真实或准现场 run 的 route execution result。
- live Nav2 route execution 或可复验 replay JSONL。
- delivery record 或 operator confirmation。
- production cloud / DB-queue / endpoint evidence。
- 真实 robot motion 与 hardware safety/HIL 材料。

这些材料未到位前，本轮只能定位为 `software_proof_same_task_route_execution_material_packet_only`。

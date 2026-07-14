# Pre Start - O3 Controlled Route Execution Gate Record

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `robot-algorithm-engineer`
- Start time: 2026-07-13 07:07 CST
- Target Objective: O3/O1 controlled route execution gate before any live route execution
- Source packet: `packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- Source task: `task_o3_28_pose_fixed_route_consumer_20260713_0402`
- Source route intent: `route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- Planned artifact: `controlled_route_execution_gate_record`
- Proof boundary: `software_proof_o3_o1_fail_closed_controlled_route_execution_gate_record_only`
- Safety boundary: fail closed, no /cmd_vel, no /api/base/manual, no NavigateToPose, no WAVE ROVER UART, `route_execution_success=false`, `delivery_success=false`, `hil_pass=false`, `safe_to_control=false`, `robot_control_executed=false`

## 必读完成

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/final.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/final.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`

## 上轮事实

05:02 sprint 已接受 O3/O1 strict no-motion same-task replay packet。关键事实：

- `schema=trashbot.o3.same_task_route_replay_packet.v1`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`
- source fingerprints 已存在：`summary_sha256`、`route_csv_sha256`、`replay_jsonl_sha256`
- 固定 false 字段已存在：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`

06:05 sprint 已接受 O6/O7 local/mock readback + PC consumer detail increment，但明确不接受为 route execution、delivery、HIL、safe-to-control、NavigateToPose/controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、O5 production/external evidence 或 production cloud ready。

## 为什么不继续 O5

当前最低数字 OKR 是 O5，约 `85%`。O5 主要缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence。最近多轮已明确 O5 readiness、checklist、handoff、support-only wrapper 无法产生新 external evidence，继续做会重复消费同一 blocker。

本轮不做 O5 的具体理由：

- 没有新的真实公网/生产 external evidence 输入可消费。
- 06:05 已完成 O6/O7 readback-only increment，不能继续做 O6/O7 readback-only wrapper。
- 05:02 packet 已具备同一 `packet_id` / `task_id` / `route_intent_id` 和 28/28/28 count，可进入 route execution 前的安全门记录。
- 下一条对北极星有用的证据不是 helper/export/readiness/route-intent，也不是 packet packaging，而是把同一 packet 转成受控 route execution 前的 fail-closed gate record。

## 用户价值和产品北极星

产品北极星仍是普通用户把垃圾交给小车后，小车沿固定路线完成送达并能被复盘。当前离用户价值最近的缺口不是更多包装，而是明确“什么时候允许进入真实路线执行”。

本轮用户价值是给 Algorithm owner 一个清晰、机器可读、可测试的安全合同：同一个 05:02 packet 在进入受控 route execution 前，必须先通过 identity/count/source hash 校验，并输出 `controlled_route_execution_gate_record`。该记录要告诉后续执行者当前为什么仍 `safe_to_control=false`，以及下一条 live command gate 需要什么真实准入材料。

本轮不让车动，不发 route goal，不向底盘下发控制，不声明 route execution 或 delivery 成功。

## 本轮核心抓手

核心抓手是 fail-closed route execution gate，而不是重复 packet/readback 包装：

- 消费 `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`。
- 校验 `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402` 和 `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`。
- 校验 `route_csv_row_count=28`、`replay_jsonl_event_count=28`、`path_structured_pose_count=28`。
- 校验 source fingerprint 与 source refs 存在且匹配。
- 生成 machine-readable `controlled_route_execution_gate_record`。
- 列出真实执行缺口和 next live command gate。
- 固定 fail-closed 安全字段：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`。

## Owner 和协作边界

- 主责 owner：`robot-algorithm-engineer`
- 交付模式：单 owner 闭环
- Product 本轮只产出 epic sprint 计划，不修改产品代码、测试代码、`OKR.md` 或其他 docs。
- Algorithm 后续实现只允许读取既有 05:02 packet artifacts 和生成 gate record / tests / sprint `tech-done.md`，不得调用控制链路。
- Robot Software、Hardware、Full-stack 本轮不介入实现。Hardware 只有在后续真实硬件准入、WAVE ROVER、UART、LiDAR 或 HIL 事实需要确认时才进入，并必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 初始验收口径

后续 Algorithm implementation 必须满足：

- 输出机器可读 `controlled_route_execution_gate_record`，建议 JSON schema 名为 `trashbot.o3.controlled_route_execution_gate_record.v1`。
- record 明确 source packet identity、counts、hashes、source refs 和 validation status。
- record 明确 `next_live_command_gate`，列出进入真实 route execution 前需要的准入证据。
- record 明确 rejected claims：route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、current live HIL、safe-to-control、O5 production/external evidence。
- safety fields 必须固定 false：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`。
- 验证必须覆盖 identity/count/source hash 和 no-motion guard。

## 风险和阻塞

- 最大风险是把 gate record 误写成 route execution readiness complete；本轮只能证明 dry-run execution readiness record / pre-control gate，不证明实际执行。
- 当前没有明确真实硬件准入，因此必须 fail closed。
- 如果 source packet 缺字段或 hash 不匹配，后续 implementation 必须输出 blocked record，不能补造 route execution evidence。
- 若后续实现只产出 checklist 文案或 wrapper，而没有机器可读 gate record 和测试断言，不可接受。
- 本轮大概率不调整 OKR 百分比；价值在于避免继续重复消费旧 wrapper，并把下一步准确收敛到真实执行 gate。

## 需要创建或更新的 sprint 文档

本轮规划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation/acceptance 阶段还必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

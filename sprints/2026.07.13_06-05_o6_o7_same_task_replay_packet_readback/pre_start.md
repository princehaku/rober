# Pre Start - O6/O7 Same-Task Replay Packet Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `full-stack-software-engineer`
- Start time: 2026-07-13 06:05 CST
- Target Objectives: O6 cloud archive/readback, O7 PC consumer detail
- Source packet: `packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- Source task: `task_o3_28_pose_fixed_route_consumer_20260713_0402`
- Source route intent: `route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- Proof boundary: `software_proof_o6_o7_same_task_replay_packet_readback_only`
- Safety boundary: no route execution, no delivery success, no HIL, no safe-to-control, no `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART

## 必读完成

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/final.md`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/pc_tools_workstation.md`

## 上轮事实

05:02 sprint 已接受 O3/O1 strict no-motion same-task replay packet。已证明事实：

- `schema=trashbot.o3.same_task_route_replay_packet.v1`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

05:02 明确拒绝把该 packet 计为 O6 archive/readback 或 O7 UI/consumer 完成。因此本轮不是重复 packet packaging，而是把同一 packet 安全消费进 O6 local/mock archive/readback 与 O7 PC consumer detail。

## 为什么不继续 O5

当前最低数字 OKR 是 O5，约 `85%`。但 O5 最近已经多轮确认缺真实 production/external evidence：真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 验收仍未到位。继续 O5 readiness、handoff、support-only wrapper 只会重复消费同一 blocker。

本轮选择 O6/O7 的理由：

- O6/O7 约 `93%`，仍有可推进的实际消费缺口。
- 05:02 packet 是新 same-task material，尚未进入 O6 archive/readback 或 O7 consumer detail。
- O6/O7 已有 local/mock archive 与 O7 consumer read adapter，适合在不触发控制的条件下做安全只读 readback。
- 本轮输出能直接为后续现场 route execution / delivery record / operator acceptance 提供同一 `task_id` 的可查证消费链。

## 用户价值和产品北极星

北极星仍是固定路线送垃圾任务的可验证闭环。本轮用户价值是让 PC 运营调试台和 O6 本地/mock 后端能围绕同一 `task_id` 读到 05:02 的 28-pose replay packet 摘要，形成可复盘、可排障、可继续接真实执行材料的证据链。

本轮不面向普通用户发车，不改变安全准入，不声明机器人已经能执行路线或完成投放。

## 本轮核心抓手

把 05:02 source packet 转成 O6 可写入、可回读、可被 O7 detail 默认消费的安全摘要：

- O6 archive/readback 能按 `task_id` 读取 same-task replay packet 的 packet id、route intent、counts、hash prefixes、basename refs 与 fixed false safety fields。
- O7 PC consumer detail 能在默认 include 或专项 section 中展示该 packet，保留 blocked reasons 与 next required evidence。
- 所有输出保持 read-only / local-mock / software-proof 边界，不误导为 route execution 或 delivery success。

## Owner 和协作边界

- 主责 owner：`full-stack-software-engineer`
- 主要范围：O6 local/mock API contract、O7 PC consumer adapter/UI detail、相关测试与文档。
- Robot Software 仅在 `remote_cloud_relay.py` 的既有 O6 store/consumer contract 需要事实确认时做只读咨询；本轮不做 ROS2 runtime、底盘、Nav2 或硬件改动。
- Hardware 不介入；本轮不涉及 WAVE ROVER、UART、引脚、电压、波特率或真实设备。
- Algorithm 不重复生成 05:02 packet；后续只消费既有 packet artifact。

## 初始验收口径

本轮后续 implementation 必须满足：

- O6 local/mock archive 接受或派生 05:02 packet 安全摘要，并能通过 `GET /api/o6/consumer/tasks/<task_id>` 回读。
- O7 consumer detail 能按同一 `task_id` 显示 packet readback，不读取本地绝对路径，不回显 raw/base64/token/credential URL。
- `packet_id`、`task_id`、`route_intent_id`、`route_csv_row_count=28`、`replay_jsonl_event_count=28`、`path_structured_pose_count=28` 保持一致。
- 固定 false 字段保持 false：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`primary_actions_enabled=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。
- 结果只允许声明 O6/O7 local/mock readback / PC consumer detail ready，不允许声明 production cloud、真实 route execution、真实 delivery record、真实 operator acceptance、真实 HIL 或 safe-to-control。

## 风险和阻塞

- 05:02 packet schema 是 O3/O1 packet，不是既有 O6 `same_task_route_execution_material_packet` schema；后续 owner 需要决定是新增 dedicated replay-packet section，还是安全映射到现有 same-task field/route material section，避免混淆 route execution。
- O7 consumer adapter 默认 include 已较大，新增 section 必须保持 fail-closed，不能把缺 section 压成成功。
- 本轮若只改展示而没有 O6 archive/readback 测试，不可接受。
- 本轮若出现危险 true 字段，必须 fail-closed，不得过滤后继续宣称 ready。

## 需要创建或更新的 sprint 文档

本轮规划阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation/acceptance 阶段还必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

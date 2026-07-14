# Side2Side Check - O6/O7 Same-Task Replay Packet Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_06-05_o6_o7_same_task_replay_packet_readback/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Product check time: 2026-07-13 06:59 CST
- Product status: accepted with conservative boundary
- Proof boundary: `software_proof_o6_o7_same_task_replay_packet_readback_only`

## 用户价值和产品北极星

北极星仍是固定路线送垃圾任务的可验证闭环。本轮价值是让 O6 local/mock archive/readback 与 O7 PC consumer detail 能围绕同一 `task_id` 安全读到 05:02 的 28-pose same-task replay packet，形成后续受控 route execution / delivery / HIL 材料可继续接入的证据链。

本轮不面向普通用户发车，不改变安全准入，不声明机器人已经执行路线、完成投放或可控制。

## PRD / Tech Plan 对照

| 验收项 | 计划要求 | 验收结果 |
| --- | --- | --- |
| O6 dedicated readback | 新增或明确区分 `same_task_replay_packet_readback`，避免混淆 route execution material | 通过。`tech-done.md` 记录 O6 schema `trashbot.o6.same_task_replay_packet_readback.v1` 与 `include=same_task_replay_packet_readback` |
| O7 consumer detail | 默认或专项 include 展示同一 packet readback | 通过。`tech-done.md` 记录 O7 schema `trashbot.pc_tools_workstation.o7_same_task_replay_packet_readback.v1`，并默认纳入 detail include |
| Exact identity | 保持 packet/task/route intent 与三类 28 count 不漂移 | 通过。Product 接受 `packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_o3_28_pose_fixed_route_consumer_20260713_0402`、`route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`、`route_csv_row_count=28`、`replay_jsonl_event_count=28`、`path_structured_pose_count=28` |
| Safety false fields | 控制、执行、交付、HIL、安全和生产云字段固定 false | 通过。`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`primary_actions_enabled=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`connects_cloud_production=false` |
| Docs sync | O6/O7 docs 同步 readback-only 边界 | 通过。`docs/interfaces/o6_cloud_archive_api.md` 与 `docs/product/pc_tools_workstation.md` 已说明 ready 只表示 readback 可用，不证明 route execution、delivery、HIL、safe-to-control、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或 production cloud |
| 验证证据 | O6/O7 测试、build、lint、scoped diff check | 通过。Full-stack 记录 O6 `Ran 185 tests in 81.295s OK`，O7 `Tests 491 passed (491)`，build/lint 通过，scoped `git diff --check` 无输出 |

## Product 验收结论

Product 接受本轮为 O6/O7 local/mock readback + PC consumer detail 增量。接受事实：

- O6 新增 dedicated `same_task_replay_packet_readback`，schema 为 `trashbot.o6.same_task_replay_packet_readback.v1`。
- O7 新增 `trashbot.pc_tools_workstation.o7_same_task_replay_packet_readback.v1`，并默认消费/展示。
- 同一 packet identity 和 28/28/28 counts 保持不变。
- O6/O7 只保存和展示白名单摘要、basename refs、sha256 prefix、blocked reasons、next required evidence 与 fixed false fields。

Product 不接受以下声明：

- route execution success
- delivery success
- HIL pass
- safe-to-control
- fixed-route movement
- NavigateToPose / controller / BT execution
- `/cmd_vel`
- `/api/base/manual`
- WAVE ROVER UART
- O5 production/external evidence
- production cloud / DB / queue / OSS / TLS / 4G ready

## OKR 映射和方向判断

- O6：继续约 `93%`。本轮是新的 same-task replay packet readback consumption，但仍是 local/mock software proof，不足以归档 KR。
- O7：继续约 `93%`。PC consumer detail 新增同一 packet 的只读展示，但未产生真实执行、送达、HIL 或生产云证据。
- O5：继续约 `85%`。本轮没有真实 external production evidence，继续不消费 O5 support-only wrapper。
- O1：继续约 `94%`。本轮不新增 current live HIL、safe-to-control、route execution 或 delivery acceptance。
- 方向判断：继续 O6/O7 read-only evidence consumption；不调整主百分比；KR `不归档`。

## 剩余风险和下一步

剩余风险：

- 当前 readback 只能证明 O6/O7 能消费和展示同一 `task_id` 的 replay packet identity/count，不证明车跑过。
- 05:02 source packet 仍是 strict no-motion offline packet，不是 route execution record。
- 没有生产云、真实隧道、production DB/queue、OSS/CDN live traffic、真实 delivery record 或 operator acceptance。

下一步 owner/action：

- `robot-algorithm-engineer`：在安全准入明确后，用同一 `packet_id` / `route_intent_id` 收集受控 route execution record。
- `full-stack-software-engineer`：后续只在拿到新的 route execution / delivery / HIL / production evidence 时继续扩展 O6/O7 consumption；不要重复 readback-only wrapper。

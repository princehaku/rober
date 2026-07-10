# O5/O6/O7 Same Task Mission Gate PRD

## 用户价值

运营人员需要知道一条任务是否已经具备“同一 `task_id` 下的云端终态结果 + 路线执行材料 + 操作员确认”最小验收材料。当前 O5 terminal result 已能进入 O6/O7 delivery evidence，但仍需要人工在多个面板里对 task、command、route 和 delivery readiness。该 PRD 要把这件事变成一个 fail-closed gate。

## 需求

新增 `same_task_mission_evidence_gate`：

- 输入来源只来自现有安全摘要：`nav2_goal_execution_evidence`、`delivery_result_evidence`、`route_execution_result_delivery_readiness`、`route_delivery_closure_packet`、`route_bag_pose_progress_replay` 与 `field_motion_evidence_packet.route_bag_or_live_nav2_log`。
- 必须要求同一 `task_id`，且 `delivery_result_evidence.source_schema=trashbot.cloud_command_terminal_result.v1` 才能说明 O5 terminal result 已接入 mission gate。
- 必须保留短 safe refs：`command_id_ref`、`task_record_ref`、`evidence_ref`。含路径、URL、token、raw/base64、credential 的输入必须 blocked，且不得回显原文。
- ready 状态只能命名为 ready-not-success-proof，不能把 `delivery_success`、`safe_to_control`、`primary_actions_enabled`、`robot_control_executed` 或 `route_execution_success` 置为 true。

## OKR 对齐

- O5：把 terminal result 从单点桥接推进到同 task mission gate，仍不声明生产云完成。
- O6：archive/readback 形成可供 PC/手机消费的统一只读 gate。
- O7：PC workstation 能直接展示同 task gate 和下一条缺失证据，减少人工对照成本。

## 非目标

- 不接真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN。
- 不启动 Nav2、不发布 `/cmd_vel`、不控制 WAVE ROVER。
- 不证明真实送达成功、真实 operator confirmation 或真实 robot motion。
- 不新增手机端控制入口，不放宽任何现有 fail-closed 逻辑。

## 验收标准

- 单元测试覆盖 ready、task mismatch、unsafe ref、dangerous true、missing linked artifact。
- O6 API 测试覆盖创建、详情、consumer detail、显式 include 回读。
- O7 测试覆盖 consumer adapter、artifact readiness、fixture preview 或等效 UI/合同展示。
- 文档明确使用本地/mock 证明边界，并给下一轮真实材料命令。

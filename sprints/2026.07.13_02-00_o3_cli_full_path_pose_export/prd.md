# PRD - O3 CLI Full Path Pose Export

## 背景

`2026.07.12_21-57` 证明真实板 strict no-motion ComputePathToPose 可生成 21-point path，但该结果来自 ROS2 CLI fallback。后续 `00:00` 和 `01:00` sprint 只能从 `stdout_tail` 解析出 14 个 pose，导致 fixed-route route-intent 和 consumer dry-run 都必须停在 partial material boundary。

## 用户价值

普通用户最终需要的是一键发车后的可验证路线执行、送达或失败结果。当前还不能执行路线，但 full structured path poses 是 fixed-route replay、route execution record、delivery acceptance 和 HIL 之前的必要材料层。把 CLI fallback 输出变成结构化路径，能让后续 sprint 不再依赖人工从日志尾部补材料。

## 需求

1. 在 no-motion helper 中解析 ROS2 CLI `ComputePathToPose` 输出里的 path poses。
2. 成功解析时输出 structured pose 列表、数量、frame、source index 和 preview 点。
3. 继续保留 `path_point_count`、`fallback_mode=ros2_cli_action_send_goal`、`path_generation_boundary=explicit_opt_in_compute_path_to_pose_cli_action_no_motion`。
4. 若旧 artifact 只有 truncated `stdout_tail`，不得补造缺失点，必须输出 `historic_stdout_tail_truncated_full_pose_replay_unavailable` 或等价窄 blocker。
5. 更新 fixed-route 文档，说明 02:00 之后的 CLI fallback artifact 应优先消费 structured poses；旧 artifact 仍只能按 partial material 处理。

## 非目标

- 不跑 route execution。
- 不跑 NavigateToPose/controller/BT。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不接 WAVE ROVER UART。
- 不改硬件配置、串口、波特率或 vendor 事实。
- 不接 O5 production external evidence。

## 验收口径

接受：

- helper/test 证明 CLI fallback 可从完整 CLI 输出解析 structured path poses；
- 本 sprint artifact 证明旧 21:57 source artifact 无法追溯完整 21 pose 时 fail-closed；
- `tech-done.md` 写清实际改动、验证结果、剩余风险。

拒绝：

- 继续只生成 partial consumer dry-run；
- 从 14 个 `stdout_tail` pose 补造 21 个点；
- 任何 motion/control/HIL/delivery/safe-to-control 字段为 true；
- 用软件 export 修复宣称 OKR route execution 或 production progress。

## OKR 边界

O5 仍是最低进度项（约 `85%`），但缺真实 external production evidence，本轮不继续消费。O1 约 `94%`，本轮若只完成 helper/export contract，通常保持 flat；只有新 live same-run full structured path material 到位，才进入是否微调 O1 的 Product 评审。

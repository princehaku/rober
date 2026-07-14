# 2026.07.13 03:00 O3 live full structured path capture - pre_start

- sprint_type: epic
- Owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- 目标 Objective: O1/O3 strict no-motion path proof lane；O5 仍为最低进度但当前缺真实 external production evidence，本轮避免重复消费 O5 support-only blocker。
- 当前时间: 2026-07-13 03:00 +0800

## 上轮状态

上一轮 `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/` 已把 helper/export contract 补齐：

- `cli_fallback_structured_path_pose_export_ready=true`
- sample parser `path_structured_pose_count=2`
- 历史 21:57 artifact fail-closed：`historic_authoritative_path_point_count=21`，但 stdout tail 只能解析 `historic_stdout_tail_structured_pose_count=14`
- 最少缺 `historic_minimum_unmaterialized_path_pose_count=7`
- 结论仅是 helper/export readiness，不是新的 live full structured path material

## 本轮启动原因

`OKR.md` 当前最低 Objective 仍是 O5 约 85%，但 O5 的可加分证据需要真实 external production evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 验收。当前环境没有这些外部条件，继续做 readiness/checklist/wrapper 会重复消费同一 blocker。

因此本轮转向当前可推进的 O1/O3 strict no-motion lane：用上轮已更新 helper 重新跑 same-run `ComputePathToPose` live capture，目标产出 `path_structured_pose_count=21` 的新 artifact，为 fixed-route replay 和后续 route execution/material intake 提供更强同轮证据。

## 红线

- 不发布 `/cmd_vel`
- 不调用 `/api/base/manual`
- 不发送 `NavigateToPose`、`FollowPath`、controller/BT 或 fixed-route movement
- 不打开 WAVE ROVER UART 或底盘串口
- 不声明 route execution、delivery/operator acceptance、HIL、safe-to-control 或 production evidence
- 所有安全字段必须保持 false

## 预期产物

- 新 live capture artifact，优先写入 `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/`
- 新 summary JSON，包含 `path_generated=true`、`path_point_count=21`、`path_structured_pose_count=21`，或明确 fail-closed blocker
- `tech-done.md` 记录实际改动、验证命令输出、剩余风险
- Product acceptance 更新 `side2side_check.md`、`final.md`，必要时保守更新 `OKR.md` 与 `docs/process/okr_progress_log.md`

# Tech Done - O3 CLI Full Path Pose Export

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/`
- Owner: `robot-algorithm-engineer`
- Status: implementation complete, validation passed

## 自主能力目标和本轮抓手

目标是把 strict no-motion `ComputePathToPose` CLI fallback 从只保存 `path_point_count` /
truncated `stdout_tail`，推进到 future live capture 可直接保存 structured path poses 的 contract。
本轮抓手是 helper parser/export、单测、fixed-route 文档和本 sprint summary artifact。

## 实际改动和接口影响

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 CLI `result.path.poses` YAML-ish parser，输出 `path_structured_poses`、
    `path_structured_pose_count`、`path_preview_points`、`path_preview_point_count`、
    `path_preview_source_point_count` 和 `path_preview_frame_id`。
  - `compute_path_generation_cli_fallback` 在 `ros2_cli_action_send_goal` 成功时，把 structured poses
    同步写入 top-level result 与 `path_goal_response`。
  - 保留 `fallback_mode=ros2_cli_action_send_goal` 和
    `path_generation_boundary=explicit_opt_in_compute_path_to_pose_cli_action_no_motion`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 扩展 CLI fallback 单测，验证 2 个完整 path pose 的 frame、stamp、坐标、preview 和 no-motion 禁止项。
  - 增加旧 21:57 artifact 回归测试，确认 saved `stdout_tail` 只能解析 14 个完整 pose，不能补造成 21 个。
- `docs/navigation/fixed_route_workflow.md`
  - 增加 2026-07-13 02:00 structured export contract 和旧 artifact fail-closed 读取边界。
- `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/artifacts/algorithm/cli_full_path_pose_export_summary.json`
  - 写出本轮 summary：`cli_fallback_structured_path_pose_export_ready=true`、
    `path_structured_pose_count=2` sample parse、historic `21 -> 14 + 7 missing` 边界。

接口影响：只扩展 artifact JSON 字段；不修改 ROS action contract、launch 参数、硬件配置、UART、
O5/O6/O7 代码或历史 sprint artifacts。

## 实现内容

CLI parser 只解析完整出现在 CLI stdout 里的 pose block。对于截断开头的 tail，它会跳过半截 pose，
不会推测缺失的 source_index 或坐标。structured poses 包含 `source_index`、`frame_id`、`stamp`、
`x/y/z` 和 `qx/qy/qz/qw`；preview 点从 structured poses 派生，因此 preview 数量不会超过真实解析数量。

旧 21:57 artifact 的权威 path count 仍是 `21`，但它的 stored fallback `stdout_tail` 只包含 14 个完整 pose block，
所以本轮明确收口为 `historic_stdout_tail_truncated_full_pose_replay_unavailable`。

## 数据、样本和调试输出变化

- 新 summary artifact：
  - `strict_no_motion=true`
  - `cli_fallback_structured_path_pose_export_ready=true`
  - `path_structured_pose_count=2`
  - `historic_authoritative_path_point_count=21`
  - `historic_stdout_tail_structured_pose_count=14`
  - `historic_minimum_unmaterialized_path_pose_count=7`
  - `historic_stdout_tail_truncated_full_pose_replay_unavailable=true`
- fixed-route 文档要求 02:00 后优先消费 `path_structured_poses`，缺字段时才降级到 `stdout_tail` partial material。

## 验证结果

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：通过。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：`Ran 140 tests in 2.303s`，`OK`。
- `python3 -m json.tool .../cli_full_path_pose_export_summary.json >/tmp/cli_full_path_pose_export_summary.pretty.json`：通过。
- summary invariant check：输出 `cli_full_path_pose_export_summary_ok`。
- anchor `rg`：命中 `cli_fallback_structured_path_pose_export_ready`、`path_structured_pose_count`、
  `historic_stdout_tail_truncated_full_pose_replay_unavailable`、`strict no-motion`、
  `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。
- scoped `git diff --check`：通过。

## Strict No-Motion 和 OKR 边界

本轮保持 strict no-motion：未发布 `/cmd_vel`，未调用 `/api/base/manual`，未运行 NavigateToPose、
controller/BT，未打开 WAVE ROVER UART，未改硬件配置。summary artifact 固定
`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、
`delivery_success=false`、`hil_pass=false`。

本轮只有 helper/export readiness 和历史 artifact fail-closed proof，没有 route execution、
delivery、HIL、safe-to-control 或 production external evidence；因此没有 OKR 可调分证据。

## 剩余风险和下一步

剩余风险：当前没有重新跑真实板 live no-motion capture，所以还没有新的 full 21 structured poses artifact。
下一步应使用更新后的 helper 重新跑 strict no-motion `ComputePathToPose` capture；只有新 artifact 中
`path_structured_pose_count=21` 且安全字段仍为 false，fixed-route replay 才能从 partial material
升级为 full structured path material。

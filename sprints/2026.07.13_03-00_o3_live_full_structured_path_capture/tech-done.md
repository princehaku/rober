# Tech Done - O3 Live Full Structured Path Capture

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/`
- Owner: `robot-algorithm-engineer`
- Status: live capture complete, validation passed, expected 21-count target not met

## 自主能力目标和本轮抓手

目标是用上一轮已更新的 helper 重新跑 strict no-motion `ComputePathToPose` live capture，
产出新的 same-run structured path artifact。抓手是复用真实板已有 `150000` LiDAR lifecycle，
只启动 no-motion Nav2 localization/planner proof，并要求 helper 持久化
`path_structured_poses`、preview 字段和 safety invariants。

## 实际改动和接口影响

- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture.raw.json`
  - 新鲜 live board strict no-motion capture，`path_generated=true`、
    `path_point_count=28`、`path_structured_pose_count=28`。
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_pinned_start.raw.json`
  - 用旧 21:57 planner start 作为 explicit initialpose 的复跑 artifact，仍返回
    `path_point_count=28`、`path_structured_pose_count=28`。
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_timeout180.partial.raw.json`
  - 首轮 180 秒外层 timeout 的 partial artifact，记录 `interrupted_before_final_artifact`。
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json`
  - 本轮 summary，固定 fresh live proof boundary、28-count 结果、blocked reason 和 no-motion false safety flags。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 2026-07-13 03:00 读取规则：后续 consumer 应优先消费 fresh 28-pose structured material；
    若仍要求复现 21，blocker 是当前 live localization/map-bound drift。
- `tech-done.md`
  - 记录本轮实际结果、验证输出和剩余风险。

接口影响：只新增/更新 artifact 与文档读取规则；未修改 ROS action contract、launch 参数、硬件配置、
WAVE ROVER UART、O5/O6/O7 代码或 Product closeout 文件。

## 实现内容

真实板连接成功：

```text
ssh -p 37878 root@192.168.1.11 'echo ssh_ok; hostname; date'
ssh_ok
op-z3-b6.home
Mon Jul 13 03:04:22 AM CST 2026
```

helper 已部署到真实板并通过远端编译；本地与远端 helper sha256 一致：

```text
56215a5325b29fe8c08c4d36b761f237d299d99d473f85a210f996ddad44df33
```

首轮命令使用 180 秒外层 timeout：

```bash
python3 /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --managed-runtime-opt-in \
  --reuse-existing-lidar-lifecycle \
  --managed-lidar-serial-port /dev/ttyACM0 \
  --managed-lidar-serial-baudrate 150000 \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output /root/rober/onboard/runtime/o3_live_full_structured_path_capture_20260713_0300.raw.json
```

首轮结果为外层 timeout 导致的 partial artifact：

```text
exit=124
status='interrupted_before_final_artifact'
path_generation_attempted=False
path_generated=False
root_causes=[
  {"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"},
  {"layer": "helper process", "reason": "sigterm_before_final_artifact"}
]
```

为避免把外层 hard timeout 误判成现场 blocker，复跑一次 420 秒外层 timeout 与 30 秒 planner action budget：

```bash
python3 /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --managed-runtime-opt-in \
  --reuse-existing-lidar-lifecycle \
  --managed-lidar-serial-port /dev/ttyACM0 \
  --managed-lidar-serial-baudrate 150000 \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --path-generation-timeout-s 30 \
  --output /root/rober/onboard/runtime/o3_live_full_structured_path_capture_20260713_0300_retry.raw.json
```

复跑结果：

```text
exit=0
status='nav2_no_motion_path_generation_runtime_observed'
evidence_type='robot_runtime_material'
managed_runtime_started=True
managed_lidar_policy='reuse_existing_lidar_lifecycle_no_driver_start'
managed_lidar_serial_baudrate=150000
managed_lidar_driver_started_by_helper=False
scan_once_observed=True
map_once_observed=True
amcl_pose_observed=True
initialpose_published=True
map_server_active=True
amcl_active=True
planner_server_active=True
path_generation_attempted=True
path_generated=True
path_point_count=28
path_structured_pose_count=28
path_preview_point_count=28
path_generation_boundary='explicit_opt_in_compute_path_to_pose_cli_action_no_motion'
root_causes=[]
```

随后用旧 21:57 planner start 作为 explicit initialpose 再复跑一次，仍返回 28：

```text
exit=0
path_generated=True
path_point_count=28
path_structured_pose_count=28
path_goal_request={
  "start_x": -0.3765056140278378,
  "start_y": 0.2500000037252903,
  "goal_x": 0.8,
  "goal_y": 0.2500000037252903,
  "adapted_from_map_bounds": true,
  "adaptation_boundary": "map_bounds_adapted_no_motion_planner_probe"
}
root_causes=[]
```

## 数据、样本和调试输出变化

本轮 summary artifact：

- `schema=trashbot.live_full_structured_path_capture_summary.v1`
- `path_generated=true`
- `expected_path_structured_pose_count=21`
- `path_point_count=28`
- `path_structured_pose_count=28`
- `path_structured_pose_count_reached_expected_21=false`
- `path_preview_point_count=28`
- `path_preview_frame_id=map`
- `blocked_reason=expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation`
- `historic_21_57_artifact_reused_as_live_proof=false`

计数偏差原因：当前 live AMCL start 在 map bounds 外侧，helper 触发
`map_bounds_adapted_no_motion_planner_probe`，把 start/goal 调整到 `y=0.25`；pinned-start
复跑仍复现同一 adaptation，因此 21 点目标没有达成。

## 验证结果

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：通过，无输出。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：

```text
Ran 140 tests in 2.292s
OK
```

- `python3 -m json.tool sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json >/tmp/live_full_structured_path_capture_summary.pretty.json`：通过，无输出。
- safety invariant check：

```text
live_full_structured_path_capture_safety_ok
```

- `rg -n "path_structured_pose_count|path_generated|publishes_cmd_vel|calls_base_manual|uses_base_uart|route_execution_success|delivery_success|hil_pass|next_evidence_required|blocked_reason" sprints/2026.07.13_03-00_o3_live_full_structured_path_capture`：通过；命中 summary 中的 `path_generated=true`、`path_structured_pose_count=28`、blocked reason、`next_evidence_required` 和 false safety fields。该命令同时命中 raw JSON artifact，终端输出过大被截断。
- `git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_03-00_o3_live_full_structured_path_capture`：通过，无输出。

## Strict No-Motion 和 OKR 边界

本轮保持 strict no-motion：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

本轮没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有运行 `NavigateToPose`、
controller/BT、fixed-route movement 或 delivery task，没有打开 WAVE ROVER UART，也没有声明
safe-to-control、HIL、delivery 或 production external evidence。

## 结果判定、失败定位和下一步

本轮达成：fresh same-run strict no-motion structured path material 已产出，helper 成功持久化
完整 `path_structured_poses` 和 preview 字段。

本轮未达成：没有达到 `path_structured_pose_count=21`。实际两次 successful live capture 均为
`path_structured_pose_count=28`。

Exact blocker:

```text
expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation
```

剩余风险和下一步建议：

- 若 Product acceptance 仍要求复现 21 点，需要先处理 current live AMCL/map bounds drift，
  让 planner start/goal 不再触发 `map_bounds_adapted_no_motion_planner_probe`。
- 若 Product acceptance 允许消费 fresh structured material，应让 fixed-route / route-intent
  consumer 接入本轮 28-pose `path_structured_poses`，不要继续依赖旧 21:57 partial stdout tail。
- 本轮仍不是 route execution、NavigateToPose、controller/BT、delivery/operator acceptance、
  current live HIL、safe-to-control 或 production external evidence。

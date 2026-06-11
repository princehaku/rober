# Clean Baseline Nav2 Path Refresh

## sprint_type

micro

## 实际改动

- 从上一轮 `sprints/2026.06.11_11-05_upper_ros_quiescence_baseline/tech-done.md`
  记录的 `upper_ros_quiescent=true` 基线继续推进，先读取 `AGENTS.md`、`OKR.md`、
  `docs/vendor/VENDOR_INDEX.md`、`docs/navigation/fixed_route_workflow.md` 和
  `docs/hardware/board_sensor_stack_smoke.md`。
- 创建本轮 artifact 目录：
  `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/artifacts/`。
- 本地没有已确认可用的 PC nav2 proxy 响应；为避免启动 workstation 触碰 PC 首屏代码，
  本轮直接调用真实上位机 Robot API `http://192.168.1.11:8787`。
- 采集清场前、重试前、结束后的目标 `ps`、`ros2 node list`、`lsof/fuser`、
  systemd 服务状态，确认不会留下 stale Nav2/LiDAR runtime。
- 通过 direct Robot API 执行 fresh no-motion `/api/nav2/proof/refresh`：
  managed runtime opt-in、initialpose opt-in、path generation opt-in，目标
  `map:(0.8, 0, 0)`。
- 同步更新 `docs/navigation/fixed_route_workflow.md` 和
  `docs/hardware/board_sensor_stack_smoke.md`，明确本轮只是 clean-baseline
  fresh no-motion path proof，不是 NavigateToPose、运动、固定路线执行或
  delivery success。

## Fresh Proof 结果

本轮开始时间：

```text
local_run_start_ms=1781146923423
local_run_start_cst=2026-06-11 11:02:03 CST +0800
```

第一轮 direct API refresh 使用 20s collector/runtime/path 窗口，返回
`blocked_with_root_cause`。定位结果：

```text
failure_reason=configured_command_failed
error.type=TimeoutExpired
elapsed_ms=87010
latest_evidence_ref=o10-amcl-nav2-runtime-wrapper-failure-1781147059542
latest_amcl_pose_observed=true
latest_path_generation_succeeded=false
latest_path_generated=false
latest_path_point_count=0
root cause: partial artifact 中 odom_to_base_link/base_link_to_laser_frame static TF 未观测，
            map_to_base_link 因缺 odom_to_base_link 阻塞；helper 被上层 timeout 清理。
```

按要求最多重试一次。重试仍使用同一 no-motion opt-in contract，只把
collector/runtime/path 窗口放宽到 30s。重试成功：

```text
response_status=refreshed
proof_status=nav2_no_motion_path_generation_runtime_observed
evidence_ref=o10-amcl-nav2-runtime-1781147133452
proof_generated_at_ms=1781147181031
fresh_vs_run_start=true
managed_runtime_started=true
managed_runtime_cleanup_ok=true
initialpose_published=true
amcl_pose_observed=true
map_server_active=true
amcl_active=true
planner_server_active=true
path_generation_succeeded=true
path_generated=true
path_point_count=31
root_causes=[]
```

安全边界：

```text
safe_to_control=false
delivery_success=false
primary_actions_enabled=false
robot_control_executed=false
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
sends_motion_commands=false
sends_base_motion_commands=false
path_execution_attempted=false
```

关键 artifacts：

- `artifacts/run_metadata.log`
- `artifacts/pre_clear_readback.log`
- `artifacts/between_retry_cleanup_readback.log`
- `artifacts/nav2_refresh_request.json`
- `artifacts/nav2_refresh_response.json`
- `artifacts/nav2_first_failure_diagnostics.json`
- `artifacts/nav2_refresh_summary.json`
- `artifacts/nav2_latest_after_first.json`
- `artifacts/nav2_status_after_first.json`
- `artifacts/nav2_retry_request.json`
- `artifacts/nav2_retry_response.json`
- `artifacts/nav2_retry_summary.json`
- `artifacts/nav2_retry_extracted_success.json`
- `artifacts/nav2_latest_after_success.json`
- `artifacts/nav2_status_after_success.json`
- `artifacts/nav2_success_readback_summary.txt`
- `artifacts/remote_nav2_lifecycle_latest_after_success.json`
- `artifacts/remote_nav2_lifecycle_latest_summary.json`
- `artifacts/freshness_check.txt`
- `artifacts/post_success_cleanup_readback.log`

## 清理与 Readback

清场前：

```text
target_process_ps: empty
ros2_node_list: empty
/dev/ttyS5 lsof/fuser: no output
/dev/ttyACM0 lsof/fuser: no output
trashbot-upper-robot-api.service=active
trashbot-local-webrtc-camera.service=active
frpc.service=inactive
ssh.service=active
sshd.service=active
```

第一轮失败后、重试前：

```text
matched_before_cleanup: empty
target_process_ps_after_cleanup: empty
ros2_node_list_after_cleanup: empty
/dev/ttyS5 lsof/fuser: no output
/dev/ttyACM0 lsof/fuser: no output
```

重试成功后的最终 readback：

```text
target_process_ps: empty
ros2_node_list: empty
/dev/ttyS5 lsof/fuser: no output
/dev/ttyACM0 lsof/fuser: no output
trashbot-upper-robot-api.service=active
trashbot-local-webrtc-camera.service=active
frpc.service=inactive
ssh.service=active
sshd.service=active
/root/rober/onboard/runtime/nav2_lifecycle_latest.json mtime_ms=1781147181000
```

## 验证结果

- `git diff --check`：通过，无输出。
- direct Robot API fresh no-motion nav2/path proof：第一次失败后已定位 root cause；
  第二次重试通过，保存 direct response/latest/status/remote runtime artifact。
- cleanup readback：通过，无 `o10_amcl_nav2_runtime_proof`、`map_server`、`amcl`、
  `planner_server`、`lifecycle_manager`、`lidar_driver` 残留；`/dev/ttyS5` 和
  `/dev/ttyACM0` 无占用。

## 剩余风险

- 本轮不是 `NavigateToPose`、`FollowPath`、controller/BT 执行、固定路线执行、
  真实运动 gate、HIL 或 delivery success；只能证明 clean-baseline no-motion
  localization/planner/path generation。
- 第一次 20s 窗口仍会因 helper timeout/TF 观测时序失败；当前可复核成功证据来自
  同一 no-motion contract 下的 30s 重试窗口。PC 固定 proxy 若仍使用 20s 窗口，
  可能需要继续用 latest fallback 或后续由 PC owner 调整预算。
- `pre_clear_readback.log` 中包含一次 legacy `/api/base/status` readback，该端点会做
  非运动 `T=130` 反馈请求；本轮 fresh Nav2 proof、重试和 cleanup artifacts 均未
  调用 `/api/base/manual`、未发布 `/cmd_vel`、未打开底盘运动链路，且成功 proof
  字段保持 `uses_base_uart=false`。后续同类 readback 应避免把 `/api/base/status`
  放入 no-motion Nav2 证据主链。

## 当前运行时间

2026-06-11 11:15:00 CST

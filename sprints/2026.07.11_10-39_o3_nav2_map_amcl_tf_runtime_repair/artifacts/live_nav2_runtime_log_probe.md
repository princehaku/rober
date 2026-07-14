# Live Nav2 Runtime Log Probe

时间：`2026-07-11`
目标板：`root@192.168.1.11:37878`
边界：只读 SSH 检查；未发送 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或任何底盘运动命令。

## 1. 板端 runtime/status 文件

- `/root/rober/onboard/runtime/nav2_lifecycle_latest.json`
  - 存在，最近一次 `proof.status=partial_runtime_in_progress`
  - `managed_runtime_started=true`
  - `last_phase=tf_probe`
  - `root_causes` 已下钻到：
    - `/amcl_pose_once_not_observed`
    - `map_to_odom_not_observed`
    - `map_to_base_link_blocked_by_missing_map_to_odom`
- `/tmp/rober_nav2_lifecycle/nav2_lifecycle_status.json`
  - 存在，但内容是旧的 `state=stopped`
  - 这不是本轮 refresh 的直接根因；因为 direct launch log 已证明 Nav2 组件确实被拉起过。
- `/tmp/rober_nav2_lifecycle/logs/nav2_lifecycle_manager.log`
  - 存在但大小为 `0`
  - 当前 `o11_nav2_lifecycle.sh` 把真正的 launch 输出写到 `autonomous_nav2_stack_only.log`，manager log 为空不代表 launch 没启动。
- `/tmp/rober_nav2_lifecycle/logs/autonomous_nav2_stack_only.log`
  - 存在且非空。

## 2. launch 日志摘录

从 `autonomous_nav2_stack_only.log` 抽到的关键只读事实：

```text
[static_transform_publisher-1] [INFO] ... [static_laser_tf]: Spinning until stopped - publishing transform
[component_container_isolated-2] [INFO] ... [controller_server]:
        controller_server lifecycle node launched.
[component_container_isolated-2] [INFO] ... [map_server]:
        map_server lifecycle node launched.
```

同一日志尾部长期重复：

```text
Timed out waiting for transform from base_link to map to become available,
tf error: Invalid frame ID "map" passed to canTransform argument target_frame - frame does not exist
```

结论：

- 不是 launch crash。
- 不是 `map_server` 包缺失或 launch 根本没包含 Nav2 组件。
- 当前更具体的 runtime 根因是 `map` frame / `map->odom` 没建立，导致后续 local costmap 一直卡在 TF。

## 3. ROS graph / lifecycle 只读观察

SSH 只读命令看到：

```text
ros2 node list:
/esp32_bridge
/lidar_driver
/static_transform_publisher_...
```

独立图查询中：

- `ros2 lifecycle get /map_server` -> `Node not found`
- `ros2 lifecycle get /amcl` -> `Node not found`
- `ros2 lifecycle get /planner_server` -> `Node not found`

这与 direct helper 并不矛盾：独立 SSH 查询针对的是“当前常驻图”，而 helper 是在 `/api/nav2/proof/refresh` 或 direct helper run 内临时拉起 managed runtime，再在它自己的窗口里观测 lifecycle / TF。

## 4. direct helper 复现

绕过 `8787`，直接在板端执行 `o10_amcl_nav2_runtime_proof.py` 同参数 no-motion 复现后，产物见：

- `artifacts/live_nav2_direct_helper.raw.json`

关键事实：

- helper 本身能完成，不是 launch crash。
- `proof.elapsed_ms=64285`
- 最终 `proof.status=blocked_with_root_cause`
- 最终 `proof.root_causes` 收敛为：
  - `map_to_odom_not_observed`
  - `map_to_base_link_blocked_by_missing_map_to_odom`
  - `localization_not_ready_for_path_generation`

## 5. 本轮推进出的更具体失败定位

1. 第一层软件 bug 已确认并修复：本地新增 fast path 初版在板端 direct helper 中触发 `UnboundLocalError: lifecycle_active referenced before assignment`。
2. 修复后，helper 可以直接完成并给出最终 root cause。
3. 但 `field_route_evidence_preflight.py` 里的 `/api/nav2/proof/refresh` 仍然 `curl (28)`，因为：
   - direct helper 同参数实际耗时约 `64.3s`
   - preflight refresh hard timeout 固定为 `38s`
   - 所以 preflight 当前拿不到 HTTP body，只能看到 `refresh_command_failed`
4. 因此，本轮最具体的软件根因已经从“lifecycle unavailable”推进为：
   - `refresh` 内部 helper 先前存在 `UnboundLocalError`
   - 修复后 helper 仍需约 `64s` 才能完成
   - 现有 preflight `curl --max-time 38` 预算小于 helper 完成预算
   - helper 最终真实 root cause 是 `map_to_odom_not_observed`，不是 launch crash 或 package missing

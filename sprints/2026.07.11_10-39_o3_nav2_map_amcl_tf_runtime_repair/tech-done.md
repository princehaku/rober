# O3 Nav2 Map AMCL TF Runtime Repair Tech Done

## sprint_type

`sprint_type: epic`

## 实际改动

本轮主价值来自现有实现链的返工验收与现场根因下钻，没有扩散到 O5/O6/O7 或运动控制面。

实际新增/落盘文件：

- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/local_preflight.raw.json`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_map_amcl_tf.raw.json`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_direct_helper.raw.json`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_runtime_log_probe.md`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/tech-done.md`

本轮验收所基于的 scoped 实现变更点已经存在于工作树中，并已通过本轮验证：

- `onboard/scripts/o11_nav2_lifecycle.sh`
  - `start` 路径会显式透传 `base_enabled` / `lidar_enabled` / `lidar_serial_port` / `lidar_serial_baudrate` / `static_laser_tf_enabled`，不再把现场 auto 判定丢在 manager 外层。
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `/initialpose` 优先走进程内 burst publisher，补了 subscriber match / publish attempts / publish error 诊断。
  - planner lifecycle / node info 只在定位链 ready 后再补 probe，避免过早把 planner inactive 和 localization blocker 混在一起。
  - 返工新增 `managed_runtime_localization_root_cause_fast_path`，当 managed runtime 已观测到 `map_server/amcl` 节点但定位仍 blocked 时，不再继续跑拖死 HTTP 的重复 `/scan` `/map` echo。
  - 修复板端 direct helper 实际触发的 `UnboundLocalError: lifecycle_active referenced before assignment`。
- `onboard/scripts/field_route_evidence_preflight.py`
  - live 模式新增 localization smoke、`/map` `/amcl_pose` metadata、lifecycle probe、managed map yaml probe、`/api/nav2/proof/refresh` 固定 no-motion readback，以及 root-cause summary 收敛。
- `onboard/scripts/upper_robot_api.py`
  - `nav2_proof_refresh` readback 允许显式回传 `managed_runtime_started -> starts_nav2`，但仍固定 `safe_to_control=false`、`robot_control_executed=false`。

## 验证命令与结果

### 1. Shell 语法

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

结果：通过，无输出。

### 2. Python 语法

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
```

结果：通过，无输出。

### 3. 目标单测

```bash
python3 -m unittest onboard.tests.test_o11_nav2_lifecycle_script onboard.tests.test_map_lifecycle_proof_helper onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
```

结果：

- `Ran 181 tests in 2.544s`
- `OK (skipped=1)`

返工后补跑：

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：

- `Ran 44 tests in 2.203s`
- `OK`

### 4. bringup 侧测试

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
```

结果：

- `Ran 23 tests in 0.045s`
- `OK`

### 5. 本地 dry-run artifact

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/local_preflight.raw.json
```

结果：

- 输出 schema：`trashbot.board_field_evidence_preflight.v1`
- 输出状态：`dry_run_template_only_not_proven`
- 证明 dry-run 模板能稳定生成，不依赖 ROS2/SSH/硬件。

### 6. live ssh artifact

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_map_amcl_tf.raw.json
```

结果：

- 输出 schema：`trashbot.board_field_evidence_preflight.v1`
- 输出状态：`blocked_refresh_readback_failed`
- 这次不是中断退出，也不是 generic 黑盒 timeout；artifact 已自然返回并给出分层 blocker：
  - `root_cause_layers=["map_server_not_active","amcl_not_active","tf_missing"]`
  - `localization_blocked_reasons=["blocked_amcl_pose_not_observed","blocked_map_to_odom_not_observed","blocked_map_to_base_link_not_observed"]`
  - `lifecycle_states` 显示 `/map_server`、`/amcl`、`/planner_server` 均为 `lifecycle_unavailable`
  - `/map`：`topic_type=null`
  - `/amcl_pose`：`topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`，但 `publisher_count=0`
- `nav2_refresh.status=refresh_command_failed`
- `nav2_refresh.returncode=28`
- `nav2_refresh.naturally_returned=true`
- `daemon_fault_detected=false`

返工后重新执行同一命令：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_map_amcl_tf.raw.json
```

返工后结果：

- 仍然落盘 `status=blocked_refresh_readback_failed`
- 但本轮已经把 `refresh` 内部问题下钻到更具体的软件根因：
  - 先前 helper 存在板端可复现的 `UnboundLocalError: lifecycle_active referenced before assignment`
  - 修复并同步到板端后，direct helper 产物 `artifacts/live_nav2_direct_helper.raw.json` 能正常完成
  - direct helper 最终 `proof.elapsed_ms=64285`
  - direct helper 最终 `proof.root_causes` 为：
    - `map_to_odom_not_observed`
    - `map_to_base_link_blocked_by_missing_map_to_odom`
    - `localization_not_ready_for_path_generation`
  - 但 preflight 的 refresh 仍固定 `curl_max_time_s=38` / `process_timeout_s=42`
  - 因此这轮 `curl (28)` 已经可具体归因为：helper 完成预算约 `64.3s`，大于 preflight refresh 的 `38s` HTTP 等待窗口

### 6.1 板端只读 runtime/log probe

本轮按要求补跑了板端只读检查，摘要见：

- `artifacts/live_nav2_runtime_log_probe.md`

关键摘录：

- `/root/rober/onboard/runtime/nav2_lifecycle_latest.json` 在 refresh 窗口内能写出 `managed_runtime_started=true`
- `/tmp/rober_nav2_lifecycle/nav2_lifecycle_status.json` 是旧的 `state=stopped`，不是当前 helper runtime 的直接根因
- `autonomous_nav2_stack_only.log` 明确出现：
  - `controller_server lifecycle node launched`
  - `map_server lifecycle node launched`
  - `static_laser_tf ... publishing transform`
  - 长时间重复 `Invalid frame ID "map"` 的 TF 错误

这把问题从“lifecycle unavailable”推进到了：

- 不是 launch crash
- 不是 package missing
- 不是 map_server 根本没被 launch
- 当前直接 runtime 根因是 `map_to_odom` 没建立，进一步阻塞 `map_to_base_link`

### 7. diff hygiene

```bash
git diff --check -- onboard/scripts/o11_nav2_lifecycle.sh onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py onboard/tests/test_o11_nav2_lifecycle_script.py onboard/tests/test_map_lifecycle_proof_helper.py onboard/tests/test_nav2_runtime_proof_helper.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py onboard/src/ros2_trashbot_bringup/test docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair
```

结果：通过，无 whitespace / conflict 标记问题。

## 失败定位

这轮现场失败已经从“refresh 超时黑盒”收敛成同窗 root cause：

1. 第一轮返工前，板端 direct helper 可稳定复现代码错误：
   - `UnboundLocalError: lifecycle_active referenced before assignment`
   - 该错误由本轮新增 fast path 作用域处理不完整导致。
2. 修复并同步后，direct helper 可以正常完成；说明 `/api/nav2/proof/refresh` 内部不是 launch crash。
3. `autonomous_nav2_stack_only.log` 明确显示 `map_server` 和 `controller_server` 生命周期节点被 launch 起来，且 `static_laser_tf` 在发布。
4. direct helper 最终 root cause 不是“node 不存在”，而是：
   - `map_to_odom_not_observed`
   - `map_to_base_link_blocked_by_missing_map_to_odom`
   - `localization_not_ready_for_path_generation`
5. 仍旧存在的 `curl returncode=28` 已推进成明确预算不匹配问题：
   - direct helper 实测约 `64.3s`
   - preflight refresh 仍只等 `38s`
   - 所以 preflight 当前拿不到 HTTP body，只能得到 `refresh_command_failed`
6. 独立 SSH graph 查询里看到的 `Node not found`，与 direct helper 结果并不冲突；前者查的是“常驻图”，后者查的是 refresh 内部临时拉起的 managed runtime 窗口。

## 剩余风险

- 本轮没有证明 `map_server`、`amcl` 或 `planner_server` active。
- 本轮没有在 preflight HTTP body 中直接回读到 helper 最终 root causes；当前仍被 `38s` refresh 等待窗口截断。
- 没有证明 `/map` 在独立常驻图中稳定建立。
- 没有证明 `/amcl_pose` 在独立常驻图中稳定有 publisher。
- 没有证明 `map->odom` 或 `map->base_link`。
- 仍然没有任何运动执行，且必须继续保持：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`
- 本轮证据边界仍是 no-motion runtime / readback proof，不等于 live Nav2 route execution、底盘运动、delivery success 或 O3/O5 OKR 增量。

## 协同判断

- `Product`: 暂不需要；方向和边界清楚。
- `Hardware`: 目前不需要先介入。当前主 blocker 先落在 Nav2 lifecycle / map / AMCL runtime 层，不是新的 UART/vendor 参数问题。
- `Algorithm`: 下一轮建议介入一次。如果 `autonomous.launch.py nav2_stack_only:=true` 下 `map_server`/`amcl` 本就未被正确纳入 bringup，或 AMCL 参数/TF 前置条件仍不满足，需要算法/导航 owner 协助确认 Nav2 localization 最小链路。
- `Full-Stack`: 不需要。

## 下一轮建议

下一轮不要再扩展 preflight/readback 包装，直接盯下面三件事做最小修复并复跑 live artifact：

1. 确认 `autonomous.launch.py nav2_stack_only:=true` 是否真的把 `map_server`、`amcl`、`planner_server` 纳入并可被 lifecycle manager 管理。
2. 优先处理 `map_to_odom_not_observed`，因为它现在是 direct helper 最终收口的最前置 blocker，且已经比旧的 `lifecycle unavailable` 更具体。
3. 再决定是继续压缩 helper 运行时长，还是上调 preflight refresh HTTP 等待窗口；当前两者预算不匹配，`38s` 不足以拿到 helper 最终 body。

# Tech Done - O3 Map/AMCL/Scan/TF Downstream Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 08:23 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_downstream_recovery_only`

## 实际改动

1. `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
   - 新增 `/map` 到 `localization_signal_freshness`，让 `/map_once_not_observed` 能继续拆成 topic missing、publisher count、sample timeout 等字段。
   - `map_lifecycle_preflight` 新增 `node_summaries` 和 `blocking_reasons`，区分 lifecycle command timeout、inactive stdout、command failed 和 skipped。
   - 新增 `proof.downstream_recovery_summary`，统一汇总 `readiness_inputs`、map lifecycle、scan、map、AMCL、TF 和 path gate。
   - CLI fallback 额外记录 `/scan` 与 `/map` 的 `ros2 topic info --verbose` endpoint 摘要。
   - 修复 `/scan` 分类：topic list 未拿到 type 但 endpoint inventory 已看到 publisher 时，不再误报 `/scan_no_publisher`，而是按 sample/QoS/window timeout 收口。
2. `onboard/tests/test_nav2_runtime_proof_helper.py`
   - 单测从 97 个增至 100 个。
   - 覆盖 lifecycle timeout vs inactive stdout、`/map` publisher=0 vs sample timeout、`downstream_recovery_summary` 目标 blocker、以及 `/scan` endpoint publisher 可见时不误报 no publisher。
3. `docs/navigation/field_route_evidence_preflight.md`
   - 补充 `2026-07-12 07:53` downstream recovery summary 读取顺序和 no-motion 边界。
4. `docs/navigation/fixed_route_workflow.md`
   - 补充 fixed-route/no-motion closeout 对 `downstream_recovery_summary` 的读取顺序。
5. `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/`
   - 新增/覆盖 local 与 true-board raw artifacts。

## 验证命令与结果

### 1. 语法检查

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 结果：`RC=0`

### 2. 定向单测

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- 结果：`Ran 100 tests in 2.269s OK`

### 3. Local dry-run

```bash
mkdir -p sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --output-json sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/local_map_amcl_scan_tf_downstream_recovery.raw.json
```

- 结果：`RC=2`，按 macOS 本机缺 `/opt/ros/humble/setup.bash` 预期 fail-closed。
- artifact：`sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/local_map_amcl_scan_tf_downstream_recovery.raw.json`
- 关键字段：
  - `status=blocked_with_root_cause`
  - `board_source_preflight.classification=board_source_preflight_source_failed`
  - `lightweight_cli_ready=false`
  - `cli_ready=false`
  - `runtime_ready=false`
  - `downstream_recovery_summary.map_lifecycle.classification=map_lifecycle_preflight_skipped_without_ros2_cli`
  - `path_generation_attempted=false`
  - `path_generated=false`
  - all no-motion danger fields remain `false`

### 4. True-board strict no-motion run

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 结果：`RC=0`

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --output-json /tmp/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json'
```

- 结果：`RC=2`
- 返工记录：第一次 live artifact 显示 `/scan.publisher_count=1` 但 `blocked_reason=/scan_no_publisher`。已修正分类器并重新同步脚本、重跑 live run，最终 canonical artifact 改为 `/scan_reliable_and_best_effort_timeout`。

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json \
  sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json
```

- 结果：`RC=0`
- artifact：`sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json`
- 关键字段：
  - `status=blocked_with_root_cause`
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `board_source_preflight.lightweight_cli_ready=true`
  - `board_source_preflight.cli_ready=true`
  - `board_source_preflight.runtime_ready=true`
  - `map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_and_amcl_inactive`
  - `map_lifecycle_preflight.blocking_reasons.map_server=map_server_lifecycle_command_timeout`
  - `map_lifecycle_preflight.blocking_reasons.amcl=amcl_lifecycle_command_timeout`
  - `downstream_recovery_summary.scan.publisher_count=1`
  - `downstream_recovery_summary.scan.blocked_reason=/scan_reliable_and_best_effort_timeout`
  - `downstream_recovery_summary.map.blocked_reason=map_server_lifecycle_command_timeout`
  - `downstream_recovery_summary.map.topic_sample.blocked_reason=/map_topic_missing`
  - `downstream_recovery_summary.amcl.blocked_reason=amcl_lifecycle_not_active`
  - `downstream_recovery_summary.tf.blocked_reason=/tf_topic_missing`
  - `path_generation_attempted=false`
  - `path_generated=false`

### 5. Scoped diff check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery
```

- 结果：`RC=0`

## 失败定位

- true-board 已保持上一轮起点：`board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`。
- primary downstream blockers 现在更清楚：
  - `/map_server` 和 `/amcl` lifecycle command 均在 10s 窗口内 timeout，不是 inactive stdout。
  - `/scan` publisher 已可见：`publisher_count=1`，但 BEST_EFFORT/RELIABLE 两类 rclpy sample probe 都 timeout，收口为 `/scan_reliable_and_best_effort_timeout`。
  - `/map` 仍未观测到 sample，且 topic sample summary 目前为 `/map_topic_missing`；顶层 map readiness 先被 `map_server_lifecycle_command_timeout` 阻塞。
  - TF 仍为 `/tf_topic_missing`，尚未进入 dynamic `map->odom` source clean state。
- planner-only path gate 未运行，因为 lifecycle/topic/AMCL/TF readiness 不 clean。

## No-motion 安全字段

本轮没有发送 NavigateToPose，没有发布 `/cmd_vel`，没有调用 `/api/base/manual`，没有打开或使用 WAVE ROVER UART。

artifact 中继续固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## 剩余风险

1. 本轮仍是 O3/O1 supporting no-motion downstream diagnostic delta，不是 same-run path generation、route execution、delivery/operator acceptance、HIL 或 production evidence。
2. `/map_server` 和 `/amcl` lifecycle command timeout 仍需下一轮继续压缩：当前 artifact 区分了 timeout vs inactive stdout，但尚未修复 lifecycle active。
3. `/scan` publisher 可见但 sample timeout，可能是 QoS/window、LiDAR runtime 发布节奏或 driver 状态；如果下一轮落到串口/硬件事实，必须交 Hardware owner 读取 `docs/vendor/VENDOR_INDEX.md`。
4. `/tf_topic_missing` 仍未解除，dynamic `map->odom` source 尚未观测。
5. `ros2 daemon status` 与 heavy `ros2 --help` 仍会 timeout，但已作为 diagnostic，不再阻塞 `cli_ready`。

## 是否需要协同

- Product：需要按本 artifact 做保守验收；本轮不应调整 OKR 百分比或归档 KR。
- Hardware：暂不改硬件配置；若下一轮确认 `/scan_reliable_and_best_effort_timeout` 是 LiDAR serial/runtime/接线事实，再升级 Hardware 并读 vendor docs。
- Autonomy：下一轮若 lifecycle timeout 解除后仍缺 AMCL/TF/path readiness，需要协同分析 AMCL/TF source。
- Full-Stack：本轮不需要。

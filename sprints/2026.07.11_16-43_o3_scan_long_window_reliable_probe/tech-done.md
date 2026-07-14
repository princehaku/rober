# O3 Scan Long Window Reliable Probe Tech Done

## sprint_type

`sprint_type: epic`

## 自主能力目标和本轮抓手

本轮返工目标不是再改 `/scan` 分类，而是把 attempt 级 artifact 语义补齐：当 child attempt 因 outer timeout 或 child timeout 被判定为 `timed_out=true` 时，对应 `sample_timing.timed_out` 也必须同步为 `true`，同时保留 `timeout_boundary_ms`、`sample_wait_started_at_ms` 等 timing 字段。抓手仍是 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 的 child probe 结果收口逻辑，并用单测锁住 outer-timeout 覆盖 child payload 的场景。

本轮证据边界仍是 live no-motion diagnostic proof，不证明 `safe_to_control`、`robot_control_executed`、`route_execution_success`、`hil_pass` 或 `delivery_success`。

## 实际改动文件

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 在 `rclpy_scan_once(...)` 收口 payload 后，把 attempt 级 `timed_out` 强制并入 `sample_timing.timed_out`。
  - 保留 child payload 已经记录的 `timeout_boundary_ms`、`sample_wait_started_at_ms`、`sample_wait_finished_at_ms` 等 timing 字段，不重写其数值。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 outer timeout 回归测试，锁定 `result.timed_out=true` 时 `result.sample_timing.timed_out` 也必须为 true。
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/local_o10_scan_long_window_reliable_probe.raw.json`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.raw.json`

## 接口影响

JSON 变化保持 additive / backward-compatible：

- `proof.localization_signal_freshness["/scan"].probe.attempts[*].sample_timing.timed_out`
- `proof.localization_signal_freshness["/scan"].probe.best_effort_attempt.sample_timing.timed_out`
- `proof.localization_signal_freshness["/scan"].probe.reliable_attempt.sample_timing.timed_out`

旧字段如 `sample_wait_started_at_ms`、`timeout_boundary_ms`、`probe.attempts`、`best_attempt`、`endpoint_inventory`、`path_generated` 和顶层 safety fields 保留。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- exit `0`

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- exit `0`
- `Ran 59 tests in 2.217s`
- 本次返工新增 1 条回归测试后为 `Ran 60 tests`
- `OK`

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/local_o10_scan_long_window_reliable_probe.raw.json
```

- exit `2`
- 本地 Mac 无 `/opt/ros/humble/setup.bash`，按预期 fail-closed。
- local artifact：`status=blocked_with_root_cause`、`/scan.probe.classification=/scan_no_publisher`、`path_generated=false`、所有 safety fields false。

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- exit `0`

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

- exit `2`
- helper 自然退出，但这次板端状态比上一轮更前置地失败：stdout 收口到 `blocked_with_root_cause`，而 `nav2_lifecycle_latest.json` 落盘内容停在 `partial_runtime_in_progress` / `partial_runtime_material`，没有真正走到 `/scan` attempt 持久化阶段。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.raw.json
```

- exit `0`

```bash
cp sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.raw.json \
  sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.partial_runtime.raw.json
```

- exit `0`
- 先冻结返工后被覆盖的 canonical partial artifact，避免后续重跑再次抹掉现场中间态。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-timeout-s 60 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest_16_43_retry.json'
```

- 远端 retry 文件已生成，但 SSH 会话收尾阶段持续悬挂；为保留现场证据，等待文件落盘后结束会话。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest_16_43_retry.json' \
  > sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.retry_managed60.raw.json
```

- 已按验收命令执行，但本地多次拿到空文件；随后用 `scp` 补拉同一远端文件，确认 retry artifact 内容。

## Live artifact 关键字段

Artifact：`sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.raw.json`

本次 live artifact 没有回到 `/scan` attempt 级：

- `status=partial_runtime_in_progress`
- `evidence_type=partial_runtime_material`
- `proof.localization_signal_freshness["/scan"].probe.boundary=not_evaluated`
- `probe.classification=null`
- `probe.best_effort_attempt` 不存在
- `probe.reliable_attempt` 不存在

Localization / path：

- `proof.localization_signal_freshness["/scan"].probe.best_effort_attempt.timed_out`：不存在
- `proof.localization_signal_freshness["/scan"].probe.best_effort_attempt.sample_timing.timed_out`：不存在
- `proof.localization_signal_freshness["/scan"].probe.reliable_attempt.timed_out`：不存在
- `proof.localization_signal_freshness["/scan"].probe.reliable_attempt.sample_timing.timed_out`：不存在
- `proof.path_generated=false`

当前 live artifact 和 stdout 暴露的更前置 blocker：

- `ros2_command_unavailable_after_bash_source`
- `managed_runtime_wait_timeout`
- `path_generation_requested_but_ros2_unavailable`

Retry artifact：`sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.retry_managed60.raw.json`

- `status=partial_runtime_in_progress`
- `evidence_type=partial_runtime_material`
- `proof.localization_signal_freshness["/scan"].probe.boundary=not_evaluated`
- `probe.classification=null`
- `probe.best_effort_attempt` 不存在
- `probe.reliable_attempt` 不存在
- 首个 root cause：`map_to_odom_not_observed`

结论：`--managed-timeout-s 60` 仍未恢复双 QoS attempt 现场证据，因此 retry artifact 不能覆盖 canonical。

Top-level false safety fields：

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `route_execution_success=false`
- `hil_pass=false`

## 失败定位

本轮返工的代码问题已经修正并被单测锁住，但 live 复验没有复现到 `/scan` attempt 层，原因是现场在更前置阶段漂移了：

1. helper stdout 最终能收口到 `blocked_with_root_cause`，说明主流程确实跑完。
2. `nav2_lifecycle_latest.json` 和新增的 `nav2_lifecycle_latest_16_43_retry.json` 都没有进入 `/scan` attempt 层，`/scan.probe.boundary=not_evaluated`，没有 `best_effort_attempt` / `reliable_attempt`。
3. 即便把 managed runtime wait 拉长到 60 秒，retry artifact 仍停在 `partial_runtime_in_progress`，主 root cause 仍前置在 `map_to_odom_not_observed`。
4. 因此这次 live 不能证明 attempt 级 `sample_timing.timed_out` 已在板端 artifact 生效；当前只完成了代码修正和本地回归锁定。

## 剩余风险

- 板端最新 live artifact 没有进入 `/scan` probe，因此缺少现场 attempt 级证据，`timed_out` / `sample_timing.timed_out` 的 live 对齐还未真正验到。
- `ros2_check` 和 managed runtime wait 在这轮现场重新成为更高优先级 blocker；如果不先恢复这层，后续 `/scan` QoS 证据会继续缺席。
- 本轮没有 route CSV、keyframe、rosbag、Nav2 success result、delivery record 或 operator confirmation，不调整 OKR 百分比，不归档 KR。

## 下一条现场执行命令

优先保留当前 helper，不再改 proof 合同，先恢复板端 `ros2` 可用性和 managed runtime wait：

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

待 live artifact 重新回到 `/scan` attempt 层后，再复核两个 attempt 的 `timed_out` 与 `sample_timing.timed_out` 是否同时为 true。

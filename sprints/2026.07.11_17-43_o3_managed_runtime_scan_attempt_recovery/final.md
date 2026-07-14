# O3 Managed Runtime Scan Attempt Recovery Final

## Sprint Summary

- Sprint: `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/`
- Sprint type: `epic`
- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- Outcome: accepted as O3/O1 supporting fail-closed diagnostic progress; latest live proof remains blocked before `/scan` attempts.

## 复盘结论

本轮目标是承接 `2026.07.11_16-43_o3_scan_long_window_reliable_probe`，先恢复 latest true-board artifact 回到 `/scan` attempt 层，再决定是否继续追 BEST_EFFORT / RELIABLE timeout 事实。

工程侧已完成：helper 增加 managed runtime lifecycle fast-path，ROS2 CLI timeout 回收不再无限等待；单测、local fail-closed、true-board helper、artifact pull 和 scoped check 都通过。latest live artifact 没有恢复 `/scan` attempt，但它也不再停在 `partial_runtime_in_progress`，而是更保守地自然收口为 `blocked_with_root_cause`，并把 blocker 前移到 `map_lifecycle_proof_not_clean` 与 `ros2_command_unavailable_after_bash_source`。

因此本轮最终按最新落盘 artifact 收口：这是一次更前置 runtime/lifecycle blocker 收敛，不是 `/scan` recovered，不是 `path_generated=true`，也不是 route execution / delivery 进展。

## 实际改动

Algorithm owner 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/tech-done.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/local_o10_managed_runtime_scan_attempt_recovery.raw.json`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/live_o10_managed_runtime_scan_attempt_recovery.raw.json`

Product closeout 新增或更新：

- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/pre_start.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/prd.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/tech-plan.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/side2side_check.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证证据

子 agent 验证：

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
exit 0
Ran 60 tests ... OK
```

```text
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/local_o10_managed_runtime_scan_attempt_recovery.raw.json
exit 2
local_status=blocked_with_root_cause
```

```text
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
exit 2
```

```text
git diff --check -- sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery
exit 0
```

## Artifact 结论

latest live artifact 当前输出：

```text
status=blocked_with_root_cause
evidence_type=blocked_with_root_cause
managed_runtime_started=true
managed_runtime_wait_boundary=managed_runtime_wait_timeout
map_server_active=false
amcl_active=false
/scan.probe.boundary=scan_probe_skipped_without_ros2
best_effort_attempt absent
reliable_attempt absent
path_generated=false
safe_to_control=false
robot_control_executed=false
delivery_success=false
route_execution_success=false
hil_pass=false
root_causes=[map_lifecycle_proof_not_clean, ros2_command_unavailable_after_bash_source]
```

现场日志同时证明 blocker 已前移到 map lifecycle / ROS2 source：

```text
[ERROR] [lifecycle_manager]: Failed to change state for node: map_server
[ERROR] [lifecycle_manager]: Failed to bring up all requested nodes. Aborting bringup.
```

```text
managed_runtime_wait_result.boundary=managed_runtime_wait_timeout
node_list.boundary=rclpy_node_names_failed
error=ModuleNotFoundError: No module named 'rclpy'
```

## OKR 结论

- O5：保持约 `85%`。本轮仍没有真实 external production evidence。
- O1：保持约 `93%`。本轮没有 current live HIL、same-run path generation success、Nav2 route execution success 或 acceptance。
- O6/O7：保持约 `93%`。本轮没有新的 current-run route/delivery/operator/production material 可消费。
- O3 live lane：latest blocker 已从 partial runtime 前移到 managed runtime / map lifecycle / ROS2 source，但仍未恢复 `/scan` attempt。
- KR：不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮证明：

- helper 能以 fail-closed 方式自然收口 latest live artifact；
- latest blocker 已前移到 `map_lifecycle_proof_not_clean` 与 `ros2_command_unavailable_after_bash_source`；
- no-motion safety 边界仍被严格保持。

本轮不证明：

- `/scan` BEST_EFFORT / RELIABLE attempt 已恢复；
- `path_generated=true`；
- `route_execution_success=true`；
- `safe_to_control=true`；
- `hil_pass=true`；
- `delivery_success=true`；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- board 侧 sourced shell 中 `ros2` CLI 与 `rclpy` runtime 可能仍处于漂移状态，是否同根因尚未拆开。
- `map_server` lifecycle bringup failure 目前仍会直接阻断 `/scan` attempt 级读数。
- 只要 `path_generated=false` 与 `route_execution_success=false` 继续固定，O6/O7 当前 run material 仍不能安全计分。

## 下一轮建议

下一轮先单独验证 board 侧 `source /opt/ros/humble/setup.bash` 之后的 `command -v ros2` 与 `python3 -c 'import rclpy'`，再单独清掉 `map_server` lifecycle clean active。只有 runtime/source 与 lifecycle 都 clean 后，才重新进入 `/scan` BEST_EFFORT / RELIABLE attempt。

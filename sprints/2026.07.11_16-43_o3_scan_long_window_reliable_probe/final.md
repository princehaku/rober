# O3 Scan Long Window Reliable Probe Final

## Sprint Summary

- Sprint: `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/`
- Sprint type: `epic`
- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- Outcome: accepted as O3/O1 supporting code/test progress; latest live proof remains blocked before `/scan` attempts.

## 复盘结论

本轮目标是延续 `2026.07.11_15-44_o3_scan_endpoint_timing_inventory`，把 `/scan` 从 publisher endpoint 可见但 sample timeout，推进成 BEST_EFFORT 与 RELIABLE 的长窗口对照。

工程侧已完成：helper 合同新增双 QoS attempt，单测覆盖 timeout 语义，首次真实板长窗口运行也曾把 root cause 推到 `/scan_reliable_and_best_effort_timeout`。随后主节点验收发现 attempt 顶层 `timed_out=true` 与 `sample_timing.timed_out=false` 有歧义，要求返工。返工后的代码和单测通过，但最新真实板复跑没有再进入 `/scan` attempt 层，canonical 与 managed60 retry artifact 都停在 `partial_runtime_in_progress`。

因此本轮最终按最新落盘 artifact 保守收口：代码与测试推进有效，但 live proof 未稳定恢复到双 attempt 层；不调整 OKR 百分比，不归档 KR。

## 实际改动

Algorithm owner 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/tech-done.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/local_o10_scan_long_window_reliable_probe.raw.json`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.raw.json`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.partial_runtime.raw.json`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.retry_managed60.raw.json`

Product closeout 新增或更新：

- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/pre_start.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/prd.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/tech-plan.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/side2side_check.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/final.md`
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
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/local_o10_scan_long_window_reliable_probe.raw.json
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
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-timeout-s 60 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest_16_43_retry.json'
exit 2
```

```text
git diff --check -- sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe
exit 0
```

## Artifact 结论

首次 live run 曾输出：

```text
probe.classification=/scan_reliable_and_best_effort_timeout
best_effort_attempt.requested_qos_profile.reliability=BEST_EFFORT
reliable_attempt.requested_qos_profile.reliability=RELIABLE
best_effort_attempt.sample_timing.sample_count=0
reliable_attempt.sample_timing.sample_count=0
path_generated=false
safe_to_control=false
delivery_success=false
hil_pass=false
```

返工后的最终 canonical / retry live artifacts 当前输出：

```text
status=partial_runtime_in_progress
evidence_type=partial_runtime_material
/scan.probe.boundary=not_evaluated
probe.best_effort_attempt absent
probe.reliable_attempt absent
path_generated=false
safe_to_control=false
robot_control_executed=false
delivery_success=false
route_execution_success=false
hil_pass=false
```

## OKR 结论

- O5：保持约 `85%`。本轮仍没有真实 external production evidence。
- O1：保持约 `93%`。本轮没有 current live HIL、safe-to-control、same-run path generation success 或 Nav2 route execution success。
- O6/O7：保持约 `93%`。本轮没有新的 current-run route/delivery/operator/production readback material 可消费。
- O3 live lane：helper 合同与单测推进，但最新 live artifact 停在 managed runtime / partial material 层。
- KR：不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮证明：

- helper 支持 BEST_EFFORT 与 RELIABLE `/scan` attempt 合同；
- timeout 语义在单测中被锁定；
- 真实板当前复验停在 `partial_runtime_in_progress`，没有形成最新 canonical 双 attempt proof。

本轮不证明：

- `/scan_sample_observed=true`；
- `map_to_odom=true`；
- `path_generated=true`；
- route execution success；
- safe-to-control；
- HIL pass；
- delivery success；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- 板端 managed runtime / ROS2 可用性出现漂移，导致最新 artifact 未进入 `/scan` attempt 层。
- 双 QoS timeout 的首次现场事实不能作为最终 canonical artifact 单独计分，因为返工后未稳定复现。
- `path_generated=false`、`map_to_odom=false` 和 no-motion proof 边界继续阻塞 O6/O7 current-run material consumption。

## 下一轮建议

下一轮先恢复板端 managed runtime / ROS2 source 后的稳定可用性，确保 `nav2_lifecycle_latest.json` 能重新进入 `/scan` attempt 层；再复验 BEST_EFFORT / RELIABLE attempt 的 timeout 语义。不要继续修改 QoS 合同，也不要回到 O5 support-only packet。

# O3 Scan Long Window Reliable Probe Side2Side Check

## 验收对象

- Sprint: `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/`
- Sprint type: `epic`
- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`

## 对照口径

本轮原始验收口径：

- 新增 RELIABLE / VOLATILE `/scan` subscription attempt。
- 保留 BEST_EFFORT / sensor_data attempt。
- 用真实板 `--timeout-s 18` 复跑 no-motion helper。
- 若仍无 sample，artifact 必须区分 BEST_EFFORT 与 RELIABLE attempt，不能只复述上一轮 `/scan_qos_or_window_timeout`。
- Safety/delivery/HIL 字段必须继续 false。

## 实际对照结果

通过项：

- 代码已新增 BEST_EFFORT 与 RELIABLE attempt 合同。
- `onboard/tests/test_nav2_runtime_proof_helper.py` 已覆盖双 attempt、QoS 参数、RELIABLE success timing、双 timeout classification 和 timeout 语义对齐。
- 本地验证通过 `py_compile` 与 targeted unittest。
- 本地无 ROS 环境按预期 fail-closed 并落盘 artifact。
- 首次真实板长窗口运行曾进入 `/scan` 双 attempt 层，分类收敛到 `/scan_reliable_and_best_effort_timeout`，说明问题不是单纯 BEST_EFFORT 选择错误。

未通过项：

- 返工后最新 canonical live artifact 被现场更前置状态覆盖为 `partial_runtime_in_progress`。
- `--managed-timeout-s 60` retry 仍没有进入 `/scan` attempt 层，`proof.localization_signal_freshness["/scan"].probe.boundary=not_evaluated`。
- 因此最终留档不能把双 QoS attempt 现场证据作为最新 canonical proof。

## 当前 live artifact 状态

Canonical live artifact:

- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.raw.json`
- `status=partial_runtime_in_progress`
- `evidence_type=partial_runtime_material`
- `/scan.probe.boundary=not_evaluated`
- `path_generated=false`
- safety fields 全部 false

Retry artifact:

- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.retry_managed60.raw.json`
- 同样停在 `partial_runtime_in_progress`
- 没有 `probe.best_effort_attempt`
- 没有 `probe.reliable_attempt`

Partial backup:

- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.partial_runtime.raw.json`

## 验收结论

本轮接受为 O3/O1 supporting implementation + diagnostic progress，但不接受为 current live `/scan` sample proof、same-run path proof 或 route execution proof。

不调整 O1/O5/O6/O7 百分比，不归档 KR。

## 下一轮建议

下一轮不要继续改 QoS 合同。应先恢复板端 managed runtime / ROS2 可用性，并确认 `nav2_lifecycle_latest.json` 能重新进入 `/scan` attempt 层；之后再复验 BEST_EFFORT / RELIABLE attempt 的 `timed_out` 与 `sample_timing.timed_out` 是否一致。

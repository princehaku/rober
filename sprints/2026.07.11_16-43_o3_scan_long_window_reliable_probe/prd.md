# O3 Scan Long Window Reliable Probe PRD

## 用户问题

普通用户最终只关心小车能否沿固定路线安全送达。当前路线生成链路被 `/scan` sample 观测阻断，导致 `/amcl_pose`、dynamic `map->odom` 和 same-run `path_generated=true` 都无法证明。

## 产品目标

本轮不追求运动和送达，而是把路线生成前置 blocker 做成可复核、可行动的现场证据。产出应能回答：

1. 长窗口是否能收到 LaserScan sample；
2. BEST_EFFORT 与 RELIABLE subscription 在当前 publisher QoS 下的行为是否不同；
3. 若仍失败，下一步应查 QoS/window、DDS timing，还是 LiDAR driver endpoint-only/no-sample。

## 范围

必须做：

- 扩展 `o10_amcl_nav2_runtime_proof.py` 的 `/scan` child probe，使 artifact 保留 BEST_EFFORT attempt 和 RELIABLE attempt 的对照结果。
- 运行本地 fail-closed 与目标单测。
- 真实板可达时用 `--timeout-s 18` 复跑 no-motion helper 并拉回 artifact。
- 更新 `docs/navigation/` 中的证据读取说明。
- 写入 `tech-done.md`，记录实际改动、验证结果、artifact 关键字段、失败定位和剩余风险。

不做：

- 不改 O5 cloud relay、O6 archive、O7 workstation；
- 不改硬件接线、串口、WAVE ROVER 或 vendor docs；
- 不执行运动控制；
- 不提升 OKR 百分比，除非出现 same-run path generation 或更强 live material。

## 关键验收字段

Artifact 至少要能读出：

- `/scan.topic_type`
- `/scan.publisher_inventory.publisher_count`
- `/scan.publisher_inventory.publisher_nodes`
- `/scan.endpoint_inventory.endpoint_qos_profiles`
- `/scan.probe.attempts[*].qos_profile`
- `/scan.probe.attempts[*].reliability`
- `/scan.probe.attempts[*].sample_timing.sample_count`
- `/scan.probe.attempts[*].timed_out`
- `/scan.probe.classification`
- `/amcl_pose`
- `map_to_odom`
- `path_generated`
- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `route_execution_success=false`
- `hil_pass=false`

## 成功定义

强成功：真实板 artifact 出现 `/scan_sample_observed`，并保留 sample timing。

可接受成功：真实板 artifact 未收到 sample，但通过 BEST_EFFORT / RELIABLE 对照把失败从泛化 `/scan_qos_or_window_timeout` 收敛到更具体 root cause。

失败：没有新 attempt 对照、没有 artifact、没有目标单测，或误把 no-motion proof 扩大为运动/HIL/delivery proof。

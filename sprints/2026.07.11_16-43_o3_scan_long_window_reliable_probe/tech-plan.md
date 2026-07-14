# O3 Scan Long Window Reliable Probe Tech Plan

## 方案

本轮在上一轮 `/scan` endpoint inventory 的基础上做最小但实质的 artifact 合同扩展：child probe 先保留现有 BEST_EFFORT / sensor_data attempt，再新增 RELIABLE / VOLATILE subscription attempt。真实板运行时使用更长 `--timeout-s 18`，让 artifact 可以区分窗口过短、QoS 不匹配、DDS endpoint timing 和 LiDAR driver endpoint-only/no-sample。

## 文件范围

Planning 阶段主节点已新增：

- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/pre_start.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/prd.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/tech-plan.md`

Implementation 阶段允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/tech-done.md`
- `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/*`

禁止修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5 relay / cloud production readiness 代码
- O6 archive / readback schema
- O7 workstation UI
- WAVE ROVER、UART、串口、引脚、电压、波特率、机械或 vendor docs
- 其他 sprint 目录

## 接口影响

`o10_amcl_nav2_runtime_proof.py` JSON 只允许 additive / backward-compatible 变化。建议在现有 `/scan` proof 下新增或扩展：

- `probe.attempts[*].requested_qos_profile`
- `probe.attempts[*].sample_timing`
- `probe.attempts[*].reliability`
- `probe.attempts[*].durability`
- `probe.best_effort_attempt`
- `probe.reliable_attempt`
- `probe.classification`

分类要求：

- 如果任一 attempt 收到 sample，classification 应进入 `/scan_sample_observed` 或等价更具体成功值。
- 如果 BEST_EFFORT 失败但 RELIABLE 成功，必须能从 artifact 看出 QoS mismatch。
- 如果两个 attempt 都失败但 publisher endpoint 仍存在，必须输出比泛化 timeout 更可执行的 classification，例如 `/scan_publisher_visible_but_no_sample`、`/scan_reliable_and_best_effort_timeout` 或同等含义字段。
- Safety fields 必须继续固定 false。

## 实施步骤

1. 读取 `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/live_o10_scan_endpoint_timing_inventory.raw.json`，确认上一轮 publisher QoS 与 timeout 事实。
2. 在 child rclpy probe 中新增 RELIABLE / VOLATILE attempt，并保留 BEST_EFFORT / sensor_data attempt。
3. 每个 attempt 独立记录 subscription created、sample wait start、sample_count、first_sample_latency、last_sample_stamp、timed_out 和 error。
4. 调整分类函数，使长窗口和 RELIABLE/BEST_EFFORT 对照不会继续只落到上一轮的泛化 timeout。
5. 更新目标单测，覆盖 BEST_EFFORT fail / RELIABLE pass、双 attempt timeout、sample observed、false safety fields。
6. 更新导航文档，说明 16:43 artifact 的读取顺序和 proof boundary。
7. 本地运行 py_compile、targeted unittest 和 local fail-closed。
8. 真实板可达时 scp helper，运行 `--timeout-s 18` no-motion helper，拉回 live artifact。
9. 写 `tech-done.md`。

## 验收命令

Implementation owner 必须运行并记录：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/local_o10_scan_long_window_reliable_probe.raw.json
```

本地 Mac 没有 ROS 时允许 exit `2`，但必须 fail-closed 并落盘 artifact。

真实板可达时必须运行：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/live_o10_scan_long_window_reliable_probe.raw.json
```

```bash
rg -n "reliable|best_effort|requested_qos_profile|sample_timing|/scan_sample_observed|/scan_reliable|safe_to_control=false|delivery_success=false|path_generated|map_to_odom" \
  sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py
```

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe
```

Product closeout 验收命令：

```bash
git diff --check -- \
  OKR.md \
  docs/process/okr_progress_log.md \
  sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe
```

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O5，约 `~85%`。
- 本 sprint 是否针对该最低 Objective：否。
- 理由：O5 当前缺真实 external production evidence；继续本地 readiness、probe、packet、checklist 或 wrapper 会重复消费同一外部生产证据 blocker，且现有合同已固定 `okr_credit_allowed=false`。本轮选择 O3/O1 live no-motion lane，是因为它能在当前环境中继续推进 current-run path generation 的前置事实链。
- final.md 收口时需复核：若仍没有 `/scan_sample_observed`、`map_to_odom=true`、`path_generated=true` 或外部生产证据，不调整 O1/O5/O6/O7 百分比，不归档 KR。

## 风险

- 真实板不可达时只能得到 local fail-closed，不能声明 live no-motion proof。
- RELIABLE attempt 可能仍无 sample；若两个 attempt 都超时，需要下一轮查 LiDAR driver publish loop、DDS discovery timing 或 launch/lifecycle。
- 即便 `/scan_sample_observed=true`，`/amcl_pose`、`map_to_odom` 和 path generation 仍可能继续 blocked。
- 本轮禁止把 no-motion diagnostic proof 夸大为 HIL、safe-to-control、route execution 或 delivery success。

## 输出要求

子 agent 必须返回：

1. 实际改动的文件列表；
2. 验证命令输出结果；
3. live/local artifact 关键字段，尤其是 BEST_EFFORT 与 RELIABLE attempt 对照、classification、`/amcl_pose`、`map_to_odom`、`path_generated` 和 false safety fields；
4. 失败定位；
5. 剩余风险和下一条现场执行命令。

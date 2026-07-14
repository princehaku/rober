# O3 Scan Endpoint Timing Inventory Tech Plan

## 方案

本轮从上一轮 live artifact 的新 blocker 出发：`/scan` topic type 可见、child Python `rclpy` import 成功，但 child probe 等样本超时，CLI fallback 也 timeout。因此方案不再修旧主进程 ImportError，而是给 helper 增加 LiDAR publisher、sample timing 和 endpoint inventory。

Implementation owner 需要在真实板或等价 ROS Humble runtime 中回答这些问题：

- managed runtime 是否启动了 LiDAR/scan publisher 相关 launch、node 或 lifecycle。
- `/scan` publisher endpoint 是否存在，publisher count 是否大于 0。
- publisher node、topic type、endpoint QoS profile 与 probe requested QoS 是否匹配。
- child probe 是否完成 import、node init、subscription created、sample wait start。
- 在 bounded window 内是否收到 sample，first sample latency 和 sample count 是多少。
- timeout 是 publisher 缺失、runtime 未启动、QoS/window 问题，还是 child probe import 后等待样本超时。

## 文件范围

本 planning 阶段允许改动且已限定为：

- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/pre_start.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/prd.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/tech-plan.md`

后续 implementation 阶段建议允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/tech-done.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/*`

禁止修改：

- `OKR.md`
- O5 relay / cloud production readiness 代码
- O6 archive / readback schema
- O7 workstation UI
- WAVE ROVER、UART、串口、引脚、电压、波特率、机械或 vendor docs
- 其他 sprint 目录

## 接口影响

O10 helper JSON 只允许 additive / backward-compatible 变化。建议新增或扩展：

- `proof.localization_signal_freshness["/scan"].publisher_inventory`
- `proof.localization_signal_freshness["/scan"].endpoint_inventory`
- `proof.localization_signal_freshness["/scan"].sample_timing`
- `proof.localization_signal_freshness["/scan"].managed_runtime_scan_status`
- `proof.localization_signal_freshness["/scan"].probe.import_check`
- `proof.localization_signal_freshness["/scan"].probe.child_runtime`
- `proof.localization_signal_freshness["/scan"].probe.classification`

建议字段至少包含：

- `topic_visible`
- `topic_type`
- `publisher_count`
- `publisher_nodes`
- `endpoint_qos_profiles`
- `requested_qos_profile`
- `managed_runtime_started`
- `lidar_runtime_started`
- `probe_window_sec`
- `sample_wait_started_at`
- `first_sample_latency_ms`
- `sample_count`
- `last_sample_stamp`
- `last_sample_received_at`
- `child_import_ok`
- `child_subscription_created`
- `classification`
- `blocked_reason`

Root cause 分类必须可执行，优先使用这些稳定值：

- `/scan_no_publisher`
- `/scan_lidar_runtime_not_started`
- `/scan_publisher_visible_but_no_sample`
- `/scan_qos_or_window_timeout`
- `/scan_rclpy_child_timeout_after_import`
- `/scan_sample_observed`

所有 safety fields 必须保持：

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `route_execution_success=false`
- `hil_pass=false`

## 实施拆分

1. `robot-algorithm-engineer` 读取上一轮 live artifact，锁定新 blocker 为 `/scan_rclpy_child_timeout_after_import`。
2. 在 helper 中新增 `/scan` endpoint inventory 采集，使用 ROS2 topic info / endpoint introspection / bounded child probe 的组合。
3. 在 child rclpy probe 中记录 sample timing，不只记录 observed/timeout。
4. 新增分类函数，把 no publisher、LiDAR runtime not started、visible no sample、QoS/window timeout、child timeout after import 和 sample observed 分开。
5. 更新 helper 单测，覆盖每个分类、additive field shape、local fail-closed 和 false safety fields。
6. 更新导航文档，说明本 sprint artifact 的读取顺序和证据边界。
7. 本地跑 fail-closed 验证；真实板可达时跑 live no-motion helper 并拉回 artifact。
8. 写 `tech-done.md`，记录实际改动、验证输出、artifact 关键字段、失败定位和剩余风险。

## 验收命令

后续 implementation owner 必须运行并记录：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/local_o10_scan_endpoint_timing_inventory.raw.json
```

本地 Mac 没有 ROS 时允许 exit 2，但必须 fail-closed 且落盘 artifact。

真实板可达时必须运行：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/live_o10_scan_endpoint_timing_inventory.raw.json
```

```bash
rg -n "publisher_inventory|endpoint_inventory|sample_timing|/scan|classification|safe_to_control=false|delivery_success=false|path_generated|map_to_odom" \
  sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory
```

本 planning 阶段验收命令为：

```bash
git diff --check -- sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/pre_start.md sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/prd.md sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/tech-plan.md
```

## OKR 最低优先级核对

当前 `OKR.md` 4.1 中最低主 Objective 是 O5，约 `~85%`。O1、O6、O7 当前均约 `~93%`。O3 是归档 Objective 的现场验证临时 lane，不单独计分。

本 sprint 不直接针对最低主 Objective O5。理由如下：

- O5 当前缺口是真实 external production evidence，包括真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实手机/browser evidence。
- 最近 O5 已连续 fail-closed 在缺真实 external production evidence；cutover readiness packet 固定 `okr_credit_allowed=false`，field execution / external evidence pivot 记录 `blocked_missing_new_field_execution_material`。
- 继续 O5 readiness、probe、checklist 或 support-only packet 会重复消费同一 external production blocker，不能产生主 OKR 增量。

本 sprint 选择 O3/O1 supporting lane 的理由：

- 最新 `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/final.md` 已把旧 ImportError 推进为新 blocker `/scan_rclpy_child_timeout_after_import`，这是当前环境可继续推进的 live no-motion 事实链。
- `/scan` publisher/sample timing 是 `/amcl_pose`、dynamic `map->odom` 和 same-run `path_generated=true` 的前置条件。
- 一旦后续生成 current-run path 或 route material，O6/O7 才能消费新的 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record 或 operator confirmation。

收口规则：

- 没有 `path_generated=true`，不调整 O1/O5/O6/O7 主 OKR 百分比。
- 没有真实 external production evidence，不回头给 O5 support-only 工作计分。
- 本轮不得归档 KR，除非后续 artifact 同时满足对应 KR 的明确验收证据。

## 风险

- Endpoint 可见但没有 sample，可能继续需要 QoS/window 或 DDS discovery 返工。
- LiDAR runtime not started 可能指向 launch/lifecycle 配置，但本轮不允许直接改硬件或 vendor 事实。
- Scan sample observed 后仍可能卡在 `/amcl_pose`、initial pose、map quality、TF source 或 planner readiness。
- 真实板不可达时只能得到 local fail-closed，不能声明 live no-motion proof。
- 任何 `safe_to_control=true`、`delivery_success=true`、`route_execution_success=true` 或 `hil_pass=true` 都必须视为验收失败，除非 CEO 另行提供真实安全验收材料。

## 输出要求

后续 implementation owner 必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. Artifact 关键字段，尤其是 publisher inventory、endpoint QoS、sample timing、classification、`/amcl_pose`、`map_to_odom`、`path_generated` 和 false safety fields。
4. 失败定位，如仍 blocked。
5. 剩余风险和下一条现场执行命令。

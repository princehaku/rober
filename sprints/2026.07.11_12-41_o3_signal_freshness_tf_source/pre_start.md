# O3 Signal Freshness TF Source Pre Start

## sprint_type

`sprint_type: epic`

## 上轮未完成项

上一轮 `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/` 已证明 real-board direct helper 越过旧 `/initialpose` verbose info 卡点，但仍 fail-closed：

- `/scan_once_not_observed`
- `/amcl_pose_once_not_observed`
- `map_to_odom_not_observed`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `localization_not_ready_for_path_generation`

O5 仍是 `OKR.md` 当前最低 Objective，约 `85%`，但最近 O5 sprint 已收口为 `blocked_missing_new_field_execution_material` / `no_real_production_external_evidence`，继续做 readiness、wrapper、probe readback 或 cutover packet 不允许计主 OKR 增量。

## 本轮目标

本轮继续 O3 real-board no-motion lane，目标不是再次追 path success，而是把 `/scan`、`/amcl_pose`、`/odom`、`/tf`、`/tf_static` 的单条 probe 耗时、观测状态、最近时间戳、freshness、publisher/subscriber 和 dynamic/static TF source 分层落盘。

若本轮不能生成 path，也必须输出比 `map_to_odom_not_observed` 更具体的 root cause：是 sensor sample stale、topic 无 publisher、AMCL 无输出、dynamic TF 缺失、static-only 被误判，还是 CLI 采样窗口/超时问题。

## Owner

- 主责 owner：`robot-algorithm-engineer`
- 协作 owner：暂不需要并行。文件范围集中在 O10 helper、对应测试和导航文档，单 owner 闭环更快。

## 验收口径

- 必须新增或扩展可回读字段，记录 signal freshness / TF source 分层事实。
- 必须保持 no-motion safety flags：`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
- 若真实板 SSH 可达，必须跑 live helper 或 preflight 并把 raw artifact 放入本 sprint `artifacts/`。
- 若仍 fail-closed，不得上调 OKR 百分比，只能记录新 root cause。

## 风险边界

本轮不做底盘运动，不改 WAVE ROVER / UART / hardware 参数，不触碰 O5/O6/O7 wrapper/readback/UI。即使拿到 `map_to_odom=true`，也不等于 delivery success、HIL pass 或 safe-to-control。

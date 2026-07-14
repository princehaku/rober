# O3 Scan Probe QoS Repair Pre Start

## sprint_type

`sprint_type: epic`

## 上轮结论

上一轮 `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/` 已完成 signal freshness / TF source 分层。真实板 artifact 证明 `/scan.topic_type=sensor_msgs/msg/LaserScan`、`/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`、`/odom` fresh、`/tf` 与 `/tf_static` topic type 可见，但 `/scan` once probe timeout、`/amcl_pose` once probe timeout，最终仍 `map_to_odom=false`、`path_generated=false`。

## 本轮目标

本轮继续现场 O3 no-motion lane，目标是先修 `/scan` once probe timeout 的诊断和采样路径，再复验 `/amcl_pose` 与 AMCL dynamic `map->odom`。本轮不执行运动控制，不触发底盘 UART，不声明 HIL、safe-to-control 或 delivery success。

## OKR 选择理由

O5 仍是当前最低主 Objective，约 `~85%`，但最近 O5 external evidence lane 已因没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence fail-closed。继续 O5 readiness、wrapper、probe 或 checklist 属于 support-only，`okr_credit_allowed=false`，不能提升主 OKR。

因此本轮选择现场 O3 lane：它虽然是归档 Objective 的临时激活 lane，但直接服务 O1 current same-run path generation、O6/O7 live route/material 消费链和后续 delivery/operator material。当前同一 blocker 已连续推进 1 轮，本轮是第 2 轮允许继续定位；若本轮仍停在同一 `/scan` / AMCL probe timeout 且无新事实，下一轮必须切换或升级。

## Owner

- 主责 owner：`robot-algorithm-engineer`
- 协作边界：Robot Software / Hardware 不并行启动。本轮不改硬件参数、不改 vendor 事实、不碰 WAVE ROVER / UART / 电压 / 引脚。

## 验收口径

- `proof.localization_signal_freshness["/scan"]` 必须比上一轮更具体，至少区分 topic type、publisher/endpoint、QoS/CLI 尝试、attempt 列表、timeout 与是否观测到消息。
- 真实板 artifact 必须落到 `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/live_o10_scan_qos_repair.raw.json`，即使 fail-closed 也要结构化给出 root causes。
- 若 `/scan` 修复后仍拿不到 `/amcl_pose` 或 `map->odom`，必须保留 false safety fields 并给出下一步 AMCL/TF blocker。
- 本轮不得把 support-only、readback-only 或 historical comparator 计为 OKR 百分比提升。

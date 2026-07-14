# O3 Scan Long Window Reliable Probe Pre Start

## Sprint Type

sprint_type: epic

## 背景

当前 `OKR.md` 4.1 中最低主 Objective 是 O5，约 `~85%`。O5 仍缺真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实手机/browser evidence。最近 O5 readiness、probe、cutover packet 都已固定 `okr_credit_allowed=false`，继续做本地 support-only 工作不会产生主 OKR 增量。

本轮因此继续临时激活的 O3/O1 live no-motion lane。上一轮 `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/` 已证明 `/scan` topic type 与 `lidar_driver` publisher endpoint 可见，publisher QoS 为 `RELIABLE` / `VOLATILE`，但 helper 以 `BEST_EFFORT` / `VOLATILE` 等待 `2.2s` 后 `sample_count=0`，classification 为 `/scan_qos_or_window_timeout`。

## 本轮目标

把 `/scan` blocker 从“publisher 可见但窗口内无 sample”推进为可执行分叉：

- 若长窗口 `--timeout-s 18` 后收到 sample，产出 `/scan_sample_observed` 和 sample timing 证据。
- 若长窗口仍无 sample，新增 RELIABLE subscription attempt，并保留 BEST_EFFORT attempt，区分 QoS mismatch、窗口过短、DDS endpoint timing 与 LiDAR driver endpoint-only/no-sample 行为。
- 继续固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`，不做运动执行。

## Owner

- Implementation owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`
- 主节点职责：计划、派单、验收、留档和汇总。

## 连续 Blocker 核对

最近两轮 root cause：

- `2026.07.11_14-42_o3_rclpy_scan_runtime_repair`: `/scan_rclpy_child_timeout_after_import`
- `2026.07.11_15-44_o3_scan_endpoint_timing_inventory`: `/scan_qos_or_window_timeout`

本轮不是重复修旧 main-process rclpy ImportError，也不是重复消费 O5 external production blocker；本轮必须新增长窗口和 RELIABLE/BEST_EFFORT 对照证据，避免第三轮只复述同一 `/scan_qos_or_window_timeout`。

## 验收口径

接受：

- `/scan_sample_observed=true`；或
- artifact 明确给出 BEST_EFFORT 与 RELIABLE attempt 的各自 sample_count、timeout、classification，并能把失败收敛到 QoS/window、DDS timing 或 driver endpoint-only/no-sample。

不接受：

- 只复述上一轮 `publisher_count=1`、`sample_count=0`、`/scan_qos_or_window_timeout`；
- 只做 checklist、wrapper、surface 或 handoff；
- 未运行目标单测或未落盘 artifact；
- safety/delivery/HIL 字段被误置为 true。

## 风险边界

本轮证据仍是 no-motion localization/path 前置诊断，不证明 current live HIL、safe-to-control、Nav2 route execution、delivery success、production cloud 或 O5 external production readiness。

# O3 Rclpy Scan Runtime Repair Side2Side Check

## 验收对象

- Sprint: `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/`
- Live artifact: `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json`
- 对照文档：`pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`

## 用户价值和产品北极星

用户价值仍是把固定路线送垃圾从历史材料推进到当前现场可生成路线。产品北极星是普通手机用户一键发车后，小车能安全、可验证地完成垃圾投递，并留下可复盘证据。

本轮只验证 no-motion `/scan` runtime 诊断是否比上一轮更具体；它不等于路线生成、导航执行、HIL、safe-to-control 或 delivery success。

## PRD / Tech Plan 对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 产出新的 live no-motion artifact | 通过 | `live_o10_rclpy_scan_runtime_repair.raw.json` 已由真实板 helper 拉回。 |
| `/scan` rclpy ImportError 是否消除 | 通过 | `/scan.probe.best_attempt.runtime=ros_sourced_child_python`，`import_check.ok=true`，旧 `librcl_action.so` / `_rclpy_pybind11` ImportError 已从 scan probe 上消除。 |
| `/scan` frame 是否 observed | 未通过，fail-closed | `/scan.probe.observed=false`，root cause 为 `/scan_rclpy_child_timeout_after_import`。 |
| CLI fallback 是否证明 scan 可读 | 未通过，fail-closed | `cli_sensor_data_echo_once` 与 `cli_default_echo_once` 均 timeout。 |
| AMCL / TF / path 是否达成 | 未通过，fail-closed | `/amcl_pose=false`、`map_to_odom=false`、`path_generated=false`。 |
| Safety fields 是否保持 false | 通过 | `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。 |

## OKR 映射和方向判断

- O1：继续，但不加分。本轮把 root cause 从主进程 rclpy ImportError 收敛到 child rclpy import 成功后的 `/scan_rclpy_child_timeout_after_import`，属于 O1/O3 supporting 诊断进展；仍没有 current same-run path generation success、Nav2 route execution success 或 HIL pass。
- O5：暂停 support-only 追分。O5 仍约 `~85%`，本轮没有 production HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O6/O7：等待 current-run material。本轮没有新的 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record、operator confirmation 或 production readback。

方向判断：继续 O3/O1 live localization/path 前置链路，下一轮指向 LiDAR publisher/sample timing/endpoint inventory；不调整 O5/O1/O6/O7 百分比，不归档 KR。

## KR 拆解、更新或历史归档

- 本轮不归档任何 KR。
- O1 current same-run path generation 仍 blocked：`path_generated=false`。
- O6/O7 current-run material 仍 blocked：没有可消费的新路线或 delivery/operator material。
- O5 production evidence 仍 blocked：没有新的真实 external production evidence。

已完成 KR 历史记录位置：无新增；本轮只在 `final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 记录诊断进展与剩余风险。

## 核心抓手与责任 Engineer

- 本轮核心抓手：将 `/scan` rclpy probe 迁移到 ROS-sourced child Python，确认 old import failure 是否仍阻塞 scan probe。
- 主责 Engineer：`robot-algorithm-engineer`。
- Product closeout 责任：确认验收边界、OKR 不加分、不归档，并写入 sprint 收口文档。

## 风险、阻塞和证据链缺口

- `/scan` topic type 可见和 `import_check.ok=true` 不能证明 scan frame observed。
- 新 blocker 是 `/scan_rclpy_child_timeout_after_import`，优先查 LiDAR publisher 是否持续发布 sample、endpoint inventory、QoS/timing/window，而不是继续修旧的 main-process rclpy ImportError。
- `/amcl_pose=false`、`map_to_odom=false`、`path_generated=false` 表明 localization/path chain 仍未 ready。
- `safe_to_control=false`、`delivery_success=false`、`hil_pass=false` 继续阻止任何运动、HIL 或送达成功声明。

## 验收结论

本轮通过 Product closeout：有新诊断进展，旧 `/scan` rclpy ImportError 已从 scan probe 上消除；但 `/scan` 未 observed，路径生成和安全/送达证明均未达成。

结论必须保持：不调整 O5/O1/O6/O7 百分比，不归档 KR，不声明 `/scan` observed、path success、HIL、safe-to-control、delivery success 或 production proof。

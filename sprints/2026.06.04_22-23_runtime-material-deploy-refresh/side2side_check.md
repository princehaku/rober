# Side-To-Side Check: Runtime Material Deploy Refresh

## sprint_type

sprint_type: epic

## 对照验收

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 确认安全 reload/service 路径 | 通过 | 精确匹配旧 PID `30042`，SIGTERM 后由 `trashbot-upper-robot-api.service` 拉起 Main PID `38154`；有备份目录 `/root/rober/runtime/deploy_backups/20260604T221619+0800`。 |
| 部署 upper refresh route 并解除 405 | 通过 | live `POST /api/radar/scan-proof/refresh` HTTP 200；`GET /api/radar/status` 已出现 `scan_proof_refresh` control。 |
| 解除 systemd ROS logging blocker | 通过 | collector 增加 `HOME/USER/LOGNAME/ROS_HOME/ROS_LOG_DIR` 兜底；最新 artifact 显示 `ros2_available=true`、`ros2_cli_check.ok=true`。 |
| 取得 fresh `/scan` runtime proof | 未通过 | refresh result `proof_state=blocked_or_not_observed`；剩余 blocker 是 `upper_api_scan_not_proven`，且 `/scan`、`/lidar/raw_packet`、`base_link -> laser_frame` TF 未发布。 |
| latest artifact 回读 | 部分通过 | `GET /api/radar/scan-proof/latest` HTTP 200 且 artifact loaded，但内容不是 fresh `/scan` 成功材料。 |
| PC fail-closed 展示 blocker | 通过软件护栏 | Full-Stack 101 tests/build/lint 通过，UI/API 展示 upper `not_proven` 和 blockers；未做 live smoke。 |
| 不触发底盘运动 | 通过 | Hardware 只读复核 `safe_to_control=false`、`robot_control_executed=false`、`hil_pass=false`；未调用 `/api/base/manual`、`/cmd_vel` 或运动命令。 |
| OKR 是否可涨产品分 | 不涨分 | O3/O7 缺 fresh runtime material；O8 可按治理进展上调到约 44%。 |

## 需求满足度

- 满足：解除现场 upper refresh route HTTP 405；解除 systemd ROS logging env blocker；把 blocker 继续收敛到真实 LiDAR ROS2 topic/TF 未发布；PC 能 fail-closed 展示 upper blockers。
- 未满足：没有 fresh `/scan` once/hz、raw packet、TF 或后续 SLAM/map/AMCL/Nav2 材料。

## Evidence Type 判定

| 材料 | Evidence type | Product 判定 |
| --- | --- | --- |
| 本地 upper unittest / compileall / diff-check | `software_guard` | 不涨 O3/O7。 |
| PC 101 tests/build/lint 和 blocker display | `software_guard` | 不涨 O7。 |
| live route HTTP 405 解除 | `deployment_progress` / `blocked_with_root_cause` | 可支撑 O8，不等于 fresh runtime。 |
| refresh HTTP 200 但 proof blocked | `blocked_with_root_cause` | 不涨 O3/O7。 |
| Hardware 只读安全复核 | `safety_boundary_evidence` | 不涨 O1；防止误触 HIL/ACK。 |

## 反思

本轮比上一轮前进了两步：HTTP 405 已解除，服务路径已确认，ROS2 logging environment 也不再遮蔽 collector。正确收口仍不是“fresh scan proof 成功”，而是“route 和 ROS2 CLI 可执行，但真实 `/scan`、raw packet 和 TF 未发布”。下一轮必须启动或修复 LiDAR ROS2 runtime/topic/TF，再谈 SLAM/map/AMCL/Nav2。

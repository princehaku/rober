# Side-To-Side Check: Runtime Material Deploy Refresh

## sprint_type

sprint_type: epic

## 对照验收

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 确认安全 reload/service 路径 | 通过 | 精确匹配旧 PID `30042`，SIGTERM 后由 `trashbot-upper-robot-api.service` 拉起 Main PID `38154`；有备份目录 `/root/rober/runtime/deploy_backups/20260604T221619+0800`。 |
| 部署 upper refresh route 并解除 405 | 通过 | live `POST /api/radar/scan-proof/refresh` HTTP 200；`GET /api/radar/status` 已出现 `scan_proof_refresh` control。 |
| 取得 fresh `/scan` runtime proof | 未通过 | refresh result `proof_state=blocked_or_not_observed`，blocker 为 `ros2_command_unavailable` 和 `upper_api_scan_not_proven`。 |
| latest artifact 回读 | 部分通过 | `GET /api/radar/scan-proof/latest` HTTP 200 且 artifact loaded，但内容不是 fresh `/scan` 成功材料。 |
| PC fail-closed 展示 blocker | 通过软件护栏 | Full-Stack 101 tests/build/lint 通过，UI/API 展示 upper `not_proven` 和 blockers；未做 live smoke。 |
| 不触发底盘运动 | 通过 | Hardware 只读复核 `safe_to_control=false`、`robot_control_executed=false`、`hil_pass=false`；未调用 `/api/base/manual`、`/cmd_vel` 或运动命令。 |
| OKR 是否可涨产品分 | 不涨分 | O3/O7 缺 fresh runtime material；O8 可按治理进展上调到约 44%。 |

## 需求满足度

- 满足：解除现场 upper refresh route HTTP 405；把 blocker 从部署缺口收敛到 ROS2 command/runtime environment；PC 能 fail-closed 展示 upper blockers。
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

本轮比上一轮前进了一步：HTTP 405 已解除，服务路径也被确认。正确收口不是“refresh 成功”，而是“route 可执行但 ROS2 command unavailable”。下一轮必须修 runtime environment 或把 collector 放进正确 ROS2 容器内执行，再谈 SLAM/map/AMCL/Nav2。

# Pre Start: O9 Fresh Scan Proof Runtime

## sprint_type

sprint_type: epic

## 本轮目标

本 sprint 面向 O9/O3/O7：用 live upper ROS2/LiDAR runtime 消除或收窄 fresh scan proof blocker，让 `POST /api/radar/scan-proof/refresh` 不再停在不可解释的 `not_proven` 状态，并形成可给下一步 SLAM `/map`、AMCL、Nav2 使用的雷达 runtime 证据边界。

- O9：短周期真实材料破局战役，目标是拿到或精确收窄 fresh `/scan` proof。
- O3：建图、定位、Nav2 与固定路线，目标是证明 LiDAR ROS2 topic/TF runtime 是否真实可用。
- O7：PC 运营调试平台，目标是支撑 PC/operator readback 能看到 fresh proof 或明确 blocker；本轮不扩大 UI。

## 最近 2 轮 blocker scan

| Sprint | 已知 blocker | 本轮处理 |
| --- | --- | --- |
| `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/final.md` | live 8787 未部署 refresh route，`POST /api/radar/scan-proof/refresh` 返回 HTTP 405。 | 不重复消费。上一轮已证明该 blocker 被解除，本轮不再把 HTTP 405 作为主要目标。 |
| `sprints/2026.06.04_22-23_runtime-material-deploy-refresh/final.md` | refresh route 已 HTTP 200，但 proof 仍 `blocked_or_not_observed`；当前 blocker 是 `ros2_command_unavailable` 历史风险、`upper_api_scan_not_proven`、missing `/scan` topics、missing `/lidar/raw_packet`、missing TF。 | 本轮聚焦 live ROS2/LiDAR runtime：确认 `ros2_command_unavailable` 是否已消除，重点消除或收窄 `upper_api_scan_not_proven` 与 missing `/scan` topics。 |

## Owner 和协作边界

- 主责 owner：Robot Software Engineer。
- 主责范围：live upper ROS2/LiDAR driver、topic/TF runtime、scan proof collector、8787 refresh/readback、只读 smoke 和本地回归。
- 可选协作：Full-stack Software Engineer 只做 PC readback 或同源 smoke 事实补充；不扩大 UI，不新增按钮，不改产品交互。
- Product 责任：本轮只定义验收口径和证据边界，不改 `OKR.md`，不宣称 KR 完成。

## 安全边界

- 本轮不要求、不允许底盘运动。
- 本轮不要求、不允许 `/cmd_vel`、`/api/base/manual`、`T=1`、`T=13`、低速 pulse 或 HIL。
- 远端命令仅允许 read-only/status/scan smoke/refresh；如果发现 `safe_to_control=true` 或任何底盘运动入口被触发，必须停止并记录风险。
- LiDAR runtime facts 来源：`docs/vendor/VENDOR_INDEX.md` -> `docs/vendor/lidar_pkg_ros2-main/`。本轮只处理雷达 ROS2 runtime，不推断 WAVE ROVER 底盘协议。

## 进入实现条件

`prd.md` 和 `tech-plan.md` 写清用户价值、验收口径、文件范围、远端只读命令、安全边界后，即可派 Robot Software Engineer 单 owner 执行修复、复测和 `tech-done.md` 留档。

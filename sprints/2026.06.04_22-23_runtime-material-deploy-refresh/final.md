# Final: Runtime Material Deploy Refresh

## sprint_type

sprint_type: epic

## 收口结论

方向判断：**继续，但 O3/O7 产品完成度不涨分**。

本轮完成了上一轮最明确的部署抓手：上位机 `192.168.1.11:8787` 的 `POST /api/radar/scan-proof/refresh` 已从 HTTP 405 变为 HTTP 200，`/api/radar/status` 已暴露 `scan_proof_refresh` control，`/api/radar/scan-proof/latest` 可加载 artifact。部署 405 blocker 已解除。

后续又修复了 collector 在 systemd 子进程环境下缺 ROS logging 目录的问题；最新 artifact 已显示 `ros2_available=true`、`ros2_cli_check.ok=true`，说明 `ros2_command_unavailable` 已解除。但 runtime proof 仍未通过：refresh result 还是 `blocked_or_not_observed`，剩余 root cause 是 `upper_api_scan_not_proven`，并且 `/scan`、`/lidar/raw_packet`、`base_link -> laser_frame` TF 未发布。PC 侧保持 fail-closed 安全边界，未做 live smoke。因此 O3/O7 不涨分。

## OKR 进度

| Objective | 当前比例 | 本轮变化 | 说明 |
| --- | --- | --- | --- |
| O3：建图、定位、Nav2 与固定路线 | 约 73% | 不变 | 405 和 ROS logging blocker 已解除，但没有 fresh `/scan` runtime material；剩余 blocker 是无 `/scan`、无 `/lidar/raw_packet`、无 TF。 |
| O7：PC 运营调试平台 | 约 90% | 不变 | PC 展示 upper `not_proven` 和 blockers，但没有 live fresh operator workflow。 |
| O8：Epic 交付节奏与证据治理 | 约 44% | 从约 43% 小幅上调 | Epic 留档完成，部署 405 blocker 解除，root cause 收敛，并补 PC fail-closed blocker display；不叠加到 45%。 |
| O1：硬件协议可信底盘 | 约 95.5% | 不变 | 本轮只读安全复核；无 HIL、ACK、ROS feedback topics 或 `safe_to_control=true`。 |
| O2：送垃圾任务 + 电梯 assisted delivery | 约 72% | 不变 | 本轮不触达真实/受控电梯图片 manifest。 |
| O5：云中转控制面 | 约 84% | 不变 | 本轮不触达 production live material。 |
| O6：云端核心后端 | 约 82% | 不变 | 本轮不触达 production archive/runtime。 |
| O9：短周期真实材料破局战役 | 0% | 不变 | 部署 route partial 不等于 fresh runtime material，暂不计 breakthrough 完成。 |

## 已完成 KR 历史记录

- `KR-O3/O7-Deploy-Refresh-Route`：**部分完成并进入历史进展**。完成范围仅限 route 部署、405 解除、latest artifact readback 和 service/reload 路径确认；证据来源为本 sprint `tech-done.md`、Robot Software owner note 和本 `final.md`。
- `KR-O8-Repeated-Blocker-Stop`：**完成本轮收敛**。root cause 从 `upper_refresh_route_not_deployed_http_405` 收敛为 ROS logging env 缺口，再收敛为真实 LiDAR ROS2 topics/TF 未发布；下一轮不得再消费 405 或 `ros2_command_unavailable` blocker。
- `KR-O7-PC-Fail-Closed-Blocker-Display`：**作为 software guard 进入历史进展**。PC 能把 HTTP 200 但 upper `not_proven` 显示为锁定状态；不进入 O7 runtime workflow 完成归档。

历史记录位置：`docs/process/okr_progress_log.md` 的 `2026-06-04 22-23｜Runtime Material Deploy Refresh` 条目，以及本 sprint `tech-done.md` / `side2side_check.md` / `final.md`。

## 本轮反思

- 有效：先确认 service/reload 路径再精确处理旧 PID，避免盲目 kill；route 405 被解除，说明上一轮 blocker 没有被重复消费。
- 有效：PC 侧把 upper HTTP 200 但业务 not_proven 的情况显式展示，降低 operator 误判风险。
- 不足：LiDAR ROS2 runtime/topics/TF 没有随 service 进入可观测状态；collector 现在能运行 ROS2 CLI，但仍读不到 `/scan`、`/lidar/raw_packet` 或 `base_link -> laser_frame`。

## 下一步

1. Robot Software：启动或修复上位机 LiDAR ROS2 driver/topic/TF runtime，让 `/scan`、`/lidar/raw_packet` 和 `base_link -> laser_frame` 可被只读 collector 观察到。
2. Robot Software + Full-Stack：复测 PC 同源触发 deployed refresh route，确认 blocker 不再是 `upper_api_scan_not_proven`，并取得 fresh `/scan` proof。
3. 取得 fresh scan proof 后再进入 SLAM `/map`、map save/load、AMCL `/initialpose`、Nav2 消费 `/scan`+map。
4. Algorithm 继续补 O2 真实/受控电梯图片 manifest；Hardware 继续按现场安全条件准备 stop-first HIL。

## 未完成事项和风险

- 未证明 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、SLAM `/map`、AMCL、Nav2 lifecycle 或固定路线。
- 未证明 PC WASD、真实雷达 start/stop、底盘 HIL、robot ACK、`safe_to_control=true` 或 delivery success。
- 未证明真实/受控电梯图片、OpenCV field eval、受控电梯流程或手机用户验收。
- 未触达 O5/O6 production cloud、4G/公网、DB/queue、OSS/CDN 或 archive runtime。

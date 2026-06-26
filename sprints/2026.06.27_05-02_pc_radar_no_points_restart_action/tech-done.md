# PC radar no-points restart action

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏在 `雷达无新点` 状态下显示 `重启雷达`。
  - 点击后串联固定传感器代理：`radar/stop -> radar/start -> radar/scan-proof/refresh`。
  - 该动作不新增后端接口，不调用底盘、Nav2、delivery、free-roam start 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 `雷达无新点` 回归测试：确认按钮文案、stop/start/refresh/status 调用，以及 manual/Nav2/`/cmd_vel` 均未触发。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏 `重启雷达` 的边界和 live 复测结果。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism --testNamePattern "running lidar with zero fresh points|running lidar proof|stale running lidar proof"`。
  - 结果：3 个目标用例通过。
- 通过：`cd pc-tools/workstation && npm test`。
  - 结果：2 个测试文件通过，262 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
  - Vite 仍提示单个 chunk 大于 500 kB，这是既有前端体积提示。

## live 证据

- 通过 PC 7001 固定代理执行传感器级恢复：
  - `POST /api/robot-control/radar/stop`：`proxy_status=lifecycle_forwarded`、`remote_http_status=200`、`command_result.mode=command`、`executed=true`、`ok=true`、`robot_control_executed=false`。
  - `POST /api/robot-control/radar/start`：`proxy_status=lifecycle_forwarded`、`remote_http_status=200`、`command_result.mode=command`、`executed=true`、`ok=true`、`robot_control_executed=false`。
  - `POST /api/robot-control/radar/scan-proof/refresh`：`proxy_status=refresh_forwarded`、`remote_http_status=200`、`last_result_evidence_ref=o1-lidar-scan-proof-1782507626480`、`hard_dangerous_true_fields=[]`。
- 重启后 refresh 仍未恢复新雷达点：
  - `scan_once_observed=false`
  - `scan_hz_observed=false`
  - `raw_packet_once_observed=false`
  - `tf_observed=true`
  - `latest_scan_proof_fresh=false`
  - `continuity_window_status=lifecycle_not_running`
- 最终 PC summary：
  - `readback_summary.lidar.continuous_scan_status=lifecycle_not_running`
  - `lifecycle_running=false`
  - `lifecycle_state=stopped`
  - `scan_preview_point_count=0`
- SSH 清理：
  - 临时 `ros2 topic echo/hz` 采样进程已清理。
  - `lidar_driver` 临时进程已退出；剩余一个 static transform publisher。

## 剩余风险

- 本轮提供了 PC 普通用户恢复入口，但没有修复上车端雷达 runtime 维持问题。
- 下一步需要继续查 `/dev/ttyACM0`、LiDAR 供电、驱动日志和上车端 radar lifecycle start 后为什么回到 stopped。
- 摄像头仍无首帧；Nav2 仍缺 wheel raw L/R 同窗口非零；自由移动 gate ready 但本轮未发运动命令。

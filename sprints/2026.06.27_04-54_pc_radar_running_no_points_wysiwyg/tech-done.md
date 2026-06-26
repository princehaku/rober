# PC radar running no-points WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增普通雷达状态 `雷达无新点`。
  - 当雷达 lifecycle 正在运行，但 `latest_scan_proof_fresh=false`、`continuous_window_observed=false`，且当前没有 scan 点数组、点数或最近障碍距离时，普通首屏不再泛化成 `雷达待刷新`。
  - 地图 marker 和 freshness 文案同步显示：雷达驱动在运行，但当前没有读到新的雷达点；这不是地图没刷新。
- `pc-tools/workstation/src/styles.css`
  - 为 `雷达无新点` 补齐雷达卡、地图 marker、扫描范围占位的警示态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live 形态回归测试：运行中、fresh=false、0 点、无障碍距离时显示 `雷达无新点`，并确认不调用 radar start、manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `雷达无新点` 产品边界和本轮 live 证据。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism --testNamePattern "running lidar proof|stale running lidar proof|running lidar with zero fresh points|conflicting radar status|updates the map radar marker"`。
  - 结果：5 个目标用例通过。
- 通过：`cd pc-tools/workstation && npm test`。
  - 结果：2 个测试文件通过，262 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
  - Vite 仍提示单个 chunk 大于 500 kB，这是既有体积提示。

## live 证据

- PC 固定只读代理刷新雷达：
  - `POST http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787`
  - 返回：`proxy_status=refresh_forwarded`、`remote_http_status=200`、`hard_dangerous_true_fields=[]`、`last_result_evidence_ref=o1-lidar-scan-proof-1782507054469`。
  - key values：`latest_proof_status=raw_packets_parsed`、`scan_once_observed=false`、`scan_hz_observed=false`、`raw_packet_once_observed=false`、`tf_observed=true`、`lifecycle_running=true`、`latest_scan_proof_fresh=false`、`blocked_reasons=["latest_scan_proof_stale"]`。
- 刷新后 PC summary：
  - `readback_summary.lidar.status=partially_observed`
  - `continuous_scan_status=latest_proof_incomplete_while_lifecycle_running`
  - `lifecycle_running=true`
  - `latest_scan_proof_fresh=false`
  - `scan_preview_point_count=0`
  - `o3_proof_summary.scan_preview_points.length=0`
- SSH 复核：
  - `ssh root@192.168.1.11 -p 37878` 可连接。
  - `/scan`、`/lidar/raw_packet`、`/tf_static` topic 存在。
  - `lidar_driver` 进程仍在运行。
  - `ros2 topic echo --once /scan` 和 `ros2 topic echo --once /lidar/raw_packet` 在 8 秒内没有输出。

## 剩余风险

- 本轮没有修 LiDAR 驱动或硬件发布链；当前雷达问题更像 LiDAR 供电、串口数据或驱动解析/发布中断，需要继续查 `/dev/ttyACM0`、驱动日志和真实雷达供电。
- 摄像头仍是 `/dev/video1` 无首帧，不是 PC 独占。
- 自由移动 gate 仍 ready，但本轮没有发送运动命令；没有把 `safe_to_control`、`delivery_success` 或 `/cmd_vel` 打开。

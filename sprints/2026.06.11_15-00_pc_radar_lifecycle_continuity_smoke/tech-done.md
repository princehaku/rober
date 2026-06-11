# 2026-06-11 15:00 PC Radar Lifecycle Continuity Smoke

sprint_type: micro

## 实际改动

- 新增本轮真实上车证据目录：
  `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/`
- 更新文档：
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `docs/product/pc_tools_workstation.md`
  - `pc-tools/README.md`

本轮未修改 PC 产品代码、普通首屏组件/样式、onboard 产品代码、launch、vendor 文件、
硬件配置或任何运动控制代码。

## 采用资料与安全边界

硬件事实入口按项目约束读取 `docs/vendor/VENDOR_INDEX.md`，并核对：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

采用边界：

- WAVE ROVER 底盘 UART 是 UTF-8 JSON + newline framing。
- Vendor Raspberry Pi 默认串口不能外推到 Orange Pi。
- 本轮只允许 LiDAR `/dev/ttyACM0`、ROS2 `/scan`、`/lidar/raw_packet`、TF，以及
  PC proxy radar endpoints。
- 未调用 `/api/base/manual`、未发布 `/cmd_vel`、未执行 Nav2、未写 `/dev/ttyS5`，
  未执行 `T=1/T=13/T=130/T=131`。

## 真实 Smoke 结果

临时 workstation API：`http://127.0.0.1:18792`。
真实上位机：`http://192.168.1.11:8787`。

执行顺序：

1. `POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787`
2. SSH 只读检查 lifecycle 和设备占用。
3. 4 轮 direct upper read-only window：
   - `GET /api/radar/status`
   - `GET /api/radar/scan-proof/latest`
   - `POST /api/radar/scan-proof/refresh` body
     `{"start_runtime":false,"timeout_s":12}`
4. `POST /api/robot-control/radar/stop?baseUrl=http://192.168.1.11:8787`
5. cleanup readback。

结果：

- PC proxy start：`proxy_status=lifecycle_forwarded`、`remote_http_status=200`、
  `command_result.executed=true`、`command_result.ok=true`。
- during window 4 次 refresh 都返回 `status=refreshed`、
  `proof_state=scan_once_hz_raw_packet_tf_observed`。
- 新 evidence refs：
  - `o1-lidar-scan-proof-1781160878302`
  - `o1-lidar-scan-proof-1781160901312`
  - `o1-lidar-scan-proof-1781160924388`
  - `o1-lidar-scan-proof-1781160947425`
- scan hz 观测约 `14.555`、`15.807`、`15.532`、`15.925` Hz。
- 每轮都观测到 raw packet once 和 TF。
- read-only refresh 显示 `read_only_topic_observation=true`、
  `sends_base_motion_commands=false`、`sends_motion_commands=false`、
  `uses_base_uart=false`。
- PC proxy stop：`proxy_status=lifecycle_forwarded`、`remote_http_status=200`、
  `command_result.executed=true`、`command_result.ok=true`。

cleanup：

- LiDAR lifecycle status 为 `running=false`、`state=stopped`。
- stop 后 `lsof/fuser /dev/ttyACM0 /dev/ttyS5` 均无占用输出。
- 上位机 `upper_robot_api.py --port 8787` 仍在运行，`GET /api/radar/status` HTTP 200。
- 本机临时 workstation API 已停止，端口 `18792` 无监听。

## 发现的 Gap

`/api/radar/status` 在 lifecycle running 和 after stop 阶段都仍返回
`continuous_scan_status=not_proven`、`blocked_reasons=["scan_continuity_not_observed"]`。
本轮 direct refresh 已能证明 existing lifecycle 下多轮新鲜 scan/raw packet/TF 证据，
但 status 合同仍只稳定表达 latest scan proof，不能表达 continuous lifecycle 状态。

另一个边界事实：前置 `GET /api/robot-control/summary` 会聚合 base readback，并命中
`base.*.sends_commands` 危险字段。本轮发现后没有继续用 PC summary 作为 during window
来源，改为只读 direct upper radar endpoints。

## 验证结果

```bash
cd pc-tools/workstation && npm run test -- test/App.test.ts -t "renders Robot Control V1"
```

结果：通过。`1 passed | 12 skipped`。

```bash
git diff --check
```

结果：通过，无 whitespace error。

## Artifacts

- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/summary.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/pc_proxy/01_pc_proxy_radar_start.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/direct_upper/02_during_window.jsonl`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/remote_device/02_during_device_process.log`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/pc_proxy/03_pc_proxy_radar_stop.json`
- `sprints/2026.06.11_15-00_pc_radar_lifecycle_continuity_smoke/artifacts/remote_device/04_after_stop_device_process.log`

## 剩余风险

- 本轮证明 PC proxy 可以 start/stop 雷达 lifecycle，并能在 lifecycle 期间用 direct upper
  read-only refresh 连续采集新鲜 scan/raw packet/TF 证据；但还不等于 PC 页面完整表达
  continuous scan 状态。
- 本轮不是 HIL movement、不是 Nav2 execution、不是真实路线或 delivery proof。
- `/api/radar/status` 需要后续产品/接口迭代表达 lifecycle running、last proof freshness
  和 continuity window，否则 PC 页面只能展示一次 proof readback。

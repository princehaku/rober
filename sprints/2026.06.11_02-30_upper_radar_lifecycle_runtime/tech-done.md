# Upper Radar Lifecycle Runtime Tech Done

## sprint_type

micro

## 实际改动

- 新增 `onboard/scripts/o1_lidar_ros2_scan_smoke.sh`：纳入真实上位机已有 LiDAR-only smoke 脚本，来源为 `root@192.168.1.11:/root/rober/onboard/scripts/o1_lidar_ros2_scan_smoke.sh`，远端 sha256 为 `4f4dcf150989b20b6833ca7be73e2b3d78c4b027491a331af9e570731197b8ba`。
- 新增 `onboard/scripts/o1_lidar_lifecycle.sh`：支持 `start|stop|status`，start 后台启动受管 `lidar_driver` 和 `base_link -> laser_frame` 静态 TF，stop 只停止该脚本创建的进程组，status 输出结构化 JSON。
- 更新 `onboard/scripts/upper_robot_api.py`：`/api/radar/start|stop` 在执行前校验只允许 `o1_lidar_lifecycle.sh`，拒绝 `/dev/ttyS5`、`/api/base`、`/cmd_vel`、`T=1/T=13/T=130/T=131` 等危险 token，并在 `/api/radar/status` 暴露推荐 start/stop command。
- 更新 `onboard/tests/test_upper_robot_api.py` 与新增 `onboard/tests/test_lidar_lifecycle_script.py`：锁定 radar lifecycle 合同、危险串口拒绝和脚本 status JSON。
- 更新 `docs/hardware/board_sensor_stack_smoke.md`：说明 runtime lifecycle 与原 scan proof refresh 的关系、真实上位机 smoke 证据和安全边界。
- 更新 `docs/product/pc_tools_workstation.md`：说明 PC 高级雷达 start/stop 入口现在可消费真实上位机 lifecycle。

## 已读 vendor 来源与采用事实

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`

采用事实：

- WAVE ROVER 底盘 UART 是 newline-delimited JSON；本项目当前真实底盘路径按既有实板证据为 `/dev/ttyS5 @ 115200`。
- WAVE ROVER 底盘命令/反馈边界包含 `T=1/T=13/T=130/T=131`；本轮雷达 lifecycle 明确不发送这些命令、不发布 `/cmd_vel`、不调用 `/api/base/manual`。
- LiDAR `/dev/ttyACM0 @ 150000` 来自真实上位机 `/api/radar/status`、既有 scan proof artifacts 和本轮 live smoke；这是现场实测/项目 artifact 边界，不是 WAVE ROVER vendor 底盘文档事实。

## 验证结果

本地验证：

```text
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_lidar_lifecycle_script
Ran 14 tests in 0.055s
OK

bash -n onboard/scripts/o1_lidar_ros2_scan_smoke.sh onboard/scripts/o1_lidar_lifecycle.sh
OK

python3 -m py_compile onboard/scripts/upper_robot_api.py
OK
```

远端部署验证：

```text
ssh root@192.168.1.11 -p 37878 'python3 -m py_compile ... && bash -n ... && systemctl restart trashbot-upper-robot-api.service && systemctl is-active trashbot-upper-robot-api.service'
active
```

systemd drop-in 当前保留：

```text
ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND=bash /root/rober/onboard/scripts/o1_lidar_ros2_scan_smoke.sh --serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame
ROBER_RADAR_START_COMMAND=bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start --serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame
ROBER_RADAR_STOP_COMMAND=bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh stop
```

真实上位机 smoke 摘要：

- `POST /api/radar/start`：`command_result.executed=true`、`ok=true`、`failure_reason=null`。
- `POST /api/radar/scan-proof/refresh` with `{"start_runtime": false, "timeout_s": 12}`：`status=refreshed`、`proof_state=scan_once_hz_raw_packet_tf_observed`、`scan_runtime_proven=true`、`ros2_runtime_proven=true`、`uses_base_uart=false`、`sends_base_motion_commands=false`。
- during 阶段 `lsof /dev/ttyS5 /dev/ttyACM0` 只有 `lidar_driver` 占用 `/dev/ttyACM0`，无 `/dev/ttyS5` 行。
- `POST /api/radar/stop`：`command_result.executed=true`、`ok=true`、`failure_reason=null`。
- stop 后 `/dev/ttyS5` 和 `/dev/ttyACM0` 均无 lsof/fuser 占用，`o1_lidar_lifecycle.sh status` 返回 `running=false`。

PC 代理 smoke 摘要：

- 使用临时 workstation API `http://127.0.0.1:8791` 调用
  `POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787`：
  HTTP 200，`proxy_status=lifecycle_forwarded`，`command_result.executed=true`，`ok=true`。
- 调用 stop：HTTP 200，`proxy_status=lifecycle_forwarded`，`command_result.executed=true`，`ok=true`。
- 本地 8787 上已有 workstation 进程，但首次 POST 命中静态 HTML fallback；有效 PC 代理证据以 8791 当前源码 API 为准。

关键 artifact：

- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/deploy_restart.log`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/required_remote_validation.log`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/radar_lifecycle_smoke_20260611_023542/summary.json`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/radar_lifecycle_smoke_20260611_023542/04_during_device_process.log`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/radar_lifecycle_smoke_20260611_023542/06_after_stop_device_process.log`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/remote_capture/final_clear_after_pc_proxy.log`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/pc_proxy/pc_proxy_radar_start_8791.json`
- `sprints/2026.06.11_02-30_upper_radar_lifecycle_runtime/artifacts/pc_proxy/pc_proxy_radar_stop_8791.json`

## 剩余风险

- 仍不是 HIL movement、Nav2 movement、route execution、map start 真实执行或 delivery success；`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 保持不变。
- `/api/radar/start|stop` 只证明 LiDAR runtime lifecycle 可控；live `/scan`/TF 证据仍要通过 `/api/radar/status` 或 `/api/radar/scan-proof/refresh` 读取。
- 本地 8787 已有 workstation 进程对 radar POST 返回静态 HTML fallback；本轮用 8791 临时 API 验证当前源码代理合同，后续如果要使用 8787，需要重启对应 workstation API 进程到当前源码/构建。

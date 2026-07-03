# 2026-07-03 09:32 相机恢复脚本与 WASD 命令日志

## sprint_type

micro

## 实际改动

- `onboard/scripts/camera_usb_recovery_smoke.py`
  - 修正 USB 设备识别：优先从 `/sys/class/video4linux/videoX/device` 反查真实 kernel 地址，例如 `6-1`；不再把 `v4l2 bus_info=usb-5310400.usb-1` 这种平台地址误当作 `/sys/bus/usb/devices/*` 设备。
  - `systemctl stop` 后增加 inactive 等待；stop 被取消时只处理目标相机服务的 MainPID，避免 STREAMON smoke 被本机 8088 服务占用。
- `onboard/scripts/test_camera_usb_recovery_smoke.py`
  - 增加无硬件单测，锁定 `video1 -> .../usb6/6-1/6-1:1.0` 时必须识别为 `6-1`，平台 bus_info 找不到 sysfs 设备时必须回退。
- `onboard/scripts/upper_robot_api.py`
  - PC/WASD `pwm + realtime` 快路径直接串口写 vendor command 时，追加同 schema 的 `wave_rover_command_debug.jsonl` 记录。
  - `/api/base/status` 的 command debug 汇总同时识别 `upper_robot_api_manual_control` 和 `esp32_bridge_cmd_vel_callback`，使 PC 手控非零命令能被只读状态读回。
- `onboard/scripts/upper_robot_api.sh`
  - 增加 8787 stale listener 清理，只清理命令行包含 `upper_robot_api.py` 的旧实例，避免 systemd 被孤儿进程挡住端口。
- `onboard/tests/test_upper_robot_api.py`
  - 增加 PC WASD serial write command debug 单测。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录本轮真实上车验证、相机剩余 blocker 和 WASD 命令证据边界。

## 验证结果

- 本地验证：
  - `python3 -m unittest onboard.tests.test_upper_robot_api onboard/scripts/test_camera_usb_recovery_smoke.py onboard/scripts/test_local_webrtc_camera_smoke_health.py` 通过：108 tests，1 skipped。
  - `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/camera_usb_recovery_smoke.py onboard/tests/test_upper_robot_api.py onboard/scripts/test_camera_usb_recovery_smoke.py` 通过。
  - `bash -n onboard/scripts/upper_robot_api.sh onboard/scripts/local_webrtc_camera_smoke.sh` 通过。
- 上车部署验证：
  - 已同步 `camera_usb_recovery_smoke.py`、`upper_robot_api.py`、`upper_robot_api.sh` 到 `root@192.168.1.11:/root/rober/onboard/scripts/`。
  - `trashbot-upper-robot-api.service` 重启后由 systemd 管理的新 `upper_robot_api.py` 监听 `0.0.0.0:8787`；journal 记录清理旧 `upper_robot_api.py` listener。
  - 修正后的相机恢复脚本 auto 模式识别 `usb_device=6-1`，实际写入 `/sys/bus/usb/devices/6-1/authorized`，并确认相机服务 stop 后 inactive。
  - 真实 STREAMON 仍失败：`YUYV@320x240@20` 与 `MJPG@480x320@30` 输出 0 bytes，`VIDIOC_STREAMON returned -1 (Input/output error)`。
  - PC `/api/robot-control/base/manual` 发 `right`、`speed=0.04`、`duration_ms=180` 返回 `proxy_status=command_forwarded`、`manual_command_executed=true`、`auto_stop_executed=true`。
  - 上车 `wave_rover_command_debug.jsonl` 新增：
    `source=upper_robot_api_manual_control`、`manual_transaction_mode=serial_write_only_realtime`、
    `command_mode=pwm`、`command_transport=serial`、`T=11,L=164,R=-164`、`serial_write_returned=true`。
  - `/api/base/status` 读到 `base_command_chain_observed=true`，latest sent nonzero command 为 `T=11,L=164,R=-164`。

## 剩余风险

- 实时图传仍未看到真实帧；现在已经排除了“恢复脚本没打到真实 USB 设备”和“相机服务占用导致 busy”两类软件误判。剩余根因仍是 DV20 摄像头在 12M full-speed USB 链路上 STREAMON I/O error，需要换高速 USB 口/线或带供电 Hub 后复测。
- PC WASD 命令非零与 stop 已能读回，但 `T=1001` wheel raw L/R 仍未证明非零；后续需要继续查 WAVE ROVER/ESP32 feedback 是否实际上报轮速，不能把 command debug 当作 wheel feedback。

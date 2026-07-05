# 2026.07.06 05:15｜pc_live_radar_overlay_wasd_smoke｜PC 实时雷达贴图与 WASD smoke

## sprint_type

micro

## 本轮目标

继续推进 PC 端打开即用目标：

- PC 大地图必须同时显示地图、机器人位置、Nav2 路线、雷达点和目标点。
- PC 键盘/WASD 必须能通过固定代理连续点动并自动 stop。
- 相机仍需真实图传首帧；若硬件无帧，要明确不是页面独占。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `DEFAULT_LIDAR_DRIVER_DIAGNOSTICS_STALE_AFTER_MS=5000`。
  - 新增 `map_preview_scan_preview_from_driver_diagnostics()`。
  - `/api/map/preview` 的 `radar_overlay` 在 LiDAR lifecycle running、driver diagnostics 新鲜且 `scan_published` 时，优先使用 diagnostics 的实时 `scan_preview_points`。
  - 旧 scan-proof artifact stale 时仍不画旧点，避免把历史雷达点贴到当前地图。
- `onboard/tests/test_upper_robot_api.py`
  - 新增 diagnostics 新鲜时地图预览应画实时雷达点的回归测试。
  - 同步 free-roam 参数序列测试的 runtime ensure / `artifact_path` 现有调用契约，恢复全量 upper API 单测。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步 PC 地图雷达点恢复、WASD smoke 和相机剩余风险。

## 验证结果

本地代码验证：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py
python3 -m unittest onboard.tests.test_upper_robot_api
```

结果：

- `py_compile` 通过。
- `onboard.tests.test_upper_robot_api` 通过：103 个测试通过，1 个跳过。

上车部署和运行态验证：

```bash
scp -P 7878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py
ssh -p 7878 root@192.168.1.11 'python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 ...'
curl http://192.168.1.11:8787/api/map/preview
curl 'http://127.0.0.1:7001/api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787'
curl -X POST 'http://127.0.0.1:7001/api/robot-control/base/manual?baseUrl=http://192.168.1.11:8787'
curl -X POST 'http://127.0.0.1:7001/api/robot-control/base/stop?baseUrl=http://192.168.1.11:8787'
```

结果：

- 上位机 8787 已用新 `upper_robot_api.py` 重启，监听 `0.0.0.0:8787`。
- 上车 `/api/map/preview` 返回 `status=loaded`、`radar_overlay.overlay_status=loaded`、当前约 148 个雷达点、18 个 Nav2 路线点和目标点。
- PC 7001 `live-summary` 返回 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`radar_overlay_current_point_count=151`。
- 两次 PC 代理 forward pulse 均返回 `proxy_status=command_forwarded`；第二次返回 `motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`、`motion_evidence_complete=true`。
- stop 返回 `proxy_status=command_forwarded`；之后 live-summary 返回 `keyboard_motion_evidence_complete=true`、`keyboard_stop_settled_after_pulse=true`。
- esp32_bridge command debug log 读到 vendor `T=11 L/R=164` 的运动命令和 `T=11 L/R=0` 的 stop 命令。

## 剩余风险

- DV20 摄像头仍然无首帧：`/dev/video1` 未被其他进程占用、USB 480M、CMA 无近期错误，但 MJPEG/YUYV 多格式仍读不到第一帧。当前判断不是页面独占问题，仍需检查摄像头输入/供电或换 known-good UVC。
- WAVE ROVER vendor `T=1001` wheel raw L/R 仍读到 `0/0`；本轮只能证明 PC WASD 命令链路、stop 链路和 IMU 运动信号，不能声明 wheel raw L/R 闭环完成。
- 本轮未自动执行 Nav2 goal，只验证现有路线贴图、雷达贴图和手控 smoke。

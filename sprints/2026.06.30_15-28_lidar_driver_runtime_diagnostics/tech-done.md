# LiDAR Driver Runtime Diagnostics Micro Sprint

## sprint_type

micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
  - 新增 LiDAR driver 只读诊断 artifact：记录启动命令写入、read 调用、空读次数、总字节数、解析 packet 数、raw packet 发布数、`/scan` 发布数和下一步诊断。
  - 诊断状态区分 `serial_open_but_no_bytes`、`bytes_read_but_no_packets`、`packets_without_scan`、`scan_published` 和 `mock_runtime`。
  - 新增 `diagnostics_path` / `read_size` ROS 参数；诊断写失败只记日志，不影响 `/scan` 发布。
- `onboard/scripts/o1_lidar_lifecycle.sh`
  - 将 `diagnostics_path` 固定传给 driver：`$RUNTIME_DIR/lidar_driver_diagnostics.json`。
  - lifecycle status 增加 `driver_diagnostics_path`，方便 API 和 SSH 定位。
- `onboard/scripts/upper_robot_api.py`
  - `/api/radar/status` 新增 `driver_diagnostics_latest`、`driver_diagnostics_status` 和 `driver_diagnostics_next_action_plain`，只读读取 lifecycle 提供的诊断文件。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC summary 将 driver 诊断压缩到 `readback_summary.lidar/radar` 和 `radar_map_points` action card evidence。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏雷达 action card DOM 新增 `data-driver-diagnostics-status`、`data-driver-diagnostics-next-action-plain`、`data-driver-serial-bytes-read-total`、`data-driver-serial-packet-count-total`、`data-driver-serial-empty-read-count`、`data-driver-published-scan-count`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
  - 锁定 driver 诊断字段、空读计数、packet 计数和 lifecycle 参数。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步雷达贴图 blocker 的新诊断口径。

## 验证结果

- 上位机只读 SSH 诊断：
  - `ssh root@192.168.1.11 -p 37878` 成功。
  - `/dev/ttyACM0` 存在，`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0`。
  - `fuser /dev/ttyACM0` 显示仅 `lidar_driver` 占用。
  - 8787 `/api/radar/status` 显示 lifecycle running，但 scan proof 缺 `scan_once`、`scan_hz`、`raw_packet_once`；当前代码尚未部署到上车，所以 driver diagnostics live 为 `not_loaded`。
  - 摄像头 `/dev/video1` 存在，`fuser` 无占用；`v4l2-ctl --all -d /dev/video1` 可读 UVC 参数；8787 `/api/camera/health` 显示 `first_frame_total_timeout` 和 `capture_read_returned_false`，不是页面独占。
- `python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py`：通过，20 tests。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`：通过。
- `bash -n onboard/scripts/o1_lidar_lifecycle.sh`：通过。
- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary preserves radar raw-packet parsed status"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`：通过。
- `npm test -- --run`：通过，2 个测试文件、397 tests。
- `npm run lint`：通过，0 error；保留既有 4 个 Vue newline warning。
- `npm run build`：通过，生成 `dist/assets/index-CVnb5M_g.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `bash onboard/scripts/docker_humble_build.sh`：通过，`Summary: 6 packages finished [46.2s]`。
- 7001 live：
  - Node 监听 `0.0.0.0:7001`，PID `23878`。
  - 页面引用 `assets/index-CVnb5M_g.js` 和 `assets/index-DCA8Xtd4.css`。
  - JS bundle 命中 6 个 `data-driver-*` DOM 字段。
  - `/api/robot-control/summary` 返回 `robot_control_executed=false`，driver diagnostics 当前 `not_loaded`，符合“上车未部署新代码”的边界。
- 本地 helper 验证：`read_lidar_driver_diagnostics_artifact()` 可读取临时 `trashbot.o1.lidar_driver_diagnostics.v1`，返回 `diagnosis_status=serial_open_but_no_bytes`、`robot_control_executed=false`、`publishes_cmd_vel=false`。

## 剩余风险

- 本轮没有部署到上车运行目录，也没有重启上车 LiDAR lifecycle；live 上 driver diagnostics 仍为 `not_loaded`，需要部署后重启雷达 lifecycle 才能得到真实 `serial_open_but_no_bytes` 或其它诊断。
- 本轮没有发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`；没有做真实运动 HIL。
- 当前 SSH 只读诊断说明雷达 lifecycle running 但 `/scan` / raw packet 未观测；真实根因仍可能是雷达供电、线序、设备波特率、STC 雷达状态或硬件本体。
- 摄像头仍是 UVC 无首帧，不是页面独占；仍需现场检查 USB、供电、摄像头输入或更换 known-good UVC。

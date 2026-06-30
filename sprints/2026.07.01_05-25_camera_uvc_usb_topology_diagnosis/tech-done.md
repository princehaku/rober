# 相机 UVC USB 拓扑诊断

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py` 新增 `uvc_usb_topology` 只读诊断，解析 `lsusb -t` 的 UVC Video 接口速率。
- 当摄像头落在 `12M` full-speed USB 上且无人占用时，`source_diagnosis.status` 可提升为 `uvc_full_speed_usb_not_exclusive`，下一步明确为 `move_camera_to_high_speed_usb_port_or_powered_hub`。
- `onboard/scripts/upper_robot_api.py` 将 `uvc_usb_topology_*` 平铺到 8787 camera health / MJPEG status。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 和 `src/shared/contracts.ts` 同步暴露 `readback_summary.camera.uvc_usb_topology_*`。
- 更新 `docs/product/pc_tools_workstation.md` 与 `docs/vision/board_camera_publisher.md`，记录 PC/上车相机诊断合同、现场证据和硬件资料来源。

## 现场证据

- 已按 `docs/vendor/VENDOR_INDEX.md` 读取本地硬件资料入口；Orange Pi Zero 3 用户手册覆盖 USB 接口、USB 摄像头和 5V/2A 或 5V/3A Type-C 供电说明，电路图覆盖 USB DM/DP/VCC_USB 信号。
- 7001 summary 当前仍显示相机缺 `camera_first_frame`，地图和雷达贴图已完成。
- PC no-motion 相机复测：`/api/robot-control/camera/first-frame/probe` 返回 HTTP 502；`/api/robot-control/camera/mjpeg/status` 显示 `waiting_for_first_frame`、`has_recent_frame=false`、`shared_preview_exclusive_camera_claim=false`。
- SSH 只读：`/dev/video1` 是 `USB Composite Device: DV20 USB` Video Capture，`fuser -v /dev/video*` 无占用。
- `lsusb -t` 显示 UVC Video 接口在 `12M` full-speed USB 拓扑上。
- 上车取帧 smoke 到 `/dev/null`：`YUYV@320x240` 与 `MJPG@640x480` 均 `VIDIOC_STREAMON returned -1 (Input/output error)`。
- `dmesg` 含 `error -71`、`Failed to resubmit video URB` 和 UVC probe control 错误。
- 部署后 8787 只读验证曾返回 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、
  `uvc_usb_topology_status=uvc_video_on_full_speed_usb`、`uvc_usb_topology_video_usb_speed=12M`、
  `uvc_usb_topology_kernel_usb_address=6-1`、`uvc_usb_topology_next_action=move_camera_to_high_speed_usb_port_or_powered_hub`。
- 随后 8787 和 SSH 只读命令出现超时，PC 7001 重启后 summary 对 15 个上位机端点均报 `fetch_timeout_2400ms`；
  该问题记录为运行时连通性/上位机负载风险，未继续执行任何会改变硬件状态的命令。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_upper_robot_api`，128 tests passed, 1 skipped。
- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_upper_robot_api onboard.tests.test_camera_first_frame_probe`，141 tests passed, 1 skipped。
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/upper_robot_api.py onboard/scripts/camera_first_frame_probe.py`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "UVC kernel transport errors"`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，6 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，230 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮没有执行任何运动/control POST，也没有重置 USB 或修改上车硬件状态；只是把真实相机卡点变得更可诊断。
- 相机首帧仍未恢复；下一步需要现场换高速 USB 口/线、减少转接、确认 5V 供电或使用 powered hub/known-good UVC 后再复测。
- 部署后上位机 API/SSH 后续出现只读超时；需要恢复板子连通性后再确认 PC 7001 summary 能实时显示新 `uvc_usb_topology_*` 字段。
- 运动闭环仍需现场安全确认后执行 Nav2/键盘/自由移动验收。

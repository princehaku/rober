# 2026.06.29 14:48 camera_shared_mjpeg_low_bandwidth_first

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 调整共享 MJPEG 首帧短预算的格式尝试顺序：`MJPG@640x480@30` 之后优先尝试 `MJPG@480x320@30`、`YUYV@320x240@25`、`YUYV@640x480@22`，最后再走 `default@current`。
  - 目标是让 DV20 UVC 在 640x480 大帧无首帧时，更早尝试低带宽真实离散模式；多人预览仍复用同一条 shared capture。
  - 修正只读归因：8088 自己短暂持有 shared capture 且没有其他 owner 时，仍保持“不是页面独占”，不降级成泛化首帧失败。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 更新回归测试，锁定共享 MJPEG 短预算先试低带宽离散模式，避免再次退回大帧模式吃完整个首屏预算。
  - 新增 self-owned shared capture 的非独占归因回归。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
  - 同步记录 8088 共享 MJPEG 尝试顺序和安全边界。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`
- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`，结果 `Ran 28 tests in 15.382s OK`。
- 通过：部署到上位机 `root@192.168.1.11:37878` 后远端 `python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py`，并按原参数重启 `0.0.0.0:8088`，新 PID `361000`。
- 通过：部署到上位机 `root@192.168.1.11:37878` 并重启 8088 后，直连 `GET http://192.168.1.11:8088/mjpeg` 返回 503，但 `first_frame_format_attempts` 已按新顺序尝试 `MJPG@640x480@30`、`MJPG@480x320@30`、`YUYV@320x240@25`；三个模式均为 `capture_read_returned_false`。
- 通过：顺序只读 `GET http://192.168.1.11:8787/api/camera/health` 返回 `status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_usage_status=not_in_use`、`source_usage_owner_count=0`，并保留新顺序 `last_attempts=[MJPG@640x480@30, MJPG@480x320@30, YUYV@320x240@25]`。
- 通过：PC 7001 只读 `GET /api/robot-control/camera/mjpeg/status` 返回 `preview_status=source_first_frame_failed`、`exclusive_camera_claim=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`preview_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`
- 通过：PC 7001 只读 `GET /api/robot-control/summary` 当前事实仍显示“画面未显示：不是页面独占...UVC 设备没有输出视频帧”。

## 剩余风险

- 本轮没有宣称摄像头硬件已恢复出图；如果低带宽模式仍读不到首帧，现场结论仍是“不是页面独占，UVC 没有输出视频帧”，需要检查 USB、摄像头输入或供电，或换 known-good UVC 复测。
- 本轮不执行 Nav2、不启动雷达、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

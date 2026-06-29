# 摄像头后端低负载首帧矩阵

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_first_frame_probe.py`：新增 `v4l2-ctl --list-formats-ext` 解析，`--include-backend-smoke` 会保留原有固定 MJPG/YUYV 尝试，同时增加当前默认格式 `v4l2_current_mmap` 和最多 2 个设备自报低负载模式的 `v4l2-ctl`/`ffmpeg` 首帧尝试。
- `onboard/tests/test_camera_first_frame_probe.py`：补充格式解析、低负载模式选择、backend smoke 尝试名和安全字段断言；原有无硬件单测继续覆盖 fail-closed 语义。
- `docs/vision/board_camera_publisher.md`：记录当前判断边界：不是 PC 页面独占，新增矩阵只增强只读诊断，不改变底盘、雷达、Nav2 或运动安全门禁。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_camera_first_frame_probe`，13 个测试通过。
- 通过：`python3 -m unittest onboard.tests.test_camera_first_frame_probe onboard.tests.test_upper_robot_api`，99 个测试通过。
- 通过：`python3 -m py_compile onboard/scripts/camera_first_frame_probe.py`。
- 通过：`python3 -m py_compile onboard/scripts/camera_first_frame_probe.py onboard/scripts/upper_robot_api.py`。
- 通过：`git diff --check`。
- 上位机只读验证：已用 `scp -P 37878` 同步 `camera_first_frame_probe.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/`，随后通过 `POST http://127.0.0.1:8787/api/camera/first-frame/probe` 执行 `include_backend_smoke=true`。
  返回 `status=first_frame_timeout`、`open_ok=true`、`read_ok=false`、`failure_reason=capture_read_call_timeout`；backend smoke 共 9 个尝试，新增的 `v4l2_current_mmap`、`v4l2_device_mjpg_480x320_mmap`、`ffmpeg_device_mjpg_480x320`、`v4l2_device_yuyv_320x240_mmap`、`ffmpeg_device_yuyv_320x240` 均执行，全部 `no_frame_timeout`、`output_bytes=0`、`jpeg_soi_observed=false`。
- 上位机 probe 后复核：`GET /api/camera/health` 返回 `status=source_first_frame_failed`、`source_usage.status=not_in_use`、`owner_count=0`、`source_diagnosis.status=uvc_no_frame_not_exclusive`，且 `safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- DV20 未恢复出帧；本轮只是把“固定参数不行”扩展为“当前默认格式、MJPG@480x320、YUYV@320x240 也都不出帧”。
- 下一步应换 known-good UVC、检查 USB 供电/输入源/摄像头本体，而不是继续归因到 PC 页面独占。

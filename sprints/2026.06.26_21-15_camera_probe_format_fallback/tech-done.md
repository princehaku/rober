# Camera probe 格式 fallback

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`：`/api/camera/first-frame/probe` 新增 `auto_format_fallback` 白名单参数。开启后，上车端用短超时依次尝试 `MJPG@640x480`、`YUYV@640x480`、`YUYV@320x240` 和默认协商 `default@640x480`，读到首帧即停止；所有尝试都失败时返回 `fallback_attempts` 摘要。
- `onboard/tests/test_upper_robot_api.py`：新增自动格式 fallback 单元测试，覆盖前一格式失败、后一格式成功时停止继续尝试，并保持 `safe_to_control=false`、`robot_control_executed=false`。
- `pc-tools/workstation/src/server/index.ts`：普通首屏 quick probe 固定发送 `auto_format_fallback=true`，并把上车 `fallback_attempts` 压缩成 `probe_key_values.fallback_attempt_count/fallback_attempts_summary`。
- `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/src/components/RobotControlConsolePanel.vue`、`pc-tools/workstation/test/catalog.test.ts`：扩展 PC 合同、诊断显示和回归断言，确保普通检查不会退回单格式 MJPG 盲测。
- `docs/product/pc_tools_workstation.md`：记录 fallback 口径、硬件资料入口和现场 smoke 结论。

## 验证结果

- 已按硬件纪律读取 `docs/vendor/VENDOR_INDEX.md`。本轮没有修改接线、电压、UART、底盘协议或运动参数；相机现场事实来自上车 `/api/camera/health` 与 `v4l2-ctl -d /dev/video1 --list-formats-ext`。
- 现场设备：`/dev/video1` 为 `USB Composite Device: DV20 USB`，支持 `MJPG` 1280x720/640x480/480x320/1920x1080 和 `YUYV` 640x480/320x240。
- 远端 8787 已更新并重启为 PID `141902`，`/api/status` 可读。
- PC 7001 live probe：`proxy_status=probe_failed`、`remote_http_status=503`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`、`backend_smoke_status=not_requested`、`fallback_attempt_count=4`，尝试摘要为 `MJPG@640x480:first_frame_timeout/capture_read_call_timeout; YUYV@640x480:first_frame_timeout/capture_read_call_timeout; YUYV@320x240:first_frame_timeout/capture_read_call_timeout; default@640x480:first_frame_timeout/capture_read_call_timeout`。
- PC 7001 summary 回写：`source_readiness=first_frame_failed`、`source_failure_reason=capture_read_call_timeout`、`first_frame_probe_status=first_frame_timeout`、`first_frame_probe_open_ok=true`、`first_frame_probe_read_ok=false`、`safe_to_control=false`。
- `python3 -m unittest onboard/tests/test_upper_robot_api.py -v`：通过，50 tests。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：通过。
- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，105 tests。
- `cd pc-tools/workstation && npm test`：通过，2 files / 242 tests。
- `cd pc-tools/workstation && npm run build`：通过；仅 Vite chunk size warning。

## 剩余风险

- 本轮证明“白名单格式都读不到首帧”，并让普通 PC 检查可见该事实；它仍没有修好摄像头硬件/驱动层读帧超时。
- 当前建图前置画面仍不 ready；自动扫图/free-roam start 不应因为 fallback 诊断而放宽。
- PC Node 和上车 API 进程重启后仍需重新触发 probe 才能刷新最近检查摘要；长期相机健康仍应由上车 camera health 或后续持久 artifact 承担。

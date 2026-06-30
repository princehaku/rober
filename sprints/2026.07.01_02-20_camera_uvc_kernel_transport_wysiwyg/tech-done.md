# Camera UVC Kernel Transport WYSIWYG Micro Sprint

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - UVC kernel 诊断从只扫 `dmesg` 短 tail 改为全量扫描、响应截断。
  - 从 `uvcvideo 3-1` / `usb 3-1` 提取同一内核 USB 地址，把同地址 `error -71`、初始化失败、URB 重提交失败和 `can't read configurations` 归到当前 UVC 摄像头。
  - 保持只读：不打开额外 camera reader、不 reset USB、不启动 ROS2、不发布 `/cmd_vel`。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 覆盖旧 UVC 错误被日志挤出短 tail 后仍能进入 health 归因。
  - 覆盖无首帧、无人占用且内核有传输错误时，source diagnosis 优先输出 `uvc_transport_error_not_exclusive`。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/camera/mjpeg/status` 把 `uvc_transport_error_not_exclusive` 视为首帧失败，普通用户不会看到“等待画面”假象。
  - MJPEG status 的 action 文案支持下划线 token 和空格化 token，新增 USB 线/接口/供电中文下一步。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - camera summary 的 action plain 增加空格化 token 兜底，避免英文 token 泄漏到普通首屏。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 UVC transport error 在 MJPEG status 和 summary 中的中文化输出。
- `docs/vision/board_camera_publisher.md`、`docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`
  - 同步记录画面 WYSIWYG 的真实 live 结论和只读边界。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke -v`，35 tests OK。
- 通过：`npm test -- test/robotControlSummary.test.ts --run`，6 tests OK。
- 通过：`npm test -- test/catalog.test.ts -t "camera MJPEG|UVC|source diagnosis" --run`，14 tests OK / 164 skipped。
- 通过：`npm test -- --run`，3 files / 413 tests OK。
- 通过：`npm run build`。
- 通过：`npm run lint`，0 errors / 4 warnings（既有 Vue 模板换行 warning，未阻塞）。
- 通过：`git diff --check`。
- 通过：远端 `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`。
- 通过：已同步脚本到 `root@192.168.1.11:37878` 并重启 `trashbot-local-webrtc-camera.service`，服务 active，PID `643668`。
- 通过：live 只读 GET `http://127.0.0.1:8088/api/camera/health`：
  - `source_diagnosis_status=uvc_transport_error_not_exclusive`
  - `source_diagnosis_next_action=check_usb_cable_port_power_or_known_good_uvc`
  - `uvc_kernel_diagnostics.status=uvc_usb_transport_errors_observed`
  - `uvc_kernel_diagnostics.transport_error_count=44`
  - `latest_transport_error=[777992.581028] usb 3-1: device descriptor read/all, error -71`
- 通过：PC Node 重启到 `0.0.0.0:7001`，PID `73235`。
- 通过：live 只读 GET `/api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`：
  - `preview_status=source_first_frame_failed`
  - `source_diagnosis_status=uvc_transport_error_not_exclusive`
  - `source_diagnosis_next_action_plain=检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`
- 通过：live 只读 GET `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `readback_summary.camera.uvc_kernel_diagnostics_status=uvc_usb_transport_errors_observed`
  - `readback_summary.camera.uvc_kernel_diagnostics_transport_error_count=44`
  - `live_closure_summary.live_wysiwyg_camera_source_diagnosis_status=uvc_transport_error_not_exclusive`

## 剩余风险

- 本轮证明了“看不到画面”的当前根因不是页面独占，而是 UVC/USB 内核传输错误；尚未恢复真实视频帧。
- 真实恢复仍需要现场检查 USB 线、接口、摄像头供电或更换 known-good UVC 后复测。
- 没有发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

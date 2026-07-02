# Camera MJPEG Fallback Readback

- sprint_type: micro
- 时间：2026-07-02 14:35 CST
- Owner：User Touchpoint Full-Stack Engineer + Robot Software Engineer

## 实际改动

- 上车 `onboard/scripts/upper_robot_api.py` 新增共享 MJPEG 首帧兜底别名，`/api/camera/mjpeg/status` 直接输出 `mjpeg_open_source_fallback_attempted`、`open_source_fallback_failure_reason`、`primary_source_failure_reason`。
- PC `pc-tools/workstation/src/server/index.ts`、`robotControlSummary.ts` 和 contracts 同步透传这些字段，并提升为 `current_camera_wysiwyg_pack_*` 与 `camera_*` summary 短字段。
- 单测补充 `onboard/tests/test_upper_robot_api.py`、`pc-tools/workstation/test/robotControlSummary.test.ts` 和 `pc-tools/workstation/test/App.test.ts` 的字段契约。
- 文档同步更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`。
- 已部署到小车：`local_webrtc_camera_smoke.py` 备份为 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py.bak-20260702-1415`，`upper_robot_api.py` 备份为 `/root/rober/onboard/scripts/upper_robot_api.py.bak-20260702-1418`；已重启 `trashbot-local-webrtc-camera.service` 和 `trashbot-upper-robot-api.service`。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，91 tests，1 skipped。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/local_webrtc_camera_smoke.py`：通过。
- `npm test -- test/robotControlSummary.test.ts`：通过，10 tests。
- `npm test -- test/App.test.ts`：通过，237 tests。
- `npm run build`：通过，Vite chunk size warning 保持既有风险。
- `git diff --check`：通过。
- 现场只读验证 `http://192.168.1.11:8787/api/camera/mjpeg/status`：`mjpeg_open_source_fallback_attempted=true`，两个失败原因均为 `first_frame_total_timeout`，`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`，USB speed 为 `12M`，`safe_to_control=false`，`robot_control_executed=false`。
- 现场只读验证 `http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`：同样透传兜底证据，并确认 `starts_nav2/manual/free_roam/map_runtime=false`、`sends_motion_when_clicked=false`。
- 现场只读验证 `http://127.0.0.1:7001/api/robot-control/summary`：`current_camera_wysiwyg_pack_mjpeg_open_source_fallback_attempted="true"`，summary/readback/current camera pack 三处均为 `first_frame_total_timeout`。

## 剩余风险

- 相机仍没有可见画面；当前根因仍是 USB `12M` full-speed 与 UVC 传输/首帧超时，建图仍被 `camera_first_frame` 阻塞。
- 本轮未发送任何运动、Nav2、manual、keyboard、free-roam、建图、delivery 或 stop 请求；未做 HIL 运动验收。
- 硬件阶段继续以 `docs/vendor/VENDOR_INDEX.md` 指向的本地 vendor 资料为准，换高速 USB 口/线或带供电 USB Hub 后需要复测首帧、MJPEG 状态和 summary。

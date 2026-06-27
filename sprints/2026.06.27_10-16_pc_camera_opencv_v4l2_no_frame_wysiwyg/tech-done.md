# PC Camera OpenCV/V4L2 无帧提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通实时画面失败文案从“后端尝试”改为“OpenCV/V4L2 后端尝试”，明确当前不是浏览器页面独占，也不是多人预览 fanout 问题，而是上车端底层采集链路没有输出帧。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 camera first-frame/backend smoke 相关断言，锁住普通首屏的 WYSIWYG 失败口径。
- `docs/vision/board_camera_publisher.md`
  - 追加 2026-06-27 10:16 live 复测结果：`/dev/video1` 可枚举、`fuser` 无占用、OpenCV/V4L2 backend smoke 均无帧。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "camera|画面|shared preview|MJPEG|first frame"`，结果 `28 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
- 已通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`、`282 passed (282)`。
- 已通过：`git diff --check`
- 已重启：PC Node 通过 `launchctl` 监听 `0.0.0.0:7001`，当前 PID `86384`。
- 重启后 live summary 正常返回：camera 仍为 `source_first_frame_failed/first_frame_failed/capture_read_returned_false`；free-roam 仍为 `start_ready=true`、`motion_ready=false`、`mapping_ready=false`。
- live SSH 只读/诊断：
  - `GET /api/camera/health`：`source_readiness=first_frame_failed`，`source_failure_reason=capture_read_returned_false`，`source_usage.status=not_in_use`。
  - 顺序 `v4l2-ctl` 采 `YUYV 640x480` 与 `MJPG 640x480` 均 10 秒超时，输出 0 字节；前后 `fuser /dev/video1 /dev/video2` 无占用输出。
  - PC fixed probe：`proxy_status=probe_failed`，`status=first_frame_timeout`，`open_ok=true`，`read_ok=false`，`backend_smoke_status=backend_no_frame_observed`，`backend_attempts=4`。

## 剩余风险

- 本轮没有重启相机服务、没有 USB unbind/bind、没有触发任何底盘运动。
- 摄像头真实首帧仍未恢复；下一步需要现场检查 DV20 输入源、USB 线/供电、采集卡模式，或替换 known-good UVC 摄像头。

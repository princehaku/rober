# PC Camera MJPEG Status Plain Aliases

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- started_at: 2026-06-29 04:48 CST
- status: done

## 实际改动

- 扩展 PC Node 只读 `GET /api/robot-control/camera/mjpeg/status` 响应合同，新增顶层 `status` 与 `plain_hint`。
- `status/plain_hint` 分别对齐 `preview_status/preview_plain_hint`，让现场脚本不用猜字段名，也能直接读到共享预览是否有画面、看不到时是不是页面独占问题。
- 保留原有 `preview_*`、`camera_wysiwyg_*`、`viewer_count`、`upstream_connected`、`has_recent_frame` 字段，兼容现有普通首屏和高级诊断。
- 补充 camera MJPEG 回归测试，锁定共享 relay 有缓存帧与 idle 未出帧两类状态下，顶层别名和原 preview 字段一致。
- 同步 `docs/product/pc_tools_workstation.md`，说明该 status 入口仍然只读本机 MJPEG relay 状态，不新增相机 reader，不调用 WebRTC offer、manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera MJPEG"`：通过，9 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个测试文件、375 个测试通过。
- 重启 PC API 到 `0.0.0.0:7001` 后执行只读 `GET /api/robot-control/camera/mjpeg/status`：通过，返回 `status=source_first_frame_failed`、`plain_hint=不是页面独占...UVC 设备没有输出视频帧...`、`preview_status=source_first_frame_failed`、`viewer_count=0`、`upstream_connected=false`、`has_recent_frame=false`、`robot_control_executed=false`。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只增强 PC 共享预览 status 的只读可读性；真实摄像头仍显示 UVC 无首帧时，需要现场检查 USB、摄像头输入、供电或更换 known-good UVC。

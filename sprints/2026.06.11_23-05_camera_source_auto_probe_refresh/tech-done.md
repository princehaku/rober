# 2026-06-11 23:05 Camera Source Auto Probe Refresh

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`：`/health` 新增 `source_readiness` 与
  `source_failure_reason`，在最近一次 offer 对当前选中源出现 `first_frame_timeout`
  或 `capture_read_call_timeout` 时，把 `status` 从泛化的 `ready` 收紧为
  `source_first_frame_failed`。
- `onboard/tests/test_local_webrtc_camera_smoke.py`：补充 health 默认未探测状态和首帧失败状态
  的单元测试。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、
  `pc-tools/workstation/src/shared/contracts.ts`、
  `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC summary 透传
  `source_readiness/source_failure_reason`，且只在默认关闭的高级诊断中展示。
- `docs/vision/board_camera_publisher.md` 与
  `docs/product/pc_tools_workstation.md`：同步记录真实板端 camera source readiness 结论。

## 真实上位机证据

- 连接目标：`ssh root@192.168.1.11 -p 37878`。
- Vendor/硬件资料入口：`docs/vendor/VENDOR_INDEX.md`。本轮只操作 UVC/V4L2 camera
  诊断，不写 WAVE ROVER UART，不发布 `/cmd_vel`，不调用 `/api/base/manual`。
- `v4l2-ctl` 枚举：`/dev/video0` 是 Cedrus decoder，`/dev/video1` 是 DV20 USB
  `Video Capture`，`/dev/video2` 是 DV20 metadata capture。
- 首帧矩阵：`/dev/video1` 在 default、`MJPG 640x480`、`YUYV 640x480` 下均
  `open_ok=true`、`read_ok=false`、`first_frame_timeout=true`、
  `failure_reason=capture_read_call_timeout`；没有发现隐藏可读 video node。
- 部署仓库内 `local_webrtc_camera_smoke.py` 到板端后，未发 offer 的 `/health` 显示
  `status=ready`、`source_readiness=source_selected_not_probed`。
- 板端 aiortc direct offer 返回 HTTP 503，body 为 `error=first_frame_unreadable`、
  `failure_reason=first_frame_timeout`、`video_source=/dev/video1`；随后 `/health`
  显示 `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=first_frame_timeout`。
- 本地 PC summary 连接 `http://192.168.1.11:8787` 后，`readback_summary.camera`
  读回 `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=first_frame_timeout`、`last_offer_error=first_frame_unreadable`。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`：通过，11 tests。
- `cd pc-tools/workstation && npm run test -- catalog.test.ts`：通过，76 tests。
- `cd pc-tools/workstation && npm run test -- App.test.ts`：通过，16 tests。
- `python3 -m unittest discover onboard/tests -p '*camera*'`：通过，16 tests。
- `cd pc-tools/workstation && npm run test`：通过，2 files / 92 tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 无报错。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 实时图传可见内容仍未恢复，`visible_content_proven=false` 保持成立；当前更像 DV20
  输入源、线缆、供电、采集卡或上游视频源问题。
- 非 stop 运动 gate 仍未放开；缺少 visible camera、轮速反馈非零、LiDAR motion delta
  和外部视频材料前，不允许把 PC 页面升级为可手动移动。

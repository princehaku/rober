# PC Camera Format Attempts WYSIWYG

## sprint_type

micro

## 实际改动

- 修改 `pc-tools/workstation/src/server/robotControlSummary.ts`：从上车 `/api/camera/health.media_diagnostics.last_offer_error.first_frame_format_attempts` 生成 `last_offer_format_attempts_summary`，把逐格式首帧失败压成普通首屏可读短摘要。
- 修改 `pc-tools/workstation/src/shared/contracts.ts`：扩展 Robot Control summary camera 合同，新增 `last_offer_format_attempts_summary`。
- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在“不是页面独占”的实时画面失败文案后追加采集尝试摘要，例如 `MJPG 无首帧；YUYV 无首帧；default 无首帧`；普通首屏继续隐藏 `capture_read_returned_false` 等 raw 原因。
- 修改 `pc-tools/workstation/test/App.test.ts` 和 `pc-tools/workstation/test/catalog.test.ts`：覆盖 live 形状下格式尝试摘要显示，并锁住普通首屏不泄漏 raw failure reason。
- 更新 `docs/product/pc_tools_workstation.md`：记录 PC 只读消费 camera health 格式尝试证据的 WYSIWYG 口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "camera|实时画面|共享画面"`，`21 passed / 120 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "camera|Camera|summary"`，`22 passed / 85 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build OK；保留既有 chunk size warning。
- 通过：`git diff --check`。
- 重启 PC Node 到当前源码后，`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，`readback_summary.camera.last_offer_format_attempts_summary="MJPG 无首帧；YUYV 无首帧；default 无首帧"`，同时 `source_usage_status=not_in_use`、`source_usage_owner_count=0`。
- 真实上位机只读/采集 smoke：
  - `/api/camera/health` 显示 `source_usage.status=not_in_use`、`owner_count=0`、`source_failure_reason=capture_read_returned_false`，最近 offer 的 `first_frame_format_attempts` 为 `MJPG/YUYV/default` 全部 `first_frame_unreadable`。
  - `v4l2-ctl --list-formats-ext -d /dev/video1` 显示 DV20 USB camera 支持 `MJPG 640x480/1280x720/1920x1080` 和 `YUYV 640x480/320x240`。
  - `timeout 8 v4l2-ctl -d /dev/video1 --stream-mmap --stream-count=3 --stream-to=/tmp/rober_camera_smoke.raw` 超时，输出文件 0 字节。
  - 直接 OpenCV 读取 `/dev/video1` 和 index `1` 均未打开或未读到帧。

## 剩余风险

- 本轮修正的是 PC 普通首屏画面失败证据的所见即所得，不证明真实摄像头已经出图。
- 当前真实根因仍偏向 `/dev/video1`/DV20 USB 摄像头或输入链路没有输出可读帧，不是 PC 页面独占；需要现场检查摄像头 USB、供电、镜头/输入或替换 known-good UVC 继续验证。

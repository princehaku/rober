# 2026-06-29 02:20 PC 相机首帧总超时非独占诊断

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC Node summary 在 `/api/camera/health` 缺少显式 `source_diagnosis` 时，若读到首帧失败且相机无人占用，派生 `uvc_no_frame_not_exclusive`。
  - free-roam 建图 gate 同步识别 `first_frame_total_timeout + not_in_use`，把 `camera_first_frame` 缺口写成“不是页面独占”。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏旧 summary 兜底：`first_frame_total_timeout` 显示为“读取首帧总超时”，不暴露字段名，也不误导成浏览器独占。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 live 形态：DV20 `/dev/video1` 首帧总超时、无人占用、无 diagnosis 时，summary 自动派生非独占无帧诊断。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏旧 summary 形态，确认显示“不是页面独占 + 读取首帧总超时”，且不触发 manual/free-roam/Nav2 执行。
- `docs/vision/board_camera_publisher.md`
  - 记录 2026-06-28 live 只读状态和本轮诊断口径。

## 验证结果

- 通过：`ssh root@192.168.1.11 -p 37878` 只读 GET 复核：
  - camera：`source_first_frame_failed / first_frame_total_timeout`
  - radar：`lifecycle_running=false / lifecycle_state=stopped`
  - free-roam：`not_proven`
  - Nav2：`not_proven`
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "first-frame total timeout"`
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "infers UVC sibling node roles|camera MJPEG status treats first-frame total timeout"`
- 通过：`cd pc-tools/workstation && npm test -- --run`，2 个文件、358 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`

## 剩余风险

- 本轮没有打开摄像头流、没有运行真实首帧探针、没有启动雷达、没有执行 Nav2、没有发送 manual/free-roam/keyboard/delivery/stop 或 `/cmd_vel`。
- 真实摄像头仍未恢复画面；当前结论只是把 `first_frame_total_timeout` 正确归因为“不是页面独占，UVC 源无首帧”，后续仍需现场检查 USB、摄像头输入、格式、供电或替换 known-good UVC。
- 自动驾驶和 free-roam 当前 live 仍是 `not_proven`，本轮只减少相机根因误判，不声明小车已能自动动起来。

# Camera Total Timeout 非独占诊断

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 `first_frame_total_timeout` 纳入相机首帧失败原因集合。
  - summary 里探针成功后会清掉旧 `first_frame_total_timeout`，共享预览失败状态也会把它视为相机源无帧。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/camera/mjpeg/status` 同步识别 `first_frame_total_timeout`。
  - 当 health 同时显示 `not_in_use` 或 `owner_count=0` 时，返回 `uvc_no_frame_not_exclusive`，提示不是浏览器独占。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 MJPEG status 用例，覆盖只有 `first_frame_total_timeout + not_in_use`、没有现成 diagnosis 的场景。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 `first_frame_total_timeout` 的普通首屏解释口径。

## 验证结果

- 已通过 focused camera/status 测试：
  - `npm test -- --testNamePattern "first-frame total timeout|MJPEG status|Camera|camera" --maxWorkers=1 --no-fileParallelism`
  - 结果：47 passed。
- 已通过 PC workstation 全量测试：
  - `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：329 passed。
- 已通过静态和构建验证：
  - `npm run lint`
  - `npm run build`
  - `git diff --check`
  - `npm run build` 仍有既有 Vite chunk size warning，不影响构建通过。

## 剩余风险

- 本轮只修只读诊断文案和状态聚合；摄像头真实首帧仍需现场检查 USB、摄像头输入/供电或换 known-good UVC。
- 本轮不发送真实运动命令、不启动 Nav2、不启动 free-roam。

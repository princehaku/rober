# PC 摄像头共享预览后进页面缓存帧

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - PC Node 共享 MJPEG relay 增加最近 frame chunk 缓存；同一个上位机 baseUrl 下，后进入的浏览器页面若已有共享上游流，会先收到最近帧，再继续跟随实时流。
  - `/api/robot-control/camera/mjpeg/status` 新增只读字段 `cached_frame_loaded/cached_frame_age_ms`，用于现场判断共享流是否已经有可复用最近帧。
  - 改动只影响只读 MJPEG 预览，不新开第二条上游 capture，不发送 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步摄像头 MJPEG status 契约字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定第三个页面在第一帧之后加入时不增加上游请求，并能在下一帧前读到缓存帧。
- `pc-tools/workstation/test/App.test.ts`
  - 同步前端默认 status fixture。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录共享预览后进页面缓存帧的产品口径和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --testNamePattern "workstation camera MJPEG proxy forwards only fixed readonly multipart stream" --maxWorkers=1 --no-fileParallelism`
  - `Tests 1 passed | 322 skipped (323)`
- 通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - `Test Files 2 passed (2)`，`Tests 323 passed (323)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单 chunk 超过 500 kB；本轮未改变该既有打包策略。
- 通过：`git diff --check`

## 剩余风险

- 本轮证明 PC Node 对后进页面会复用已有共享流和最近帧；不证明真实 DV20/UVC 已输出首帧。
- 现场 live summary 仍显示 `uvc_no_frame_not_exclusive` 时，应继续检查 USB 摄像头输入、供电或替换 known-good UVC。

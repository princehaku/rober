# PC Camera Service Owned No Frame Hint Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏相机首帧失败文案新增 `in_use_by_camera_service` 分支，区分“相机服务自己持有设备但读不到帧”和“其他进程独占”。
- `pc-tools/workstation/test/App.test.ts`：新增 live-like 回归用例，覆盖 `source_usage_status=in_use_by_camera_service`、`source_failure_reason=capture_read_returned_false`。
- `docs/product/pc_tools_workstation.md`：同步现场口径和 MJPEG 共享链路实测结论。

## 验证结果

- `npm test -- App.test.ts`：通过，137 tests passed。
- `npm test`：通过，2 files / 240 tests passed。
- `npm run build`：通过；Vite 保留既有大 chunk warning。
- live 只读复测：
  - PC `GET /api/robot-control/camera/mjpeg/status` 在无人观看时返回 `client_count=0`、`upstream_active=false`、`shared_capture=true`、`exclusive_camera_claim=false`。
  - PC 拉取 `GET /api/robot-control/camera/mjpeg` 返回 502；直接拉上车 `GET http://192.168.1.11:8787/api/camera/mjpeg` 返回 502，body 指向上游 503。
  - 上车 `GET /api/camera/health` 返回 `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=capture_read_returned_false`、`source_usage.status=in_use_by_camera_service`，owner 是 camera service 自身。

## 剩余风险

- 本轮只修 PC 首屏归因和测试，不修复 `/dev/video1` 实际读帧失败。
- camera service 已接管设备但 `last_successful_frame=null`，所以自动扫图/建图运动门禁仍不能放行。
- 要让“谁进来都能看到实时预览”真正成立，还需要上车端 camera service 能成功读到首帧；当前阻塞在相机输入/USB/供电/设备输出层。

# PC camera MJPEG status 首帧诊断字段对齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/camera/mjpeg/status` 顶层补齐
  `source_readiness` 和 `source_failure_reason`，优先来自只读 `/api/camera/health`；当 health 已证明
  `source_first_frame_failed` 时，status 也直接返回 `source_readiness=first_frame_failed` 与具体失败原因。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：MJPEG relay overlay 类型补齐同一组字段，保证 status/summary 使用同源诊断材料。
- `pc-tools/workstation/src/shared/contracts.ts`：同步固定 camera MJPEG status response contract。
- `pc-tools/workstation/test/catalog.test.ts`：补充首帧失败、非独占无帧、未探测三类 MJPEG status 的 `source_readiness/source_failure_reason` 断言。
- `docs/product/pc_free_roam_mapping_design.md`：记录 camera status 与 summary 的只读首帧诊断字段对齐。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- 重启 PC Node：`HOST=0.0.0.0 PORT=7001 ROBOT_CONTROL_DEFAULT_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `*:7001`，PID `56192`。
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status`：
  - `status=source_first_frame_failed`
  - `preview_visible_status=not_visible_source_first_frame_failed`
  - `source_readiness=first_frame_failed`
  - `source_failure_reason=first_frame_total_timeout`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `source_usage_status=not_in_use`
  - `source_usage_owner_count=0`
  - `viewer_count=0`
  - `upstream_connected=false`
  - `has_recent_frame=false`
  - `robot_control_executed=false`
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/summary`：camera summary 与 MJPEG status 同步显示 `source_readiness=first_frame_failed`、`source_failure_reason=first_frame_total_timeout`。

## 剩余风险

- 本轮只补只读状态字段，没有打开额外 camera stream，也没有执行 WebRTC offer、manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- 当前摄像头仍然无首帧；现有证据说明不是页面独占，下一步仍是检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。
- 建图验收仍缺相机首帧和雷达新鲜扫描；自由移动可先做，但不能按可验收建图收口。

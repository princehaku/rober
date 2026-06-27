# 共享摄像头 MJPEG status 非独占诊断

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/server/index.ts`：
  - `/api/robot-control/camera/mjpeg/status` 只读 `/api/camera/health` 时，如果相机首帧失败且 `source_usage` 明确显示没人占用，则把 source diagnosis 统一解释为 `uvc_no_frame_not_exclusive`。
  - status 仍然不会打开 `/api/camera/mjpeg` 上游流；它只返回当前共享 relay 状态和 health 诊断。
- 修改 `pc-tools/workstation/test/catalog.test.ts`：
  - 新增 live-shaped 回归，覆盖 `source_first_frame_failed + source_usage.not_in_use + source_diagnosis.not_exclusive=false` 时，PC status 必须输出“不是页面独占”的中文可读诊断。
- 更新 `docs/product/pc_free_roam_mapping_design.md`：
  - 记录 summary、MJPEG status 和普通首屏对相机无首帧/非独占诊断的统一口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "MJPEG status"`（5 tests）
- 通过：`cd pc-tools/workstation && npm test`（313 tests）
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`git diff --check`
- 通过：重启 PC workstation Node 后只读 live status：
  - `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`
  - `proxy_status=status_loaded`
  - `last_failure_reason=camera_source_first_frame_failed`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `source_diagnosis_next_action=check_usb_camera_input_power_or_known_good_uvc`
  - `source_diagnosis_not_exclusive=true`
  - `robot_control_executed=false`
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `*:7001`

## 剩余风险

- 本轮没有发送真实自由移动、键盘手控、Nav2 或底盘命令。
- live 摄像头仍然没有输出 JPEG 帧；本轮修正的是 PC status/UI 的原因归因，不能替代换线、供电、摄像头输入或 known-good UVC 复测。

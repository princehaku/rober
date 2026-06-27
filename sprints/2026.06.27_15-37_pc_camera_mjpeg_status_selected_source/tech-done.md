# 2026-06-27 15:37 PC camera MJPEG status selected source

## sprint_type: micro

## 设计结论

本轮继续推进“画面必须所见即所得”。live 状态显示：

- summary 已能从 camera health 读到 `/dev/video1` 已选中、未被占用、但还没读首帧。
- `/api/robot-control/camera/mjpeg/status` 在没有 active preview client 时仍返回
  `source_diagnosis_status=not_loaded`，导致新页面只看共享预览 status 时不知道当前不是独占问题。

正确口径：

- MJPEG status 仍不能创建 MJPEG client、不能打开额外 camera reader。
- 但它可以短读只读 `/api/camera/health`，把 `source_diagnosis` 贴到 status。
- 当 health 是 `source_not_probed/source_selected_not_probed` 时，status 也应显示“已选中、不是独占、下一步打开共享预览或运行首帧检查”。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `cameraSourceFirstFrameFailureForStatus()` 扩展为 source diagnosis overlay。
  - 除 `source_first_frame_failed` 外，也支持 `source_selected_not_probed` 和已有 `source_diagnosis` 的只读诊断返回。
  - 未失败的 selected-source 诊断保持 `last_failure_reason=""`、`last_failure_at_ms=null`，避免把“未 probe”伪装成失败。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增回归测试：status 短读 health、返回 selected-source diagnosis，同时 `/api/camera/mjpeg` 请求计数保持 0。
- `docs/product/pc_tools_workstation.md`
- `docs/vision/board_camera_publisher.md`
  - 同步记录 selected-source diagnosis 的共享预览 WYSIWYG 口径和 no-motion 边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "workstation camera MJPEG status"`
  - `Tests 4 passed | 124 skipped`
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Tests 295 passed`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 保留既有 Vite chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation run lint`
- 已通过：`git diff --check`

## Live 只读验证

- PC Node 已重启并监听 `0.0.0.0:7001`。
- `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回：
  - `client_count=0`
  - `upstream_active=false`
  - `shared_capture=true`
  - `exclusive_camera_claim=false`
  - `last_failure_reason=""`
  - `last_remote_http_status=200`
  - `last_failure_at_ms=null`
  - `source_diagnosis_status=source_selected_not_probed`
  - `source_diagnosis_not_exclusive=true`
  - `source_diagnosis_next_action=open_shared_preview_or_run_first_frame_probe`
  - `robot_control_executed=false`
- 同轮只读 map preview 仍返回真实地图图像 `223x116`、free cells `421`、`robot_control_executed=false`。

## 剩余风险

- 当前摄像头仍未证明真实首帧；本轮只修 status 诊断一致性，不把画面提升为 ready。
- 建图验收仍应保留 `camera_first_frame` 缺口，直到共享预览 load 或首帧 probe 证明真实帧。
- 本轮未执行任何运动 POST，也未打开 MJPEG stream；真实预览恢复仍需要 operator 打开共享预览或执行首帧检查。

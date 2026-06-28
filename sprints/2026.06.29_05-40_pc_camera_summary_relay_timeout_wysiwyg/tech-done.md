# PC camera summary relay timeout WYSIWYG

## sprint_type

micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts`：当 `/api/camera/health` 在 summary 读取窗口内失败，但 PC 共享 MJPEG relay 已记录 `first_frame_total_timeout`、`capture_read_returned_false` 等首帧失败，或已带出 `uvc_no_frame_not_exclusive` 诊断时，`readback_summary.camera.status` 归一为 `source_first_frame_failed`。
- 同步补齐 `source_readiness=first_frame_failed` 与可用的 `source_failure_reason`，避免普通首屏显示 `fetch_failed/not_loaded`，而高级诊断又显示“不是页面独占、UVC 无首帧”。
- 新增 catalog 回归测试，覆盖 live 7001 形态：health 超时、relay 最近失败为原始 `first_frame_total_timeout`、summary 仍必须显示源头无帧并保留格式尝试摘要。
- 更新 `docs/product/pc_tools_workstation.md`，记录共享预览多人可共享、当前无画面归因为 UVC 源头无首帧，不是页面独占；本改动不新开相机上游，不发送任何运动命令。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --testNamePattern "Robot Control summary treats relay first-frame total timeout"` 通过：1 个目标测试通过，364 个测试跳过。
- `npm --prefix pc-tools/workstation test` 通过：2 个 test files、365 个 tests 全部通过。
- `npm --prefix pc-tools/workstation run build` 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。
- PC Node 已按 `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 重启，`lsof` 确认 PID `19488` 监听 `*:7001`。
- 只读复核 `GET http://127.0.0.1:7001/api/robot-control/summary`：`camera.status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`shared_preview_exclusive_camera_claim=false`、`robot_control_executed=false`。
- 只读复核 `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status`：`proxy_status=status_loaded`、`shared_capture=true`、`exclusive_camera_claim=false`、`last_failure_reason=camera_source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`robot_control_executed=false`。

## 剩余风险

- 该轮只修正 PC summary 所见即所得归因；真实摄像头仍需现场检查 USB/供电/输入模式或替换 known-good UVC 才能恢复实时画面。
- 未发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；自动驾驶真实发车仍需要现场安全确认后单独执行。

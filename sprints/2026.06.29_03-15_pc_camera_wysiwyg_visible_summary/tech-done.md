# PC Camera WYSIWYG Visible Summary

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `readback_summary.camera` 增加 `preview_visible_status`、`preview_visible_plain`、`camera_wysiwyg_status_plain` 和 `camera_wysiwyg_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 shared MJPEG relay、source first-frame failure 和 source diagnosis 合成直接的画面可见性结论；`preview_status=idle_not_started` 但 UVC 无首帧时，短字段会明确写成未可见且不是页面独占。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补齐默认夹具、UVC 无首帧和 shared MJPEG streaming 场景断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录只读 summary 合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera|shared preview|first-frame|MJPEG|mjpeg"`：通过，1 个文件，25 个测试通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `preview_visible_status=not_visible_source_first_frame_failed`、`camera_wysiwyg_status_plain=画面未可见：不是页面独占...UVC 设备没有输出视频帧...`，同时 `source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 PC 只读可见性字段，不新开相机采集、不重启相机、不修复 UVC 无首帧硬件/驱动问题。
- 当前 live 仍显示 UVC 无首帧；新增字段会让脚本直接读到“画面未可见，不是页面独占”。

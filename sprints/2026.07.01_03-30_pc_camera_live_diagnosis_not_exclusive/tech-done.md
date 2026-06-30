# PC 相机 live 诊断排除独占误判

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_wysiwyg_camera_diagnostic_plain` 在相机未显示时不再只写“读取首帧超时”。
  - 当 `readback_summary.camera.source_diagnosis_*` 已有结论时，live 诊断会补充 `diagnosis status`、`已排除页面独占`、具体根因和下一步。
  - 对现场 live 状态，这会把“不是页面独占、UVC/USB 传输错误、检查 USB 线/接口/供电或换 known-good UVC”直接放进当前所见诊断。
  - 可见文案会把 `uvc_no_frame_not_exclusive` / `uvc_transport_error_not_exclusive` 翻译成“UVC 无首帧”或“UVC/USB 传输错误”，不在普通首屏泄漏工程枚举名。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 `uvc_no_frame_not_exclusive` 和 `uvc_transport_error_not_exclusive` 两类相机首帧失败，锁定 live 诊断必须暴露非独占与 USB/UVC 根因。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏 live closure fixture 和可见诊断断言，确认默认页面会显示“已排除页面独占”和可执行下一步。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 live 相机诊断合同：只读消费 summary/health，不创建 MJPEG client，不发送任何运动命令。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，6 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Robot Control V1|live closure|camera"`，1 file passed，39 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，Vite chunk size warning 仍为既有提示，构建成功。
- 通过：`cd pc-tools/workstation && npm test -- --run`，3 files passed，413 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`，0 errors，0 warnings。
- 通过：`git diff --check`。
- 标点清理后复跑通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，6 tests passed。
- 标点清理后复跑通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Robot Control V1|live closure|camera"`，1 file passed，39 tests passed。
- 标点清理后复跑通过：`cd pc-tools/workstation && npm run lint`，0 errors，0 warnings。
- 标点清理后复跑通过：`cd pc-tools/workstation && npm run build`，Vite chunk size warning 仍为既有提示，构建成功。
- 标点清理后复跑通过：`cd pc-tools/workstation && npm test -- --run`，3 files passed，413 tests passed。
- 标点清理后复跑通过：`git diff --check`。
- 通过：7001 只读 smoke，listener PID `30475`，`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_status=needs_wheel_rerun`、`camera_visible=false`，`live_wysiwyg_camera_diagnostic_plain` 包含“已排除页面独占”和 `UVC/USB`，不含 `uvc_no_frame_not_exclusive` / `uvc_transport_error_not_exclusive`，无 `。；` / `。。`，且 `objective_audit_sends_motion_when_clicked=false`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`。

## 剩余风险

- 本轮只修正 PC/live summary 的相机诊断表达，不修复真实 USB/UVC 物理链路。
- live 当前仍显示相机首帧失败；需要现场检查 USB 线、接口、供电或更换 known-good UVC 后再复测画面 WYSIWYG。

# PC camera diagnosis placeholder cleanup

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts` 新增相机源名称和中文诊断清洗逻辑，`/api/robot-control/camera/mjpeg/status` 不再把 `not_loaded 当前没人占用` 当成设备名返回。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 修正 `cameraDisplayDeviceName()`，让 `not_loaded/none/unknown/null` 触发 fallback；summary overlay 和 health source diagnosis 都会清洗占位设备名。
- 更新 catalog 测试，覆盖 MJPEG status 与 Robot Control summary 两条只读路径，断言 `source_diagnosis_plain_hint` 不含 `not_loaded`。
- 更新 `docs/product/pc_tools_workstation.md`，记录该变化只改只读诊断文字，不触发相机、底盘、Nav2 或自由移动动作。

## 验证结果

- `npm --prefix pc-tools/workstation test` 通过：2 个 test files、365 个 tests 全部通过。
- `npm --prefix pc-tools/workstation run build` 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。
- 7001 live 只读复核：`node` PID `58761` 监听 `*:7001`；`GET /api/robot-control/summary` 返回 `source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、中文 hint 为 `不是页面独占：USB Composite Device: DV20 USB ... 当前没人占用...known-good UVC 复测`，不再出现 `not_loaded 当前没人占用`；`safe_command_boundary.robot_control_executed=false`。
- `GET /api/robot-control/camera/mjpeg/status` 只读复核：`source_diagnosis_plain_hint` 同样保留 DV20 UVC 诊断且不含占位设备名，`robot_control_executed=false`。
- Chrome/Playwright DOM 只读复核 `http://127.0.0.1:7001/`：首屏当前事实和共享画面状态均不含 `not_loaded 当前没人占用`，仍显示“不是页面独占 / UVC 没有输出视频帧 / 检查 USB、摄像头输入或供电 / 自由移动不受影响”。

## 剩余风险

- 该轮只清理 PC API/首屏诊断占位词；真实摄像头无帧仍需要现场检查 USB、摄像头输入/供电或更换 known-good UVC。
- 未发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`；真实小车移动和 Nav2 复跑仍需现场安全确认。

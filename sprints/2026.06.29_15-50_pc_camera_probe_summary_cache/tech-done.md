# PC 相机首帧 probe 共享诊断

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通相机卡片的“只读检查”摘要新增 summary 缓存消费；当本页没有刚点击的 probe result，但 PC Node summary 已带最近一次 `first_frame_probe_*` overlay 时，直接显示“最近一次检查”的首帧/后端诊断。
- `pc-tools/workstation/test/App.test.ts`：补强 live 无帧场景，锁定刷新页面后也能看到最近 probe 结论，且不触发 camera offer、manual、free-roam 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步普通相机卡片消费最近 probe overlay 的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "live not-in-use camera first-frame failure"`，结果 `1 passed | 216 skipped`。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "camera"`，结果 `33 passed | 184 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed` test files，`382 passed` tests。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提示，不影响本轮相机状态逻辑。
- 通过：`git diff --check`。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读检查 live `/api/robot-control/summary`，相机仍为 `source_first_frame_failed`、`source_diagnosis_status="uvc_no_frame_not_exclusive"`、`shared_preview_exclusive_camera_claim="false"`；本轮未主动运行 probe，因此 live `first_frame_probe_status="not_loaded"` 符合边界。

## 剩余风险

- 本轮只改善普通页面消费共享 probe 诊断的方式，不自动运行 probe、不抢占相机、不修复真实 UVC 无首帧。
- 真实摄像头仍需要现场检查 USB、摄像头输入/供电或换 known-good UVC；Nav2 仍需要现场安全确认后 ROS 模式重跑并复验 wheel L/R 非零。

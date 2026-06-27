# PC 摄像头共享重试按钮文案

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 把 `first_frame_total_timeout` 纳入摄像头首帧失败识别，和上车端共享 MJPEG 当前真实返回保持一致。
  - 普通首屏实时画面主按钮新增只读状态文案：当 health/summary 已证明相机源首帧失败，且诊断是非独占、设备没人占用或共享预览明确非独占时，按钮显示 `重试共享画面`；其他首帧失败显示 `重试打开画面`。
  - 改动只影响 PC UI 文案，不扩大 camera offer、probe、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel` 调用面。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 live 形态 `not_in_use + uvc_no_frame_not_exclusive` 下，普通首屏按钮显示 `重试共享画面`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏按钮文案和 `first_frame_total_timeout` 识别边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "not-in-use camera first-frame failure"`
  - 结果：`1 passed | 171 skipped`
- 已通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "keeps camera source first-frame failure visible while streaming waits for a drawable frame"`
  - 结果：`1 passed | 171 skipped`
- 已通过：`cd pc-tools/workstation && npm test -- --run`
  - 结果：`2 passed` test files，`301 passed`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 结果：`tsc` 与 `vite build` 通过；仍有既有的 chunk size warning。
- 已通过：`cd pc-tools/workstation && npm run lint`
  - 结果：`eslint .` 通过。
- 已通过：`git diff --check`

## 剩余风险

- 该 micro sprint 只修正 PC 端所见即所得文案；真实 DV20/UVC 仍可能因为 USB、输入、供电或设备兼容问题没有输出视频帧，需要现场更换/复测摄像头才能完成“实时预览可见”验收。
- 未执行任何真实发车、Nav2 路线、free-roam 或底盘命令；自动驾驶无法运动的问题仍以现有 `goal_succeeded_but_wheel_lr_zero` 和后续 ROS 重跑路线验证为准。

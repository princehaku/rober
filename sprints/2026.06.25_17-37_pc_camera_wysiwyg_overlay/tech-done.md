# PC Camera WYSIWYG Overlay

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“实时画面”新增固定画面框。
  - `未打开 / 连接中 / 已打开 / 画面偏暗 / 失败` 时，直接在画面框内显示状态和短提示；采样确认 `画面可见` 后隐藏遮罩，不遮挡真实视频帧。
- `pc-tools/workstation/src/styles.css`
  - 增加 16:9 camera preview frame 和状态遮罩样式。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认未打开、相机在线未打开、画面可见、画面偏暗四种状态的画面框行为。
- `docs/product/pc_tools_workstation.md`
  - 同步“实时画面”所见即所得遮罩口径。

## 验证结果

- `npm test`
  - 通过：2 个 test files，158 个 tests 全部通过。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 只读 7001 smoke：
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
  - 当前 camera readback 为 `status=ready`、`devices_status=loaded`、`preview_status=idle_not_started`；本轮前端会在画面框内显示未打开状态，不自动打开图传。

## 剩余风险

- 本轮只改善 PC 前端画面框呈现，没有自动打开 WebRTC，也没有调用 first-frame probe。
- 真实摄像头是否持续出画面仍以 operator 显式点击 `打开画面` 后的 WebRTC 像素采样为准。
- 本轮不证明 Nav2 路线执行、wheel raw L/R 非零或 delivery success。

# 2026-06-26 04:20 PC 相机首帧失败不被等待画面覆盖

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当上位机 summary 已归因为相机 source first-frame 失败，且浏览器 video 元素尚未绘出帧时，普通首屏保持 `失败 / 相机没有出画面，检查摄像头/视频线`。
  - 只有真实绘出帧并完成本地采样后，才进入画面可见/偏暗/已打开口径，避免 streaming 状态掩盖摄像头源失败。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 WebRTC track 到达但未绘出帧、同时 source first-frame 失败的组件测试，确认首屏不显示“等待画面”。
- `docs/product/pc_tools_workstation.md`
  - 记录相机 source first-frame 失败在普通首屏的 WYSIWYG 优先级。

## 验证结果

- 通过：`npm test -- -t "keeps camera source first-frame failure visible while streaming waits for a drawable frame"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 178 skipped (179)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-BHxcA7Ax.js 474.09 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 179 passed (179)`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node 90259 ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端状态和 mock WebRTC 测试，不触发真实 camera probe、manual、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需在 `0.0.0.0:7001` 打开画面，确认失败归因和实际摄像头/视频线状态一致。

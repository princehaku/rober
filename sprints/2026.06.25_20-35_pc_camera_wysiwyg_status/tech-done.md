# PC 实时画面 WYSIWYG 状态

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“实时画面”新增 `画面状态` 行，把未打开、相机在线但未打开、连接中、已打开待确认、画面可见、画面偏暗和失败状态明确翻译成普通用户可理解的文案。
  - 该状态只消费现有 camera summary 和本地视频帧采样结果，不自动打开摄像头、不触发 Nav2、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖未打开、相机在线但未打开、真实视频帧可见、近黑画面偏暗四类实时画面 WYSIWYG 文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏实时画面 WYSIWYG 状态口径和控制边界。

## 验证结果

- `npm test -- --testNamePattern "camera|plain user|实时画面|near-black|online"`：通过，2 个测试文件，9 个相关测试通过。
- `npm run lint`：通过。
- `npm test`：通过，2 个测试文件，167 个测试通过。
- `npm run build`：通过，完成 TypeScript 和 Vite production build。

## 剩余风险

- 本轮验证为 PC 本地 DOM/Mock 与构建验证，未打开真实摄像头、未做真实 WebRTC/HIL 视频链路验证。
- 本轮未触发真实小车控制；真实运动、Nav2 执行和摄像头现场画面仍需现场 operator 在 7001 页面按安全流程确认。

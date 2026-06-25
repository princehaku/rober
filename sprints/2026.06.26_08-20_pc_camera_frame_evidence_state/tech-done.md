# PC 实时画面帧证据状态

sprint_type: micro

## 实际改动

- PC 普通首屏实时画面框新增 `data-frame-state=已绘制帧/等待绘帧/未绑定/未观测`，把浏览器是否真的绘制出视频帧从业务状态 `画面可见/等待画面/未打开` 中拆出来。
- 真实 `<video>` 同步暴露 `data-frame-state`，并为已绘制帧、等待绘帧、未绑定/未观测补充稳定样式，避免“已连接但没出图”的状态在视觉合同里被混淆。
- 测试覆盖 `画面可见` 必须对应 `已绘制帧`，以及 `等待画面`、关闭后 `未打开` 的帧证据状态。
- 产品文档同步记录该展示边界：只影响 PC 前端呈现，不自动打开相机、不重试 WebRTC、不修改 Clash/端口、不执行 Nav2/manual/keyboard/stop/delivery，也不调用 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "starts and stops Camera Preview through workstation camera proxy while keeping control locked|keeps camera preview in waiting state until the browser draws a video frame"`，`2 passed | 190 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 产物生成成功。
- 通过：`npm test`，`192 passed`。
- 通过：全量测试改写的两个旧 smoke artifact `checked_at` 已恢复到原值，未纳入本轮改动。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 当前仍是 PC 前端/mock 合同验证；未触发真实小车运动，未做真实相机/WebRTC HIL。

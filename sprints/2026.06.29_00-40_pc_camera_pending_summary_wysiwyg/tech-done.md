# PC 共享画面 Pending Summary WYSIWYG Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：共享 MJPEG status pending 时，不再丢掉 summary 中已有的共享流事实；若 summary 显示上游已连接、已有视频边界或最近缓存帧，普通首屏先展示这些事实，同时继续声明“返回前不证明本页已出图”。
- `pc-tools/workstation/test/App.test.ts`：更新共享画面 pending 用例，锁定 summary 中的 2 个页面观看、上游已连接、缓存帧先显示，并继续断言不会触发 manual、free-roam、Nav2 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步记录共享画面 pending 状态保留 summary 事实的边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "shared camera status pending"`，结果 `1 passed (1)`，`1 passed | 201 skipped (202)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`350 passed (350)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 首屏只读展示，不触发真实摄像头、真实 WebRTC/MJPEG HIL 或真实小车运动。
- 若上位机 `/api/camera/mjpeg` 本身没有首帧，页面仍只能显示非独占/无首帧诊断，不能凭 summary 缓存事实证明本页已绘制实时帧。

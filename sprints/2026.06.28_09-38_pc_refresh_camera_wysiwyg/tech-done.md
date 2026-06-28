# PC 连接刷新同步共享画面状态

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `连接/刷新` 除了 summary、地图画面和雷达状态外，同步刷新共享 MJPEG status，避免实时画面卡继续显示旧观看人数、旧上游连接或旧失败原因。
- `pc-tools/workstation/test/App.test.ts`：扩展连接刷新测试，锁定刷新会额外读取 `/api/robot-control/camera/mjpeg/status`，同时不调用 camera offer、manual、Nav2 execute、free-roam start 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步说明画面 WYSIWYG 刷新口径。

## 验证结果

- `npm test -- --run test/App.test.ts -t "refreshes visible map, radar, and shared camera readback"`：通过，1 passed / 204 skipped。
- `git diff --check`：通过。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `npm test`：通过，2 files / 354 tests passed。

## 剩余风险

- 本轮只改 PC 只读刷新闭环，不发送真实 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实摄像头是否有画面仍取决于上位机 `/api/camera/mjpeg` 和 UVC 首帧；本轮保证普通刷新能及时读到共享预览事实，不证明硬件画面必定可见。
